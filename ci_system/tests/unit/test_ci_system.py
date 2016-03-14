import mock
import os

from django.core.exceptions import ValidationError
from django.test import TestCase
from unittest import skip
import jenkins

from ci_system import constants
from ci_system.models import CiSystem, Status
from ci_checks.models import Rule, RuleCheck


VALID_URL = 'http://localhost/'
FIXTURES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'fixtures'
)
SEED_FILE_PATH = os.path.join(
    FIXTURES_DIR,
    'seeds.yaml'
)
INVALID_SEED_FILE_PATH = os.path.join(
    FIXTURES_DIR,
    'invalid_seeds.yaml'
)


class CiSystemTests(TestCase):

    def test_string_representation(self):
        name = 'Product CI'
        ci = CiSystem(url=VALID_URL, name=name)
        self.assertEqual(str(ci), ci.name)

    @skip('We have removed this functionality')
    def test_ci_name_is_url_by_default(self):
        ci = CiSystem.objects.create(url=VALID_URL)
        self.assertEqual(ci.url, ci.name)

    def test_name_must_be_uniq(self):
        first = CiSystem.objects.create(url=VALID_URL, name='1')
        first.full_clean()

        second = CiSystem(url=VALID_URL + 'x', name='1')
        with self.assertRaises(ValidationError):
            second.full_clean()

    def test_created_with_valid_fields(self):
        before = CiSystem.objects.count()
        ci = CiSystem.objects.create(url=VALID_URL, name='1')

        ci.full_clean()
        self.assertEqual(CiSystem.objects.count(), before + 1)

    def test_not_created_without_required_fields(self):
        ci = CiSystem()

        with self.assertRaises(ValidationError):
            ci.full_clean()

    def test_url_must_be_uniq(self):
        first = CiSystem.objects.create(url=VALID_URL, name='1')
        first.full_clean()

        second = CiSystem(url=VALID_URL)
        with self.assertRaises(ValidationError):
            second.full_clean()

    def test_valid_default_values(self):
        ci = CiSystem.objects.create(url=VALID_URL)

        self.assertEqual(ci.username, '')
        self.assertEqual(ci.password, '')
        self.assertEqual(ci.is_active, False)

    @skip('Skipped to reimplement with minimal length not maximum')
    def test_length_restrictions_are_set(self):
        ci = CiSystem(url=VALID_URL, name='1')
        ci.username = 'a' * 51

        with self.assertRaises(ValidationError):
            ci.full_clean()

        ci.username = 'username'
        ci.password = 'a' * 101
        with self.assertRaises(ValidationError):
            ci.full_clean()

        ci.name = 'a' * 51
        with self.assertRaises(ValidationError):
            ci.full_clean()

        ci.name = 'Fine name'
        ci.password = 'password'
        ci.full_clean()

    def test_aware_of_its_rules(self):
        ci = CiSystem.objects.create(url=VALID_URL)
        rule = Rule.objects.create(name='test_job', ci_system=ci)

        self.assertEqual(list(ci.rule_set.all()), [rule])

    def test_name_is_required_and_uniq(self):
        ci = CiSystem(url=VALID_URL)

        with self.assertRaises(ValidationError):
            ci.full_clean()

        CiSystem.objects.create(url=VALID_URL, name='1')
        ci2 = CiSystem(url=VALID_URL + 'x', name='1')

        with self.assertRaises(ValidationError):
            ci2.full_clean()

        before = CiSystem.objects.count()
        ci2 = CiSystem.objects.create(url=VALID_URL + 'x', name='2')
        self.assertEqual(CiSystem.objects.count() - 1, before)

    def test_aware_of_latest_status(self):
        ci = CiSystem.objects.create(url=VALID_URL, name='1')
        ci.status_set.create(summary='Last')

        self.assertEqual(ci.latest_status().summary, 'Last')

        ci = CiSystem.objects.create(url=VALID_URL + 'x', name='2')
        self.assertEqual(ci.latest_status(), None)

    @mock.patch.object(Rule, 'check_job_rule')
    def test_ci_status_calculated_by_single_rule(self, _job_mock):
        ci = CiSystem.objects.create(url=VALID_URL)

        job_rule = ci.rule_set.create(
            name='kilo',
            is_active=True,
            version='7.0'
        )

        job_rule_check = RuleCheck(
            rule=job_rule,
            build_number=547,
            status_type=2,
        )
        _job_mock.return_value = job_rule_check

        new_status = ci.check_the_status()
        self.assertEqual(new_status.status_type, 2)
        self.assertEqual(
            new_status.last_changed_at,
            job_rule_check.created_at
        )

        ci = CiSystem.objects.create(url=VALID_URL + 'test', name='test')
        job_rule = ci.rule_set.create(
            name='neutron',
            is_active=True,
            version='7.0'
        )

        job_rule_check = RuleCheck(
            rule=job_rule,
            build_number=547,
            status_type=1,
        )
        _job_mock.return_value = job_rule_check

        new_status = ci.check_the_status()
        self.assertEqual(new_status.status_type, 1)
        self.assertEqual(
            new_status.last_changed_at,
            job_rule_check.created_at
        )

    @mock.patch.object(Rule, 'check_view_rule')
    @mock.patch.object(Rule, 'check_job_rule')
    def test_ci_status_calculated_by_multiple_rules(self,
                                                    _job_mock,
                                                    _view_mock):
        ci = CiSystem.objects.create(url=VALID_URL)
        job_rule = ci.rule_set.create(
            name='neutron',
            is_active=True,
            version='7.0'
        )
        view_rule = ci.rule_set.create(
            name='kilo',
            rule_type=2,
            is_active=True,
            version='7.0'
        )

        job_rule_check = RuleCheck(
            rule=job_rule,
            build_number=547,
            status_type=1,
        )
        _job_mock.return_value = job_rule_check
        view_rule_check = RuleCheck(
            rule=view_rule,
            build_number=548,
            status_type=1,
        )
        _view_mock.return_value = view_rule_check

        new_status = ci.check_the_status()
        self.assertEqual(new_status.status_type, 1)  # all green, overall too
        self.assertEqual(
            new_status.last_changed_at,
            max(job_rule_check.created_at, view_rule_check.created_at)
        )

        ci = CiSystem.objects.create(url=VALID_URL + 'test', name='test')
        job_rule = ci.rule_set.create(
            name='neutron',
            is_active=True,
            version='7.0'
        )
        view_rule = ci.rule_set.create(
            name='kilo',
            rule_type=2,
            is_active=True,
            version='7.0'
        )

        job_rule_check = RuleCheck(
            rule=job_rule,
            build_number=547,
            status_type=2,
        )
        _job_mock.return_value = job_rule_check
        view_rule_check = RuleCheck(
            rule=view_rule,
            build_number=548,
            status_type=1,
        )
        _view_mock.return_value = view_rule_check

        new_status = ci.check_the_status()
        self.assertEqual(new_status.status_type, 2)  # one fail, overall fail
        self.assertEqual(
            new_status.last_changed_at,
            max(job_rule_check.created_at, view_rule_check.created_at)
        )

    @mock.patch.object(Rule, 'check_job_rule')
    def test_ci_doesnot_change_status_twice_but_tracks_rulechecks(self,
                                                                  _job_mock):
        ci = CiSystem.objects.create(url=VALID_URL)
        before = (Status.objects.count(), RuleCheck.objects.count())

        rule = ci.rule_set.create(
            name='neutron',
            is_active=True,
            version='7.0'
        )
        rule_check = RuleCheck(
                rule=rule,
                build_number=547,
                status_type=1,
        )
        _job_mock.return_value = rule_check
        new_status = ci.check_the_status()

        self.assertEqual(new_status.status_type, 1)
        self.assertEqual(
            new_status.last_changed_at,
            rule_check.created_at
        )
        self.assertEqual(
            (Status.objects.count() - 1, RuleCheck.objects.count() - 1),
            before
        )

        _job_mock.return_value = RuleCheck.objects.last()  # no new results
        previous_status = ci.check_the_status()

        self.assertEqual(previous_status, new_status)  # status not changed
        self.assertEqual(
            (Status.objects.count() - 1, RuleCheck.objects.count() - 1),
            before
        )  # as well as new records were not created

        rule_check = RuleCheck(
                rule=rule,
                build_number=548,
                status_type=2,
        )  # new build comes in
        _job_mock.return_value = rule_check
        last_status = ci.check_the_status()

        self.assertEqual(last_status.status_type, 2)
        self.assertEqual(
            last_status.last_changed_at,
            rule_check.created_at
        )
        self.assertEqual(
            (Status.objects.count() - 2, RuleCheck.objects.count() - 2),
            before
        )  # new records created

    @mock.patch.object(Rule, 'check_job_rule')
    def test_ci_status_saves_all_rule_checks(self, _job_mock):
        ci = CiSystem.objects.create(url=VALID_URL)
        before = RuleCheck.objects.count()

        rule = ci.rule_set.create(
            name='kilo',
            is_active=True,
            version='7.0'
        )
        rule_check = RuleCheck(
                rule=rule,
                build_number=547,
                status_type=1,
        )
        _job_mock.return_value = rule_check
        status = ci.check_the_status()
        last_rule_check = RuleCheck.objects.last()

        self.assertEqual(RuleCheck.objects.count(), before + 1)
        self.assertEqual(last_rule_check.status.first(), status)
        self.assertEqual(last_rule_check.status_type, constants.STATUS_SUCCESS)

    def test_ci_has_own_jenkins_server_object(self):
        ci = CiSystem.objects.create(url=VALID_URL)
        self.assertIs(type(ci.server), jenkins.Jenkins)

    def test_ci_server_object_is_cached(self):
        ci = CiSystem.objects.create(url=VALID_URL)
        with mock.patch.object(
            jenkins.Jenkins, '__init__',
            return_value=None
        ) as m:
            ci.server
            ci.server

        m.assert_called_once_with(VALID_URL)

    def test_could_be_marked_with_sticky_failure(self):
        ci = CiSystem.objects.create(
            url=VALID_URL, sticky_failure=True, name='1')
        ci.full_clean()

    @mock.patch.object(Rule, 'check_job_rule')
    def test_product_ci_fail_status_could_be_changed_only_manually(
        self, _job_mock
    ):
        # success --> success
        ci = CiSystem.objects.create(url=VALID_URL, sticky_failure=True)
        Status.objects.create(summary='Success',
                              ci_system=ci,
                              status_type=1)

        job_rule = ci.rule_set.create(
            name='kilo',
            is_active=True,
            version='7.0'
        )
        job_rule_check = RuleCheck(
            rule=job_rule,
            build_number=547,
            status_type=1,
        )
        _job_mock.return_value = job_rule_check

        new_status = ci.check_the_status()
        self.assertEqual(new_status.status_type, 1)
        self.assertEqual(ci.status_set.count(), 2)

        # fail -x-> success
        ci = CiSystem.objects.create(
            url=VALID_URL + 'x',
            sticky_failure=True,
            name='x')
        Status.objects.create(summary='Fail',
                              ci_system=ci,
                              status_type=2)

        job_rule = ci.rule_set.create(
            name='neutron',
            is_active=True,
            version='7.0'
        )
        job_rule_check = RuleCheck(
            rule=job_rule,
            build_number=547,
            status_type=1,
        )
        _job_mock.return_value = job_rule_check

        new_status = ci.check_the_status()
        self.assertEqual(new_status.status_type, 2)
        self.assertEqual(
            new_status.summary,
            '`FAIL` status on CI with `sticky_failure` set to `True` '
            'could not be changed automatically.'
        )

        # fail --> success for not product ci's
        ci = CiSystem.objects.create(url=VALID_URL + 'y', name='y')
        Status.objects.create(summary='Fail',
                              ci_system=ci,
                              status_type=2)

        job_rule = ci.rule_set.create(
            name='neutron2',
            is_active=True,
            version='7.0'
        )
        job_rule_check = RuleCheck(
            rule=job_rule,
            build_number=547,
            status_type=1,
        )
        _job_mock.return_value = job_rule_check

        new_status = ci.check_the_status()
        self.assertEqual(new_status.status_type, 1)

    def test_could_parse_a_valid_seed_file(self):
        seeds = CiSystem.parse_seeds_file(SEED_FILE_PATH)
        self.assertEqual(
            next(
                (ci['url']
                 for ci in seeds['ci_systems']
                 if ci['name'] == 'Product CI:'),
                None),
            'https://product-ci.abc.net/')

    def test_seed_wrong_path_could_not_be_parsed(self):
        self.assertIs(None, CiSystem.parse_seeds_file(SEED_FILE_PATH + 'abc'))

    def test_seed_wrong_format_could_not_be_parsed(self):
        self.assertIs(None, CiSystem.parse_seeds_file(INVALID_SEED_FILE_PATH))

    def test_could_create_cis_from_the_file_without_rules(self):
        before = CiSystem.objects.count()
        CiSystem.create_from_seed_file(SEED_FILE_PATH)

        self.assertEqual(CiSystem.objects.count(), before + 10)
        ci = CiSystem.objects.filter(
            url='https://product-ci.abc.net/'
        ).first()
        self.assertEqual(ci.name, 'Product CI:')
        self.assertEqual(ci.sticky_failure, True)

    @mock.patch.object(CiSystem, 'parse_seeds_file')
    def test_cis_creation_from_file_handles_errors(self, _seed_file_mock):
        _seed_file_mock.return_value = {
            'ci_systems': [{
                'name': 'Product CI',
                'url': 'https://product-ci.infra.abc.net/',
                'is_active': True,
                'sticky_failure': True,
                'username': '',
                'password': '',
                'rules': [{
                    'rule_type': 'Job',
                    'name': '8.0.test_all',
                    'version': '8.0'
                }],
            }, {
                'name': 'Product CI2',
                'url': 'https://product-ci.infra.abc.net/',
                'is_active': True,
                'sticky_failure': True,
                'username': '',
                'password': '',
                'rules': [{
                    'rule_type': 'job',
                    'name': '8.0.test_all',
                    'version': '8.0'
                }],
            }]
        }

        before = CiSystem.objects.count()
        result = CiSystem.create_from_seed_file(SEED_FILE_PATH)

        self.assertEqual(CiSystem.objects.count(), before + 1)
        self.assertEqual(1, result['cis_imported'])
        self.assertTrue(
            result['errors'][0].find(
                'Ci system with this Url already exists.'
            ) != -1
        )

    def test_could_create_rules_by_attributes_list(self):
        ci = CiSystem.objects.create(url=VALID_URL, name='1')
        rule = Rule.objects.create(
            name='test_job',
            ci_system=ci,
            is_active=True,
            version='7.0')

        result1 = CiSystem.create_rule_for_ci(
            [{'name': 'test_job', 'rule_type': 'job', 'version': '7.0'}], ci
        )
        self.assertEqual(result1[0][0].name, rule.name)
        self.assertIsNone(result1[1])

        result2 = CiSystem.create_rule_for_ci(
            [{
                'name': 'test_job2', 'rule_type': 'View', 'version': '7.0'
            }, {
                'name': 'test_job3', 'rule_type': 'Job', 'version': '7.0'
            }],
            ci
        )
        self.assertEqual(result2[0][0].name, 'test_job2')
        self.assertEqual(result2[0][1].name, 'test_job3')
        self.assertIsNone(result2[1])

        result3 = CiSystem.create_rule_for_ci(
            [{
                'name': 'test_job4', 'rule_type': 'View', 'version': '7.0'
            }, {
                'name': 'test_job5', 'rule_type': 'Invalid', 'version': '7.0'
            }],
            ci
        )
        self.assertEqual(result3[0], [])
        self.assertIsNotNone(result3[1])

    @mock.patch.object(CiSystem, 'parse_seeds_file')
    def test_cis_creation_with_rules_assigned(self, _seed_file_mock):
        _seed_file_mock.return_value = {
            'ci_systems': [{
                'name': 'Product CI',
                'url': 'https://product-ci.infra.abc.net/',
                'is_active': True,
                'sticky_failure': True,
                'username': '',
                'password': '',
                'rules': [{
                    'rule_type': 'Job',
                    'name': '8.0.test_all',
                    'version': '7.0',
                    'trigger_type': 'Gerrit trigger',
                    'is_active': True,
                }],
            }]
        }

        result = CiSystem.create_from_seed_file(SEED_FILE_PATH)

        self.assertEqual(result['cis_imported'], 1)
        self.assertEqual(result['errors'], [])
        self.assertEqual(
            result['objects'][0].rule_set.first().name,
            '8.0.test_all'
        )
