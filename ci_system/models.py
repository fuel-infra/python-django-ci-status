from __future__ import unicode_literals

import jsonschema
import logging
import yaml

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db import models, IntegrityError
from django.db.models.signals import pre_delete
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.timesince import timesince

from jenkins import Jenkins, JenkinsException

from ci_system import constants

from ci_checks.models import Rule, RuleCheck, RuleException

LOGGER = logging.getLogger(__name__)


class CiSystem(models.Model):

    url = models.URLField(unique=True)
    name = models.CharField(max_length=50, default='', blank=True)

    username = models.CharField(max_length=50, blank=True, default='')
    password = models.CharField(max_length=100, blank=True, default='')
    is_active = models.BooleanField(default=False)
    sticky_failure = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name if self.name else self.url

    def latest_status(self):
        try:
            status = self.status_set.latest()
        except Status.DoesNotExist:
            status = None

        return status

    def _new_rulechecks_results(self):
        new_results = {}

        for rule in self.rule_set.filter(is_active=True):
            rule_check = self._process_the_rule(rule)

            if not rule_check:
                continue

            new_results[rule_check.rule.unique_name] = rule_check

        return new_results

    def _set_skipped_status(self):
        return self.status_set.create(
            status_type=constants.STATUS_SKIP,
            summary='No rules configured or all of them are invalid.',
            last_changed_at=timezone.now(),
        )

    def _get_status_type_for_results(self, statuses_types_list):
        # TODO: move checks severity to settings
        checks_severity = (
            constants.STATUS_FAIL,
            constants.STATUS_SUCCESS,
            constants.STATUS_ABORTED,
            constants.STATUS_SKIP
        )
