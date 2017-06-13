# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models
from mci.models import CompletedTask

class Migration(DataMigration):

    def forwards(self, orm):
        for completed_task in CompletedTask.objects.all():
            if completed_task.workspace.find("/p/") == -1:
                completed_task.workspace = completed_task.workspace.replace(":443/",":443/p/")
                completed_task.workspace = completed_task.workspace.replace(":9000/",":9000/p/")
            completed_task.workspace = completed_task.workspace.replace("cci.podconsulting.net:443/","cci.podconsulting.net:9000/")
            completed_task.save()

    def backwards(self, orm):
        for completed_task in CompletedTask.objects.all():
            completed_task.workspace = completed_task.workspace.replace(":443/p/",":443/")
            completed_task.workspace = completed_task.workspace.replace(":9000/p/",":9000/")
            completed_task.save()


    models = {
        'mci.completedtask': {
            'Meta': {'ordering': "['-start_time']", 'object_name': 'CompletedTask'},
            'completed_task_order': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'expected_finish_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'expected_start_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mci.Session']"}),
            'session_group': ('django.db.models.fields.IntegerField', [], {}),
            'start_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'task': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mci.Task']"}),
            'workspace': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        },
        'mci.completedtaskgriditem': {
            'Meta': {'object_name': 'CompletedTaskGridItem'},
            'answer': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'completed_task': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mci.CompletedTask']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'subject': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mci.Subject']", 'null': 'True'}),
            'task_grid_item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mci.TaskGridItem']"})
        },
        'mci.etherpadlite': {
            'Meta': {'ordering': "['key']", 'object_name': 'EtherpadLite', 'db_table': "'store'", 'managed': 'False'},
            'key': ('django.db.models.fields.TextField', [], {'max_length': '100', 'primary_key': 'True'}),
            'value_raw': ('django.db.models.fields.TextField', [], {'db_column': "'value'"})
        },
        'mci.eventlog': {
            'Meta': {'object_name': 'EventLog'},
            'completed_task': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mci.CompletedTask']", 'null': 'True'}),
            'data': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'event': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip_address': ('django.db.models.fields.IPAddressField', [], {'max_length': '15', 'null': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mci.Session']", 'null': 'True'}),
            'session_group': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'subject': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mci.Subject']", 'null': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        'mci.session': {
            'Meta': {'object_name': 'Session'},
            'done_redirect_url': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'done_text': ('django.db.models.fields.TextField', [], {}),
            'done_time': ('django.db.models.fields.PositiveIntegerField', [], {'default': '15'}),
            'group_creation_method': ('django.db.models.fields.CharField', [], {'default': "'F'", 'max_length': '1'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'initial_task_group': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['mci.TaskGroup']"}),
            'introduction_text': ('django.db.models.fields.TextField', [], {}),
            'introduction_time': ('django.db.models.fields.PositiveIntegerField', [], {'default': '15'}),
            'max_group_size': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'min_group_size': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'start_datetime': ('django.db.models.fields.DateTimeField', [], {}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'task_groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['mci.TaskGroup']", 'symmetrical': 'False'}),
            'waiting_room_time': ('django.db.models.fields.PositiveIntegerField', [], {'default': '900'})
        },
        'mci.subject': {
            'Meta': {'object_name': 'Subject'},
            'consent_and_individual_tests_completed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'external_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '32'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_waiting_room': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mci.Session']"}),
            'session_group': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'mci.task': {
            'Meta': {'ordering': "['task_group', 'task_order']", 'object_name': 'Task'},
            'chat_enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'grid_css': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'grid_header_instructions': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instructions': ('django.db.models.fields.TextField', [], {}),
            'instructions_time': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'instructions_width': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'interaction_instructions': ('django.db.models.fields.TextField', [], {}),
            'interaction_time': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'interaction_workspace_source': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'primer': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'primer_time': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'task_group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mci.TaskGroup']"}),
            'task_order': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'task_type': ('django.db.models.fields.CharField', [], {'max_length': '1'})
        },
        'mci.taskgriditem': {
            'Meta': {'object_name': 'TaskGridItem'},
            'column': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'correct_answer': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'field_width': ('django.db.models.fields.PositiveSmallIntegerField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image_label': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'blank': 'True'}),
            'readonly': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'row': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'task': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mci.Task']"}),
            'text_label': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'})
        },
        'mci.taskgroup': {
            'Meta': {'object_name': 'TaskGroup'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        },
        'mci.taskprivateinformation': {
            'Meta': {'ordering': "['information']", 'object_name': 'TaskPrivateInformation'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'information': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'task': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mci.Task']"})
        },
        'mci.text': {
            'Meta': {'object_name': 'Text'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'text': ('django.db.models.fields.TextField', [], {})
        }
    }

    complete_apps = ['mci']
    symmetrical = True
