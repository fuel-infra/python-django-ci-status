import time

from django.core.exceptions import ValidationError
from django.test import TestCase
from unittest import skip

from ci_system.models import CiSystem, Status
from ci_checks.models import Rule, RuleCheck


class RuleCheckTests(TestCase):

    def setUp(self):
        self.ci = CiSystem.objects.create(url='http://localhost/', name='CI')
        self.status = Status.objects.create(summary='Auto', ci_system=self.ci)
        self.rule = Rule.objects.create(
            name='kilo',
            rule_type=1,
            version='7.0',
            ci_system=self.ci)

    def test_string_representation(self):
        rule_check = RuleCheck(rule=self.rule, status_type=1)

        self.assertEqual(
            str(rule_check),
            'Success (ci: "CI", rule: "kilo", version: "7.0")')

    def test_created_with_valid_fields(self):
        before = RuleCheck.objects.count()
        rule_check = RuleCheck.objects.create(rule=self.rule)

        rule_check.full_clean()
        self.assertEqual(RuleCheck.objects.count(), before + 1)

    def test_not_created_without_required_fields(self):
        rule_check = RuleCheck()
        with self.assertRaises(ValidationError):
            rule_check.full_clean()

    def test_checks_types_are_predefined(self):
        rule_check = RuleCheck(rule=self.rule,
                               status_type=10)
        with self.assertRaises(ValidationError):
            rule_check.full_clean()

    def test_checks_ordered_by_creation_date_desc(self):
        RuleCheck.objects.create(rule=self.rule, status_type=1)
        time.sleep(1)  # timestamps in testing enviroment lacks of miliseconds
        RuleCheck.objects.create(rule=self.rule, status_type=2)

        sorted_checks = (
            RuleCheck.objects
            .values_list('created_at', flat=True)
            .order_by('-created_at')
        )

        actual_checks = RuleCheck.objects.values_list('created_at', flat=True)

        self.assertEqual(map(str, actual_checks), map(str, sorted_checks))

    def test_checks_removed_when_status_removed(self):
        status = Status.objects.create(summary='Auto', ci_system=self.ci)
        rule_check = RuleCheck.objects.create(rule=self.rule)
        rule_check.status.add(status)
        before = RuleCheck.objects.count()

        status.delete()
        self.assertEqual(RuleCheck.objects.count(), before - 1)

    def test_checks_removed_when_rule_removed(self):
        rule = Rule.objects.create(
            name='kilo',
            rule_type=2,
            ci_system=self.ci,
            version='7.0')
        RuleCheck.objects.create(rule=rule)
        before = RuleCheck.objects.count()

        rule.delete()
        self.assertEqual(RuleCheck.objects.count(), before - 1)

    @skip('This functionality was deprecated')
    def test_could_return_status_type_for_check_result(self):
        self.assertEqual(RuleCheck.status_type_by(True), Status.STATUS_SUCCESS)
        self.assertEqual(RuleCheck.status_type_by(False), Status.STATUS_FAIL)
        self.assertEqual(RuleCheck.status_type_by(None), Status.STATUS_SKIP)
        self.assertEqual(RuleCheck.status_type_by(), Status.STATUS_SKIP)
