from django.db.models.query_utils import Q
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
import types
from mci.models import CompletedTask, EventLog, Session, Subject, \
    ConcentrationRound, EtherpadLiteRecord
from mci.util.export import *
import re
from datetime import datetime, timedelta
from settings import MCI_REDIS_SERVER         \
                   , MCI_REDIS_PORT           \
                   , MCI_ETHERPAD_API_URL     \
                   , MCI_ETHERPAD_API_KEY
import pprint 
from mci.workspace.py_etherpad import EtherpadLiteClient

import logging
_log = logging.getLogger("cci")

__author__ = 'jlicht'

def task_log(request, completed_task_id):
  ct = CompletedTask.objects.get(pk=completed_task_id)
  users = {}
  EtherpadLiteRecord.objects.clear_querysets()      
  log = ct.build_log()
  conc_summary    = ct.conc_summary_with_totals()
  tiles_summary   = ct.tiles_summary_with_totals()
  squares_summary = ct.squares_summary_with_totals()

  return render_to_response("mci/reporting/task_log.html", {
      "log": log,
      'conc_summary':    conc_summary,
      'tiles_summary':   tiles_summary,
      'squares_summary': squares_summary,
      "users" : users,
      "completed_task" : ct,
      'seconds_before_correction': ct.seconds_to_first_tiles_correction(),
      'team_score': ct.team_tiles_score(),
      'scribe': ct.scribe().external_id if ct.scribe() else None,
  }, context_instance=RequestContext(request))

def task_log_export(request,completed_task_id):
	completed_task = CompletedTask.objects.get(pk=completed_task_id)
	EtherpadLiteRecord.objects.clear_querysets()      
	log = completed_task.build_log()
	response = csv_response("task_log")
	write_log_csv(response, event_log_fields, log)
	return response

def session_log(request, session_id, session_group=1):
    session = Session.objects.get(pk=session_id)
    if not isinstance(session_group,types.IntType) and not session_group.isdigit():
      session_group = 1
    log = session.build_session_log(session_group)
    summary_conc    = session.log_summary_with_totals_for_task_type('C', session_group)
    summary_tiles   = session.log_summary_with_totals_for_task_type('I', session_group)
    summary_squares = session.log_summary_with_totals_for_task_type('S', session_group)
    if session.scribe_enabled:
      confirmed_users = session.subject_set.filter(scribe__in=['C','S'], session_group=session_group)
      unconfirmed_users = session.subject_set.filter(scribe__in=['U','R'], session_group=session_group)
    else:
      confirmed_users = session.subject_set.filter(in_waiting_room=True, session_group=session_group)
      unconfirmed_users = None
    missing_users = session.subject_set.filter(in_waiting_room=False)
    return render_to_response("mci/reporting/session_log.html", {
      "log": log,
      "session" : session,
      "session_group": session_group,
      "confirmed_users": confirmed_users,
      "unconfirmed_users": unconfirmed_users,
      "missing_users": missing_users,
      'conc_summary':    summary_conc,
      'tiles_summary':   summary_tiles,
      'squares_summary': summary_squares,
      'task_groups': session.task_groups.all(),
      'team_tiles_score': sum([ct.team_tiles_score() for ct in session.group_cts()
                                                      if ct.task.task_type == 'I']),
  }, context_instance=RequestContext(request))

def session_log_export(request,session_id, session_group=1):
	session = Session.objects.get(pk=session_id)
	if not isinstance(session_group,types.IntType) and not session_group.isdigit(): session_group = 1
	log = session.build_session_log(session_group)
	response = csv_response("session_log")
	write_log_csv(response, event_log_fields, log)
	return response

def session_zip_export(request, session_id):
  session = Session.objects.get(pk=session_id)
  filelike = export_zip(session)

  response = HttpResponse(filelike, content_type = "application/x-zip-compressed")
  response['Content-Disposition'] = 'attachment; filename=%s.zip' % urlquote(session.name)

  return response

def session_metadata_export(request, session_id, session_group):
  session = Session.objects.get(pk=session_id)
  response = csv_response("%s_group_%s" % (session.name, session_group))
  write_metadata_csv(response, session, session_group)
  return response

def session_reset(request, session_id):
    session = Session.objects.get(pk=session_id)
    session.reset()
    from django.contrib import messages
    messages.add_message(request, messages.INFO, 'Session reset.')
    return HttpResponseRedirect(reverse(
        'admin:mci_session_change',
        args=(session.id,)))

def workspace_text(request, completed_task_id):
    pad_client = EtherpadLiteClient(MCI_ETHERPAD_API_KEY, MCI_ETHERPAD_API_URL)
    ct = CompletedTask.objects.get(pk=completed_task_id)
    contents = pad_client.getText(padID = ct.pad_id())
    resp = HttpResponse(contents['text'], content_type="text/plain")
    resp['Content-Disposition'] = 'attachment; filename=%s.txt' % slugify(ct)
    return resp
