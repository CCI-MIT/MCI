# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Text'
        db.create_table('mci_text', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('text', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('mci', ['Text'])

        # Adding model 'Session'
        db.create_table('mci_session', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('start_datetime', self.gf('django.db.models.fields.DateTimeField')()),
            ('min_group_size', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
            ('max_group_size', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
            ('status', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('initial_task_group', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, to=orm['mci.TaskGroup'])),
            ('introduction_text', self.gf('django.db.models.fields.TextField')()),
            ('done_text', self.gf('django.db.models.fields.TextField')()),
            ('done_redirect_url', self.gf('django.db.models.fields.CharField')(max_length=256)),
        ))
        db.send_create_signal('mci', ['Session'])

        # Adding M2M table for field task_groups on 'Session'
        db.create_table('mci_session_task_groups', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('session', models.ForeignKey(orm['mci.session'], null=False)),
            ('taskgroup', models.ForeignKey(orm['mci.taskgroup'], null=False))
        ))
        db.create_unique('mci_session_task_groups', ['session_id', 'taskgroup_id'])

        # Adding model 'TaskGroup'
        db.create_table('mci_taskgroup', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=64)),
        ))
        db.send_create_signal('mci', ['TaskGroup'])

        # Adding model 'Task'
        db.create_table('mci_task', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('task_group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mci.TaskGroup'])),
            ('task_order', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True, blank=True)),
            ('task_type', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('instructions', self.gf('django.db.models.fields.TextField')()),
            ('instructions_time', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
            ('instructions_width', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('primer', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('primer_time', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True, blank=True)),
            ('interaction_instructions', self.gf('django.db.models.fields.TextField')()),
            ('interaction_workspace_source', self.gf('django.db.models.fields.CharField')(max_length=256, null=True)),
            ('interaction_time', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
            ('grid_header_instructions', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('mci', ['Task'])

        # Adding model 'TaskPrivateInformation'
        db.create_table('mci_taskprivateinformation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('task', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mci.Task'])),
            ('information', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('mci', ['TaskPrivateInformation'])

        # Adding model 'TaskGridItem'
        db.create_table('mci_taskgriditem', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('task', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mci.Task'])),
            ('row', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
            ('column', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
            ('text_label', self.gf('django.db.models.fields.CharField')(max_length=256, blank=True)),
            ('image_label', self.gf('django.db.models.fields.files.ImageField')(max_length=100, blank=True)),
            ('field_width', self.gf('django.db.models.fields.PositiveSmallIntegerField')(max_length=256, null=True, blank=True)),
            ('correct_answer', self.gf('django.db.models.fields.CharField')(max_length=256, blank=True)),
            ('readonly', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('mci', ['TaskGridItem'])

        # Adding model 'Subject'
        db.create_table('mci_subject', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('session', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mci.Session'])),
            ('external_id', self.gf('django.db.models.fields.CharField')(unique=True, max_length=32)),
            ('consent_and_individual_tests_completed', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('in_waiting_room', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('session_group', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal('mci', ['Subject'])

        # Adding model 'CompletedTask'
        db.create_table('mci_completedtask', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('task', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mci.Task'])),
            ('session', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mci.Session'])),
            ('session_group', self.gf('django.db.models.fields.IntegerField')()),
            ('workspace', self.gf('django.db.models.fields.URLField')(max_length=200, blank=True)),
            ('completed_task_order', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
            ('start_time', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('expected_start_time', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('expected_finish_time', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal('mci', ['CompletedTask'])

        # Adding model 'CompletedTaskGridItem'
        db.create_table('mci_completedtaskgriditem', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('task_grid_item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mci.TaskGridItem'])),
            ('completed_task', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mci.CompletedTask'])),
            ('answer', self.gf('django.db.models.fields.CharField')(max_length=256)),
        ))
        db.send_create_signal('mci', ['CompletedTaskGridItem'])


    def backwards(self, orm):
        
        # Deleting model 'Text'
        db.delete_table('mci_text')

        # Deleting model 'Session'
        db.delete_table('mci_session')

        # Removing M2M table for field task_groups on 'Session'
        db.delete_table('mci_session_task_groups')

        # Deleting model 'TaskGroup'
        db.delete_table('mci_taskgroup')

        # Deleting model 'Task'
        db.delete_table('mci_task')

        # Deleting model 'TaskPrivateInformation'
        db.delete_table('mci_taskprivateinformation')

        # Deleting model 'TaskGridItem'
        db.delete_table('mci_taskgriditem')

        # Deleting model 'Subject'
        db.delete_table('mci_subject')

        # Deleting model 'CompletedTask'
        db.delete_table('mci_completedtask')

        # Deleting model 'CompletedTaskGridItem'
        db.delete_table('mci_completedtaskgriditem')


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
            'task_grid_item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mci.TaskGridItem']"})
        },
        'mci.session': {
            'Meta': {'object_name': 'Session'},
            'done_redirect_url': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'done_text': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'initial_task_group': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['mci.TaskGroup']"}),
            'introduction_text': ('django.db.models.fields.TextField', [], {}),
            'max_group_size': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'min_group_size': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'start_datetime': ('django.db.models.fields.DateTimeField', [], {}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'task_groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['mci.TaskGroup']", 'symmetrical': 'False'})
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
            'grid_header_instructions': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instructions': ('django.db.models.fields.TextField', [], {}),
            'instructions_time': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'instructions_width': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'interaction_instructions': ('django.db.models.fields.TextField', [], {}),
            'interaction_time': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'interaction_workspace_source': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True'}),
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
