# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting model 'ArabicPseudonym'
        db.delete_table('mci_arabicpseudonym')

        # Adding model 'SessionTemplateFrequency'
        db.create_table('mci_sessiontemplatefrequency', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('session_template', self.gf('django.db.models.fields.related.ForeignKey')(related_name='freqs_visavis_session_builders', to=orm['mci.SessionTemplate'])),
            ('session_builder', self.gf('django.db.models.fields.related.ForeignKey')(related_name='session_template_freqs', to=orm['mci.SessionBuilder'])),
            ('frequency', self.gf('django.db.models.fields.FloatField')(default=1.0)),
        ))
        db.send_create_signal('mci', ['SessionTemplateFrequency'])

        # Adding model 'SessionTemplate'
        db.create_table('mci_sessiontemplate', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('subjects_disguised', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('solo_task_group_start', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, on_delete=models.SET_NULL, to=orm['mci.TaskGroup'])),
            ('solo_task_group_end', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, on_delete=models.SET_NULL, to=orm['mci.TaskGroup'])),
            ('initial_task_group', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, on_delete=models.SET_NULL, to=orm['mci.TaskGroup'])),
            ('introduction_text', self.gf('django.db.models.fields.TextField')()),
            ('introduction_time', self.gf('django.db.models.fields.PositiveIntegerField')(default=15)),
            ('done_text', self.gf('django.db.models.fields.TextField')()),
            ('done_time', self.gf('django.db.models.fields.PositiveIntegerField')(default=15)),
            ('done_redirect_url', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('load_test', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('mci', ['SessionTemplate'])

        # Adding M2M table for field task_groups on 'SessionTemplate'
        db.create_table('mci_sessiontemplate_task_groups', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('sessiontemplate', models.ForeignKey(orm['mci.sessiontemplate'], null=False)),
            ('taskgroup', models.ForeignKey(orm['mci.taskgroup'], null=False))
        ))
        db.create_unique('mci_sessiontemplate_task_groups', ['sessiontemplate_id', 'taskgroup_id'])

        # Adding model 'RegionDisguiseFrequency'
        db.create_table('mci_regiondisguisefrequency', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('session_template', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='region_disguise_frequencies', null=True, to=orm['mci.SessionTemplate'])),
            ('session', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='region_disguise_frequencies', null=True, to=orm['mci.Session'])),
            ('region', self.gf('django.db.models.fields.related.ForeignKey')(related_name='region_disguise_frequencies', to=orm['mci.Region'])),
            ('frequency', self.gf('django.db.models.fields.FloatField')(default=1.0)),
            ('round_up', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('pct_feminine', self.gf('django.db.models.fields.FloatField')(default=0.5)),
        ))
        db.send_create_signal('mci', ['RegionDisguiseFrequency'])

        # Adding model 'Pseudonym'
        db.create_table('mci_pseudonym', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('pseudonym', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('region', self.gf('django.db.models.fields.related.ForeignKey')(default=20L, to=orm['mci.Region'])),
            ('feminine', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('mci', ['Pseudonym'])

        # Adding unique constraint on 'Region', fields ['name']
        db.create_unique('mci_region', ['name'])

        # Deleting field 'Session.sessionbuilder'
        db.delete_column('mci_session', 'sessionbuilder_id')

        # Deleting field 'Session.disguise_subjects'
        db.delete_column('mci_session', 'disguise_subjects')

        # Adding field 'Session.subjects_disguised'
        db.add_column('mci_session', 'subjects_disguised',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'Session.session_template_frequency'
        db.add_column('mci_session', 'session_template_frequency',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mci.SessionTemplateFrequency'], null=True, blank=True),
                      keep_default=False)

        # Deleting field 'SessionBuilder.introduction_time'
        db.delete_column('mci_sessionbuilder', 'introduction_time')

        # Deleting field 'SessionBuilder.load_test'
        db.delete_column('mci_sessionbuilder', 'load_test')

        # Deleting field 'SessionBuilder.solo_task_group_start'
        db.delete_column('mci_sessionbuilder', 'solo_task_group_start_id')

        # Deleting field 'SessionBuilder.disguise_subjects'
        db.delete_column('mci_sessionbuilder', 'disguise_subjects')

        # Deleting field 'SessionBuilder.done_redirect_url'
        db.delete_column('mci_sessionbuilder', 'done_redirect_url')

        # Deleting field 'SessionBuilder.done_text'
        db.delete_column('mci_sessionbuilder', 'done_text')

        # Deleting field 'SessionBuilder.done_time'
        db.delete_column('mci_sessionbuilder', 'done_time')

        # Deleting field 'SessionBuilder.initial_task_group'
        db.delete_column('mci_sessionbuilder', 'initial_task_group_id')

        # Deleting field 'SessionBuilder.solo_task_group_end'
        db.delete_column('mci_sessionbuilder', 'solo_task_group_end_id')

        # Deleting field 'SessionBuilder.introduction_text'
        db.delete_column('mci_sessionbuilder', 'introduction_text')

        # Removing M2M table for field task_groups on 'SessionBuilder'
        db.delete_table('mci_sessionbuilder_task_groups')

        # Deleting field 'SubjectCountry.arab_country'
        db.delete_column('mci_subjectcountry', 'arab_country')


    def backwards(self, orm):
        # Removing unique constraint on 'Region', fields ['name']
        db.delete_unique('mci_region', ['name'])

        # Adding model 'ArabicPseudonym'
        db.create_table('mci_arabicpseudonym', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('pseudonym', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal('mci', ['ArabicPseudonym'])

        # Deleting model 'SessionTemplateFrequency'
        db.delete_table('mci_sessiontemplatefrequency')

        # Deleting model 'SessionTemplate'
        db.delete_table('mci_sessiontemplate')

        # Removing M2M table for field task_groups on 'SessionTemplate'
        db.delete_table('mci_sessiontemplate_task_groups')

        # Deleting model 'RegionDisguiseFrequency'
        db.delete_table('mci_regiondisguisefrequency')

        # Deleting model 'Pseudonym'
        db.delete_table('mci_pseudonym')

        # Adding field 'Session.sessionbuilder'
        db.add_column('mci_session', 'sessionbuilder',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mci.SessionBuilder'], null=True, blank=True),
                      keep_default=False)

        # Adding field 'Session.disguise_subjects'
        db.add_column('mci_session', 'disguise_subjects',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Deleting field 'Session.subjects_disguised'
        db.delete_column('mci_session', 'subjects_disguised')

        # Deleting field 'Session.session_template_frequency'
        db.delete_column('mci_session', 'session_template_frequency_id')

        # Adding field 'SessionBuilder.introduction_time'
        db.add_column('mci_sessionbuilder', 'introduction_time',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=15),
                      keep_default=False)

        # Adding field 'SessionBuilder.load_test'
        db.add_column('mci_sessionbuilder', 'load_test',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'SessionBuilder.solo_task_group_start'
        db.add_column('mci_sessionbuilder', 'solo_task_group_start',
                      self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', null=True, to=orm['mci.TaskGroup'], on_delete=models.SET_NULL, blank=True),
                      keep_default=False)

        # Adding field 'SessionBuilder.disguise_subjects'
        db.add_column('mci_sessionbuilder', 'disguise_subjects',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'SessionBuilder.done_redirect_url'
        db.add_column('mci_sessionbuilder', 'done_redirect_url',
                      self.gf('django.db.models.fields.CharField')(default='http://www.mit.edu', max_length=256),
                      keep_default=False)

        # Adding field 'SessionBuilder.done_text'
        db.add_column('mci_sessionbuilder', 'done_text',
                      self.gf('django.db.models.fields.TextField')(default="Default text for 'Done' field."),
                      keep_default=False)

        # Adding field 'SessionBuilder.done_time'
        db.add_column('mci_sessionbuilder', 'done_time',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=15),
                      keep_default=False)

        # Adding field 'SessionBuilder.initial_task_group'
        db.add_column('mci_sessionbuilder', 'initial_task_group',
                      self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', null=True, to=orm['mci.TaskGroup'], on_delete=models.SET_NULL, blank=True),
                      keep_default=False)

        # Adding field 'SessionBuilder.solo_task_group_end'
        db.add_column('mci_sessionbuilder', 'solo_task_group_end',
                      self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', null=True, to=orm['mci.TaskGroup'], on_delete=models.SET_NULL, blank=True),
                      keep_default=False)

        # Adding field 'SessionBuilder.introduction_text'
        db.add_column('mci_sessionbuilder', 'introduction_text',
                      self.gf('django.db.models.fields.TextField')(default="Default text for 'Introduction' field."),
                      keep_default=False)

        # Adding M2M table for field task_groups on 'SessionBuilder'
        db.create_table('mci_sessionbuilder_task_groups', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('sessionbuilder', models.ForeignKey(orm['mci.sessionbuilder'], null=False)),
            ('taskgroup', models.ForeignKey(orm['mci.taskgroup'], null=False))
        ))
        db.create_unique('mci_sessionbuilder_task_groups', ['sessionbuilder_id', 'taskgroup_id'])

        # Adding field 'SubjectCountry.arab_country'
        db.add_column('mci_subjectcountry', 'arab_country',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)


    models = {
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
        'mci.pseudonym': {
            'Meta': {'object_name': 'Pseudonym'},
            'feminine': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pseudonym': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'region': ('django.db.models.fields.related.ForeignKey', [], {'default': '20L', 'to': "orm['mci.Region']"})
        },
        'mci.region': {
            'Meta': {'object_name': 'Region'},
            'countries': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['mci.SubjectCountry']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'})
        },
        'mci.regiondisguisefrequency': {
            'Meta': {'object_name': 'RegionDisguiseFrequency'},
            'frequency': ('django.db.models.fields.FloatField', [], {'default': '1.0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pct_feminine': ('django.db.models.fields.FloatField', [], {'default': '0.5'}),
            'region': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'region_disguise_frequencies'", 'to': "orm['mci.Region']"}),
            'round_up': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'region_disguise_frequencies'", 'null': 'True', 'to': "orm['mci.Session']"}),
            'session_template': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'region_disguise_frequencies'", 'null': 'True', 'to': "orm['mci.SessionTemplate']"})
        },
        'mci.session': {
            'Meta': {'ordering': "['-start_datetime']", 'object_name': 'Session'},
            'disguise_regions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['mci.Region']", 'through': "orm['mci.RegionDisguiseFrequency']", 'symmetrical': 'False'}),
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
            'session_template_frequency': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mci.SessionTemplateFrequency']", 'null': 'True', 'blank': 'True'}),
            'solo_task_group_end': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['mci.TaskGroup']"}),
            'solo_task_group_start': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['mci.TaskGroup']"}),
            'start_datetime': ('django.db.models.fields.DateTimeField', [], {}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'subjects_disguised': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'task_groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['mci.TaskGroup']", 'symmetrical': 'False'}),
            'waiting_room_time': ('django.db.models.fields.PositiveIntegerField', [], {'default': '900'})
        },
        'mci.sessionbuilder': {
            'Meta': {'object_name': 'SessionBuilder'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_survey_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'mturk': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'previous_play_forbidden': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'previous_play_required': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'session_templates': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['mci.SessionTemplate']", 'through': "orm['mci.SessionTemplateFrequency']", 'symmetrical': 'False'}),
            'subjects_per_session': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
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
        'mci.sessiontemplate': {
            'Meta': {'object_name': 'SessionTemplate'},
            'disguise_regions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['mci.Region']", 'through': "orm['mci.RegionDisguiseFrequency']", 'symmetrical': 'False'}),
            'done_redirect_url': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'done_text': ('django.db.models.fields.TextField', [], {}),
            'done_time': ('django.db.models.fields.PositiveIntegerField', [], {'default': '15'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'initial_task_group': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['mci.TaskGroup']"}),
            'introduction_text': ('django.db.models.fields.TextField', [], {}),
            'introduction_time': ('django.db.models.fields.PositiveIntegerField', [], {'default': '15'}),
            'load_test': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'solo_task_group_end': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['mci.TaskGroup']"}),
            'solo_task_group_start': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['mci.TaskGroup']"}),
            'subjects_disguised': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'task_groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['mci.TaskGroup']", 'symmetrical': 'False'})
        },
        'mci.sessiontemplatefrequency': {
            'Meta': {'object_name': 'SessionTemplateFrequency'},
            'frequency': ('django.db.models.fields.FloatField', [], {'default': '1.0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'session_builder': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'session_template_freqs'", 'to': "orm['mci.SessionBuilder']"}),
            'session_template': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'freqs_visavis_session_builders'", 'to': "orm['mci.SessionTemplate']"})
        },
        'mci.si_sb_status': {
            'Meta': {'object_name': 'SI_SB_Status'},
            'arrival_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'dispatch_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_waiting_room_checkin': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 2, 19, 0, 0)'}),
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