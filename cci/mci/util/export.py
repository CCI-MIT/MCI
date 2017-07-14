import csv
from django.http import HttpResponse
from django.utils.http import urlquote
from django.template.defaultfilters import slugify
from django.utils.encoding import smart_str
from mci.models import EventLog, CompletedTaskGridItem
from mci.util.summaries import listWithTotalsLast
from pprint import pformat
import logging
import zipfile
from StringIO import StringIO
from mci.workspace.py_etherpad import EtherpadLiteClient
from settings import MCI_ETHERPAD_API_URL     \
                   , MCI_ETHERPAD_API_KEY     \
                   , MCI_BASE_URL
_log = logging.getLogger("cci")
from django.utils.encoding import smart_str
from django.core.urlresolvers import reverse

event_log_fields = [f.name for f in EventLog._meta.fields]

def write_log_csv(filelike, fields, rows):
	writer = csv.writer(filelike)

	# Write headers 
	headers = fields
	writer.writerow(headers)

	# Write data 
	for obj in rows:
		if obj.subject and obj.subject.external_id == None:
				obj.subject.external_id = ""
		row = []
		for field in headers:
			if field in headers:
				try:
					val = getattr(obj, field)
					if callable(val):
						val = val()
				except AttributeError:
					val = "Error"
				row.append(smart_str(val if val else ""))
		writer.writerow(row)

def write_metadata_csv(filelike, session, session_group):
  writer = csv.writer(filelike)

  # Write headers
  writer.writerow([
      'Session Name',
      'Session Group',
      'Session Builder Name', 
      'Start Time',
      'Subjects Disguised',
      'Solo Task Group at Start',
      'Initial Common Task Group',
      'Common Task Groups',
      'Solo Task Group at End',
      'Done Redirect URL',
      'Team Tiles Score',
  ])
  stf = session.session_template_frequency

	# Write data 
  writer.writerow(map(smart_str, [
      session.name,
      session_group,
      stf.session_builder if stf else None,
      session.start_datetime,
      session.subjects_disguised,
      session.solo_task_group_start,
      session.initial_task_group,
      "; ".join([tg.name for tg in session.task_groups.all()]),
      session.solo_task_group_end,
      session.done_redirect_url,
      sum([ct.team_tiles_score() for ct in session.group_cts()
                                  if ct.task.task_type == 'I']),
  ]))
  subs = session.subjects_in_group(session_group)

  def summary_table_row_header(task_type, summary, metrics):
      row = ['']
      row.extend([m[1] for m in metrics if type(m) is not dict])
      if task_type == 'S' and summary is not None:
          row.extend([ext_id for (ext_id, data) in summary if ext_id is not "Totals"])
      return map(smart_str, row)

  def summary_table_row_body(task_type, ext_id, data, metrics):
      # We have some unicode, foreign characters in the subject ID
      row = [smart_str(ext_id)]
      row.extend([data[m[0]] for m in metrics if type(m) is not dict])
      if task_type == 'S' and ext_id is not "Totals":
          row.extend(data['interactions'])
      return map(smart_str, row)

  # Session-wide per-task-type summary tables
  for task_type in ['C', 'I', 'S']:
      if session.has_task_of_type(task_type):
          metrics = session.per_subject_metrics(task_type, session_group)
          summary = session.log_summary_with_totals_for_task_type(task_type, session_group)
          if summary is not None:
              writer.writerows([[], summary_table_row_header(ct.task.task_type, summary, metrics)])
              writer.writerows([summary_table_row_body(task_type, ext_id, data, metrics) for (ext_id, data) in summary])

  # Per-CompletedTask summary tables
  for ct in session.completed_tasks_for_session_group(session_group).order_by('start_time'):
      metrics = session.per_subject_metrics(ct.task.task_type, session_group)
      if metrics:
          if ct.task.task_type == 'C':
              summary    = ct.conc_summary_with_totals()
          elif ct.task.task_type == 'I':
              summary   = ct.tiles_summary_with_totals()
          elif ct.task.task_type == 'S':
              summary = ct.squares_summary_with_totals()
          if summary is not None:
              writer.writerows([ []
                               , [ct.task]
                               , ["%s%s?id=%s" % (MCI_BASE_URL[:-1], reverse('admin:mci_completedtask_changelist'), ct.pk)]
                               , summary_table_row_header(ct.task.task_type, summary, metrics)
                               ])
              writer.writerows([summary_table_row_body(ct.task.task_type, ext_id, data, metrics) for (ext_id, data) in summary])

