from django.core.exceptions import ValidationError
from django.test import TestCase
from unittest import skip

from ci_system import constants
from ci_system.models import CiSystem, Status
from ci_checks.models import Rule


class StatusTests(TestCase):

    def setUp(self):
        self.summary = 'all down'
        self.ci = CiSystem.objects.create(url='http://localhost/', name='CI')

    def test_string_representation(self):
        status = Status(
            summary=self.summary,
            status_type=1,
            ci_system=self.ci)

        self.assertEqual(
            str(status),
            'Success (ci: "CI")'
        )

    def test_created_with_valid_fields(self):
        before = Status.objects.count()
        status = Status.objects.create(summary=self.summary, ci_system=self.ci)

        status.full_clean()
        self.assertEqual(Status.objects.count(), before + 1)

    def test_not_created_without_required_fields(self):
        status = Status()

        with self.assertRaises(ValidationError):
            status.full_clean()

    def test_status_types_are_predefined(self):
        status = Status(summary=self.summary,
                        ci_system=self.ci,
                        status_type=10)

        with self.assertRaises(ValidationError):
            status.full_clean()

    def test_statuses_ordered_by_creation_date_desc(self):
        Status.objects.create(summary=self.summary,
                              ci_system=self.ci)
        Status.objects.create(summary=self.summary,
                              ci_system=self.ci,
                              status_type=2)

        sorted_statuses = (
            Status.objects
            .values_list('created_at', flat=True)
            .order_by('-created_at')
        )

        actual_statuses = Status.objects.values_list('created_at', flat=True)

        self.assertEqual(map(str, actual_statuses), map(str, sorted_statuses))

    def test_statuses_removed_when_ci_removed(self):
        ci = CiSystem.objects.create(url='http://example.com/')
        Status.objects.create(summary=self.summary, ci_system=ci)
        before = Status.objects.count()

        ci.delete()
        self.assertEqual(Status.objects.count(), before - 1)

    @skip('This functionality was deprecated')
    def test_status_has_boolean_representation(self):
        status = Status.objects.create(summary=self.summary,
                                       ci_system=self.ci,
                                       status_type=1)
        self.assertEqual(status.status_bool(), True)

        status = Status.objects.create(summary=self.summary,
                                       ci_system=self.ci,
                                       status_type=2)
        self.assertEqual(status.status_bool(), False)

        status = Status.objects.create(summary=self.summary,
                                       ci_system=self.ci,
                                       status_type=3)
        self.assertEqual(status.status_bool(), None)

        status = Status.objects.create(summary=self.summary,
                                       ci_system=self.ci,
                                       status_type=4)
        self.assertEqual(status.status_bool(), None)

    def test_status_knows_its_rule_checks(self):
        status = Status.objects.create(summary=self.summary,
                                       ci_system=self.ci,
                                       status_type=1)

        self.assertEqual(list(status.rule_checks()), [])

        rule = Rule.objects.create(name='kilo', ci_system=self.ci)
        status.rulecheck_set.create(rule=rule)

        self.assertEqual(status.rule_checks().count(), 1)

    def test_knows_which_status_assign_based_on_rule_checks(self):
        self.assertEqual(
            Status.get_type_by_check_results(set([1, 1, 1])),
            constants.STATUS_SUCCESS
        )
        self.assertEqual(
            Status.get_type_by_check_results(set([1, 2, 1])),
            constants.STATUS_FAIL
        )
        self.assertEqual(
            Status.get_type_by_check_results(set([1, None, 1])),
            constants.STATUS_SKIP
        )

    def test_could_be_marked_as_manual(self):
        status = Status.objects.create(summary=self.summary,
                                       ci_system=self.ci,
                                       is_manual=True)
        status.full_clean()
