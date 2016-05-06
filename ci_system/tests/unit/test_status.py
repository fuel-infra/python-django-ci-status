from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.test import TestCase

from ci_system.constants import (
    STATUS_TYPE_CHOICES,
    STATUS_SUCCESS,
    STATUS_FAIL,
    STATUS_SKIP,
)
from ci_system.models import CiSystem, Status
from ci_checks.models import Rule, RuleCheck


class StatusTests(TestCase):

    def setUp(self):
        self.summary = 'all down'
        self.ci = CiSystem.objects.create(url='http://localhost/', name='CI')
        self.status_type = STATUS_SUCCESS

    def _make_status(self, **kwargs):
        default_props = {
            'summary': self.summary,
            'status_type': self.status_type,
            'ci_system': self.ci,
        }
        default_props.update(kwargs)

        return Status(**default_props)

    def test_string_representation(self):
        status = self._make_status()
        status.save()
        self.assertEqual(
            str(status),
            'Success (ci: "CI")'
        )

    def test_could_display_a_text_status(self):
        status = self._make_status()
        status.save()
        self.assertEqual(status.status_text(), 'Success')

    def test_status_mapped_to_text_value(self):
        for status_type, text in STATUS_TYPE_CHOICES:
            self.assertEqual(
                Status.text_for_type(status_type), text)

        self.assertEqual(Status.text_for_type(None), 'Aborted')

    def test_created_with_valid_fields(self):
        Status.objects.create(
            summary=self.summary, ci_system=self.ci).full_clean()

    def test_not_created_without_required_fields(self):
        with self.assertRaises(ValidationError):
            Status().full_clean()

    def test_status_types_are_predefined(self):
        with self.assertRaises(ValidationError):
            self._make_status(status_type=10).full_clean()

    def test_statuses_ordered_by_creation_date_desc(self):
        Status.objects.create(summary=self.summary,
                              ci_system=self.ci)
        Status.objects.create(summary=self.summary,
                              ci_system=self.ci,
                              status_type=2)

        sorted_statuses = (
            Status.objects
            .values_list('created_at', flat=True)
            .order_by('created_at', 'id')
        )
        actual_statuses = Status.objects.values_list('created_at', flat=True)

        self.assertEqual(map(str, actual_statuses), map(str, sorted_statuses))

    def test_statuses_removed_when_ci_removed(self):
        ci = CiSystem.objects.create(url='http://example.com/')
        Status.objects.create(summary=self.summary, ci_system=ci)
        before = Status.objects.count()

        ci.delete()
        self.assertEqual(Status.objects.count(), before - 1)

    def test_status_knows_its_rule_checks(self):
        """Shortcut method to retrieve the rulecheks for status"""
        status = Status.objects.create(summary=self.summary,
                                       ci_system=self.ci,
                                       status_type=1)

        self.assertEqual(list(status.rule_checks()), [])

        rule = Rule.objects.create(name='kilo', ci_system=self.ci)
        status.rulecheck_set.create(rule=rule)

        self.assertEqual(status.rule_checks().count(), 1)

    def test_knows_which_status_assign_based_on_rule_checks(self):
        """Status assigns based on rule checks results types"""
        self.assertEqual(
            Status.get_type_by_check_results(set([1, 1, 1])), STATUS_SUCCESS)
        self.assertEqual(
            Status.get_type_by_check_results(set([1, 2, 1])), STATUS_FAIL)
        self.assertEqual(
            Status.get_type_by_check_results(set([1, None, 1])), STATUS_SKIP)

    def test_could_be_marked_as_manual(self):
        Status.objects.create(
            summary=self.summary,
            ci_system=self.ci,
            is_manual=True
        ).full_clean()

    def test_status_author(self):
        """Status could be assigned automatically or by user"""
        status = self._make_status(is_manual=True)
        status.save()
        self.assertEqual(status.author_username(), 'Inactive User')

        status.user = User.objects.create(username='Toast')
        status.save()
        self.assertEqual(status.author_username(), 'Toast')

        status = self._make_status()
        status.save()
        self.assertEqual(status.author_username(), 'Assigned Automatically')
        status.user = User.objects.create(username='Tasty')
        self.assertEqual(status.author_username(), 'Tasty')

    def test_status_aware_of_its_failed_rule_checks(self):
        """Shortcut method to get failed rule checks (for UI)"""
        status = Status.objects.create(summary=self.summary, ci_system=self.ci)
        self.assertEqual(list(status.failed_rule_checks()), [])

        rule = Rule.objects.create(name='kilo', ci_system=self.ci)
        status.rulecheck_set.create(rule=rule)
        self.assertEqual(status.failed_rule_checks().count(), 0)

        status.rulecheck_set.create(
            rule=rule, status_type=STATUS_FAIL
        )
        self.assertEqual(status.failed_rule_checks().count(), 1)

    def test_status_could_delete_unused_rule_checks_on_delete(self):
        """As each RuleCheck could be shared between statuses we want to be
           sure that one status deletion will not delete the RuleChecks
           used in other but will delete unused ones.
        """
        status1 = self._make_status()
        status1.save()
        status2 = self._make_status()
        status2.save()

        rule = Rule.objects.create(name='kilo', ci_system=self.ci)
        rule_check1 = RuleCheck.objects.create(rule=rule)
        rule_check2 = RuleCheck.objects.create(rule=rule)

        status1.rulecheck_set.add(rule_check1, rule_check2)
        status2.rulecheck_set.add(rule_check2)

        status1.delete()
        self.assertEqual(status2.rule_checks().count(), 1)

        status2.delete()
        self.assertEqual(RuleCheck.objects.count(), 0)