#        if not [i for i in checks_severity if type(i) is int]:
#            raise ValueError("checks_severity must be non-empty numeric list")

        # find all checks that matches from high status to low
        status_type = checks_severity[0]
        for status in checks_severity:
            result = 0
            for rule_check in statuses_types_list:
                result |= rule_check.status_type
            if result & status:
                status_type = status
                break

        return status_type

    def _check_for_sticky_status(self, status_type, previous_status=None):
        if (
            self.sticky_failure and
            previous_status and
            previous_status.status_type == constants.STATUS_FAIL and
            status_type == constants.STATUS_SUCCESS
        ):
            status_type = constants.STATUS_FAIL
            summary = (
                "`FAIL` status on CI with `sticky_failure` set to `True`"
                " could not be changed automatically."
            )
        else:
            summary = 'Assigned automaticaly by a periodic task'

        return status_type, summary

    def check_the_status(self):
        previous_status = self.latest_status()
        new_results = self._new_rulechecks_results()

        # find previous status and its rule_checks to make sure that
        # theirs build_numbers are not the same
        if previous_status:
            old_results = {
                rc.rule.unique_name: rc
                for rc in previous_status.rule_checks()
            }

            if new_results == old_results:
                return previous_status

        # in case all job checks are failed skip the status as wrong configured
        if not new_results:
            return self._set_skipped_status()

        new_results = new_results.values()
        status_type = self._get_status_type_for_results(new_results)

        # don't let sticky ci FAIL status be updated to SUCCESS automatically
        status_type, summary = self._check_for_sticky_status(
            status_type, previous_status)

        # in case status haven't changed leave the previous timestamp
        if previous_status and previous_status.status_type == status_type:
            last_changed_at = (
                previous_status.last_changed_at or previous_status.created_at)
        else:
            last_changed_at = max(
                rc.updated_at or rc.created_at for rc in new_results)

        status = self.status_set.create(
            status_type=status_type,
            summary=summary,
            last_changed_at=last_changed_at,
        )

        for rule_check in new_results:
            rule_check.save()
            rule_check.status.add(status)

        return status

    @cached_property
    def server(self):
        if self.username and self.password:
            server = Jenkins(self.url,
                             username=self.username,
                             password=self.password)
        else:
            server = Jenkins(self.url)

        return server

    def _process_the_rule(self, rule):
        try:
            rule_check = rule.check_rule(self.server)
        except JenkinsException:
            LOGGER.exception(
                'Jenkins can not connect to server %s and rule %s',
                self.url, rule.name)
            return None
        except RuleException:
            LOGGER.exception(
                'Rule %s can not be processed on the server %s',
                rule.name, self.url)
            return None

        return rule_check

    @staticmethod
    def parse_seeds_file(file_path):
        result = None

        try:
            result = yaml.safe_load(open(file_path))
        except IOError as exc:
            LOGGER.exception(
                'The file %s could not be found or read: %s',
                file_path, exc
            )
        except yaml.YAMLError as exc:
            LOGGER.exception(
                'The file %s could not be parsed: %s',
                file_path, exc
            )

        return result

    @classmethod
    def create_rule_for_ci(cls, rules_list, ci):
        created = False
        result = []
        new_rules = set()
        previous_rules = set(
            ci.rule_set.filter(is_active=True).values_list('id', flat=True)
        )

        for rule_dict in rules_list:
            try:
                rule, created = Rule.objects.get_or_create(
                    name=rule_dict['name'],
                    ci_system=ci,
                    rule_type=Rule.type_by_name(
                        rule_dict.get(
                            'rule_type',
                            constants.DEFAULT_RULE_TYPE
                        )
                    ),
                    trigger_type=Rule.trigger_type_by_name(
                        rule_dict.get(
                            'trigger_type',
                            constants.DEFAULT_TRIGGER_TYPE
                        )
                    ),
                    gerrit_refspec=rule_dict.get('gerrit_refspec', ''),
                    gerrit_branch=rule_dict.get('gerrit_branch', ''),
                )

                rule.is_active = rule_dict.get('is_active', False)
                rule.full_clean()
                result.append(rule)
            except (IntegrityError, ValidationError, KeyError) as exc:
                msg = 'Can not create rule during CI import: %s'
                LOGGER.error(msg, exc)

                if created:
                    rule.delete()

                return [], msg % exc

        for rule in result:
            rule.save()
            new_rules.add(rule.id)

        if previous_rules:
            cls.deactivate_previous_rules(previous_rules, new_rules)

        return result, None

    @classmethod
    def deactivate_previous_rules(cls, previous_rules, new_rules):
        for rule_id in previous_rules - new_rules:
            try:
                rule = Rule.objects.get(id=rule_id)
                rule.is_active = False
                rule.save()
            except Rule.DoesNotExist as exc:
                LOGGER.error(
                    'Can not deactivate unexistent rule during import: %s',
                    exc)

    @staticmethod
    def parse_seeds_from_stream(stream):
        result = None

        try:
            result = yaml.safe_load(stream)
        except yaml.YAMLError:
            LOGGER.exception('The file stream %s could not be parsed', stream)

        return result

    @classmethod
    def create_from_seed_file(cls, file_path):
        seeds = cls.parse_seeds_file(file_path)
        return cls.create_from_seeds(seeds)

    @classmethod
    def create_from_seeds(cls, seeds):
        result = {
            'objects': [],
            'errors': [],
            'cis_total': 0,
            'cis_imported': 0,
            'ps_total': 0,
            'ps_imported': 0,
        }

        if settings.JSON_SCHEMA:
            try:
                jsonschema.validate(seeds, settings.JSON_SCHEMA)
            except jsonschema.ValidationError as exc:
                msg = 'Import file does not follow json schema: %s' % exc
                LOGGER.error(msg)
                result['errors'].append(msg)
                return result
        else:
            msg = ('Something went wrong with schema.json validation. '
                   'Please contact the administrator.')
            LOGGER.error(msg)
            result['errors'].append(msg)
            return result

        previous_cis = {ci.url for ci in cls.objects.all()}
        previous_products_names = {
            (p.name, p.version) for p in ProductCi.objects.all()
        }
        new_cis, new_products_names = set(), set()

        if seeds:
            cis, products, error = cls._construct_cis_from_import_dict(seeds)
            result['cis_total'] = len(cis)
            result['ps_total'] = len(products)

            if error:
                result['errors'].append(error)
                return result

            for ci in cis:
                new_ci, error = cls._import_ci(ci)
                if error:
                    result['errors'].append(error)
                else:
                    result['objects'].append(new_ci)
                    result['cis_imported'] += 1
                    new_cis.add(ci['url'])

            for product in products:
                new_product, error = cls._import_product_status(product)
                if error:
                    result['errors'].append(error)
                else:
                    result['objects'].append(new_product)
                    result['ps_imported'] += 1
                    new_products_names.add(
                        (new_product.name, new_product.version)
                    )

            cls.deactivate_previous_cis(previous_cis, new_cis)
            ProductCi.deactivate_previous_products(
                previous_products_names,
                new_products_names
            )

        return result

    @classmethod
    def _parse_job(cls, job, name, rule_type='Job'):
        filters = job.get('filter', {})

        rule = {
            'name': name,
            'rule_type': rule_type,
            'is_active': True
        }

        rule['trigger_type'] = filters.get(
            'triggered_by', constants.DEFAULT_TRIGGER_TYPE
        )

        for gerrit_param, gerrit_value in filters.get(
            'parameters', {}
        ).items():
            rule[gerrit_param.lower()] = gerrit_value

        return rule

    @classmethod
    def _construct_cis_from_import_dict(cls, seeds_dict):
        dashboards = seeds_dict.get('dashboards', {})
        ci_dicts = dashboards.get('ci_systems', [])
        product_dicts = dashboards.get('products', [])
        jenkins_list = seeds_dict.get('sources', {}).get('jenkins', [])
        ci_systems, products = [], {}

        cis_map = {
            ci['key']: {'name': ci['title']} for ci in ci_dicts
        }

        for version in product_dicts:
            try:
                for section in version['sections']:
                    products.update({
                        section['key']: {
                            'name': section['title'],
                            'version': version['version'],
                            'is_active': True,
                            'rules': [],
                        }
                    })
            except KeyError as exc:
                msg = (
                    u'Can not import Product Ci: "%s" from the seeds file. '
                    u'Required parameter is missed: %s'
                ) % (section.get('title', ''), exc)
                LOGGER.error(msg)
                return jenkins_list, product_dicts, msg

        for jenkins_dict in jenkins_list:
            try:
                ci = {
                    'name': '',
                    'rules': [],
                    'is_active': True,
                    'url': jenkins_dict['url'],
                    'username': jenkins_dict.get('auth', {}).get(
                        'username', ''
                    ),
                    'password': jenkins_dict.get('auth', {}).get(
                        'password', ''
                    ),
                }
            except KeyError as exc:
                msg = (
                    u'Can not import CI System from the seeds file. '
                    u'Required parameter is missed: %s'
                ) % exc
                LOGGER.error(msg)
                return jenkins_list, product_dicts, msg

            jobs = jenkins_dict.get('query', {}).get('jobs', [])
            views = jenkins_dict.get('query', {}).get('views', [])

            try:
                for job in jobs:
                    for name in job['names']:
                        rule = cls._parse_job(job, name)

                        for key in job['dashboards']:
                            # ci exist, get the name
                            if key in cis_map.keys():
                                ci['name'] = cis_map[key]['name']

                            # rule in product
                            if key in products.keys():
                                rule['ci_system_name'] = ci['name']
                                products[key]['rules'].append(rule)
                        ci['rules'].append(rule)

                for job in views:
                    for name in job['names']:
                        rule = cls._parse_job(job, name, 'View')

                        for key in job['dashboards']:
                            # ci exist, get the name
                            if key in cis_map.keys():
                                ci['name'] = cis_map[key]['name']

                            # rule in product
                            if key in products.keys():
                                rule['ci_system_name'] = ci['name']
                                products[key]['rules'].append(rule)
                        ci['rules'].append(rule)
            except KeyError as exc:
                msg = 'Can not create rule during CI import: %s' % exc
                LOGGER.error(msg)
                return jenkins_list, product_dicts, msg

            for rule in ci['rules']:
                if ci['rules'].count(rule) > 1:
                    ci['rules'].remove(rule)

            ci_systems.append(ci)

        return ci_systems, products.values(), False

    @classmethod
    def _import_ci(cls, ci):
        try:
            ci_url = ci['url']

            try:
                new_ci = cls.objects.get(url=ci_url)
            except cls.DoesNotExist:
                new_ci = cls(url=ci_url)

            new_ci.username = ci.get('username', '')
            new_ci.password = ci.get('password', '')
            new_ci.is_active = ci.get('is_active', False)
            new_ci.sticky_failure = ci.get('sticky_failure', False)
            new_ci.name = ci.get('name', '')
            new_ci.full_clean()
            new_ci.save()

            rules, error = cls.create_rule_for_ci(
                ci.get('rules', []), new_ci
            )
            if error:
                return None, error
        except (IntegrityError, ValidationError) as exc:
            msg = (
                'Can not import CI: "%s" from the seeds file. '
                'Error(s) occured: %s'
            )
            LOGGER.error(msg, ci_url, exc)
            return None, msg % (ci_url, exc)
        except KeyError as exc:
            msg = (
                'Can not import CI: "%s" from the seeds file. '
                'Required parameter is missed: %s'
            )
            LOGGER.error(msg, ci_url, exc)
            return None, msg % (ci_url, exc)

        return new_ci, None

    @classmethod
    def _import_product_status(cls, product):
        product_name = product.get('name', '')
        version = product.get('version', '')

        try:
            if not product_name:
                raise KeyError('name')

            try:
                new_product = ProductCi.objects.get(
                    name=product_name,
                    version=version
                )
            except ProductCi.DoesNotExist:
                new_product = ProductCi(name=product_name, version=version)

            new_product.is_active = product.get('is_active', False)
            new_product.full_clean()
            new_product.save()

            product_rules, error = cls.find_rules_for_product(
                product.get('rules', [])
            )
            if error is not True:
                new_product.rules = product_rules
                new_product.save()
            else:
                return None, 'Product Status {} has invalid rules.'.format(
                   new_product.name
                )
        except (IntegrityError, ValidationError) as exc:
            msg = (
                'Can not import ProductCi: "%s" from the seeds file. '
                'Error(s) occured: %s'
            )
            LOGGER.error(msg, product_name, exc)
            return None, msg % (product_name, exc)
        except KeyError as exc:
            msg = (
                'Can not import ProductCi: "%s" from the seeds file. '
                'Required parameter is missed: %s'
            )
            LOGGER.error(msg, product_name, exc)
            return None, msg % (product_name, exc)

        return new_product, None

    @classmethod
    def find_rules_for_product(cls, rules_dicts):
        rules = []

        for rule_dict in rules_dicts:
            rule, error = cls._rule_by_dict(rule_dict)

            if error:
                return [], True

            rules.append(rule)

        return rules, False

    @classmethod
    def _rule_by_dict(cls, rule_dict):
        try:
            ci = cls.objects.get(name=rule_dict['ci_system_name'])

            rule = Rule.objects.get(
                name=rule_dict['name'],
                rule_type=Rule.type_by_name(
                    rule_dict.get(
                        'rule_type',
                        constants.DEFAULT_RULE_TYPE
                    )
                ),
                ci_system_id=ci.pk,
                trigger_type=Rule.trigger_type_by_name(
                    rule_dict.get(
                        'trigger_type',
                        constants.DEFAULT_TRIGGER_TYPE
                    )
                ),
                gerrit_refspec=rule_dict.get('gerrit_refspec', ''),
                gerrit_branch=rule_dict.get('gerrit_branch', ''),
            )
        except cls.DoesNotExist as exc:
            LOGGER.error(
                'Can not find CiSystem mentioned in rule '
                'for Product Status during import: %s',
                exc)
        except Rule.DoesNotExist as exc:
            LOGGER.error(
                'Can not find the rule for Product Status '
                'during import: %s',
                exc
            )
        except KeyError as exc:
            LOGGER.error(
                'Rule for Product Status configure improperly: %s', exc)
        else:
            return rule, False

        return None, True

    @classmethod
    def deactivate_previous_cis(cls, previous_cis, new_cis):
        for url in previous_cis - new_cis:
            try:
                ci = cls.objects.get(url=url)
                ci.is_active = False
                ci.save()
            except cls.DoesNotExist as exc:
                LOGGER.error(
                    'Can not deactivate unexistent ci during import: %s', exc
                )


