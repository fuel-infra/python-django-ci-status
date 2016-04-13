# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Removing unique constraint on 'Rule', fields ['rule_type', 'name', 'trigger_type', 'gerrit_refspec', 'version', 'ci_system', 'gerrit_branch']
        db.delete_unique(u'ci_checks_rule', ['rule_type', 'name', 'trigger_type', 'gerrit_refspec', 'version', 'ci_system_id', 'gerrit_branch'])

        # Deleting field 'Rule.version'
        db.delete_column(u'ci_checks_rule', 'version')

        # Adding unique constraint on 'Rule', fields ['rule_type', 'name', 'trigger_type', 'gerrit_refspec', 'ci_system', 'gerrit_branch']
        db.create_unique(u'ci_checks_rule', ['rule_type', 'name', 'trigger_type', 'gerrit_refspec', 'ci_system_id', 'gerrit_branch'])


    def backwards(self, orm):
        # Removing unique constraint on 'Rule', fields ['rule_type', 'name', 'trigger_type', 'gerrit_refspec', 'ci_system', 'gerrit_branch']
        db.delete_unique(u'ci_checks_rule', ['rule_type', 'name', 'trigger_type', 'gerrit_refspec', 'ci_system_id', 'gerrit_branch'])

        # Adding field 'Rule.version'
        db.add_column(u'ci_checks_rule', 'version',
                      self.gf('django.db.models.fields.CharField')(default=u'', max_length=255),
                      keep_default=False)

        # Adding unique constraint on 'Rule', fields ['rule_type', 'name', 'trigger_type', 'gerrit_refspec', 'version', 'ci_system', 'gerrit_branch']
        db.create_unique(u'ci_checks_rule', ['rule_type', 'name', 'trigger_type', 'gerrit_refspec', 'version', 'ci_system_id', 'gerrit_branch'])


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'ci_checks.rule': {
            'Meta': {'unique_together': "((u'name', u'rule_type', u'trigger_type', u'ci_system', u'gerrit_refspec', u'gerrit_branch'),)", 'object_name': 'Rule'},
            'ci_system': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['ci_system.CiSystem']"}),
            'description': ('django.db.models.fields.TextField', [], {'default': "u''", 'blank': 'True'}),
            'gerrit_branch': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '255', 'blank': 'True'}),
            'gerrit_refspec': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '255', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'rule_type': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'trigger_type': ('django.db.models.fields.IntegerField', [], {'default': '1'})
        },
        u'ci_checks.rulecheck': {
            'Meta': {'ordering': "(u'-created_at',)", 'object_name': 'RuleCheck'},
            'build_number': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_running_now': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'queued': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'rule': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['ci_checks.Rule']"}),
            'running': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'status': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['ci_system.Status']", 'symmetrical': 'False'}),
            'status_type': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'ci_system.cisystem': {
            'Meta': {'object_name': 'CiSystem'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '50', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '100', 'blank': 'True'}),
            'sticky_failure': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'unique': 'True', 'max_length': '200'}),
            'username': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '50', 'blank': 'True'})
        },
        u'ci_system.status': {
            'Meta': {'ordering': "(u'-created_at',)", 'object_name': 'Status'},
            'ci_system': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['ci_system.CiSystem']"}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'default': "u''", 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_manual': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_changed_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'status_type': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'summary': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "u'ci_system_status_author'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['ci_checks']