def csv_response(filename):
  # EDFIX: changed from mimetype to content_type for Django 1.7+
  response = HttpResponse(content_type='text/csv')
  response['Content-Disposition'] = 'attachment; filename=%s.csv' % slugify(filename)
  return response

def admin_export(modeladmin, qs, fields=None):
	model = qs.model
	response = csv_response(model.__name__)
	writer = csv.writer(response)

	# Write headers 
	if fields:
		headers = fields
	else:
		headers = []
		for field in model._meta.fields:
			headers.append(field.name)
	writer.writerow(headers)

	# Write data 
	for obj in qs:
		row = []
		for field in headers:
			if field in headers:
				try:
					val = getattr(obj, field)
					if callable(val):
						val = val()
				except AttributeError:
					# Try callables defined on the modeladmin if not on the model
					val = getattr(modeladmin,field)
					if callable(val):
						val = val(obj)
				row.append(smart_str(val))
		writer.writerow(row)
		# Return CSV file to browser as download
	return response

def admin_list_export(modeladmin, request, queryset):
	"""Admin site action for exporting objects to CSV"""
	try:
		fields = list(modeladmin.export_fields)
	except AttributeError:
		try:
			fields = list(modeladmin.list_display)
			try: fields.remove('action_checkbox')
			except ValueError: pass
		except AttributeError:
			fields = None

	return admin_export(modeladmin, queryset, fields)
admin_list_export.short_description = "Export selected items"

def write_ctgi_csv(csv_grid_items, ctgis):
      writer = csv.writer(csv_grid_items) 

      fields = [ 'Session'
               , 'Session Group'
               , 'Task'
               , 'Subject'
               , 'Task Grid Item'
               , 'Correct Answer'
               , 'Answer'
               ]

      ## Write headers 
      if fields:
        headers = fields
      else:
        headers = []
        for field in model._meta.fields:
          headers.append(field.name)
      writer.writerow(headers)
    
      ## Write data 
      for ctgi in ctgis:
          ct = ctgi.completed_task
          fields = [ ct.session
                   , ct.session_group
                   , ct.task
                   , ctgi.subject
                   , ctgi.task_grid_item
                   , ctgi.task_grid_item.correct_answer
                   , ctgi.answer
                   ]
          writer.writerow(map(smart_str, fields))

class UniquePathManager(object):
    paths = {}
    def construct_unique_path(self, path, extension, index=0):
        tail = (" - %s" % index) if index else ""
        path_with_tail = path + tail + "." + extension 
        try:
            self.paths[path_with_tail]
        except KeyError as e:
            return path_with_tail
        return self.construct_unique_path(path, extension, index + 1)
    def add(self, path, extension):
        unique_path = self.construct_unique_path(path, extension)
        self.paths[unique_path] = True
        return unique_path

def export_zip(session):
  """Create a zip export file."""

  string = StringIO()
  zf = zipfile.ZipFile(string, "w", zipfile.ZIP_DEFLATED)
  upm = UniquePathManager()

  for session_group in session.session_groups():
      tag = "%s - Group %s" % (session.name, session_group)
      group_cts = session.completed_tasks_for_session_group(session_group)

      # Session Log CSV
      csv_session_log = StringIO()
      log = session.build_session_log(session_group)
      write_log_csv(csv_session_log, event_log_fields, log)
      path_session_log = upm.add("%s/%s - LogFile" % (tag, tag), "csv")
      zf.writestr(path_session_log, csv_session_log.getvalue())

      # Contents of pads
      pad_client = EtherpadLiteClient(MCI_ETHERPAD_API_KEY, MCI_ETHERPAD_API_URL)
      for ct in group_cts.filter(task__task_type="T"):
          contents = pad_client.getText(padID = ct.pad_id())
          path_task_workspace_contents = upm.add("%s/%s - %s" % (tag, tag, ct.task.name), "txt")
          zf.writestr(path_task_workspace_contents, smart_str(contents['text']))

      # Grid items
      grid_cts = group_cts.filter(task__task_type="G")
      ctgis = CompletedTaskGridItem.objects.filter(completed_task__in=grid_cts)
      csv_grid_items = StringIO()
      write_ctgi_csv(csv_grid_items, ctgis)
      path_session_grid_items = upm.add("%s/%s - GridItems" % (tag, tag), "csv")
      zf.writestr(path_session_grid_items, csv_grid_items.getvalue())

      # Metadata
      csv_session_metadata = StringIO()
      write_metadata_csv(csv_session_metadata, session, session_group)
      path_session_metadata = upm.add("%s/%s - Metadata" % (tag, tag), "csv")
      zf.writestr(path_session_metadata, csv_session_metadata.getvalue())

  zf.close()
  return string.getvalue()
