# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CiSystem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url', models.URLField(unique=True)),
                ('name', models.CharField(default='', max_length=50, blank=True)),
                ('username', models.CharField(default='', max_length=50, blank=True)),
                ('password', models.CharField(default='', max_length=100, blank=True)),
                ('is_active', models.BooleanField(default=False)),
                ('sticky_failure', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='ProductCi',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('is_active', models.BooleanField(default=False)),
                ('version', models.CharField(default='', max_length=255, blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('last_changed_at', models.DateTimeField(default=django.utils.timezone.now)),
            ],
        ),
        migrations.CreateModel(
            name='ProductCiStatus',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('status_type', models.IntegerField(default=1, choices=[(1, b'Success'), (2, b'Failed'), (4, b'Skipped'), (8, b'Aborted'), (16, b'In Progress'), (32, b'Error')])),
                ('summary', models.CharField(max_length=255)),
                ('description', models.TextField(default='', blank=True)),
                ('is_manual', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('last_changed_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('version', models.CharField(default='', max_length=255)),
                ('product_ci', models.ForeignKey(to='ci_dashboard.ProductCi')),
                ('user', models.ForeignKey(related_name='ci_dashboard_productcistatus_author', on_delete=django.db.models.deletion.SET_NULL, blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ('created_at', 'id'),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Rule',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(default='', blank=True)),
                ('rule_type', models.IntegerField(default=1, choices=[(1, b'Job'), (2, b'View')])),
                ('trigger_type', models.IntegerField(default=1, choices=[(1, b'Timer'), (2, b'Gerrit trigger'), (4, b'Manual'), (7, b'Any')])),
                ('gerrit_refspec', models.CharField(default='', max_length=255, blank=True)),
                ('gerrit_branch', models.CharField(default='', max_length=255, blank=True)),
                ('is_active', models.BooleanField(default=False)),
                ('last_updated', models.DateTimeField(default=None, null=True, blank=True)),
                ('ci_system', models.ForeignKey(to='ci_dashboard.CiSystem')),
            ],
        ),
        migrations.CreateModel(
            name='RuleCheck',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('status_type', models.IntegerField(default=1, choices=[(1, b'Success'), (2, b'Failed'), (4, b'Skipped'), (8, b'Aborted'), (16, b'In Progress'), (32, b'Error')])),
                ('running', models.IntegerField(default=0)),
                ('queued', models.IntegerField(default=0)),
                ('build_number', models.IntegerField(default=0)),
                ('is_running_now', models.BooleanField(default=False)),
                ('last_successfull_build_link', models.URLField(default='', blank=True)),
                ('last_failed_build_link', models.URLField(default='', blank=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('rule', models.ForeignKey(to='ci_dashboard.Rule')),
            ],
            options={
                'ordering': ('created_at', 'id'),
            },
        ),
        migrations.CreateModel(
            name='Stats',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Status',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('status_type', models.IntegerField(default=1, choices=[(1, b'Success'), (2, b'Failed'), (4, b'Skipped'), (8, b'Aborted'), (16, b'In Progress'), (32, b'Error')])),
                ('summary', models.CharField(max_length=255)),
                ('description', models.TextField(default='', blank=True)),
                ('is_manual', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('last_changed_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('ci_system', models.ForeignKey(to='ci_dashboard.CiSystem')),
                ('user', models.ForeignKey(related_name='ci_dashboard_status_author', on_delete=django.db.models.deletion.SET_NULL, blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ('created_at', 'id'),
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='rulecheck',
            name='status',
            field=models.ManyToManyField(to='ci_dashboard.Status'),
        ),
        migrations.AddField(
            model_name='productci',
            name='rules',
            field=models.ManyToManyField(to='ci_dashboard.Rule'),
        ),
        migrations.AlterUniqueTogether(
            name='rule',
            unique_together=set([('name', 'rule_type', 'trigger_type', 'ci_system', 'gerrit_refspec', 'gerrit_branch')]),
        ),
        migrations.AlterUniqueTogether(
            name='productci',
            unique_together=set([('name', 'version')]),
        ),
    ]
