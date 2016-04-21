from __future__ import unicode_literals

import json
import logging

from datetime import datetime
from jenkins import NotFoundException
from six.moves.urllib.request import Request

from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property

from ci_system import constants

LOGGER = logging.getLogger(__name__)


class RuleException(Exception):
    pass


class Rule(models.Model):

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    rule_type = models.IntegerField(default=constants.RULE_JOB,
                                    choices=constants.RULE_TYPE_CHOICES)
    trigger_type = models.IntegerField(default=constants.TRIGGER_TIMER,
                                       choices=constants.TRIGGER_TYPE_CHOICES)

    ci_system = models.ForeignKey('ci_system.CiSystem',
                                  on_delete=models.CASCADE)
    gerrit_refspec = models.CharField(max_length=255, default='', blank=True)
    gerrit_branch = models.CharField(max_length=255, default='', blank=True)
    is_active = models.BooleanField(default=False)
    last_updated = models.DateTimeField(null=True, default=None, blank=True)

    class Meta:
        unique_together = (
            'name',
            'rule_type',
            'trigger_type',
            'ci_system',
            'gerrit_refspec',
            'gerrit_branch',
        )

    @cached_property
    def unique_name(self):
        name = ''
        for attr in self._meta.unique_together[0]:
            name = name + '_' + str(getattr(self, attr))
        return name

    def __unicode__(self):
        return self.name

    def rule_type_text(self):
        return next(
            (text
             for idx, text
             in constants.RULE_TYPE_CHOICES
             if idx == self.rule_type),
            'Job'
        )

    @staticmethod
    def type_by_name(text):
        return next(
            (rule_type
             for rule_type, name
             in constants.RULE_TYPE_CHOICES
             if name.lower() == text.lower()),
            0
        )

    @staticmethod
    def trigger_type_by_name(text):
        return next(
            (trigger_type
             for trigger_type, name
             in constants.TRIGGER_TYPE_CHOICES
             if name.lower() == text.lower()),
            0
        )

    @staticmethod
    def status_by_jenkins_text(text):
        return constants.JENKINS_STATUSES.get(
            text,
            constants.STATUS_IN_PROGRESS
        )

    def check_rule(self, server):
        if self.rule_type == constants.JOB_RULE:
            return self.check_job_rule(server)
        elif self.rule_type == constants.VIEW_RULE:
            return self.check_view_rule(server)
        else:
            raise RuleException(
                'Unsupported rule type %s', self.rule_type)

    def check_view_rule(self, server):
        last_updated = timezone.now()

        jobs = self.get_view_jobs(self.name, server)
        rule_checks = [
            self._check_job_status(server, job['name']) for job in jobs
        ]

        # remove jobs without statuses
        while None in rule_checks:
            rule_checks.remove(None)

        if not rule_checks:
            return None
        # for view there is no build number, because of this we use the max one
        build_number = max(rc.build_number for rc in rule_checks)
        statuses = [rc.status_type for rc in rule_checks]
        running = sum(rc.running for rc in rule_checks)
        queued = sum(rc.queued for rc in rule_checks)

        if all(s == constants.STATUS_SUCCESS for s in statuses):
            status = constants.STATUS_SUCCESS
        elif all(s == constants.STATUS_ERROR for s in statuses):
            status = constants.STATUS_ERROR
        elif constants.STATUS_FAIL in statuses:
            status = constants.STATUS_FAIL
        else:
            status = constants.STATUS_SKIP

        return RuleCheck(
            rule=self,
            build_number=build_number,
            status_type=status,
            running=running,
            queued=queued,
            created_at=last_updated)

    def check_job_rule(self, server):
        return self._check_job_status(server, self.name)

    def _check_job_status(self, server, job_name, limit=10):
        is_view = self.rule_type == constants.RULE_VIEW
        last_updated = timezone.now()
        status = None

        try:
            job_info = server.get_job_info(job_name)
        except NotFoundException:
            LOGGER.error(
                'Could not retrive job info. Job %s, server %s', self, server)
            return None

        if not job_info['lastCompletedBuild']:
            LOGGER.error(
                'Job "%s" on server "%s" was never built. Skipped it.',
                job_name, server)
            return None

        last_build_id = job_info['lastBuild']['number'] \
            if 'lastBuild' in job_info else 0

        # last_check seems to be useless, because there is a build number, but
        # build_number is the last job matched our criteria.
        # last_check shows moment of last check and all earlier checks
        # are already parsed
        last_check = self.rulecheck_set.first()
        build_id = last_check.build_number if last_check else None
        # TODO: queue isn't counting now, need to implement
        running = queued = 0

        # iterating through all builds to find latest result which
        # match our criterias
        for number in range(last_build_id, last_build_id - limit - 1, -1):
            if number < 1:
                LOGGER.warning(
                    "job %s build %s on CI %s exceeded limit of builds",
                    job_name, number, self.ci_system)
                break

            try:
                LOGGER.debug("Getting job %s build %s on CI %s",
                             job_name, number, self.ci_system)
                build_info = server.get_build_info(job_name, number)
                build_id = int(build_info['number'])
            except NotFoundException:
                # go to next number in case of absence
                LOGGER.warning(
                    "Build '%s' for job '%s' not found", number, job_name)
                continue

            cause = ''
            gerrit_refspec_set = False if self.gerrit_refspec else True
            gerrit_branch_set = False if self.gerrit_branch else True
            for action in build_info['actions']:
                if 'causes' in action and not cause:
                    cause = action['causes'][0]['shortDescription']

                if not gerrit_refspec_set and 'parameters' in action:
                    for param in action['parameters']:
                        if (
                            param['name'] == 'GERRIT_REFSPEC' and
                            param['value'] == self.gerrit_refspec
                        ):
                            gerrit_refspec_set = True

                if not gerrit_branch_set and 'parameters' in action:
                    for param in action['parameters']:
                        if (
                            param['name'] == 'GERRIT_BRANCH' and
                            param['value'] == self.gerrit_branch
                        ):
                            gerrit_branch_set = True

                if cause and gerrit_refspec_set and gerrit_branch_set:
                    break

            if not gerrit_refspec_set or not gerrit_branch_set:
                continue

            if build_info['building']:
                running += 1
                continue

            timestamp = timezone.make_aware(
                datetime.fromtimestamp(build_info['timestamp'] / 1000),
                timezone.get_current_timezone()
            )
            if self.last_updated and self.last_updated >= timestamp:
                break

            # if project is started by upstream project, we can't detect
            # what has caused this run
            # TODO: make it possible to detect run
            pattern = constants.TRIGGER_MESSAGES[self.trigger_type]
            if cause.startswith('Started by upstream project'):
                cause = pattern
            # there is no internal trigger type in answer,
            # so we can detect run cause only by string comparison
            if cause.startswith(pattern):
                LOGGER.debug(
                    'Match cause: "%s", pattern: "%s"',
                    cause,
                    pattern
                )
                status = self.status_by_jenkins_text(build_info['result'])
                break

        if status:
            if not is_view:
                self.last_updated = last_updated
                self.save()

            if job_info.get('lastSuccessfulBuild'):  # might be None
                success_build = job_info.get('lastSuccessfulBuild').get(
                    'url', ''
                )
            else:
                success_build = ''
            if job_info.get('lastFailedBuild'):
                failed_build = job_info.get('lastFailedBuild').get(
                    'url', ''
                )
            else:
                failed_build = ''

            return RuleCheck(
                rule=self,
                build_number=build_id,
                status_type=status,
                running=running,
                queued=queued,
                last_successfull_build_link=success_build,
                last_failed_build_link=failed_build,
                created_at=self.last_updated)
        else:
            return None if is_view else last_check

    @staticmethod
    def get_view_by_name(view_name, server):
        views = server.get_views()

        return next(
            (view for view in views if view['name'] == view_name),
            None
        )

    @classmethod
    def get_view_jobs(cls, view_name, server):
        jobs = []
        view = cls.get_view_by_name(view_name, server)

        if view:
            url = view['url'] + '/api/json'
            response = cls._make_request(url, server)

            if response:
                jobs = json.loads(response)['jobs']

        return jobs

    @classmethod
    def _make_request(cls, url, server):
        response = server.jenkins_open(Request(url))
        return response


