# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'SI_SB_Status.rejection_reason'
        db.add_column('mci_si_sb_status', 'rejection_reason',
                      self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'SI_SB_Status.rejection_reason'
        db.delete_column('mci_si_sb_status', 'rejection_reason')


    models = {
        'mci.arabicpseudonym': {
            'Meta': {'object_name': 'ArabicPseudonym'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pseudonym': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'mci.avatar': {
            'Meta': {'object_name': 'Avatar'},
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mci.SubjectCountry']", 'null': 'True', 'blank': 'True'}),
            'display_name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'viewed': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'avatars_of'", 'to': "orm['mci.Subject']"}),
            'viewer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'avatars_for'", 'to': "orm['mci.Subject']"})
        },
        'mci.completedtask': {
            'Meta': {'ordering': "['-start_time']", 'object_name': 'CompletedTask'},
            'completed_task_order': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'etherpad_workspace_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'expected_finish_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'expected_start_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mci.Session']"}),
            'session_group': ('django.db.models.fields.IntegerField', [], {}),
            'solo_subject': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['mci.Subject']"}),
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
        'mci.region': {
            'Meta': {'object_name': 'Region'},
            'countries': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['mci.SubjectCountry']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'mci.session': {
            'Meta': {'ordering': "['-start_datetime']", 'object_name': 'Session'},
            'disguise_subjects': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'done_redirect_url': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'done_text': ('django.db.models.fields.TextField', [], {}),
            'done_time': ('django.db.models.fields.PositiveIntegerField', [], {'default': '15'}),
            'group_creation_method': ('django.db.models.fields.CharField', [], {'default': "'F'", 'max_length': '1'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'initial_task_group': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['mci.TaskGroup']"}),
            'introduction_text': ('django.db.models.fields.TextField', [], {}),
            'introduction_time': ('django.db.models.fields.PositiveIntegerField', [], {'default': '15'}),
            'load_test': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'max_group_size': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'min_group_size': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'opentok_session_id': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'sessionbuilder': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mci.SessionBuilder']", 'null': 'True', 'blank': 'True'}),
            'solo_task_group_end': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['mci.TaskGroup']"}),
            'solo_task_group_start': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['mci.TaskGroup']"}),
            'start_datetime': ('django.db.models.fields.DateTimeField', [], {}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'task_groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['mci.TaskGroup']", 'symmetrical': 'False'}),
            'waiting_room_time': ('django.db.models.fields.PositiveIntegerField', [], {'default': '900'})
        },
        'mci.sessionbuilder': {
            'Meta': {'object_name': 'SessionBuilder'},
            'disguise_subjects': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'done_redirect_url': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'done_text': ('django.db.models.fields.TextField', [], {}),
            'done_time': ('django.db.models.fields.PositiveIntegerField', [], {'default': '15'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'initial_task_group': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['mci.TaskGroup']"}),
            'introduction_text': ('django.db.models.fields.TextField', [], {}),
            'introduction_time': ('django.db.models.fields.PositiveIntegerField', [], {'default': '15'}),
            'last_survey_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'load_test': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'mturk': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'previous_play_forbidden': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'previous_play_required': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'solo_task_group_end': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['mci.TaskGroup']"}),
            'solo_task_group_start': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['mci.TaskGroup']"}),
            'subjects_per_session': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '6'}),
            'task_groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['mci.TaskGroup']", 'symmetrical': 'False'}),
            'waiting_room_closes': ('django.db.models.fields.DateTimeField', [], {}),
            'waiting_room_opens': ('django.db.models.fields.DateTimeField', [], {})
        },
        'mci.sessionbuildersurvey': {
            'Meta': {'object_name': 'SessionBuilderSurvey'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sessionbuilder': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mci.SessionBuilder']", 'unique': 'True'})
        },
        'mci.sessionregionquota': {
            'Meta': {'object_name': 'SessionRegionQuota'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'region': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mci.Region']"}),
            'sessionbuilder': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mci.SessionBuilder']"}),
            'subjects': ('django.db.models.fields.PositiveSmallIntegerField', [], {})
        },
        'mci.sessionsetup': {
            'Meta': {'object_name': 'SessionSetup'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mci.Session']", 'unique': 'True'})
        },
        'mci.si_sb_status': {
            'Meta': {'object_name': 'SI_SB_Status'},
            'arrival_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'dispatch_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_waiting_room_checkin': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 2, 6, 0, 0)'}),
            'rejected': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'rejection_reason': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'sessionbuilder': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'subject_identity_statuses'", 'to': "orm['mci.SessionBuilder']"}),
            'subject': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mci.Subject']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'subject_identity': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'sessionbuilder_statuses'", 'to': "orm['mci.SubjectIdentity']"}),
            'survey_tag': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'waiting_for': ('django.db.models.fields.IntegerField', [], {'default': '-1'})
        },
        'mci.subject': {
            'Meta': {'object_name': 'Subject'},
            'consent_and_individual_tests_completed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mci.SubjectCountry']", 'null': 'True', 'blank': 'True'}),
            'display_name': ('django.db.models.fields.CharField', [], {'max_length': '12', 'null': 'True', 'blank': 'True'}),
            'external_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '32'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_waiting_room': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'opentok_token': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True', 'blank': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mci.Session']"}),
            'session_group': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'mci.subjectcountry': {
            'Meta': {'ordering': "['flag']", 'object_name': 'SubjectCountry'},
            'arab_country': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'flag': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'mci.subjectidentity': {
            'Meta': {'object_name': 'SubjectIdentity'},
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mci.SubjectCountry']", 'null': 'True', 'blank': 'True'}),
            'display_name': ('django.db.models.fields.CharField', [], {'max_length': '12', 'null': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mturk_id': ('django.db.models.fields.CharField', [], {'max_length': '200', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'opentok_token': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True', 'blank': 'True'}),
            'sessionbuilders': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'subject_identities'", 'symmetrical': 'False', 'through': "orm['mci.SI_SB_Status']", 'to': "orm['mci.SessionBuilder']"})
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
            'mousemove_interval': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'pairs_in_generated_round': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '16'}),
            'preplay_countdown_sublabel': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'primer': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'primer_sidebar_text': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'primer_time': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '15'}),
            'task_group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mci.TaskGroup']"}),
            'task_order': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'task_type': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'time_before_play': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'time_between_rounds': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '5'}),
            'time_unmatched_pairs_remain_faceup': ('django.db.models.fields.FloatField', [], {'default': '1'})
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