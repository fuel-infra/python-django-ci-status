import json

import mock

from django.core.exceptions import ValidationError
from django.test import TestCase
from jenkins import Jenkins

from ci_system.models import CiSystem
from ci_checks.models import Rule, RuleCheck, RuleException


class RuleTests(TestCase):
    JENKINS_URL = 'https://ci.fuel-abc.net'

    VIEWS_JSON = [
        {"url": "https://ci.fuel-abc.net/view/All/", "name": "All"},
        {"url": "https://ci.fuel-abc.net/view/ISO/", "name": "ISO"},
        {"url": "https://ci.fuel-abc.net/", "name": "current"},
        {"url": "https://ci.fuel-abc.net/view/devops/", "name": "devops"},
        {"url": "https://ci.fuel-abc.net/view/docs/", "name": "docs"},
        {"url": "https://ci.fuel-abc.net/view/gating/", "name": "gating"},
        {"url": "https://ci.fuel-abc.net/view/kilo/", "name": "kilo"}
    ]

    JOBS_LIST = [{
        "name": "kilo.ha_nova_vlan",
        "url": "https://ci.fuel-abc.net/job/kilo.ha_nova_vlan/",
        "color": "disabled"
    }, {
        "name": "kilo.ha_neutron_vlan",
        "url": "https://ci.fuel-abc.net/job/kilo.ha_neutron_vlan/",
        "color": "red"
    }, {
        "name": "kilo.master_node",
        "url": "https://ci.fuel-abc.net/job/kilo.master_node/",
        "color": "blue"
    }]

    ONE_VIEW_JSON_RED = {
        "description": "description",
        "jobs": JOBS_LIST,
        "name": "kilo",
        "property": [],
        "url": "https://ci.fuel-abc.net/view/kilo/"
    }

    ONE_VIEW_JSON_GREEN = {
        "description": "description",
        "jobs": [JOBS_LIST[2]],
        "name": "kilo",
        "property": [],
        "url": "https://ci.fuel-abc.net/view/kilo/"
    }

    JOB_INFO_LIST = [{
        "actions": [{
            "parameterDefinitions": [{
                "defaultParameterValue": {"value": "cleanable"},
                "description": "",
                "name": "LABEL",
                "type": "StringParameterDefinition"
            }]
        }, {}, {}, {}, {}],
        "description": "<!-- Managed by Jenkins Job Builder -->",
        "displayName": "kilo.ha_nova_vlan",
        "displayNameOrNull": "null",
        "name": "kilo.ha_nova_vlan",
        "url": "https://ci.fuel-abc.net/job/kilo.ha_nova_vlan/",
        "buildable": True,
        "builds": [{
            "number": 547,
            "url": "https://ci.fuel-abc.net/job/kilo.ha_nova_vlan/547/"
        }, {
            "number": 546,
            "url": "https://ci.fuel-abc.net/job/kilo.ha_nova_vlan/546/"
        }, {
            "number": 545,
            "url": "https://ci.fuel-abc.net/job/kilo.ha_nova_vlan/545/"
        }],
        "color": "disabled",
        "firstBuild": {
            "number": 1,
            "url": "https://ci.fuel-abc.net/job/kilo.ha_nova_vlan/547/1/"
        },
        "healthReport": [{
            "description": "Build stability: No recent builds failed.",
            "iconClassName": "icon-health-80plus",
            "iconUrl": "health-80plus.png",
            "score": 100
        }],
        "inQueue": False,
        "keepDependencies": False,
        "lastBuild": {
            "number": 547,
            "url": "https://ci.fuel-abc.net/job/kilo.ha_nova_vlan/547/"
        },
        "lastCompletedBuild": {
            "number": 547,
            "url": "https://ci.fuel-abc.net/job/kilo.ha_nova_vlan/547/"
        },
        "lastFailedBuild": "null",
        "lastStableBuild": {
            "number": 547,
            "url": "https://ci.fuel-abc.net/job/kilo.ha_nova_vlan/547/"
        },
        "lastSuccessfulBuild": {
            "number": 547,
            "url": "https://ci.fuel-abc.net/job/kilo.ha_nova_vlan/547/"
        },
        "lastUnstableBuild": "null",
        "lastUnsuccessfulBuild": "null",
        "nextBuildNumber": 548,
        "property": [{
            "parameterDefinitions": [{
                "defaultParameterValue": {
                    "name": "LABEL", "value": "cleanable"
                },
                "description": "",
                "name": "LABEL",
                "type": "StringParameterDefinition"
            }]
        }],
        "queueItem": "null",
        "concurrentBuild": False,
        "downstreamProjects": [],
        "scm": {},
        "upstreamProjects": []
    }, {
        "actions": [{
            "parameterDefinitions": [{
                "defaultParameterValue": {"value": "cleanable"},
                "description": "",
                "name": "LABEL",
                "type": "StringParameterDefinition"}]
            },
            {}, {}, {}, {}
        ],
        "description": "<!-- Managed by Jenkins Job Builder -->",
        "displayName": "kilo.ha_neutron_vlan",
        "displayNameOrNull": "null",
        "name": "kilo.ha_neutron_vlan",
        "url": "https://ci.fuel-abc.net/job/kilo.ha_neutron_vlan/",
        "buildable": True,
        "builds": [{
            "number": 547,
            "url": "https://ci.fuel-abc.net/job/kilo.ha_neutron_vlan/547/"
        }, {
            "number": 546,
            "url": "https://ci.fuel-abc.net/job/kilo.ha_neutron_vlan/546/"
        }, {
            "number": 545,
            "url": "https://ci.fuel-abc.net/job/kilo.ha_neutron_vlan/545/"
        }],
        "color": "red",
        "firstBuild": {
            "number": 1,
            "url": "https://ci.fuel-abc.net/job/kilo.ha_neutron_vlan/547/1/"
        },
        "healthReport": [{
            "description": "Build stability: No recent builds failed.",
            "iconClassName": "icon-health-80plus",
            "iconUrl": "health-80plus.png",
            "score": 100
        }],
        "inQueue": False,
        "keepDependencies": False,
        "lastBuild": {
            "number": 547,
            "url": "https://ci.fuel-abc.net/job/kilo.ha_neutron_vlan/547/"
        },
        "lastCompletedBuild": {
            "number": 547,
            "url": "https://ci.fuel-abc.net/job/kilo.ha_neutron_vlan/547/"
        },
        "lastFailedBuild": "null",
        "lastStableBuild": {
            "number": 547,
            "url": "https://ci.fuel-abc.net/job/kilo.ha_neutron_vlan/547/"
        },
        "lastSuccessfulBuild": {
            "number": 547,
            "url": "https://ci.fuel-abc.net/job/kilo.ha_neutron_vlan/547/"
        },
        "lastUnstableBuild": "null",
        "lastUnsuccessfulBuild": "null",
        "nextBuildNumber": 548,
        "property": [{
            "parameterDefinitions": [{
                "defaultParameterValue": {
                    "name": "LABEL",
                    "value": "kilo"
                },
                "description": "",
                "name": "LABEL",
                "type": "StringParameterDefinition"
            }]
        }],
        "queueItem": "null",
        "concurrentBuild": False,
        "downstreamProjects": [],
        "scm": {},
        "upstreamProjects": []
    }, {
        "actions": [{
            "parameterDefinitions": [{
                "defaultParameterValue": {"value": "cleanable"},
                "description": "",
                "name": "LABEL",
                "type": "StringParameterDefinition"
            }]
        }, {}, {}, {}, {}],
        "description": "<!-- Managed by Jenkins Job Builder -->",
        "displayName": "kilo.master_node",
        "displayNameOrNull": "null",
        "name": "kilo.master_node",
        "url": "https://ci.fuel-abc.net/job/kilo.master_node/",
        "buildable": True,
        "builds": [{
            "number": 547,
            "url": "https://ci.fuel-abc.net/job/kilo.master_node/547/"
        }, {
            "number": 546,
            "url": "https://ci.fuel-abc.net/job/kilo.master_node/546/"
        }, {
            "number": 545,
            "url": "https://ci.fuel-abc.net/job/kilo.master_node/545/"
        }],
        "color": "blue",
        "firstBuild": {
            "number": 1,
            "url": "https://ci.fuel-abc.net/job/kilo.master_node/547/1/"
        },
        "healthReport": [{
            "description": "Build stability: No recent builds failed.",
            "iconClassName": "icon-health-80plus",
            "iconUrl": "health-80plus.png",
            "score": 100
        }],
        "inQueue": False,
        "keepDependencies": False,
        "lastBuild": {
            "number": 547,
            "url": "https://ci.fuel-abc.net/job/kilo.master_node/547/"
        },
        "lastCompletedBuild": {
            "number": 547,
            "url": "https://ci.fuel-abc.net/job/kilo.master_node/547/"
        },
        "lastFailedBuild": "null",
        "lastStableBuild": {
            "number": 547,
            "url": "https://ci.fuel-abc.net/job/kilo.master_node/547/"
        },
        "lastSuccessfulBuild": {
            "number": 547,
            "url": "https://ci.fuel-abc.net/job/kilo.master_node/547/"
        },
        "lastUnstableBuild": "null",
        "lastUnsuccessfulBuild": "null",
        "nextBuildNumber": 548,
        "property": [{
            "parameterDefinitions": [{
                "defaultParameterValue": {"name": "LABEL", "value": "kilo"},
                "description": "",
                "name": "LABEL",
                "type": "StringParameterDefinition"
            }]
        }],
        "queueItem": "null",
        "concurrentBuild": False,
        "downstreamProjects": [],
        "scm": {},
        "upstreamProjects": []
    }]

    BUILD_INFO_LIST = [{
        'actions': [{u'causes': [{u'shortDescription': u'Started by timer'}]}],
        'building': False,
        'result': u'SUCCESS',
        'number': 547,
        'timestamp': 9455417720075,
    }, {
        'actions': [{u'causes': [{u'shortDescription': u'Started by timer'}]}],
        'building': False,
        'result': u'FAILURE',
        'number': 547,
        'timestamp': 9455417720075,
    }, {
        'actions': [{u'causes': [{u'shortDescription': u'Started by timer'}]}],
        'building': False,
        'result': u'ABORTED',
        'number': 547,
        'timestamp': 9455417720075,
    }]

    def setUp(self):
        self.server = Jenkins('http://localhost/')
        self.ci = CiSystem.objects.create(
            url='http://localhost/',
            name='test_ci'
        )
        # mock the real http calls during the testing
        self.server.get_views = lambda: self.VIEWS_JSON

    def test_string_representation(self):
        rule = Rule(name='test_all')
        self.assertEqual(str(rule), rule.name)

    def test_created_with_valid_fields(self):
        before = Rule.objects.count()
        rule = Rule.objects.create(name='kil', ci_system=self.ci, version='7')

        rule.full_clean()
        self.assertEqual(Rule.objects.count(), before + 1)

    def test_not_created_without_required_fields(self):
        rule = Rule()

        with self.assertRaises(ValidationError):
            rule.full_clean()

    def test_name_must_be_uniq_together_with_type_version_and_ci(self):
        first = Rule.objects.create(
            name='first',
            rule_type=1,
            ci_system=self.ci,
            version='8.0')
        first.full_clean()

        second = Rule(
            name='first',
            rule_type=1,
            ci_system=self.ci,
            version='8.0')
        with self.assertRaises(ValidationError):
            second.full_clean()

        second.rule_type = 2
        second.full_clean()

    def test_assert_valid_default_values(self):
        rule = Rule.objects.create(
            name='kilo',
            ci_system=self.ci,
            version='7.0')

        self.assertEqual(rule.description, '')
        self.assertEqual(rule.rule_type, 1)

    def test_rule_types_are_predefined(self):
        rule = Rule(
            name='kilo',
            rule_type=5,
            ci_system=self.ci,
            version='5.0')

        with self.assertRaises(ValidationError):
            rule.full_clean()

    def test_check_rule_process_rules_by_types(self):
        rule = Rule(
            name='kilo',
            rule_type=1,
            ci_system=self.ci,
            version='7.0',
            )
        with mock.patch.object(rule, 'check_job_rule') as m:
            rule.check_rule(self.server)

        m.assert_called_once_with(self.server)

        rule = Rule(
            name='kilo',
            rule_type=2,
            ci_system=self.ci,
            version='7.0')
        with mock.patch.object(rule, 'check_view_rule') as m:
            rule.check_rule(self.server)

        m.assert_called_once_with(self.server)

        rule = Rule(
            name='kilo',
            rule_type=5,
            ci_system=self.ci,
            version='7.0')
        with self.assertRaises(RuleException):
            rule.check_rule(self.server)

    def test_get_view_by_name(self):
        view = Rule.get_view_by_name('kilo', self.server)
        self.assertEqual(view.get('name', ''), 'kilo')

    @mock.patch.object(Rule, '_make_request')
    def test_get_jobs_list_for_view(self, _make_request_mock):
        _make_request_mock.return_value = json.dumps(self.ONE_VIEW_JSON_RED)
        jobs = Rule.get_view_jobs('kilo', self.server)

        self.assertEqual(jobs, self.ONE_VIEW_JSON_RED['jobs'])

    @mock.patch.object(Jenkins, 'get_build_info')
    @mock.patch.object(Jenkins, 'get_job_info')
    def test_check_job_status(self, _get_job_mock, _get_build_mock):
        rule = Rule(name='kilo', rule_type=1, ci_system=self.ci)

        _get_job_mock.return_value = self.JOB_INFO_LIST[0]
        _get_build_mock.return_value = self.BUILD_INFO_LIST[0]
        self.assertEqual(
            rule._check_job_status(self.server, self.JOBS_LIST[0]['name']),
            RuleCheck(
                rule=rule,
                build_number=547,
                status_type=1,
            )
        )

        _get_job_mock.return_value = self.JOB_INFO_LIST[1]
        _get_build_mock.return_value = self.BUILD_INFO_LIST[1]
        self.assertEqual(
            rule._check_job_status(self.server, self.JOBS_LIST[1]['name']),
            RuleCheck(
                rule=rule,
                build_number=547,
                status_type=2,
            )
        )

        _get_job_mock.return_value = self.JOB_INFO_LIST[2]
        _get_build_mock.return_value = self.BUILD_INFO_LIST[2]
        self.assertEqual(
            rule._check_job_status(self.server, self.JOBS_LIST[2]['name']),
            RuleCheck(
                rule=rule,
                build_number=547,
                status_type=8,
            )
        )

    @mock.patch.object(Rule, '_make_request')
    @mock.patch.object(Jenkins, 'get_build_info')
    @mock.patch.object(Jenkins, 'get_job_info')
    def test_view_rule(
        self, _get_job_mock, _get_build_mock, _make_request_mock
    ):
        rule = Rule(name='kilo', rule_type=2, ci_system=self.ci, version='1')

        _make_request_mock.return_value = json.dumps(self.ONE_VIEW_JSON_RED)
        _get_job_mock.return_value = self.JOB_INFO_LIST[1]
        _get_build_mock.return_value = self.BUILD_INFO_LIST[1]
        self.assertEqual(
            rule.check_view_rule(self.server),
            RuleCheck(
                build_number=self.BUILD_INFO_LIST[1]['number'],
                status_type=2,
                rule=rule
            )
        )

        _make_request_mock.return_value = json.dumps(self.ONE_VIEW_JSON_GREEN)
        _get_job_mock.return_value = self.JOB_INFO_LIST[2]
        _get_build_mock.return_value = self.BUILD_INFO_LIST[0]
        self.assertEqual(
            rule.check_view_rule(self.server),
            RuleCheck(
                build_number=self.BUILD_INFO_LIST[1]['number'],
                status_type=1,
                rule=rule
            )
        )

    @mock.patch.object(Jenkins, 'get_job_info')
    @mock.patch.object(Jenkins, 'get_build_info')
    def test_job_rule(self, _get_build_mock, _get_job_mock):
        rule = Rule(name='kilo', rule_type=1, ci_system=self.ci, version='2')

        build_info = self.BUILD_INFO_LIST[0]
        _get_job_mock.return_value = self.JOB_INFO_LIST[1]
        _get_build_mock.return_value = build_info

        self.assertEqual(
            rule.check_job_rule(Jenkins('localhost')),
            RuleCheck(
                build_number=build_info['number'],
                status_type=1,
                rule=rule
            )
        )

        _get_job_mock.return_value = self.JOB_INFO_LIST[2]
        self.assertEqual(
            rule.check_job_rule(Jenkins('localhost')),
            RuleCheck(
                build_number=build_info['number'],
                status_type=1,
                rule=rule
            )
        )

    def test_rule_type_has_text_representation(self):
        rule = Rule(name='kilo', rule_type=1, ci_system=self.ci, version='1')
        self.assertEqual(rule.rule_type_text(), 'Job')

        rule = Rule(name='kilo', rule_type=2, ci_system=self.ci, version='2')
        self.assertEqual(rule.rule_type_text(), 'View')

    @mock.patch.object(Jenkins, 'get_build_info')
    @mock.patch.object(Jenkins, 'get_job_info')
    def test_status_checked_correctly_in_chained_results(
        self,
        _get_job_mock,
        _get_build_mock
    ):
        rule = Rule.objects.create(name='swift', ci_system=self.ci)

        _get_job_mock.return_value = {
            "name": "swift",
            "color": "disabled",
            "lastBuild": {
                "number": 548,
                "url": "https://ci.fuel-abc.net/job/kilo.ha_nova_vlan/547/"
            },
            "lastCompletedBuild": {
                "number": 547,
                "url": "https://ci.fuel-abc.net/job/kilo.ha_nova_vlan/547/"
                },
        }
        _get_build_mock.return_value = {
            'actions': [
                {u'causes': [{u'shortDescription': u'Started by timer'}]}
            ],
            'building': False,
            'result': u'ABORTED',
            'number': 548,
            'timestamp': 1455417720075,
        }
        self.assertEqual(
            rule.check_job_rule(self.server),
            RuleCheck(
                build_number=548,
                status_type=8,
                rule=rule
            )
        )

        _get_job_mock.return_value = {
            "name": "swift",
            "color": "blue",
            "lastBuild": {
                "number": 549,
                "url": "https://ci.fuel-abc.net/job/kilo.ha_nova_vlan/547/"
            },
            "lastCompletedBuild": {
                "number": 548,
                "url": "https://ci.fuel-abc.net/job/kilo.ha_nova_vlan/548/"
            },
        }
        _get_build_mock.return_value = {
            'actions': [
                {u'causes': [{u'shortDescription': u'Started by timer'}]}
            ],
            'building': False,
            'result': u'SUCCESS',
            'number': 549,
            'timestamp': 2455417720075,
        }
        self.assertEqual(
            rule.check_job_rule(self.server),
            RuleCheck(
                build_number=549,
                status_type=1,
                rule=rule
            )
        )

        _get_job_mock.return_value = {
            "name": "swift",
            "color": "red",
            "lastBuild": {
                "number": 550,
                "url": "https://ci.fuel-abc.net/job/kilo.ha_nova_vlan/547/"
            },
            "lastCompletedBuild": {
                "number": 549,
                "url": "https://ci.fuel-abc.net/job/kilo.ha_nova_vlan/549/"
            },
        }
        _get_build_mock.return_value = {
            'actions': [
                {u'causes': [{u'shortDescription': u'Started by timer'}]}
            ],
            'building': False,
            'result': u'FAILURE',
            'number': 550,
            'timestamp': 3455417720075,
        }
        self.assertEqual(
            rule.check_job_rule(self.server),
            RuleCheck(
                build_number=550,
                status_type=2,
                rule=rule
            )
        )