class RuleCheck(models.Model):
    rule = models.ForeignKey(Rule, on_delete=models.CASCADE)
    status = models.ManyToManyField('ci_system.Status')

    status_type = models.IntegerField(default=constants.STATUS_SUCCESS,
                                      choices=constants.STATUS_TYPE_CHOICES)

    running = models.IntegerField(default=0)
    queued = models.IntegerField(default=0)
    build_number = models.IntegerField(default=0)
    is_running_now = models.BooleanField(default=False)
    last_successfull_build_link = models.URLField(blank=True, default='')
    last_failed_build_link = models.URLField(blank=True, default='')

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __eq__(self, other):
        if not other or other.__class__ != self.__class__:
            return False

        return all(
            getattr(self, attr) == getattr(other, attr)
            for attr in ('rule', 'status_type', 'build_number',)
        )

    class Meta:
        ordering = ('-created_at',)
        get_latest_by = 'created_at'

    def __unicode__(self):
        text = '{status} (ci: "{ci}", rule: "{rule}")'

        return text.format(
            status=self.status_text,
            ci=self.rule.ci_system.name,
            rule=self.rule.name,
        )

    @cached_property
    def status_text(self):
        return next(
            (name
             for idx, name
             in constants.STATUS_TYPE_CHOICES
             if idx == self.status_type),
            constants.STATUS_ERROR
        )

    def link_to_ci(self):
        rule = self.rule

        return (rule.ci_system.url +
                rule.rule_type_text().lower() + '/' +
                rule.name)
