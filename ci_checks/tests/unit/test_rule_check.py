from django.core.exceptions import ValidationError
from django.test import TestCase

from ci_system.models import CiSystem, Status
from ci_checks.models import Rule, RuleCheck


class RuleCheckTests(TestCase):

    def setUp(self):
        self.ci = CiSystem.objects.create(url='http://localhost/', name='CI')
        self.status = Status.objects.create(summary='Auto', ci_system=self.ci)
        self.rule = Rule.objects.create(
            name='kilo',
            ci_system=self.ci,
        )

    def test_string_representation(self):
        rule_check = RuleCheck(rule=self.rule, status_type=1)

        self.assertEqual(
            str(rule_check),
            'Success (ci: "CI", rule: "kilo")')

    def test_created_with_valid_fields(self):
        RuleCheck.objects.create(rule=self.rule).full_clean()

    def test_not_created_without_required_fields(self):
        with self.assertRaises(ValidationError):
            RuleCheck().full_clean()

    def test_checks_types_are_predefined(self):
        with self.assertRaises(ValidationError):
            RuleCheck(rule=self.rule, status_type=10).full_clean()

    def test_checks_ordered_by_creation_date_desc(self):
        RuleCheck.objects.create(rule=self.rule, status_type=1)
        RuleCheck.objects.create(rule=self.rule, status_type=2)

        sorted_checks = (
            RuleCheck.objects
            .values_list('created_at', flat=True)
            .order_by('created_at', 'id')
        )

        actual_checks = RuleCheck.objects.values_list('created_at', flat=True)

        self.assertEqual(map(str, actual_checks), map(str, sorted_checks))

    def test_checks_removed_when_status_removed(self):
        """Make sure that if we delete a Status its checks deletes as well.
           We no need to have checks without a status.
        """
        status = Status.objects.create(summary='Auto', ci_system=self.ci)
        rule_check = RuleCheck.objects.create(rule=self.rule)
        rule_check.status.add(status)
        before = RuleCheck.objects.count()

        status.delete()
        self.assertEqual(RuleCheck.objects.count(), before - 1)

    def test_checks_removed_when_rule_removed(self):
        """Make sure that if we delete a Rule its checks deletes as well.
           Checks without assigned rule just have no any sense.
        """
        rule = Rule.objects.create(
            name='kilo',
            rule_type=2,
            ci_system=self.ci,
        )
        RuleCheck.objects.create(rule=rule)
        before = RuleCheck.objects.count()

        rule.delete()
        self.assertEqual(RuleCheck.objects.count(), before - 1)
