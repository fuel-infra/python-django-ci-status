import mock
import os

from django.core.exceptions import ValidationError
from django.test import TestCase
from jenkins import Jenkins, JenkinsException

from ci_system import constants
from ci_system.models import CiSystem, ProductCi, Status
from ci_checks.models import Rule, RuleCheck, RuleException


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
        ci = CiSystem(url=VALID_URL)
        self.assertEqual(str(ci), VALID_URL)

        name = 'Product CI'
        ci = CiSystem(url=VALID_URL, name=name)
        self.assertEqual(str(ci), name)

    def test_name_must_be_uniq(self):
        first = CiSystem.objects.create(url=VALID_URL, name='1')
        first.full_clean()

        second = CiSystem(url=VALID_URL + 'x', name='1')
        with self.assertRaises(ValidationError):
            second.full_clean()

    def test_url_must_be_uniq(self):
        first = CiSystem.objects.create(url=VALID_URL, name='1')
        first.full_clean()

        second = CiSystem(url=VALID_URL, name='2')
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

    def test_valid_default_values(self):
        ci = CiSystem.objects.create(url=VALID_URL)

        self.assertEqual(ci.username, '')
        self.assertEqual(ci.password, '')
        self.assertEqual(ci.is_active, False)

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
            status_type=constants.STATUS_FAIL,
        )
        _job_mock.return_value = job_rule_check

        new_status = ci.check_the_status()
        self.assertEqual(new_status.status_type, constants.STATUS_FAIL)
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
            status_type=constants.STATUS_SUCCESS,
        )
        _job_mock.return_value = job_rule_check

        new_status = ci.check_the_status()
        self.assertEqual(new_status.status_type, constants.STATUS_SUCCESS)
        self.assertEqual(
            new_status.last_changed_at,
            job_rule_check.created_at
        )

    def test_ci_status_checks_only_active_rules(self):
        ci = CiSystem.objects.create(url=VALID_URL)
        ci.rule_set.create(name='kilo', version='7.0')

        new_status = ci.check_the_status()
        self.assertEqual(new_status.status_type, constants.STATUS_SKIP)
        self.assertEqual(
            new_status.summary,
            'No rules configured or all of them are invalid.'
        )

    @mock.patch.object(Rule, 'check_rule')
    def test_ci_status_skips_exceptional_rules(
        self, _check_rule_mock
    ):
        ci = CiSystem.objects.create(url=VALID_URL)
        ci.rule_set.create(name='kilo', version='7.0', is_active=True)

        _check_rule_mock.side_effect = JenkinsException('server error')
        new_status = ci.check_the_status()
        self.assertEqual(new_status.status_type, constants.STATUS_SKIP)
        self.assertEqual(
            new_status.summary,
            'No rules configured or all of them are invalid.'
        )

        _check_rule_mock.side_effect = RuleException('rule error')
        new_status = ci.check_the_status()
        self.assertEqual(new_status.status_type, constants.STATUS_SKIP)
        self.assertEqual(
            new_status.summary,
            'No rules configured or all of them are invalid.'
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
            status_type=constants.STATUS_SUCCESS,
        )
        _job_mock.return_value = job_rule_check
        view_rule_check = RuleCheck(
            rule=view_rule,
            build_number=548,
            status_type=constants.STATUS_SUCCESS,
        )
        _view_mock.return_value = view_rule_check

        new_status = ci.check_the_status()
        self.assertEqual(
            new_status.status_type,
            constants.STATUS_SUCCESS
        )  # all green, overall too
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
            status_type=constants.STATUS_FAIL,
        )
        _job_mock.return_value = job_rule_check
        view_rule_check = RuleCheck(
            rule=view_rule,
            build_number=548,
            status_type=constants.STATUS_SUCCESS,
        )
        _view_mock.return_value = view_rule_check

        new_status = ci.check_the_status()
        self.assertEqual(
            new_status.status_type,
            constants.STATUS_FAIL
        )  # one fail, overall fail
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
            status_type=constants.STATUS_SUCCESS,
        )
        _job_mock.return_value = rule_check
        new_status = ci.check_the_status()

        self.assertEqual(new_status.status_type, constants.STATUS_SUCCESS)
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
            status_type=constants.STATUS_FAIL,
        )  # new build comes in
        _job_mock.return_value = rule_check
        last_status = ci.check_the_status()

        self.assertEqual(last_status.status_type, constants.STATUS_FAIL)
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
            status_type=constants.STATUS_SUCCESS,
        )
        _job_mock.return_value = rule_check
        status = ci.check_the_status()
        last_rule_check = RuleCheck.objects.last()

        self.assertEqual(RuleCheck.objects.count(), before + 1)
        self.assertEqual(last_rule_check.status.first(), status)
        self.assertEqual(last_rule_check.status_type, constants.STATUS_SUCCESS)

    def test_ci_has_own_jenkins_server_object(self):
        ci = CiSystem.objects.create(url=VALID_URL)
        self.assertIs(type(ci.server), Jenkins)

    def test_ci_server_object_is_cached(self):
        ci = CiSystem.objects.create(url=VALID_URL)
        with mock.patch.object(
            Jenkins, '__init__',
            return_value=None
        ) as m:
            ci.server
            ci.server

        m.assert_called_once_with(VALID_URL)

    def test_ci_server_works_with_credentials_if_both_are_present(self):
        password = 'password'
        username = 'username'

        ci = CiSystem(
            url=VALID_URL, password=password, username=username
        )
        with mock.patch.object(
            Jenkins, '__init__',
            return_value=None
        ) as m:
            ci.server

        m.assert_called_once_with(
            VALID_URL, password=password, username=username
        )

        ci = CiSystem(url=VALID_URL, password=password)
        with mock.patch.object(
            Jenkins, '__init__',
            return_value=None
        ) as m:
            ci.server

        m.assert_called_once_with(VALID_URL)

        ci = CiSystem(url=VALID_URL, username=username)
        with mock.patch.object(
            Jenkins, '__init__',
            return_value=None
        ) as m:
            ci.server

        m.assert_called_once_with(VALID_URL)

    def test_could_be_marked_with_sticky_failure(self):
        ci = CiSystem.objects.create(
            url=VALID_URL, sticky_failure=True, name='1')
        ci.full_clean()

    @mock.patch.object(Rule, 'check_job_rule')
    def test_sticky_failure_ci_fail_status_could_be_changed_only_manually(
        self, _job_mock
    ):
        # success --> success
        ci = CiSystem.objects.create(url=VALID_URL, sticky_failure=True)
        Status.objects.create(summary='Success',
                              ci_system=ci,
                              status_type=constants.STATUS_SUCCESS)

        job_rule = ci.rule_set.create(
            name='kilo',
            is_active=True,
            version='7.0'
        )
        job_rule_check = RuleCheck(
            rule=job_rule,
            build_number=547,
            status_type=constants.STATUS_SUCCESS,
        )
        _job_mock.return_value = job_rule_check

        new_status = ci.check_the_status()
        self.assertEqual(new_status.status_type, constants.STATUS_SUCCESS)
        self.assertEqual(ci.status_set.count(), 2)

        # fail -x-> success
        ci = CiSystem.objects.create(
            url=VALID_URL + 'x',
            sticky_failure=True,
            name='x')
        Status.objects.create(summary='Fail',
                              ci_system=ci,
                              status_type=constants.STATUS_FAIL)

        job_rule = ci.rule_set.create(
            name='neutron',
            is_active=True,
            version='7.0'
        )
        job_rule_check = RuleCheck(
            rule=job_rule,
            build_number=547,
            status_type=constants.STATUS_SUCCESS,
        )
        _job_mock.return_value = job_rule_check

        new_status = ci.check_the_status()
        self.assertEqual(new_status.status_type, constants.STATUS_FAIL)
        self.assertEqual(
            new_status.summary,
            '`FAIL` status on CI with `sticky_failure` set to `True` '
            'could not be changed automatically.'
        )

        # fail --> success for not product ci's
        ci = CiSystem.objects.create(url=VALID_URL + 'y', name='y')
        Status.objects.create(summary='Fail',
                              ci_system=ci,
                              status_type=constants.STATUS_FAIL)

        job_rule = ci.rule_set.create(
            name='neutron2',
            is_active=True,
            version='7.0'
        )
        job_rule_check = RuleCheck(
            rule=job_rule,
            build_number=547,
            status_type=constants.STATUS_SUCCESS,
        )
        _job_mock.return_value = job_rule_check

        new_status = ci.check_the_status()
        self.assertEqual(new_status.status_type, constants.STATUS_SUCCESS)

    @mock.patch.object(CiSystem, '_new_rulechecks_results')
    def test_ci_status_assigned_by_severity(
        self, _new_rulechecks_results_mock
    ):
        ci = CiSystem.objects.create(url=VALID_URL + '1', name='fail')
        new_results = {}

        for status_type in (
            constants.STATUS_SUCCESS, constants.STATUS_FAIL,
            constants.STATUS_SKIP, constants.STATUS_ABORTED
        ):
            rule = ci.rule_set.create(
                name='kilo_%s' % status_type,
                is_active=True,
                version='7.0'
            )
            rule_check = RuleCheck(
                rule=rule,
                build_number=547,
                status_type=status_type,
            )

            new_results[rule.unique_name] = rule_check

        _new_rulechecks_results_mock.return_value = new_results
        status = ci.check_the_status()
        self.assertEqual(status.status_type, constants.STATUS_FAIL)

        ci = CiSystem.objects.create(url=VALID_URL + '2', name='success')
        new_results = {}

        for status_type in (
            constants.STATUS_SUCCESS, constants.STATUS_ABORTED,
            constants.STATUS_SKIP
        ):
            rule = ci.rule_set.create(
                name='kilo_%s' % status_type,
                is_active=True,
                version='7.0'
            )
            rule_check = RuleCheck(
                rule=rule,
                build_number=547,
                status_type=status_type,
            )

            new_results[rule.unique_name] = rule_check

        _new_rulechecks_results_mock.return_value = new_results
        status = ci.check_the_status()
        self.assertEqual(status.status_type, constants.STATUS_SUCCESS)

        ci = CiSystem.objects.create(url=VALID_URL + '3', name='aborted')
        new_results = {}

        for status_type in (constants.STATUS_ABORTED, constants.STATUS_SKIP):
            rule = ci.rule_set.create(
                name='kilo_%s' % status_type,
                is_active=True,
                version='7.0'
            )
            rule_check = RuleCheck(
                rule=rule,
                build_number=547,
                status_type=status_type,
            )

            new_results[rule.unique_name] = rule_check

        _new_rulechecks_results_mock.return_value = new_results
        status = ci.check_the_status()
        self.assertEqual(status.status_type, constants.STATUS_ABORTED)

        ci = CiSystem.objects.create(url=VALID_URL + '4', name='skipped')
        new_results = {}
        rule = ci.rule_set.create(
            name='kilo_%s' % constants.STATUS_SKIP,
            is_active=True,
            version='7.0'
        )
        rule_check = RuleCheck(
            rule=rule,
            build_number=547,
            status_type=constants.STATUS_SKIP,
        )

        new_results[rule.unique_name] = rule_check

        _new_rulechecks_results_mock.return_value = new_results
        status = ci.check_the_status()
        self.assertEqual(status.status_type, constants.STATUS_SKIP)

    @mock.patch.object(Rule, 'check_job_rule')
    def test_ci_uses_last_changed_timestamp_from_previous_status(self,
                                                                 _job_mock):
        ci = CiSystem.objects.create(url=VALID_URL)

        rule = ci.rule_set.create(
            name='neutron',
            is_active=True,
            version='7.0'
        )
        _job_mock.return_value = RuleCheck(
            rule=rule,
            build_number=547,
            status_type=constants.STATUS_SUCCESS,
        )
        ci.check_the_status()

        _job_mock.return_value = RuleCheck(
            rule=rule,
            build_number=548,
            status_type=constants.STATUS_SUCCESS,
        )  # new build but same status type

        previous_status = Status.objects.last()
        new_status = ci.check_the_status()

        self.assertEqual(
            new_status.last_changed_at,
            previous_status.last_changed_at,
        )

        rule_check = RuleCheck(
            rule=rule,
            build_number=549,
            status_type=constants.STATUS_FAIL,
        )  # new build but and new status type

        _job_mock.return_value = rule_check
        new_status = ci.check_the_status()
        self.assertEqual(
            new_status.last_changed_at,
            rule_check.created_at,
        )

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

    def test_deactivate_previous_cis(self):
        previous = {'http://1.com/', 'http://2.com/', 'http://3.com/'}
        for name in previous:
            CiSystem.objects.create(url=name, name=name, is_active=True)

        self.assertEqual(CiSystem.objects.filter(is_active=True).count(), 3)

        new = {'http://4.com/', 'http://1.com/', 'http://5.com/'}
        CiSystem.deactivate_previous_cis(previous, new)
        self.assertEqual(CiSystem.objects.filter(is_active=True).count(), 1)

    def test_deactivate_previous_rules(self):
        ci = CiSystem.objects.create(url=VALID_URL, is_active=True)

        for name in '123':
            Rule.objects.create(
                name=name,
                version=name,
                ci_system=ci,
                is_active=True,
            )
        previous = set(
            Rule.objects.filter(is_active=True).values_list('id', flat=True)
        )
        self.assertEqual(len(previous), 3)

        CiSystem.deactivate_previous_rules(
            previous, {'x10', Rule.objects.first().id, 'x5'}
        )
        self.assertEqual(Rule.objects.filter(is_active=True).count(), 1)

    def test_parse_seeds_from_stream(self):
        with open(INVALID_SEED_FILE_PATH) as f:
            self.assertIsNone(CiSystem.parse_seeds_from_stream(f.read()))

        with open(SEED_FILE_PATH) as f:
            seeds = CiSystem.parse_seeds_from_stream(f.read())
            self.assertIsInstance(seeds, dict)
            self.assertTrue('ci_systems' in seeds)

    def test_find_rules_for_product(self):
        cis_names = '123'
        for name in cis_names:
            ci = CiSystem.objects.create(
                url=VALID_URL + '_' + name,
                name=name,
                is_active=True,
            )
            Rule.objects.create(
                name='rule_' + name,
                ci_system=ci,
                version=name,
                is_active=True,
            )

        rules, error = CiSystem.find_rules_for_product([{
            'name': 'rule_1',
            'version': '1',
            'ci_system_name': '1',
        }, {
            'name': 'rule_3',
            'version': '3',
            'ci_system_name': 'unknown',
        }])

        self.assertTrue(error)
        self.assertEqual(rules, [])  # error because of missed ci

        rules, error = CiSystem.find_rules_for_product([{
            'name': 'rule_1',
            'version': '1',
            'ci_system_name': '1',
        }, {
            'name': 'rule_10',
            'version': '2',
            'ci_system_name': '2',
        }])

        self.assertTrue(error)
        self.assertEqual(rules, [])  # error because of missed rule

        rules, error = CiSystem.find_rules_for_product([{
            'name': 'rule_1',
            'version': '1',
            'ci_system_name': '1',
        }, {
            'name': 'rule_2',
            'ci_system_name': '2',
        }])

        self.assertTrue(error)
        self.assertEqual(rules, [])  # error because of missed rule properties

        rules, error = CiSystem.find_rules_for_product([{
            'name': 'rule_1',
            'version': '1',
            'ci_system_name': '1',
        }, {
            'name': 'rule_2',
            'version': '2',
            'ci_system_name': '2',
        }, {
            'name': 'rule_3',
            'version': '3',
            'ci_system_name': '3',
        }])

        self.assertFalse(error)
        self.assertEqual(len(rules), 3)  # all good

    def test_create_rule_for_ci_with_existent_rules(self):
        rule_names = '123'
        ci = CiSystem.objects.create(
            url=VALID_URL,
            name='ci',
            is_active=True,
        )
        for name in rule_names:
            Rule.objects.create(
                name='rule_' + name,
                ci_system=ci,
                version=name,
                is_active=True,
            )

        before = Rule.objects.count()
        rules, error = CiSystem.create_rule_for_ci([{
            'name': 'rule_1',
            'version': '1',
            'ci_system_name': 'ci',
        }, {
            'name': 'rule_2',
            'version': '2',
            'ci_system_name': 'ci',
        }, {
            'name': 'rule_3',
            'version': '3',
            'ci_system_name': 'ci',
        }], ci)

        self.assertFalse(error)
        self.assertEqual(len(rules), 3)
        self.assertEqual(Rule.objects.count(), before)

    def test_create_rule_for_ci_with_mixed_rules(self):
        rule_names = '12'
        ci = CiSystem.objects.create(
            url=VALID_URL,
            name='ci',
            is_active=True,
        )
        for name in rule_names:
            Rule.objects.create(
                name='rule_' + name,
                ci_system=ci,
                version=name,
                is_active=True,
            )

        before = Rule.objects.count()
        rules, error = CiSystem.create_rule_for_ci([{
            'name': 'rule_1',
            'version': '1',
            'ci_system_name': 'ci',
        }, {
            'name': 'rule_2',
            'version': '2',
            'ci_system_name': 'ci',
        }, {
            'name': 'rule_3',
            'version': '3',
            'ci_system_name': 'ci',
        }], ci)

        self.assertFalse(error)
        self.assertEqual(len(rules), 3)
        self.assertEqual(Rule.objects.count(), before + 1)

    def test_create_rule_for_ci_with_wrong_rules(self):
        rule_names = '12'
        ci = CiSystem.objects.create(
            url=VALID_URL,
            name='ci',
            is_active=True,
        )
        for name in rule_names:
            Rule.objects.create(
                name='rule_' + name,
                ci_system=ci,
                version=name,
                is_active=True,
            )

        before = Rule.objects.count()
        rules, error = CiSystem.create_rule_for_ci([{
            'name': 'rule_1',
            'version': '1',
            'ci_system_name': 'ci',
        }, {
            'name': 'rule_2',
            'ci_system_name': 'ci',
        }], ci)

        self.assertTrue(error)
        self.assertEqual(len(rules), 0)
        self.assertEqual(Rule.objects.count(), before)

        before = Rule.objects.count()
        rules, error = CiSystem.create_rule_for_ci([{
            'version': '2',
            'ci_system_name': 'ci',
        }, {
            'name': 'rule_1',
            'version': '1',
            'ci_system_name': 'ci',
        }], ci)

        self.assertTrue(error)
        self.assertEqual(len(rules), 0)
        self.assertEqual(Rule.objects.count(), before)

        before = Rule.objects.count()
        rules, error = CiSystem.create_rule_for_ci([{
            'name': 'rule_1',
            'version': '1',
            'ci_system_name': 'ci',
        }, {
            'name': 'rule_3',
            'version': '1',
            'ci_system_name': 'ci',
            'rule_type': 'unknown',
        }], ci)

        self.assertTrue(error)
        self.assertEqual(len(rules), 0)
        self.assertEqual(Rule.objects.count(), before)

    def test_create_rule_for_ci_deactivate_previous_rules(self):
        rule_names = '12'
        ci = CiSystem.objects.create(
            url=VALID_URL,
            name='ci',
            is_active=True,
        )
        for name in rule_names:
            Rule.objects.create(
                name='rule_' + name,
                ci_system=ci,
                version=name,
                is_active=True,
            )

        before = Rule.objects.filter(is_active=True).count()
        self.assertEqual(before, 2)
        rules, error = CiSystem.create_rule_for_ci([{
            'name': 'rule_1',
            'version': '1',
            'ci_system_name': 'ci',
            'is_active': True,
        }, {
            'name': 'rule_3',
            'version': '3',
            'ci_system_name': 'ci',
        }], ci)

        self.assertFalse(error)
        self.assertEqual(len(rules), 2)
        self.assertEqual(Rule.objects.count(), before + 1)
        self.assertEqual(Rule.objects.filter(is_active=True).count(), 1)

    def test_create_from_seeds_with_empty_seeds(self):
        self.assertEqual(
            CiSystem.create_from_seeds({}),
            {
                'objects': [],
                'errors': [],
                'cis_total': 0,
                'cis_imported': 0,
                'ps_total': 0,
                'ps_imported': 0,
            }
        )

    def test_create_from_seeds_with_missed_seeds(self):
        self.assertEqual(
            CiSystem.create_from_seeds({'test': [1, 2, 3]}),
            {
                'objects': [],
                'errors': [],
                'cis_total': 0,
                'cis_imported': 0,
                'ps_total': 0,
                'ps_imported': 0,
            }
        )

    def test_create_from_seeds_with_valid_unexistent_cis_without_rules(self):
        before = CiSystem.objects.count()

        seeds = {
            'ci_systems': [{
                'name': 'Product CI',
                'url': 'https://product-ci.infra.abc.net/',
                'is_active': True,
                'sticky_failure': True,
                'username': '',
                'password': '',
            }]
        }
        self.assertEqual(
            CiSystem.create_from_seeds(seeds),
            {
                'objects': [CiSystem.objects.first()],
                'errors': [],
                'cis_total': 1,
                'cis_imported': 1,
                'ps_total': 0,
                'ps_imported': 0,
            }
        )
        self.assertEqual(CiSystem.objects.count(), before + 1)

        seeds = {
            'ci_systems': [{
                'name': 'Product CI2',
                'url': 'https://product-ci2.infra.abc.net/',
            }]
        }
        self.assertEqual(
            CiSystem.create_from_seeds(seeds),
            {
                'objects': [CiSystem.objects.last()],
                'errors': [],
                'cis_total': 1,
                'cis_imported': 1,
                'ps_total': 0,
                'ps_imported': 0,
            }
        )
        self.assertEqual(CiSystem.objects.count(), before + 2)

    def test_create_from_seeds_with_invalid_cis_without_rules(self):
        missed_msg = (
            u'Can not import CI: "%s" from the seeds file. '
            u'Required parameter is missed: u\'%s\''
        )
        before = CiSystem.objects.count()

        seeds = {
            'ci_systems': [{
                'name': 'Product CI',
            }]
        }
        self.assertEqual(
            CiSystem.create_from_seeds(seeds),
            {
                'objects': [],
                'errors': [missed_msg % ('Product CI', 'url')],
                'cis_total': 1,
                'cis_imported': 0,
                'ps_total': 0,
                'ps_imported': 0,
            }
        )
        self.assertEqual(CiSystem.objects.count(), before)

    def test_create_from_seeds_with_valid_existent_cis_without_rules(self):
        CiSystem.objects.create(
            name='Product CI',
            url='https://product-ci.infra.abc.net/',
        )
        before = CiSystem.objects.count()

        seeds = {
            'ci_systems': [{
                'name': 'Product CI',
                'url': 'https://product-ci.infra.abc.net/',
            }, {
                'name': 'Status CI',
                'url': 'https://status-ci.infra.abc.net/',
            }]
        }
        result = CiSystem.create_from_seeds(seeds)
        self.assertEqual(len(result['objects']), 2)
        self.assertEqual(result['cis_total'], 2)
        self.assertEqual(result['cis_imported'], 2)
        self.assertEqual(result['errors'], [])
        self.assertEqual(CiSystem.objects.count(), before + 1)

    def test_create_from_seeds_deactivates_old_cis(self):
        CiSystem.objects.create(
            name='Product CI',
            url='https://product-ci.infra.abc.net/',
            is_active=True,
        )
        seeds = {
            'ci_systems': [{
                'name': 'Product CI',
                'url': 'https://product-ci.infra.abc.net/',
            }, {
                'name': 'Status CI',
                'url': 'https://status-ci.infra.abc.net/',
            }]
        }

        CiSystem.create_from_seeds(seeds)
        self.assertEqual(CiSystem.objects.filter(is_active=True).count(), 0)

    def test_create_from_seeds_handles_errors(self):
        CiSystem.objects.create(
            name='Product CI',
            url='https://product-ci.infra.abc.net/',
        )
        before = CiSystem.objects.count()

        seeds = {
            'ci_systems': [{
                'name': 'Product CI2',
                'url': 'https://product-ci.infra.abc.net/',
            }]
        }
        result = CiSystem.create_from_seeds(seeds)
        self.assertEqual(result['cis_total'], 1)
        self.assertEqual(result['cis_imported'], 0)
        self.assertTrue('Url already exist' in ''.join(result['errors']))

        seeds = {
            'ci_systems': [{
                'name': 'Product CI3',
                'url': 'https://',
            }]
        }
        result = CiSystem.create_from_seeds(seeds)
        self.assertEqual(result['cis_total'], 1)
        self.assertEqual(result['cis_imported'], 0)
        self.assertTrue('Enter a valid URL.', ''.join(result['errors']))

        self.assertEqual(CiSystem.objects.count(), before)

    def test_create_from_seeds_cis_errors_doesnt_affect_valid_records(self):
        before = CiSystem.objects.count()

        seeds = {
            'ci_systems': [{
                'name': 'Product CI',
                'url': 'https://product-ci.infra.abc.net/',
            }, {
                'url': 'https://product-ci.infra.abc.net/',
            }]
        }

        result = CiSystem.create_from_seeds(seeds)
        self.assertEqual(len(result['objects']), 1)
        self.assertEqual(result['cis_total'], 2)
        self.assertEqual(result['cis_imported'], 1)
        self.assertTrue('Url already exist' in ''.join(result['errors']))
        self.assertEqual(CiSystem.objects.count(), before + 1)

    def test_create_from_seeds_cis_with_valid_rules(self):
        seeds = {
            'ci_systems': [{
                'name': 'Product CI',
                'url': 'https://product-ci.infra.abc.net/',
                'rules': [{
                    'rule_type': 'Job',
                    'name': '8.0.test_all',
                    'version': '7.0',
                    'trigger_type': 'Gerrit trigger',
                    'is_active': True,
                }, {
                    'rule_type': 'View',
                    'name': '8.0.test_all',
                    'version': '7.0',
                    'trigger_type': 'Gerrit trigger',
                    'is_active': False,
                }],
            }]
        }

        result = CiSystem.create_from_seeds(seeds)
        self.assertEqual(len(result['objects']), 1)
        self.assertEqual(result['cis_total'], 1)
        self.assertEqual(result['cis_imported'], 1)
        self.assertEqual(CiSystem.objects.first().rule_set.count(), 2)

    def test_create_from_seeds_cis_with_invalid_rules(self):
        seeds = {
            'ci_systems': [{
                'name': 'Product CI',
                'url': 'https://product-ci.infra.abc.net/',
                'rules': [{
                    'version': '7.0',
                    'trigger_type': 'Gerrit trigger',
                    'is_active': True,
                }],
            }]
        }

        result = CiSystem.create_from_seeds(seeds)
        self.assertEqual(len(result['objects']), 0)
        self.assertEqual(result['cis_total'], 1)
        self.assertEqual(result['cis_imported'], 0)
        self.assertTrue('Can not create rule' in ''.join(result['errors']))

    def test_create_from_seeds_cis_updates_existent_cis(self):
        CiSystem.objects.create(
            name='Product CI',
            url='https://product.abc.net/',
            is_active=False,
            sticky_failure=False,
            username='a',
            password='b',
        )
        seeds = {
            'ci_systems': [{
                'name': 'Product CI',
                'url': 'https://product-ci.infra.abc.net/',
                'is_active': True,
                'username': 'user',
                'password': 'pass',
                'sticky_failure': True,
                'rules': [{
                    'name': '7.test_all',
                    'version': '7.0',
                    'trigger_type': 'Gerrit trigger',
                    'is_active': True,
                }],
            }]
        }

        CiSystem.create_from_seeds(seeds)
        ci = CiSystem.objects.first()

        self.assertEqual(ci.url, 'https://product-ci.infra.abc.net/')
        self.assertTrue(ci.is_active, True)
        self.assertTrue(ci.sticky_failure, True)
        self.assertTrue(ci.username, 'user')
        self.assertTrue(ci.password, 'pass')
        self.assertEqual(ci.rule_set.filter(is_active=True).count(), 1)

        seeds = {
            'ci_systems': [{
                'name': 'Product CI',
                'url': 'https://product-ci.infra.abc.net/',
                'is_active': True,
                'username': 'user',
                'password': 'pass',
                'sticky_failure': True,
                'rules': [],
            }]
        }
        CiSystem.create_from_seeds(seeds)
        self.assertEqual(ci.rule_set.filter(is_active=True).count(), 0)

    def test_create_from_seeds_with_valid_unexistent_psis_without_rules(self):
        before = ProductCi.objects.count()

        seeds = {
            'product_statuses': [{
                'name': 'Product CI',
                'is_active': True,
            }]
        }
        self.assertEqual(
            CiSystem.create_from_seeds(seeds),
            {
                'objects': [ProductCi.objects.first()],
                'errors': [],
                'cis_total': 0,
                'cis_imported': 0,
                'ps_total': 1,
                'ps_imported': 1,
            }
        )
        self.assertEqual(ProductCi.objects.count(), before + 1)

    def test_create_from_seeds_with_invalid_psis_without_rules(self):
        missed_msg = (
            u'Can not import ProductCi: "%s" from the seeds file. '
            u'Required parameter is missed: u\'%s\''
        )
        before = ProductCi.objects.count()

        seeds = {
            'product_statuses': [{
                'is_active': True,
            }]
        }
        self.assertEqual(
            CiSystem.create_from_seeds(seeds),
            {
                'objects': [],
                'errors': [missed_msg % ('', 'name')],
                'cis_total': 0,
                'cis_imported': 0,
                'ps_total': 1,
                'ps_imported': 0,
            }
        )
        self.assertEqual(ProductCi.objects.count(), before)

    def test_create_from_seeds_with_valid_existent_psis_without_rules(self):
        ProductCi.objects.create(name='Product CI')

        seeds = {
            'product_statuses': [{
                'name': 'Product CI',
                'is_active': True,
            }]
        }
        result = CiSystem.create_from_seeds(seeds)
        self.assertEqual(len(result['objects']), 1)
        self.assertEqual(result['ps_total'], 1)
        self.assertEqual(result['ps_imported'], 1)
        self.assertEqual(result['errors'], [])
        self.assertEqual(ProductCi.objects.count(), 1)

    def test_create_from_seeds_deactivates_old_psis(self):
        ProductCi.objects.create(name='Product CI', is_active=True)

        seeds = {
            'product_statuses': [{
                'name': 'Product CI2',
            }]
        }

        CiSystem.create_from_seeds(seeds)
        self.assertEqual(ProductCi.objects.filter(is_active=True).count(), 0)

    def test_create_from_seeds_psis_handles_errors(self):
        ProductCi.objects.create(name='Product CI')

        seeds = {
            'product_statuses': [{
                'name': '*' * 200,  # just simulating validation error here
            }]
        }
        result = CiSystem.create_from_seeds(seeds)
        self.assertEqual(len(result['objects']), 0)
        self.assertEqual(result['ps_total'], 1)
        self.assertEqual(result['ps_imported'], 0)
        self.assertTrue('Ensure this value' in ''.join(result['errors']))
        self.assertEqual(ProductCi.objects.count(), 1)

    def test_create_from_seeds_psis_errors_doesnt_affect_valid_records(self):
        seeds = {
            'product_statuses': [{
                'name': 'Product CI',
                'is_active': True,
            }, {
                'is_active': False
            }]
        }

        result = CiSystem.create_from_seeds(seeds)
        self.assertEqual(len(result['objects']), 1)
        self.assertEqual(result['ps_total'], 2)
        self.assertEqual(result['ps_imported'], 1)
        self.assertTrue('parameter is missed' in ''.join(result['errors']))
        self.assertEqual(ProductCi.objects.count(), 1)

    def test_create_from_seeds_psis_with_valid_rules(self):
        ci = CiSystem.objects.create(name='Fuel')
        ci.rule_set.create(
            name='8.0.test_all',
            version='7.0',
            trigger_type=2,
            is_active=True,
        )
        ci.rule_set.create(
            name='8.0.test_all',
            version='7.0',
            rule_type=2,
            trigger_type=2,
            is_active=False,
        )

        seeds = {
            'product_statuses': [{
                'name': 'Product CI',
                'rules': [{
                    'rule_type': 'Job',
                    'name': '8.0.test_all',
                    'version': '7.0',
                    'trigger_type': 'Gerrit trigger',
                    'is_active': True,
                    'ci_system_name': 'Fuel',
                }, {
                    'rule_type': 'View',
                    'name': '8.0.test_all',
                    'version': '7.0',
                    'trigger_type': 'Gerrit trigger',
                    'is_active': False,
                    'ci_system_name': 'Fuel',
                }],
            }]
        }

        result = CiSystem.create_from_seeds(seeds)
        self.assertEqual(len(result['objects']), 1)
        self.assertEqual(result['ps_total'], 1)
        self.assertEqual(result['ps_imported'], 1)
        self.assertEqual(ProductCi.objects.first().rules.count(), 2)

    def test_create_from_seeds_psis_with_invalid_rules(self):
        ci = CiSystem.objects.create(name='Fuel')
        ci.rule_set.create(
            name='8.0.test_all',
            version='7.0',
            trigger_type=2,
            is_active=True,
        )

        seeds = {
            'product_statuses': [{
                'name': 'Product CI',
                'rules': [{  # missed name
                    'version': '7.0',
                    'trigger_type': 'Gerrit trigger',
                    'is_active': True,
                    'ci_system_name': 'Fuel',
                }],
            }]
        }

        result = CiSystem.create_from_seeds(seeds)
        self.assertEqual(len(result['objects']), 0)
        self.assertEqual(result['ps_total'], 1)
        self.assertEqual(result['ps_imported'], 0)
        self.assertTrue('has invalid rules' in ''.join(result['errors']))

        seeds = {
            'product_statuses': [{
                'name': 'Product CI',
                'rules': [{
                    'name': 'unexistent',  # unexistent rule
                    'version': '7.0',
                    'trigger_type': 'Gerrit trigger',
                    'is_active': True,
                    'ci_system_name': 'Fuel',
                }],
            }]
        }

        result = CiSystem.create_from_seeds(seeds)
        self.assertEqual(len(result['objects']), 0)
        self.assertEqual(result['ps_total'], 1)
        self.assertEqual(result['ps_imported'], 0)
        self.assertTrue('has invalid rules' in ''.join(result['errors']))

    def test_create_from_seeds_psis_updates_existent_psis_rules(self):
        ci = CiSystem.objects.create(name='Fuel')
        ci.rule_set.create(
            name='7',
            version='7.0',
            is_active=True,
        )
        ci.rule_set.create(
            name='8',
            version='8.0',
            trigger_type=2,
            rule_type=2,
            is_active=True,
        )

        previous = ProductCi.objects.create(name='Product CI')
        previous.rules.add(Rule.objects.first())
        self.assertEqual(previous.rules.count(), 1)

        seeds = {
            'product_statuses': [{
                'name': 'Product CI',
                'is_active': True,
                'rules': [{
                    'name': '7',
                    'rule_type': 'Job',
                    'version': '7.0',
                    'ci_system_name': 'Fuel',
                }, {
                    'name': '8',
                    'rule_type': 'View',
                    'version': '8.0',
                    'trigger_type': 'Gerrit trigger',
                    'is_active': True,
                    'ci_system_name': 'Fuel',
                }],
            }]
        }

        CiSystem.create_from_seeds(seeds)
        product = ProductCi.objects.first()

        self.assertTrue(product.is_active)
        self.assertEqual(product.rules.count(), 2)

        seeds = {
            'product_statuses': [{
                'name': 'Product CI',
                'is_active': True,
                'rules': [{
                    'rule_type': 'View',
                    'name': '8',
                    'version': '8.0',
                    'trigger_type': 'Gerrit trigger',
                    'is_active': True,
                    'ci_system_name': 'Fuel',
                }],
            }]
        }

        CiSystem.create_from_seeds(seeds)
        self.assertEqual(product.rules.filter(is_active=True).count(), 1)

        seeds = {
            'product_statuses': [{
                'name': 'Product CI',
                'is_active': True,
                'rules': [],
            }]
        }

        CiSystem.create_from_seeds(seeds)
        self.assertEqual(product.rules.filter(is_active=True).count(), 0)
