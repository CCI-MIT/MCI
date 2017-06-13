# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Session.opentok_session_id'
        db.add_column('mci_session', 'opentok_session_id',
                      self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True),
                      keep_default=False)

        # Deleting field 'CompletedTask.opentok_session_id'
        db.delete_column('mci_completedtask', 'opentok_session_id')


    def backwards(self, orm):
        # Deleting field 'Session.opentok_session_id'
        db.delete_column('mci_session', 'opentok_session_id')

        # Adding field 'CompletedTask.opentok_session_id'
        db.add_column('mci_completedtask', 'opentok_session_id',
                      self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True),
                      keep_default=False)


    models = {
        'mci.completedtask': {
            'Meta': {'ordering': "['-start_time']", 'object_name': 'CompletedTask'},
            'completed_task_order': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'etherpad_workspace_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'expected_finish_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'expected_start_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mci.Session']"}),
            'session_group': ('django.db.models.fields.IntegerField', [], {}),
            'start_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'task': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mci.Task']"})
        },
        'mci.completedtaskgriditem': {
            'Meta': {'object_name': 'CompletedTaskGridItem'},
            'answer': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'completed_task': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mci.CompletedTask']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'subject': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mci.Subject']", 'null': 'True'}),
            'task_grid_item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mci.TaskGridItem']"})
        },
        'mci.concentrationcard': {
            'Meta': {'object_name': 'ConcentrationCard'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        },
        'mci.concentrationcardset': {
            'Meta': {'object_name': 'ConcentrationCardSet'},
            'cards': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['mci.ConcentrationCard']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        },
        'mci.concentrationcardsetmember': {
            'Meta': {'unique_together': "(('card', 'card_set'),)", 'object_name': 'ConcentrationCardSetMember'},
            'card': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mci.ConcentrationCard']"}),
            'card_set': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mci.ConcentrationCardSet']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'mci.concentrationround': {
            'Meta': {'object_name': 'ConcentrationRound'},
            'completed_task': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mci.CompletedTask']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'position': ('django.db.models.fields.SmallIntegerField', [], {}),
            'started': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'mci.concentrationroundposition': {
            'Meta': {'object_name': 'ConcentrationRoundPosition'},
            'card': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mci.ConcentrationCard']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'position': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'rnd': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mci.ConcentrationRound']"})
        },
        'mci.concentrationroundtemplate': {
            'Meta': {'object_name': 'ConcentrationRoundTemplate'},
            'card_set': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mci.ConcentrationCardSet']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'positions': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'mci.etherpadlite': {
            'Meta': {'ordering': "['key']", 'object_name': 'EtherpadLite', 'db_table': "'store'", 'managed': 'False'},
            'key': ('django.db.models.fields.TextField', [], {'max_length': '100', 'primary_key': 'True'}),
            'value_raw': ('django.db.models.fields.TextField', [], {'db_column': "'value'"})
        },
        'mci.eventlog': {
            'Meta': {'object_name': 'EventLog'},
            'chat_name': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'completed_task': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mci.CompletedTask']", 'null': 'True'}),
            'data': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'event': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip_address': ('django.db.models.fields.IPAddressField', [], {'max_length': '15', 'null': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mci.Session']", 'null': 'True'}),
            'session_group': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'subject': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mci.Subject']", 'null': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {})
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
            'opentok_session_id': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'start_datetime': ('django.db.models.fields.DateTimeField', [], {}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'task_groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['mci.TaskGroup']", 'symmetrical': 'False'}),
            'waiting_room_time': ('django.db.models.fields.PositiveIntegerField', [], {'default': '900'})
        },
        'mci.subject': {
            'Meta': {'object_name': 'Subject'},
            'consent_and_individual_tests_completed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'emblem': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'external_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '32'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_waiting_room': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'opentok_token': ('django.db.models.fields.CharField', [], {'max_length': '300', 'null': 'True', 'blank': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mci.Session']"}),
            'session_group': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'mci.task': {
            'Meta': {'ordering': "['task_group', 'task_order']", 'object_name': 'Task'},
            'chat_enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'etherpad_template': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'grid_css': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'grid_header_instructions': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instructions': ('django.db.models.fields.TextField', [], {}),
            'instructions_time': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'instructions_width': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'interaction_instructions': ('django.db.models.fields.TextField', [], {}),
            'interaction_time': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'primer': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'primer_time': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'task_group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mci.TaskGroup']"}),
            'task_order': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'task_type': ('django.db.models.fields.CharField', [], {'max_length': '1'})
        },
        'mci.taskconcentrationroundtemplateindex': {
            'Meta': {'object_name': 'TaskConcentrationRoundTemplateIndex'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'position': ('django.db.models.fields.SmallIntegerField', [], {}),
            'rnd_template': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mci.ConcentrationRoundTemplate']"}),
            'task': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mci.Task']"})
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