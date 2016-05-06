from django.core.exceptions import ValidationError
from django.test import TestCase

from ci_system import constants
from ci_system.models import CiSystem, ProductCi, ProductCiStatus
from ci_checks.models import RuleCheck


VALID_URL = 'http://localhost/'


class ProductStatusTests(TestCase):

    def test_string_representation(self):
        ps = ProductCi(name='First')
        self.assertEqual(str(ps), 'First')

    def test_must_be_uniq_with_version(self):
        ProductCi.objects.create(name='1')

        second = ProductCi(name='1')
        with self.assertRaises(ValidationError):
            second.full_clean()

        second = ProductCi(name='1', version='v1')
        second.full_clean()

    def test_created_with_valid_fields(self):
        ProductCi.objects.create(
            name='1', version='v1', is_active=True
        ).full_clean()

    def test_not_created_without_required_fields(self):
        with self.assertRaises(ValidationError):
            ProductCi().full_clean()

    def test_valid_default_values(self):
        ps = ProductCi.objects.create(name='first')

        self.assertEqual(ps.version, '')
        self.assertEqual(ps.is_active, False)

    def test_aware_of_rule_checks(self):
        """The is a special shortcut method to retrive status rule checks"""
        ps = ProductCi.objects.create(name='first')
        rules = _create_rules(3)
        ps.rules.add(*rules)

        rule_checks = [
            RuleCheck.objects.create(
                rule=r, status_type=constants.STATUS_SUCCESS
            ) for r in rules
        ]
        self.assertEqual(list(ps.latest_rule_checks()), rule_checks)
        self.assertEqual(
            ps.latest_rule_checks()[0].status_type, constants.STATUS_SUCCESS
        )

        rule_checks_last = [
            RuleCheck.objects.create(
                rule=r, status_type=constants.STATUS_FAIL
            ) for r in rules
        ]
        self.assertEqual(list(ps.latest_rule_checks()), rule_checks_last)
        self.assertEqual(
            ps.latest_rule_checks()[0].status_type, constants.STATUS_FAIL
        )

    def test_only_active_rules_calculated(self):
        """Deactivated rules are skipped during new status assignment"""
        ps = ProductCi.objects.create(name='first')
        rules = _create_rules(2, active=False)  # two inactive
        rules.append(_create_rules())  # one active
        ps.rules.add(*rules)

        for r in rules:
            RuleCheck.objects.create(
                rule=r, status_type=constants.STATUS_SUCCESS
            )
        self.assertEqual(len(ps.latest_rule_checks()), 1)

    def test_none_checks_are_handled(self):
        """We are fine if there was not rule checks yet"""
        ps = ProductCi.objects.create(name='first')
        rules = _create_rules(3)
        ps.rules.add(*rules)

        self.assertEqual(ps.latest_rule_checks(), [])

    def test_deactivate_previous_products(self):
        """Test for method the deactivates previous unused Product's"""
        previous = {('p1', 'v1'), ('p2',  'v2'), ('p3', 'v3')}
        for name, ver in previous:
            ProductCi.objects.create(name=name, version=ver, is_active=True)

        new = {('p4', 'v4'), ('p1',  'v1'), ('p2', 'v22')}
        ProductCi.deactivate_previous_products(previous, new)
        self.assertEqual(ProductCi.objects.filter(is_active=True).count(), 1)

    def test_update_status(self):
        """New ProductCiStatus assignment test"""
        ps = ProductCi.objects.create(name='first')
        rules = _create_rules(3)
        ps.rules.add(*rules)

        for r in rules:
            RuleCheck.objects.create(
                rule=r, status_type=constants.STATUS_SUCCESS
            )

        ps.set_status()
        self.assertEqual(ProductCiStatus.objects.count(), 1)

    def test_update_status_only_for_active_rules(self):
        """New ProductCiStatus assigns only for active rules"""
        ps = ProductCi.objects.create(name='first')
        rules = _create_rules(2, active=False)
        ps.rules.add(*rules)

        for r in rules:
            RuleCheck.objects.create(
                rule=r, status_type=constants.STATUS_SUCCESS
            )

        ps.set_status()
        self.assertEqual(ProductCiStatus.objects.count(), 0)

    def test_update_status_checks_for_latest_checks_only(self):
        """ProductCiStatus assigns only by the latest checks for each rule"""
        ps = ProductCi.objects.create(name='first')
        rules = _create_rules(3)
        ps.rules.add(*rules)

        for r in rules:
            RuleCheck.objects.create(
                rule=r, status_type=constants.STATUS_SUCCESS
            )

        ps.set_status()
        self.assertEqual(
            ProductCiStatus.objects.last().status_type,
            constants.STATUS_SUCCESS
        )

        for r in rules:
            RuleCheck.objects.create(rule=r, status_type=constants.STATUS_FAIL)

        ps.set_status()
        self.assertEqual(
            ProductCiStatus.objects.last().status_type, constants.STATUS_FAIL
        )

    def test_update_status_skips_absent_rule_checks(self):
        """Check that rules without rule checks are ignored when
           setting status
        """
        ps = ProductCi.objects.create(name='first')
        rules = _create_rules(3)
        ps.rules.add(*rules)

        RuleCheck.objects.create(
            rule=rules[0], status_type=constants.STATUS_FAIL
        )  # only one

        ps.set_status()
        self.assertEqual(
            ProductCiStatus.objects.first().status_type, constants.STATUS_FAIL
        )

    def test_update_status_assigns_status_according_to_types(self):
        """Each status calculated by the statuses of rule checks related"""
        ps = ProductCi.objects.create(name='first')
        rules = _create_rules(3)
        ps.rules.add(*rules)

        for r in rules:
            RuleCheck.objects.create(
                rule=r, status_type=constants.STATUS_SUCCESS
            )

        ps.set_status()
        self.assertEqual(
            ProductCiStatus.objects.first().status_type,
            constants.STATUS_SUCCESS
        )
        ProductCiStatus.objects.first().delete()

        RuleCheck.objects.create(
            rule=rules[0], status_type=constants.STATUS_FAIL)  # one fail
        ps.set_status()
        self.assertEqual(
            ProductCiStatus.objects.first().status_type, constants.STATUS_FAIL
        )
        ProductCiStatus.objects.first().delete()

        RuleCheck.objects.create(
            rule=rules[0],
            status_type=constants.STATUS_IN_PROGRESS)  # one progress
        ps.set_status()
        self.assertEqual(
            ProductCiStatus.objects.first().status_type,
            constants.STATUS_IN_PROGRESS
        )
        ProductCiStatus.objects.first().delete()

        RuleCheck.objects.create(
            rule=rules[0], status_type=constants.STATUS_SKIP)  # one skip
        ps.set_status()
        self.assertEqual(
            ProductCiStatus.objects.first().status_type, constants.STATUS_SKIP)
        ProductCiStatus.objects.first().delete()

        for r in rules:
            RuleCheck.objects.create(
                rule=r, status_type=constants.STATUS_ERROR)  # all errors

        ps.set_status()
        self.assertEqual(
            ProductCiStatus.objects.first().status_type,
            constants.STATUS_ERROR
        )

    def test_update_status_caches_previous_status(self):
        """Not changed status does not create new record and keep timestamp"""
        ps = ProductCi.objects.create(name='first')
        rules = _create_rules(3)
        ps.rules.add(*rules)

        for r in rules:
            RuleCheck.objects.create(
                rule=r, status_type=constants.STATUS_SUCCESS
            )
        ps.set_status()

        for r in rules:
            RuleCheck.objects.create(
                rule=r, status_type=constants.STATUS_SUCCESS)
        ps.set_status()
        self.assertEqual(ProductCiStatus.objects.count(), 1)  # was not changed

        RuleCheck.objects.create(
            rule=rules[0], status_type=constants.STATUS_IN_PROGRESS
        )
        ps.set_status()
        self.assertEqual(ProductCiStatus.objects.count(), 1)  # was not changed

        RuleCheck.objects.create(
            rule=rules[0], status_type=constants.STATUS_FAIL)
        ps.set_status()
        self.assertEqual(ProductCiStatus.objects.count(), 2)  # changed

    def test_aware_of_its_current_status(self):
        """There is a shortcut method to retrieve the latest status"""
        ps = ProductCi.objects.create(name='first')
        rules = _create_rules(3)
        ps.rules.add(*rules)

        self.assertIsNone(ps.current_status())

        for r in rules:
            RuleCheck.objects.create(
                rule=r, status_type=constants.STATUS_SUCCESS
            )
        ps.set_status()
        self.assertEqual(
            ps.current_status().status_type, constants.STATUS_SUCCESS)

        RuleCheck.objects.create(
            rule=rules[0], status_type=constants.STATUS_FAIL
        )
        ps.set_status()
        self.assertEqual(
            ps.current_status().status_type, constants.STATUS_FAIL)

    def test_aware_of_its_current_status_type(self):
        """There is a shortcut method to retrieve the latest status type"""
        ps = ProductCi.objects.create(name='first')
        rules = _create_rules(3)
        ps.rules.add(*rules)

        for r in rules:
            RuleCheck.objects.create(
                rule=r, status_type=constants.STATUS_SUCCESS
            )
        ps.set_status()
        self.assertEqual(ps.current_status_type(), constants.STATUS_SUCCESS)

        RuleCheck.objects.create(
            rule=rules[0], status_type=constants.STATUS_FAIL
        )
        ps.set_status()
        self.assertEqual(ps.current_status_type(), constants.STATUS_FAIL)

    def test_new_product_has_skipped_status(self):
        """ProductCi has Skipped status until it gets first checks results"""
        ps = ProductCi.objects.create(name='first')
        self.assertEqual(ps.current_status_type(), constants.STATUS_SKIP)

    def test_aware_of_its_current_status_text(self):
        """ProductCiStatus correctly mapped to its string representation"""
        ps = ProductCi.objects.create(name='first')
        rules = _create_rules(2)
        ps.rules.add(*rules)

        for r in rules:
            RuleCheck.objects.create(
                rule=r, status_type=constants.STATUS_FAIL
            )
        ps.set_status()
        self.assertEqual(ps.current_status_text(), 'Failed')

    def test_active_status_time_calculation(self):
        """Unchanged status keeps its last_changed timestamp"""
        ps = ProductCi.objects.create(name='first')
        rules = _create_rules(2)
        ps.rules.add(*rules)

        self.assertIsNone(ps.active_status_time())

        for r in rules:
            RuleCheck.objects.create(
                rule=r, status_type=constants.STATUS_FAIL
            )
        ps.set_status()
        self.assertEqual(ps.active_status_time(), u'0\xa0minutes')

    def test_active_status_time_calculation_with_version(self):
        """Unchanged status keeps its last_changed timestamp"""
        ps = ProductCi.objects.create(name='first', version='old')
        rules = _create_rules(2)
        ps.rules.add(*rules)

        for r in rules:
            RuleCheck.objects.create(
                rule=r, status_type=constants.STATUS_SUCCESS
            )
        ps.set_status()
        self.assertEqual(ps.active_status_time(version='old'), u'0\xa0minutes')

        ps.version = 'new'
        ps.save()

        self.assertIsNone(ps.active_status_time(version='new'))

        for r in rules:
            RuleCheck.objects.create(
                rule=r, status_type=constants.STATUS_FAIL
            )
        ps.set_status()
        self.assertEqual(ps.active_status_time(version='new'), u'0\xa0minutes')


def _create_rules(num=1, active=True):
    ci, _ = CiSystem.objects.get_or_create(url=VALID_URL)

    if num == 1:
        return ci.rule_set.create(name='test_job', is_active=active)
    else:
        rules = []
        for n in range(1, num):
            rules.append(ci.rule_set.create(
                name='test_job_' + str(n),
                is_active=active)
            )
        return rules
