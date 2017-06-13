# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'SessionTemplate.scribe_enabled'
        db.add_column(u'mci_sessiontemplate', 'scribe_enabled',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'SessionTemplate.confirmation_required'
        db.add_column(u'mci_sessiontemplate', 'confirmation_required',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Deleting field 'CompletedTask.scribe'
        db.delete_column(u'mci_completedtask', 'scribe_id')

        # Adding field 'Subject.scribe'
        db.add_column(u'mci_subject', 'scribe',
                      self.gf('django.db.models.fields.CharField')(default='U', max_length=1),
                      keep_default=False)

        # Adding field 'Session.scribe_enabled'
        db.add_column(u'mci_session', 'scribe_enabled',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'Session.confirmation_required'
        db.add_column(u'mci_session', 'confirmation_required',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Deleting field 'Task.scribe'
        db.delete_column(u'mci_task', 'scribe')


    def backwards(self, orm):
        # Deleting field 'SessionTemplate.scribe_enabled'
        db.delete_column(u'mci_sessiontemplate', 'scribe_enabled')

        # Deleting field 'SessionTemplate.confirmation_required'
        db.delete_column(u'mci_sessiontemplate', 'confirmation_required')

        # Adding field 'CompletedTask.scribe'
        db.add_column(u'mci_completedtask', 'scribe',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mci.Subject'], null=True, blank=True),
                      keep_default=False)

        # Deleting field 'Subject.scribe'
        db.delete_column(u'mci_subject', 'scribe')

        # Deleting field 'Session.scribe_enabled'
        db.delete_column(u'mci_session', 'scribe_enabled')

        # Deleting field 'Session.confirmation_required'
        db.delete_column(u'mci_session', 'confirmation_required')

        # Adding field 'Task.scribe'
        db.add_column(u'mci_task', 'scribe',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)


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
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'mci.avatar': {
            'Meta': {'object_name': 'Avatar'},
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mci.SubjectCountry']", 'null': 'True', 'blank': 'True'}),
            'display_name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'viewed': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'avatars_of'", 'to': u"orm['mci.Subject']"}),
            'viewer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'avatars_for'", 'to': u"orm['mci.Subject']"})
        },
        u'mci.completedtask': {
            'Meta': {'ordering': "['-expected_start_time']", 'object_name': 'CompletedTask'},
            'board_area_height': ('django.db.models.fields.IntegerField', [], {'default': '98'}),
            'board_area_width': ('django.db.models.fields.IntegerField', [], {'default': '192'}),
            'completed_task_order': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'etherpad_workspace_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'expected_finish_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'expected_start_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'num_rounds': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mci.Session']"}),
            'session_group': ('django.db.models.fields.IntegerField', [], {}),
            'solo_subject': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['mci.Subject']"}),
            'start_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'task': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mci.Task']"})
        },
        u'mci.completedtaskgriditem': {
            'Meta': {'object_name': 'CompletedTaskGridItem'},
            'answer': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'completed_task': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mci.CompletedTask']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'subject': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mci.Subject']", 'null': 'True'}),
            'task_grid_item': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mci.TaskGridItem']"})
        },
        u'mci.concentrationcard': {
            'Meta': {'object_name': 'ConcentrationCard'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        },
        u'mci.concentrationcardset': {
            'Meta': {'object_name': 'ConcentrationCardSet'},
            'cards': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['mci.ConcentrationCard']", 'symmetrical': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        },
        u'mci.concentrationround': {
            'Meta': {'object_name': 'ConcentrationRound'},
            'completed_task': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mci.CompletedTask']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'position': ('django.db.models.fields.SmallIntegerField', [], {}),
            'started': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'mci.concentrationroundposition': {
            'Meta': {'object_name': 'ConcentrationRoundPosition'},
            'card': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mci.ConcentrationCard']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'position': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'rnd': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mci.ConcentrationRound']"})
        },
        u'mci.concentrationroundtemplate': {
            'Meta': {'object_name': 'ConcentrationRoundTemplate'},
            'card_set': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mci.ConcentrationCardSet']", 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'positions': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'mci.disguiseselection': {
            'Meta': {'object_name': 'DisguiseSelection'},
            'feminine': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'position': ('django.db.models.fields.SmallIntegerField', [], {}),
            'region': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'disguise_selections'", 'to': u"orm['mci.Region']"}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'disguise_selections'", 'null': 'True', 'to': u"orm['mci.Session']"}),
            'session_template': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'disguise_selections'", 'null': 'True', 'to': u"orm['mci.SessionTemplate']"})
        },
        u'mci.etherpadliterecord': {
            'Meta': {'ordering': "['key']", 'object_name': 'EtherpadLiteRecord', 'db_table': "'store'", 'managed': 'False'},
            'key': ('django.db.models.fields.TextField', [], {'max_length': '100', 'primary_key': 'True'}),
            'value_raw': ('django.db.models.fields.TextField', [], {'db_column': "'value'"})
        },
        u'mci.eventlog': {
            'Meta': {'object_name': 'EventLog'},
            'chat_name': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'completed_task': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mci.CompletedTask']", 'null': 'True'}),
            'data': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'event': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip_address': ('django.db.models.fields.IPAddressField', [], {'max_length': '15', 'null': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mci.Session']", 'null': 'True'}),
            'session_group': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'subject': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mci.Subject']", 'null': 'True'}),
            'timestamp': ('mci.models.DateTimeFractionField', [], {})
        },
        u'mci.pseudonym': {
            'Meta': {'object_name': 'Pseudonym'},
            'feminine': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pseudonym': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'region': ('django.db.models.fields.related.ForeignKey', [], {'default': '9L', 'to': u"orm['mci.Region']"})
        },
        u'mci.region': {
            'Meta': {'object_name': 'Region'},
            'countries': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['mci.SubjectCountry']", 'symmetrical': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'})
        },
        u'mci.session': {
            'Meta': {'ordering': "['-start_datetime']", 'object_name': 'Session'},
            'confirmation_required': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'disguise_regions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['mci.Region']", 'through': u"orm['mci.DisguiseSelection']", 'symmetrical': 'False'}),
            'display_name_page': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'display_name_time': ('django.db.models.fields.PositiveIntegerField', [], {'default': '15'}),
            'done_redirect_url': ('django.db.models.fields.CharField', [], {'default': "'http://www.google.com'", 'max_length': '256'}),
            'done_text': ('django.db.models.fields.TextField', [], {'default': "'Some default text.'"}),
            'done_time': ('django.db.models.fields.PositiveIntegerField', [], {'default': '15'}),
            'etherpad_admin_author_id': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'etherpad_admin_session_id': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'etherpad_group_id': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'group_creation_method': ('django.db.models.fields.CharField', [], {'default': "'F'", 'max_length': '1'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'initial_task_group': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['mci.TaskGroup']"}),
            'introduction_text': ('django.db.models.fields.TextField', [], {'default': "'Some default text.'"}),
            'introduction_time': ('django.db.models.fields.PositiveIntegerField', [], {'default': '15'}),
            'load_test': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'max_group_size': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'min_group_size': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'msg_err_cannot_form_group': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'opentok_session_id': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'roster_page': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'roster_time': ('django.db.models.fields.PositiveIntegerField', [], {'default': '10'}),
            'scribe_enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'session_template_frequency': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mci.SessionTemplateFrequency']", 'null': 'True', 'blank': 'True'}),
            'solo_task_group_end': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['mci.TaskGroup']"}),
            'solo_task_group_start': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['mci.TaskGroup']"}),
            'start_datetime': ('django.db.models.fields.DateTimeField', [], {}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'subjects_disguised': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'task_groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['mci.TaskGroup']", 'symmetrical': 'False'}),
            'usergroups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['mci.UserGroup']", 'symmetrical': 'False'}),
            'video_enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'waiting_room_time': ('django.db.models.fields.PositiveIntegerField', [], {'default': '900'})
        },
        u'mci.sessionbuilder': {
            'Meta': {'object_name': 'SessionBuilder'},
            'ask_for_group_id': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'custom_id_label': ('django.db.models.fields.CharField', [], {'default': "'Username (e.g. Mturk ID)'", 'max_length': '200'}),
            'error_connecting_to_game_server_msg': ('django.db.models.fields.TextField', [], {'default': "'Your browser is Javascript-enabled but for some reason\\n        cannot connect to our real-time game server.  We have logged this and\\n        will do our best to improve compatibility in the future.'"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'javascript_test_explanation': ('django.db.models.fields.TextField', [], {'default': "'We are testing Javascript in your browser.  If this message\\n        does not go away, Javascript is disabled or broken in your browser.\\n        You must have Javascript working in order to continue.'"}),
            'last_survey_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'mturk': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'previous_play_forbidden': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'previous_play_required': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'session_templates': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['mci.SessionTemplate']", 'through': u"orm['mci.SessionTemplateFrequency']", 'symmetrical': 'False'}),
            'subjects_per_session': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'usergroups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['mci.UserGroup']", 'symmetrical': 'False'}),
            'waiting_room_closes': ('django.db.models.fields.DateTimeField', [], {}),
            'waiting_room_opens': ('django.db.models.fields.DateTimeField', [], {})
        },
        u'mci.sessionbuildersurvey': {
            'Meta': {'object_name': 'SessionBuilderSurvey'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sessionbuilder': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mci.SessionBuilder']", 'unique': 'True'})
        },
        u'mci.sessionregionquota': {
            'Meta': {'object_name': 'SessionRegionQuota'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'region': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mci.Region']"}),
            'sessionbuilder': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mci.SessionBuilder']"}),
            'subjects': ('django.db.models.fields.PositiveSmallIntegerField', [], {})
        },
        u'mci.sessionsetup': {
            'Meta': {'object_name': 'SessionSetup'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mci.Session']", 'unique': 'True'})
        },
        u'mci.sessiontemplate': {
            'Meta': {'object_name': 'SessionTemplate'},
            'confirmation_required': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'disguise_regions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['mci.Region']", 'through': u"orm['mci.DisguiseSelection']", 'symmetrical': 'False'}),
            'display_name_page': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'display_name_time': ('django.db.models.fields.PositiveIntegerField', [], {'default': '15'}),
            'done_redirect_url': ('django.db.models.fields.CharField', [], {'default': "'http://www.google.com'", 'max_length': '256'}),
            'done_text': ('django.db.models.fields.TextField', [], {'default': "'Some default text.'"}),
            'done_time': ('django.db.models.fields.PositiveIntegerField', [], {'default': '15'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'initial_task_group': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['mci.TaskGroup']"}),
            'introduction_text': ('django.db.models.fields.TextField', [], {'default': "'Some default text.'"}),
            'introduction_time': ('django.db.models.fields.PositiveIntegerField', [], {'default': '15'}),
            'load_test': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'msg_err_cannot_form_group': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'roster_page': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'roster_time': ('django.db.models.fields.PositiveIntegerField', [], {'default': '10'}),
            'scribe_enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'solo_task_group_end': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['mci.TaskGroup']"}),
            'solo_task_group_start': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['mci.TaskGroup']"}),
            'subjects_disguised': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'task_groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['mci.TaskGroup']", 'symmetrical': 'False'}),
            'usergroups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['mci.UserGroup']", 'symmetrical': 'False'}),
            'video_enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'mci.sessiontemplatefrequency': {
            'Meta': {'object_name': 'SessionTemplateFrequency'},
            'frequency': ('django.db.models.fields.FloatField', [], {'default': '1.0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'session_builder': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'session_template_freqs'", 'to': u"orm['mci.SessionBuilder']"}),
            'session_template': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'freqs_visavis_session_builders'", 'to': u"orm['mci.SessionTemplate']"})
        },
        u'mci.si_sb_status': {
            'Meta': {'object_name': 'SI_SB_Status'},
            'arrival_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'dispatch_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_waiting_room_checkin': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2015, 5, 9, 0, 0)'}),
            'rejected': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'rejection_reason': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'sb_group_id': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'sessionbuilder': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'subject_identity_statuses'", 'to': u"orm['mci.SessionBuilder']"}),
            'subject': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mci.Subject']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'subject_identity': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'sessionbuilder_statuses'", 'to': u"orm['mci.SubjectIdentity']"}),
            'survey_tag': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'waiting_for': ('django.db.models.fields.IntegerField', [], {'default': '-1'})
        },
        u'mci.squarespiece': {
            'Meta': {'object_name': 'SquaresPiece'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'squares_set': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mci.SquaresSet']"}),
            'v0_x': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'v0_y': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'v1_x': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'v1_y': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'v2_x': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'v2_y': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'v3_x': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'v3_y': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'v4_x': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'v4_y': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'v5_x': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'v5_y': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'v6_x': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'v6_y': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        u'mci.squaresround': {
            'Meta': {'object_name': 'SquaresRound'},
            'completed_task': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mci.CompletedTask']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'position': ('django.db.models.fields.SmallIntegerField', [], {}),
            'squares_sets': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['mci.SquaresSet']", 'through': u"orm['mci.SquaresRoundSquaresSetThrough']", 'symmetrical': 'False'})
        },
        u'mci.squaresroundsquaressetthrough': {
            'Meta': {'object_name': 'SquaresRoundSquaresSetThrough'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'position': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'squares_round': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mci.SquaresRound']"}),
            'squares_set': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mci.SquaresSet']"})
        },
        u'mci.squaresroundtemplate': {
            'Meta': {'object_name': 'SquaresRoundTemplate'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'squares_sets': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['mci.SquaresSet']", 'through': u"orm['mci.SquaresRoundTemplateSquaresSetThrough']", 'symmetrical': 'False'})
        },
        u'mci.squaresroundtemplatesquaressetthrough': {
            'Meta': {'object_name': 'SquaresRoundTemplateSquaresSetThrough'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'position': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'squares_round_template': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mci.SquaresRoundTemplate']"}),
            'squares_set': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mci.SquaresSet']"})
        },
        u'mci.squaresset': {
            'Meta': {'object_name': 'SquaresSet'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        },
        u'mci.subject': {
            'Meta': {'object_name': 'Subject'},
            'consent_and_individual_tests_completed': ('django.db.models.fields.BooleanField', [], {}),
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mci.SubjectCountry']", 'null': 'True', 'blank': 'True'}),
            'display_name': ('django.db.models.fields.CharField', [], {'max_length': '12', 'null': 'True', 'blank': 'True'}),
            'etherpad_author_id': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'etherpad_session_id': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'external_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '32'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_waiting_room': ('django.db.models.fields.BooleanField', [], {}),
            'opentok_token': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True', 'blank': 'True'}),
            'scribe': ('django.db.models.fields.CharField', [], {'default': "'U'", 'max_length': '1'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mci.Session']"}),
            'session_group': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        u'mci.subjectcountry': {
            'Meta': {'ordering': "['-list_priority', 'flag']", 'object_name': 'SubjectCountry'},
            'flag': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'list_priority': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'mci.subjectidentity': {
            'Meta': {'object_name': 'SubjectIdentity'},
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mci.SubjectCountry']", 'null': 'True', 'blank': 'True'}),
            'display_name': ('django.db.models.fields.CharField', [], {'max_length': '12', 'null': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mturk_id': ('django.db.models.fields.CharField', [], {'max_length': '200', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'opentok_token': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True', 'blank': 'True'}),
            'sessionbuilders': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'subject_identities'", 'symmetrical': 'False', 'through': u"orm['mci.SI_SB_Status']", 'to': u"orm['mci.SessionBuilder']"})
        },
        u'mci.task': {
            'Meta': {'ordering': "['task_group', 'task_order']", 'object_name': 'Task'},
            'chat_enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'etherpad_template': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'grid_css': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'grid_header_instructions': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instructions': ('django.db.models.fields.TextField', [], {'default': "'This is default text.'"}),
            'instructions_time': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '10'}),
            'instructions_width': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'interaction_instructions': ('django.db.models.fields.TextField', [], {'default': "'This is default text.'"}),
            'interaction_time': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '60'}),
            'mousemove_interval': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'pairs_in_generated_round': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '16'}),
            'pct_tiles_on': ('django.db.models.fields.FloatField', [], {'default': '0.29999999999999999'}),
            'preplay_countdown_sublabel': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'primer': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'primer_sidebar_text': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'primer_time': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '15'}),
            'starting_height': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '2'}),
            'starting_width': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '3'}),
            'task_group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mci.TaskGroup']"}),
            'task_order': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'task_type': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'tiles_preview_seconds': ('django.db.models.fields.FloatField', [], {'default': '2.0'}),
            'time_before_play': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'time_between_rounds': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '5'}),
            'time_unmatched_pairs_remain_faceup': ('django.db.models.fields.FloatField', [], {'default': '1'})
        },
        u'mci.taskconcentrationroundtemplateindex': {
            'Meta': {'object_name': 'TaskConcentrationRoundTemplateIndex'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'position': ('django.db.models.fields.SmallIntegerField', [], {}),
            'rnd_template': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mci.ConcentrationRoundTemplate']"}),
            'task': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mci.Task']"})
        },
        u'mci.taskgriditem': {
            'Meta': {'object_name': 'TaskGridItem'},
            'column': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'correct_answer': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'field_width': ('django.db.models.fields.PositiveSmallIntegerField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image_label': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'blank': 'True'}),
            'readonly': ('django.db.models.fields.BooleanField', [], {}),
            'row': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'task': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mci.Task']"}),
            'text_label': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'})
        },
        u'mci.taskgroup': {
            'Meta': {'object_name': 'TaskGroup'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'usergroups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['mci.UserGroup']", 'symmetrical': 'False'})
        },
        u'mci.taskprivateinformation': {
            'Meta': {'ordering': "['information']", 'object_name': 'TaskPrivateInformation'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'information': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'task': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mci.Task']"})
        },
        u'mci.tasksquaresroundtemplateindex': {
            'Meta': {'object_name': 'TaskSquaresRoundTemplateIndex'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'position': ('django.db.models.fields.SmallIntegerField', [], {}),
            'rnd_template': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'task_joints'", 'to': u"orm['mci.SquaresRoundTemplate']"}),
            'task': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'squares_round_template_indices'", 'to': u"orm['mci.Task']"})
        },
        u'mci.text': {
            'Meta': {'object_name': 'Text'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'text': ('django.db.models.fields.TextField', [], {})
        },
        u'mci.usergroup': {
            'Meta': {'object_name': 'UserGroup'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'ugroups'", 'symmetrical': 'False', 'to': u"orm['auth.User']"})
        },
        u'mci.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'owns_all_owned_objects': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['auth.User']", 'unique': 'True'})
        }
    }

    complete_apps = ['mci']