class ProductCi(models.Model):

    rules = models.ManyToManyField(Rule)
    name = models.CharField(max_length=50)
    is_active = models.BooleanField(default=False)
    version = models.CharField(max_length=255, default='', blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_changed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = (
            'name',
            'version',
        )

    def __unicode__(self):
        return self.name

    def update_status(self):
        self.set_status(self.rules.filter(is_active=True))

    def set_status(self, rules):
        previous_status = None
        checks = []

        for rule in rules:
            try:
                check = rule.rulecheck_set.latest()
                checks.append(check)
            except RuleCheck.DoesNotExist:
                pass

        if checks:
            status_type = self._get_status_for_checks(checks)

            try:
                previous_status = self.productcistatus_set.latest()
            except ProductCiStatus.DoesNotExist:
                pass

            if previous_status and (
                    status_type == previous_status.status_type or
                    status_type == constants.STATUS_IN_PROGRESS):
                return

            ProductCiStatus.objects.create(
                product_ci=self,
                summary='Assigned automaticaly by a periodic task',
                status_type=status_type,
                version=self.version,
                last_changed_at=timezone.now()
            )

    def latest_rule_checks(self):
        checks = []

        for rule in self.rules.filter(is_active=True):
            try:
                check = rule.rulecheck_set.latest()
                checks.append(check)
            except RuleCheck.DoesNotExist:
                pass

        return checks

    def all_statuses(self):
        return [rule_check.status for rule_check in self.latest_rule_checks()]

    def active_status_time(self, version):
        if version:
            try:
                status = self.productcistatus_set.filter(
                    version=version).latest()
                return timesince(status.last_changed_at)
            except ProductCiStatus.DoesNotExist:
                return None
        else:
            status = self.current_status()
            if status:
                return timesince(status.last_changed_at)

    def current_status(self):
        try:
            status = self.productcistatus_set.latest()
        except ProductCiStatus.DoesNotExist:
            status = None

        return status

    def _get_status_for_checks(self, checks):
        statuses = [check.status_type for check in checks]

        if all(s == constants.STATUS_SUCCESS for s in statuses):
            return constants.STATUS_SUCCESS
        elif all(s == constants.STATUS_ERROR for s in statuses):
            return constants.STATUS_ERROR
        elif constants.STATUS_IN_PROGRESS in statuses:
            return constants.STATUS_IN_PROGRESS
        elif constants.STATUS_FAIL in statuses:
            return constants.STATUS_FAIL
        else:
            return constants.STATUS_SKIP

    def current_status_type(self):
        try:
            return self.productcistatus_set.latest().status_type
        except ProductCiStatus.DoesNotExist:
            return constants.STATUS_SKIP

    def current_status_text(self):
        status = self.current_status()
        return Status.text_for_type(status)

    @classmethod
    def deactivate_previous_products(cls, old_names, new_names):
        for name, version in old_names - new_names:
            try:
                p = cls.objects.get(name=name, version=version)
                p.is_active = False
                p.save()
            except cls.DoesNotExist as exc:
                LOGGER.error(
                    'Can not deactivate unexistent Product Status '
                    'during import: %s',
                    exc
                )


class AbstractStatus(models.Model):

    status_type = models.IntegerField(default=constants.STATUS_SUCCESS,
                                      choices=constants.STATUS_TYPE_CHOICES)
    summary = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    is_manual = models.BooleanField(default=False)
    user = models.ForeignKey(
        User,
        limit_choices_to={'is_staff': True},
        on_delete=models.SET_NULL,
        related_name="%(app_label)s_%(class)s_author",
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(default=timezone.now)
    last_changed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        abstract = True
        ordering = ('-created_at',)
        get_latest_by = 'created_at'

    def __str__(self):
        text = self.text_for_type(self.status_type)

        try:
            ci = self.ci_system
        except AttributeError:
            ci = self.product_ci

        return '{status} (ci: "{ci}")'.format(
            status=text,
            ci=ci)

    def status_text(self):
        return self.text_for_type(self.status_type)

    @staticmethod
    def text_for_type(status_type):
        return next(
            (name
             for idx, name
             in constants.STATUS_TYPE_CHOICES
             if idx == status_type),
            'Aborted'
        )

    def author_username(self):
        if self.is_manual:
            if self.user:
                author = self.user.username
            else:
                author = 'Inactive User'
        else:
            if self.user:
                author = self.user.username
            else:
                author = 'Assigned Automatically'

        return author


class Status(AbstractStatus):

    ci_system = models.ForeignKey(CiSystem, on_delete=models.CASCADE)

    def get_absolute_url(self):
        return reverse('status_detail', kwargs={'pk': self.pk})

    def rule_checks(self):
        return self.rulecheck_set.all()

    def failed_rule_checks(self):
        return self.rule_checks().filter(status_type=constants.STATUS_FAIL)

    @staticmethod
    def delele_unused_rulechecks(sender, instance, **kwargs):
        for rule_check in instance.rule_checks():
            if rule_check.status.count() == 1:
                rule_check.delete()

    @staticmethod
    def get_type_by_check_results(rule_checks_mask):
        if rule_checks_mask == {constants.STATUS_SUCCESS}:
            return constants.STATUS_SUCCESS
        elif rule_checks_mask == {constants.STATUS_ERROR}:
            return constants.STATUS_ERROR
        elif constants.STATUS_IN_PROGRESS in rule_checks_mask:
            return constants.STATUS_IN_PROGRESS
        elif constants.STATUS_FAIL in rule_checks_mask:
            return constants.STATUS_FAIL

        return constants.STATUS_SKIP

pre_delete.connect(Status.delele_unused_rulechecks, sender=Status)


class ProductCiStatus(AbstractStatus):

    product_ci = models.ForeignKey(ProductCi, on_delete=models.CASCADE)
    version = models.CharField(max_length=255, default='')

    def get_absolute_url(self):
        return reverse('product_ci_status_detail', kwargs={'pk': self.pk})
