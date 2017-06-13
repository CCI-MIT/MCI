from datetime import timedelta, datetime
import json
from random import random, shuffle, choice, sample
import traceback
from django.core.urlresolvers import reverse
from django.http \
  import HttpResponse            \
       , HttpResponseRedirect    \
       , HttpResponseBadRequest
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.forms import ModelForm, ValidationError, CharField
from django.template.context import RequestContext
from django.db.models import Q
from django.db import transaction
from mci.models import Subject, Session, CompletedTask, Task, Text, \
                       ConcentrationCard, SubjectCountry, Avatar, \
                       SessionBuilder, SubjectIdentity, SI_SB_Status, \
                       Pseudonym
from mci.util import audit
from settings import MCI_CONCENTRATION_BASE_URL \
                   , MCI_BASE_URL \
                   , MCI_DOMAIN \
                   , MCI_OPENTOK_API_KEY \
                   , MCI_OPENTOK_API_SECRET \
                   , VERSION \
                   , squares_set_width \
                   , squares_set_height \
                   , board_area_border_thickness
import OpenTokSDK
from django.views.decorators.cache import never_cache, patch_cache_control
from mci.workspace.py_etherpad import *
from pprint import pformat
from django.utils.http import urlquote
import logging
_log = logging.getLogger('cci')

def _get_text(key):
  try:
    result = Text.objects.get(key=key).text
  except Text.DoesNotExist:
    result = key
    _log.error("Could not find text for message key = [%s]" % key)
  return result

def _error_response(request):
  _log.error(traceback.format_exc())
  _log.error("Sending 500 error response")
  return render_to_response('500.html',context_instance=RequestContext(request))

def _error_response_json(request):
  _log.error(traceback.format_exc())
  _log.error("Sending JSON error response")
  return HttpResponse(json.dumps({'error':True}), content_type="application/json")

def _log_completedtask_dne(request, ctid, seid, validation_type):
    try:
        subject = Subject.objects.get(external_id=seid)
        _log.error(("Subject %s requested %s with bad Completed Task ID "
            "(%s).") % (subject, validation_type, ctid))
    except Subject.DoesNotExist:
        _log.error(("Someone requested %s with bad Completed Task ID (%s) and "
            "bad Subject External ID (%s).") % (validation_type, ctid, seid))

def _message_response(message, request):
  _log.debug("Sending message: %s" % message)
  return render_to_response('mci/message.html', {
    'version': VERSION,
    'no_header_timer' : True,
    'message': message,
  }, context_instance=RequestContext(request))

def _avatar_dict(p):
    return  { 'sid'           : p.viewed.id
            , 'display_name'  : p.display_name if p.display_name else p.viewed.display_name
            , 'flag_url'      : p.country.flag.url if p.country and p.country.flag else ""
            , 'classes'       : 'avatar'
            }

def _avatar_classes(classes, rightmost):
    if rightmost:
        classes += ' rightmost'
    return classes

def _avatars_list(ps):
    as_list = [_avatar_dict(p) for p in ps]
    for i, p in enumerate(as_list):
        p['classes'] = _avatar_classes(p['classes'], i == len(as_list) - 1)
    return as_list

def _avatars_dict(ps):
    return dict([(str(p.viewed.id), _avatar_dict(p)) for p in ps])

def _preview_response(task_id, field, template, timer, request):
  try:
    task = Task.objects.get(pk=task_id)
  except CompletedTask.DoesNotExist:
    return _error_response(request=request)
  return render_to_response(template, {
    'version': VERSION,
    'timer' : timer,
    'timerDebug': "false",
    'message' : getattr(task,field),
  }, context_instance=RequestContext(request))

def home(request):
  return HttpResponseRedirect(reverse(register))

def consent(request):
  """ Register that a subject has completed the consent forms and individual tests. """
  if request.method == "POST":
    try:
      subject = Subject.objects.get(external_id=request.POST['seid'])
      subject.consent_and_individual_tests_completed = True
      subject.save()
      audit.audit_log("Consent",request=request,subject=subject)
      return _message_response(_get_text(key="CONFIRM_REGISTRATION"), request=request)
    except Subject.DoesNotExist:
      return render_to_response('mci/consent.html', {
          'version': VERSION,
          'error_message': _get_text("ERROR_NOT_RECOGNIZED"),
          'no_header_timer' : True,
      }, context_instance=RequestContext(request))
  else:
    return render_to_response('mci/consent.html', {
        'version': VERSION,
        'message' : _get_text("CONSENT_FORM_MESSAGE"),
        'no_header_timer' : True,
    }, context_instance=RequestContext(request))

def sessionbuilder_register(request, sbid):
    """ Initial registration form for a SessionBuilder. """

    try: 
        sessionbuilder = SessionBuilder.objects.get(pk=sbid)
    except SessionBuilder.DoesNotExist:
        _log.error(("Bad request for initial registration form of nonexistent "
            "SessionBuilder (ID provided: %s) %s") % (sbid,
                ("POST data: %s" % request.POST) if request.method == 'POST' else ''))
        return _error_response(request=request)

    if datetime.now() < sessionbuilder.waiting_room_opens:
        _log.info(("SessionBuilder %s registration form requested before "
            "waiting room opened.") % sbid)
        return _message_response("Too early", request)
    elif datetime.now() > sessionbuilder.waiting_room_closes:
        _log.info(("SessionBuilder %s registration form requested after "
            "waiting room closed. ") % sbid)
        return _message_response("Too late", request)

    class RegistrationForm(ModelForm):
        sb_group_id = CharField(label="Group ID", required=False)
        class Meta:
            model = SubjectIdentity
            fields = ('mturk_id',) if sessionbuilder.mturk else ('email',)
        def __init__(self, *args, **kwargs):
            super(RegistrationForm, self).__init__(*args, **kwargs)
            if 'mturk_id' in self.fields:
                self.fields['mturk_id'].label = sessionbuilder.custom_id_label
        def clean_email(self):
            email = self.cleaned_data['email']
            if not email:
                raise ValidationError("Email is required.")
            return email
        def clean_mturk_id(self):
            mturk_id = self.cleaned_data['mturk_id']
            if not mturk_id:
                raise ValidationError("Your ID (e.g. MTurk ID) is required.")
            return mturk_id

    if request.method == 'POST':
        try:
            if sessionbuilder.mturk:
                inst = SubjectIdentity.objects.get(mturk_id=request.POST['mturk_id'])
            else:
                inst = SubjectIdentity.objects.get(email=request.POST['email'])
        except SubjectIdentity.DoesNotExist:
            inst = None

        form = RegistrationForm(request.POST, instance=inst)
        if form.is_valid():
            if sessionbuilder.mturk:
                subject_identity = SubjectIdentity.objects.get_or_create(mturk_id=form.cleaned_data['mturk_id'])[0]
            else:
                subject_identity = SubjectIdentity.objects.get_or_create(email=form.cleaned_data['email'])[0]
            siid = subject_identity.pk
            sb_group_id = form.cleaned_data['sb_group_id']
            _log.info( "sessionbuilder_start >> Form submitted."
                       "\n\tSessionBuilder:    %s (%s)"
                       "\n\tSubjectIdentity:   %s (%s)"
                       "\n\tGroup ID:          %s"
                       % (sessionbuilder, sbid, subject_identity, siid, sb_group_id)
                     )

            # Make sure there's an SI_SB_Status, so that we have someplace to store the SB Group ID value (assuming it's been inputted)
            stat, __ = SI_SB_Status.objects.get_or_create( sessionbuilder__id   = sbid
                                                         , subject_identity__id = siid
                                                         , defaults={ 'sessionbuilder_id':   sbid
                                                                    , 'subject_identity_id': siid
                                                                    }
                                                         )
            stat.sb_group_id = sb_group_id
            stat.save()

            skip_more_info = subject_identity.display_name and subject_identity.country
            next_view = sessionbuilder_waiting_room if skip_more_info else sessionbuilder_more_info
            return HttpResponseRedirect(reverse(next_view, args=(sbid, siid,)))

    template_vars = {
        'version': VERSION,
        'no_header_timer' : True,
        'message' : 'Please register for %s' % sessionbuilder,
        'sessionbuilder_id' : sbid,
        'form' : RegistrationForm() if request.method == 'GET' else form,
        'ask_for_group_id': sessionbuilder.ask_for_group_id
    }
    return render_to_response(
        'mci/sessionbuilder_start.html',
        template_vars,
        context_instance=RequestContext(request))

def sessionbuilder_more_info(request, sbid, siid):
    """ """

    try: 
        sessionbuilder = SessionBuilder.objects.get(pk=sbid)
        subject_identity = SubjectIdentity.objects.get(pk=siid)
    except (SessionBuilder.DoesNotExist, SubjectIdentity.DoesNotExist):
        return _error_response(request=request)
    if datetime.now() > sessionbuilder.waiting_room_closes:
        _log.error("SessionBuilder %s start page: waiting room closed" % sbid)
        return _message_response("Too late", request)
    class MoreInfoForm(ModelForm):
        class Meta:
            model = SubjectIdentity
            fields = ('display_name', 'country',)
        def clean_display_name(self):
            display_name = self.cleaned_data['display_name']
            if not display_name or len(display_name) == 0:
                raise ValidationError("Display Name is required.")
            return display_name
        def clean_country(self):
            country = self.cleaned_data['country']
            if not country:
                raise ValidationError("Country is required.")
            return country 
    if request.method == 'POST':
        form = MoreInfoForm(request.POST)
        if form.is_valid():
            subject_identity.display_name = form.cleaned_data['display_name']
            subject_identity.country = form.cleaned_data['country']
            subject_identity.save()
            _log.info("SubjectIdentity %s submitted display name and country" %
                        subject_identity)
            return HttpResponseRedirect(reverse(
                sessionbuilder_waiting_room,
                args=(sbid, siid,)))
    template_vars = {
        'version': VERSION,
        'no_header_timer': True,
        'message': 'Welcome, %s!' % subject_identity,
        'sessionbuilder_id': sbid,
        'subject_identity_id': siid,
        'sbid': sbid,
        'form': MoreInfoForm() if request.method == 'GET' else form,
        'javascript_test_explanation': sessionbuilder.javascript_test_explanation,
        'error_connecting_to_game_server_msg': sessionbuilder.error_connecting_to_game_server_msg,
        'concentration_domain': MCI_CONCENTRATION_BASE_URL,        
        'domain': MCI_BASE_URL,        
    }
    return render_to_response(
        'mci/sessionbuilder_start.html',
        template_vars,
        context_instance=RequestContext(request)) 

def get_statuses_by_pk(siid, sbid):
    statuses = SI_SB_Status.objects.filter( sessionbuilder__id   = sbid
                                          , subject_identity__id = siid
                                          )
    status_pks = list(statuses.values_list('pk', flat=True))
    status_pks.sort()
    statuses_by_pk = SI_SB_Status.objects.filter(pk__in=status_pks)
    return statuses_by_pk

def sessionbuilder_waiting_room(request, sbid, siid):
    try:
        subject_identity = SubjectIdentity.objects.get(pk=siid)
        sessionbuilder = SessionBuilder.objects.get(pk=sbid)
    except (SubjectIdentity.DoesNotExist, SessionBuilder.DoesNotExist):
        return _error_response(request)
    status, created = SI_SB_Status.objects.get_or_create(
        sessionbuilder__id=sbid,
        subject_identity__id=siid,
        defaults={
            'sessionbuilder_id': sbid,
            'subject_identity_id': siid,
        })
    if created or status.arrival_time is None:
        _log.debug("Just created Status %s" % status)
        statuses_by_pk = get_statuses_by_pk(siid, sbid)
        statuses_by_pk.update(arrival_time=datetime.now())
    if status.rejected:
        return _message_response(
            message=_get_text("Sorry, you will not be placed in a Session."),
            request=request)
    return render_to_response('mci/sessionbuilder_wait.html', {
        'version': VERSION,
        'sessionbuilder': sessionbuilder,
        'subject_identity': subject_identity,
        'no_header_timer': True,
        'checkin_interval': 5,
        'waiting_for': status.get_waiting_for(), 
    }, context_instance=RequestContext(request))

@never_cache
def sessionbuilder_waiting_room_checkin(request, sbid, siid):
    try:
        status = SI_SB_Status.objects.get(
            sessionbuilder=sbid,
            subject_identity=siid)
        sessionbuilder = SessionBuilder.objects.get(pk=sbid)
    except (SI_SB_Status.DoesNotExist, SessionBuilder.DoesNotExist):
        return _error_response(request)
    if sessionbuilder.should_survey(status.last_waiting_room_checkin):
        sessionbuilder.survey()
    statuses_by_pk = get_statuses_by_pk(siid, sbid)
    statuses_by_pk.update(last_waiting_room_checkin=datetime.now())
    # Refetch 'status', since 'status' will have been updated during survey.
    status = SI_SB_Status.objects.get(
        sessionbuilder=sbid,
        subject_identity=siid)
    response_data = {
        'waiting_for': status.get_waiting_for(),
    }
    # Dispatch this Subject if appropriate
    if status.subject:
        _log.debug("Forwarding SubjectIdentity %s to waiting room" % status)
        response_data['next_url'] = reverse(
            waiting_room,
            args=(status.subject.external_id,)),
        response_data['goodbye'] = "Your session is ready!"
    else:
        sb = status.sessionbuilder
        if datetime.now() > sb.waiting_room_closes:
            _log.error(("SessionBuilder %s waiting room checkin by %s: waiting "
                "room closed") % (sbid, siid))
            response_data['next_url'] = sb.done_redirect_url,
            response_data['goodbye'] = "This waiting room has closed."
    return HttpResponse(json.dumps(response_data), content_type="application/json")


def register(request):
    """ Session registration form.

        On POST, ensure that the subject's session is starting soon, has not already
        started, and that the subject has completed their consent forms and
        individual tests. Send them to the waiting room if so.  """
    if request.method == 'POST':
        def session_start_error_response(error, error_type):
            seid = request.REQUEST['seid'] if 'seid' in request.REQUEST else "NO SEID"
            _log.error("Session start error: %s : [     : %20s]" % (error_type, seid,))
            return render_to_response('mci/start.html', {
                'version': VERSION,
                'no_header_timer' : True,
                'error_message': error,
                'message' : _get_text("START_FORM_MESSAGE"),
            }, context_instance=RequestContext(request)) 
        try:
            if not 'seid' in request.REQUEST:
                audit.audit_log("No SEID provided", request=request)
                return session_start_error_response(
                    _get_text("ERROR_NOT_RECOGNIZED"), "ERROR_NO_SEID")
            subject = Subject.objects.get(external_id=request.REQUEST['seid'])
            if not subject.consent_and_individual_tests_completed:
                audit.audit_log("Complete prereqs", request=request, subject=subject)
                return session_start_error_response(
                    _get_text("ERROR_COMPLETE_PREREQS"), "ERROR_COMPLETE_PREREQS")
            elif subject.session.too_late() and not subject.session_group:
                audit.audit_log("Too late",request=request,subject=subject)
                return session_start_error_response(
                    _get_text("ERROR_TOO_LATE"),
                    "ERROR_TOO_LATE")
            elif subject.session.too_early():
                audit.audit_log("Too early",request=request,subject=subject)
                delta = subject.session.time_to_waiting_room_opens()
                return session_start_error_response(_get_text("ERROR_TOO_EARLY").format(
                    subject.session.start_datetime.strftime("%c"),
                    delta.days * 3600 * 24 + (delta.seconds / 60)), "ERROR_TOO_EARLY")
            return HttpResponseRedirect(
                reverse(waiting_room, args=(request.REQUEST['seid'],)))
        except Subject.DoesNotExist:
            audit.audit_log("Not recognized", request=request,
                data="Subject External Id: %s" % request.REQUEST['seid'])
            return session_start_error_response(
                _get_text("ERROR_NOT_RECOGNIZED"), "ERROR_NOT_RECOGNIZED")
    return render_to_response('mci/start.html', {
        'version': VERSION,
        'no_header_timer' : True,
        'message' : _get_text("START_FORM_MESSAGE"),
    }, context_instance=RequestContext(request))

def waiting_room(request, seid):
    try:
        subject = Subject.objects.get(external_id=seid)
    except Subject.DoesNotExist:
        return _error_response(request=request)
    subject.in_waiting_room = True
    subject.save()
    audit.audit_log("Entering waiting room",request=request,subject=subject)
    cci_session = subject.session
    # Get the subject an OpenTok token (replacing any existing one)
    #if cci_session.video_enabled:
    #    opentok = OpenTokSDK.OpenTokSDK(MCI_OPENTOK_API_KEY, MCI_OPENTOK_API_SECRET)
    #    subject.opentok_token = opentok.generate_token(
    #        cci_session.opentok_session_id,
    #        OpenTokSDK.RoleConstants.PUBLISHER,
    #        None,
    #        json.dumps({ 'sid': subject.id }))
    #    subject.save()
    template_vars = {
        'version': VERSION,
        'session' : cci_session,
        'seconds_to_start': max(15, cci_session.total_seconds_to_start()),
        'start_url': reverse(confirm_participation, kwargs={
            'seid' : subject.external_id
        }),
        'subject_external_id': subject.external_id,
        'no_header_timer': True,
        'checkin_interval': 10,
        'has_cards_task': cci_session.has_realtimegame_task(),
        # Only used when the Session includes a Concentration-type Task.
        'video': cci_session.video_enabled,
        'domain': MCI_BASE_URL,
        'sid': subject.id,
        'display_name': subject.display_name,
        #'opentok_session_id': cci_session.opentok_session_id,
        #'opentok_token': subject.opentok_token,
        'video_height': 80,
        'video_width': 130,
    }
    if cci_session.has_realtimegame_task() or cci_session.roster_page:
        Avatar.objects.filter(viewer=subject, viewed=subject).delete()
        own_avatar = Avatar.objects.create( viewer=subject
                                          , viewed=subject
                                          , country=subject.country
                                          )
        template_vars['avatars_json'] = json.dumps(_avatars_dict([own_avatar]))
        template_vars['a'] = _avatar_dict(own_avatar)
    return render_to_response(
        'mci/wait.html',
        template_vars,
        context_instance=RequestContext(request))

def _setup_participants(session):
    audit.audit_log("Setup participants",session=session)
    participants = list(Subject.objects.filter(
        session=session.id,
        in_waiting_room=True,
        session_group__isnull=True))
    shuffle(participants)
    if session.group_creation_method == 'X': # matrix
        group_sizes = session.matrix_group_sizes(len(participants))
        if group_sizes:
            participant_index = 0
            for group_number, group_size in enumerate(group_sizes):
                for i in range(group_size):
                    participant = participants[participant_index]
                    participant.session_group = group_number + 1
                    participant.save()
                    _log.info("%s : Assigned Subject %s to Session Group %s using matrix" %
                        (participant_index, participant.external_id, participant.session_group))
                    participant_index += 1
        else:
            _log.error("Could not configure groups for Session %s because cohort size %s was not in the matrix" %
                        (session.id, len(participants)))
            # Particpants will receive an error message eventually, since they were never assigned to a group
    else: # min or max group sizes
        if session.group_creation_method == 'M':
            number_of_groups = len(participants) // session.min_group_size
        else:
            number_of_groups = len(participants) // session.max_group_size
        if number_of_groups == 0 and len(participants) >= session.min_group_size:
            number_of_groups = 1
        for index, participant in enumerate(participants):
            if index < number_of_groups * session.max_group_size:
                participant.session_group = index % number_of_groups + 1
            else:
                participant.session_group = 0
            _log.info("%s : Assigned Subject %s to Session Group %s" %
                (index, participant.external_id, participant.session_group))
            participant.save()

def _get_base_task_url(ctid, seid, suffix):
  url = '/mci/session/task/{completed_task_id}/{subject_external_id}/{suffix}'
  return url.format(completed_task_id=ctid, subject_external_id=urlquote(seid), suffix=suffix)

def _completed_task_next_url(completed_task, seid):
    try:
        ct = completed_task.next_completed_task(seid)
    except CompletedTask.DoesNotExist:
        return reverse(done, kwargs={ "seid": seid })
    return _get_base_task_url(ct.id, seid, 'I')
    

def _get_private_information(completed_task, subject_external_id):
  """
  Get the "Private Information" that should be displayed for a particular
  subject on a particular test.
  Each person must get exactly one. To parcel out the information, we order the
  information and subjects alphabetically, and then match them up.
  """
  private_info = completed_task.task.taskprivateinformation_set.all().order_by('information')
  if private_info:
    subjects = map(
        lambda x:x.external_id,
        list(completed_task.session.subject_set.all().order_by('external_id')))
    index = subjects.index(subject_external_id)
    result = []
    if private_info.count() <= len(subjects):
      result.append(private_info[index % private_info.count()].information)
    else:
      while index < private_info.count():
        if not result:
          result.append(private_info[index].information)
        index += len(subjects)
    return result


# NOTE: _setup_participants needs to have been called already, and each
#       subject's own avatar has already been set up.
def _setup_avatars(session):
    session_groups = list(set([sub.session_group for sub in
                          session.subject_set.filter(
                              session_group__isnull=False)]))
    for group in session_groups:
        group_subjects = session.subject_set.filter(session_group=group)
        for viewer in group_subjects:
            other_subjects = [viewed for viewed in group_subjects
                                      if viewed != viewer]
            if session.subjects_disguised:
                av_ct = len(other_subjects)
                disguises = session.disguises(av_ct)
                for viewed, d in zip(other_subjects, sample(disguises, av_ct)):
                    Avatar.objects.create( viewer       = viewer
                                         , viewed       = viewed
                                         , display_name = d['display_name']
                                         , country      = d['country']
                                         )
            else:
                for viewed in other_subjects:
                    Avatar.objects.create( viewer  = viewer
                                         , viewed  = viewed
                                         , country = viewed.country
                                         )
                
#@transaction.atomic 
def _configure_session(session, subject_external_id):
    _log.info("Session configuration starting [     : %20s]" % (subject_external_id,))
    session.start_now()
    session.save()

    _setup_participants(session)
    _setup_avatars(session)

    if session.has_etherpad_lite_task():
        session.configure_etherpad_lite_user_mgmt()

    if session.scribe_enabled:
        session.select_scribes()
    if session.confirmation_required:
        session.confirmation_deadline_datetime = session.start_datetime + timedelta(seconds=30)

    # If scribes or confirmation are required, we setup tasks after those are done 
    # in confirm_participation_confirm()
    if not session.scribe_enabled and not session.confirmation_required:
        audit.audit_log("Setup tasks",session=session)
        session.set_up_completed_tasks()

    session.status = 'S'
    session.save()

    # Clear lock that prevents more than one person from configuring a session
    for setup_lock in session.sessionsetup_set.all():
      setup_lock.delete()

    _log.info("Session configuration finished [     : %20s]" % (subject_external_id,)) 

@never_cache
def waiting_room_checkin(request, seid):
  try: 
      subject = Subject.objects.get(external_id=seid)
  except Subject.DoesNotExist:
      return _error_response(request=request)
  session = subject.session
  if session.status == 'P':
      subjects_waiting = list(session.subject_set.filter(in_waiting_room__exact=True))
      if len(subjects_waiting) == session.subject_set.count() or session.ready_to_start():
          should_start = False
          if session.should_configure():
              try:
                  _configure_session(session, seid)
              except Exception:
                  session.status = 'E'
                  session.save()
                  _log.error(("Error in _configure_session for Session %s "
                      "(Subject %s was configuring it)") % (session.id, subject))
                  return _error_response_json(request=request)
              session = Session.objects.get(pk=session.id)
  if session.status == 'E':
      _log.error(("Waiting room checkin attempt for errored session: %s by %s") 
                    % (session.id, subject))
      return _error_response_json(request=request)
  else:
      response_data = {
          'timetostart': session.total_seconds_to_start(),
          'status': session.status,
      }
  return HttpResponse(json.dumps(response_data), content_type="application/json")

def confirm_participation(request, seid):
  """
      Confirm that the user is present to participate in the session 
  """
  try:  
    subject = Subject.objects.get(external_id=seid)
  except Subject.DoesNotExist:
    return _error_response(request=request)
  audit.audit_log("Entering confirmation stage",request=request,subject=subject)
  if not subject.session.confirmation_required:
    _log.debug("Confirmation not required for subject %s" % (seid))
    return redirect(reverse(session_intro_page, kwargs={'seid' : subject.external_id}))

  template_vars = {
      'version': VERSION,
      'session' : subject.session,
      'subject_external_id': subject.external_id,
      'no_header_timer': True,
      'checkin_interval': 3,
      'domain': MCI_BASE_URL,
      'sid': subject.id,
      'display_name': subject.display_name,
      'start_url' : reverse(session_intro_page, kwargs={'seid' : subject.external_id}),
  }

  return render_to_response(
    'mci/confirmation.html',
    template_vars,
    context_instance=RequestContext(request))

@never_cache
def confirm_participation_confirm(request, seid):
  try:
    subject = Subject.objects.get(external_id=seid)
  except Subject.DoesNotExist:
    return _error_response_json(request=request)
  if subject.scribe == 'U':
    subject.scribe = 'C'
  elif subject.scribe == 'R':
    subject.scribe = 'S'   
    # Hack: EDFIX: need to handle session_group  
    # _log.debug("Confirmed user %s as scribe for group %s in session %s" % (subject.external_id, str(subject.session_group), subject.session.id))
    _log.debug("Confirmed user as scribe for group in session")
  subject.save()

  # If all scribes are confirmed, and and there is one scribe per group (or not using scribes)
  # then update the confirmation deadline to be 30 seconds from now, 
  # and setup the tasks
  unconfirmed_scribes = subject.session.subject_set.filter(scribe='R')
  confirmed_scribes = subject.session.subject_set.filter(scribe='S')

  # OK, so we need to find out how many groups are scribeless, and
  # therefore broken. The method we are using will return a list,
  # but we just need the number
  scribeless_groups = subject.session.retrieve_scribeless_group_ids()

  # About to check scribe situation
  _log.debug("Confirm participation checkin...")

  num_uncomfirmed_scribes = unconfirmed_scribes.count()
  num_confirmed_scribes = confirmed_scribes.count()
  num_scribeless_groups = len(scribeless_groups)
  num_session_groups = len(subject.session.session_groups())

  _log.debug("There are %d groups, %d unconfirmed scribes, %d confirmed scribes, %d scribeless groups" % (num_session_groups, num_uncomfirmed_scribes, num_confirmed_scribes, num_scribeless_groups))

  if (num_uncomfirmed_scribes == 0 and (num_confirmed_scribes + num_scribeless_groups) == num_session_groups) \
    or not subject.session.scribe_enabled:
    _log.debug("Ready to set up session.")
    session = subject.session
    # Wrap in a database lock, so this only happens once
    if session.should_configure():
      # Only setup if they haven't been setup yet
      if len(session.completedtask_set.all()) == 0:
        session.confirmation_deadline_datetime = datetime.today() + timedelta(seconds=30)
        session.start_datetime = session.confirmation_deadline_datetime
        session.set_up_completed_tasks()
        session.save()
      # Clear locks
      for setup_lock in subject.session.sessionsetup_set.all():
        setup_lock.delete()

  else:
    _log.debug("Not yet ready to set up session.")

  return HttpResponse('{}', content_type="application/json")


@never_cache
def confirm_participation_checkin(request, seid):
  try:
    subject = Subject.objects.get(external_id=seid)
  except Subject.DoesNotExist:
    return _error_response_json(request=request)

  scribes_count = subject.session.subject_set.filter(scribe='S').count()
  session_groups_count = len(subject.session.session_groups())

  if datetime.today() > subject.session.confirmation_deadline_datetime:
    # Wrap in a database lock, so this only happens once
    if subject.session.should_configure():
      # First, bump any people who didn't confirm when asked
      for sub in subject.session.subject_set.all():
        if sub.scribe == 'R' or (sub.scribe == 'U' and ((scribes_count == session_groups_count) or not subject.session.scribe_enabled)):
          sub.scribe = 'X'
          sub.save()
      # Now, select a new scribe, if using scribes
      if subject.session.scribe_enabled:
          subject.session.select_scribes()
      subject.session.confirmation_deadline_datetime = datetime.today() + timedelta(seconds=30)
      subject.session.save()
      for setup_lock in subject.session.sessionsetup_set.all():
        setup_lock.delete()
      # Refresh the subject, in case it's been updated by scribe selection
      try:
        subject = Subject.objects.get(external_id=seid)
      except Subject.DoesNotExist:
        return _error_response_json(request=request)

  delta = subject.session.confirmation_deadline_datetime - datetime.now()
  seconds_remaining = delta.days * 3600 * 24 + delta.seconds

  # If user's been confirmed, they can wait, unless everyone's been
  # confirmed, in which case it's time to move forwards
  if subject.scribe in ['C','S']:
    unconfirmed_subjects = subject.session.subject_set.filter(scribe__in=['R','U']).count()
    if unconfirmed_subjects == 0:
      confirmed_subjects = subject.session.subject_set.filter(scribe__in=['C','S'], session_group=subject.session_group).count()
      _log.debug("Session group contains %d confirmed subject in session %s" % (confirmed_subjects, subject.session.id))
      if confirmed_subjects >= subject.session.min_group_size:        
        response_data = {
          'status': subject.scribe,
          'action': 'advance',
          'time_remaining' : subject.session.total_seconds_to_start(),
        }
      else:
        response_data = { 
          'error' : True,
          'error_text' : 'There are not enough confirmed particpants.'
        }
    else:
      response_data = {
        'status': subject.scribe,
        'action': 'wait'
      }

  # If user's been requested to be a scribe, they need to respond
  if subject.scribe in ['R']:
    response_data = {
      'status': subject.scribe,
      'action': 'confirm',
      'time_remaining' : seconds_remaining,
    }
    
  if subject.scribe in ['U']:
    # If there are not yet scribes for all groups, then user should wait
    # ...but we need to account for the number of broken groups. Previously
    # that calculation was:
    # if (scribes_count < session_groups_count) and subject.session.scribe_enabled:
    # ...but we need to take the broken, scribeless groups into account.

    # Need to re-do this call as the number of scribes may have changed from code above
    scribes_count = subject.session.subject_set.filter(scribe='S').count()

    if subject.session.scribe_enabled and (scribes_count + len(subject.session.retrieve_scribeless_group_ids()) < session_groups_count):
      response_data = {
        'status': subject.scribe,
        'action': 'wait'
      }
    else:
      # If there are scribes for all groups, user needs to confirm
      response_data = {
        'status': subject.scribe,
        'action': 'confirm',
        'time_remaining' : seconds_remaining,
      }
  if subject.scribe in ['X']:
    response_data = { 
      'error' : True,
      'error_text' : 'You have not responded, and thus cannot participate in this session.'
    }
  
  return HttpResponse(json.dumps(response_data), content_type="application/json")

def session_intro_page(request, seid):
  """
      Start the session.
      If the session has not already started, assign people to groups, and mark the session as started.
      Then send the person the introduction page.
  """
  try:
      subject = Subject.objects.get(external_id=seid)
  except (Subject.DoesNotExist, Session.DoesNotExist):
      return _error_response(request=request)
  session = subject.session 

  if not session.ready_to_start():
      _log.info("Not ready to start [ %4s   : %20s]" % (session.status, seid))
      return HttpResponseRedirect(reverse(waiting_room, args=(seid,)))

  # This should never happen, since this URL should never be requested
  # unless the session has already been set up during a waiting_room_checkin.
  if session.status != "S":
      return HttpResponseRedirect(reverse(waiting_room, args=(seid,)))

  if not subject.session_group:
      _log.error("Subject not assigned to a group (due to group size issues) [ %4s   : %20s]" %
                    (subject.session_group, seid,))
      audit.audit_log(
          "Group assignment error",
          data="Subject not assigned to a group",
          request=request,
          subject=subject)
      mecfg = session.msg_err_cannot_form_group
      return _message_response(
          message=mecfg if mecfg else _get_text("ERROR_CANNOT_FORM_GROUP"),
          request=request)
  else:
      if session.intro_seconds_remaining() == 0:
          return go_to_current_task(request, seid)
      else:
          _log.info("Show introduction [    : %20s]" % (seid,))
          audit.audit_log(
              "Introduction",
              request=request,
              subject=subject,
              data="Starting in %s seconds " % session.intro_seconds_remaining())
          if session.display_name_page:
              return render_to_response('mci/message.html', {
                  'version': VERSION,
                  'timer' : True,
                  'timerDebug': "false",
                  'message' : session.introduction_text,
                  'next_url': reverse(session_display_name_page, kwargs={ "seid": seid, }),
                  'count_from': session.intro_seconds_remaining(),
              }, context_instance=RequestContext(request))
          elif session.roster_page:
              return render_to_response('mci/message.html', {
                  'version': VERSION,
                  'timer' : True,
                  'timerDebug': "false",
                  'message' : session.introduction_text,
                  'next_url': reverse(session_roster_page, kwargs={ "seid": seid, }),
                  'count_from': session.intro_seconds_remaining(),
              }, context_instance=RequestContext(request))
          else:
              solo_cts = CompletedTask.objects.filter(
                  completed_task_order=0,
                  solo_subject=subject)
              if solo_cts.count() > 0:
                  if solo_cts.count() > 1:
                      return _error_response(request=request)
                  ct = solo_cts[0]
              else:
                  ct = CompletedTask.objects.get(
                      completed_task_order=0,
                      session_group=subject.session_group,
                      session__id=session.id)
              return render_to_response('mci/message.html', {
                  'version': VERSION,
                  'timer' : True,
                  'timerDebug': "false",
                  'message' : session.introduction_text,
                  'next_url': _get_base_task_url(ct.id, seid, "I"),
                  'count_from': session.intro_seconds_remaining(),
              }, context_instance=RequestContext(request))

def session_display_name_page(request, seid):
    """Gives subjects the ability to set their own display names."""
    try:
        subject = Subject.objects.get(external_id=seid)
    except (Subject.DoesNotExist, Session.DoesNotExist):
        return _error_response(request=request)
    session = subject.session 

    class DisplayNameForm(ModelForm):
        class Meta:
            model = Subject
            fields = ('display_name',)
        def clean_display_name(self):
            display_name = self.cleaned_data['display_name']
            if not display_name or len(display_name) == 0:
                raise ValidationError("Name must be at least one character.")
            return display_name

    if request.method == 'POST':
        form = DisplayNameForm(request.POST, instance=subject)
        if form.is_valid():
            subject.display_name = form.cleaned_data['display_name']
            subject.save()
            _log.info("Subject %s submitted Display Name." % subject)
    else:
        form = DisplayNameForm()

    subject = Subject.objects.get(external_id=seid)
    if session.roster_page:
        return render_to_response('mci/display_name_page.html',
          { 'version'    : VERSION
          , 'timer'      : True
          , 'timerDebug' : "false"
          , 'form'       : form
          , 'next_url'   : reverse(session_roster_page, kwargs={ "seid": seid, })
          , 'count_from' : session.display_name_seconds_remaining()
          , 'seid'       : seid
          , 'display_name' : subject.display_name
          }, context_instance=RequestContext(request))
    else:
        solo_cts = CompletedTask.objects.filter(
            completed_task_order=0,
            solo_subject=subject)
        if solo_cts.count() > 0:
            if solo_cts.count() > 1:
                return _error_response(request=request)
            ct = solo_cts[0]
        else:
            ct = CompletedTask.objects.get(
                completed_task_order=0,
                session_group=subject.session_group,
                session__id=session.id)
        return render_to_response('mci/display_name_page.html', 
          { 'version'     : VERSION
          , 'timer'       : True
          , 'timerDebug'  : "false"
          , 'form'        : form
          , 'next_url'    : reverse(instructions_page, kwargs={ "ctid": ct.id
                                                              , "seid": seid } )
          , 'count_from'  : session.display_name_seconds_remaining()
          , 'seid'        : seid
          , 'display_name' : subject.display_name
          }, context_instance=RequestContext(request))
    

def session_roster_page(request, seid):
    """ If deception is disabled for the session, the roster page will list the 
        real names and flags of the session participants.  If deception is 
        enabled then the version of the roster page shown to a given participant
        will list the same false names and flags that that participant will 
        later see in the workspace.  
    """
    try:
        subject = Subject.objects.get(external_id=seid)
    except (Subject.DoesNotExist, Session.DoesNotExist):
        return _error_response(request=request)
    session = subject.session 
    solo_cts = CompletedTask.objects.filter(
        completed_task_order=0,
        solo_subject=subject)
    if solo_cts.count() > 0:
        if solo_cts.count() > 1:
            return _error_response(request=request)
        ct = solo_cts[0]
    else:
        try:
            ct = CompletedTask.objects.get(
                completed_task_order=0,
                session_group=subject.session_group,
                session__id=session.id)
        except CompletedTask.DoesNotExist:
            all_cts = session.completedtask_set.all()
            _log.error( "Couldn't find the first CT for Session %s.  CTs found: %s"
                      % (session, all_cts) )
            return _error_response(request=request)
    avatars = Avatar.objects.filter(viewer=subject).order_by('viewed__id')
    return render_to_response('mci/roster.html', {
        'version': VERSION,
        'timer' : True,
        'timerDebug': "false",
        'message': "Your team roster:",
        'avatars_list': _avatars_list(avatars),
        'next_url': reverse(instructions_page, kwargs={ "ctid": ct.id
                                                      , "seid": seid 
                                                      }),
        'count_from': session.roster_seconds_remaining(),
    }, context_instance=RequestContext(request))


def instructions_page(request, ctid, seid):
    """Show the instructions for the coming task """

    _log.info("Show instructions [%4s : %20s]" % (ctid, seid))
    try:
        completed_task = CompletedTask.objects.get(pk=ctid)
    except CompletedTask.DoesNotExist:
        _log_completedtask_dne(request, ctid, seid, "Task Instructions Page")
        return _error_response(request=request)
    # TODO: replace the next two lines with a call to a 'start' method
    completed_task.start_time = datetime.today()
    completed_task.save()
    audit.audit_log(
        "Load Instructions", 
        request=request, 
        completed_task=completed_task,
        subject_external_id=seid)
    resp = render_to_response('mci/message.html', {
        'version': VERSION,
        'timer': True,
        'timerDebug': "false",
        'message': completed_task.task.instructions,
        'next_url': _get_base_task_url(ctid, seid, 'P' if completed_task.task.primer else 'W'),
        'count_from': completed_task.instructions_seconds_remaining(),
        'checkin_url': reverse(instructions_checkin, kwargs={ "ctid": ctid, "seid": seid, }),
    }, context_instance=RequestContext(request))
    return resp    

def instructions_preview(request, task_id):
  """Preview the instructions for a task"""
  return _preview_response(
      task_id=task_id,
      field="instructions",
      template='mci/message.html',
      timer=True,
      request=request)

@never_cache
def instructions_checkin(request, ctid, seid):
    try:
        completed_task = CompletedTask.objects.get(pk=ctid)
    except CompletedTask.DoesNotExist:
        _log_completedtask_dne(request, ctid, seid, "Task Instructions Checkin URL")
        return _error_response(request)
    response_data = {
        'count_from': completed_task.instructions_seconds_remaining(),
    }
    return HttpResponse(json.dumps(response_data), content_type="application/json")

def primer_page(request, ctid, seid):
    """Show the primer for the task """
    _log.info("Show primer       [%4s : %20s]" % (ctid, seid))
    try:
        completed_task = CompletedTask.objects.get(pk=ctid)
    except CompletedTask.DoesNotExist:
        _log_completedtask_dne(request, ctid, seid, "Task Primer Page")
        return _error_response(request=request)
    try:
        subject = Subject.objects.get(external_id=seid)
    # TODO: create a similar 'exception log' method for the "bad SEID" case
    except Subject.DoesNotExist:
        pass
    audit.audit_log(
        "Load Primer",
        request=request,
        completed_task=completed_task,
        subject_external_id=seid)
    template_vars = {
        'version': VERSION,
        'task_type': completed_task.task.task_type,
        'subject_external_id': seid,
        'sid': subject.id,
        'display_name': subject.display_name,
        #'opentok_session_id': completed_task.session.opentok_session_id,
        #'opentok_token': subject.opentok_token,
        'video_height': 80,
        'video_width': 130,
        'message' : completed_task.task.primer,
        'message_left_sidebar': completed_task.task.primer_sidebar_text,
        'next_url': _get_base_task_url(ctid, seid, 'W'),
        'count_from': completed_task.primer_seconds_remaining(),
        'checkin_url': reverse(primer_checkin, kwargs={ "ctid": ctid, "seid": seid, }),
        'timer': True,
        'timerDebug': "false",        
    }
    return render_to_response(
        'mci/message.html',
        template_vars,
        context_instance=RequestContext(request))

def primer_preview(request, task_id):
    """Preview the primer (if any) for a task"""
    return _preview_response(
        task_id=task_id,
        field="primer",
        template='mci/message.html',
        timer=True,
        request=request)

@never_cache
def primer_checkin(request, ctid, seid):
    try:
        completed_task = CompletedTask.objects.get(pk=ctid)
    except CompletedTask.DoesNotExist:
        _log_completedtask_dne(request, ctid, seid, "Task Primer Checkin URL")
        return _error_response(request)
    response_data = {
        'next_url': _get_base_task_url(ctid, seid, 'W'),
        'count_from': completed_task.primer_seconds_remaining(),
    }
    return HttpResponse(json.dumps(response_data), content_type="application/json")

@never_cache
def workspace_page(request, ctid, seid):
    """Show the workspace task"""
    _log.info("Show workspace    [%4s : %20s]" % (ctid, seid))
    try:
        completed_task = CompletedTask.objects.get(pk=ctid)
        sesh = completed_task.session
    except (CompletedTask.DoesNotExist, Subject.DoesNotExist):
        _log_completedtask_dne(request, ctid, seid, "Task Primer Checkin URL")
        return _error_response(request=request)
    subject = Subject.objects.get(external_id=seid)
    if sesh.has_etherpad_lite_task() and not subject.etherpad_lite_identity_assigned():
        subject.assign_etherpad_lite_identity(sesh.get_pad_client())
    subject = Subject.objects.get(external_id=seid)
    audit.audit_log(
        "Load Workspace",
        request=request,
        completed_task=completed_task,
        subject_external_id=seid)
    iframe_src = completed_task.etherpad_workspace_url + \
                  "?client=true" + \
                  "&showLineNumbers=false" + \
                  ("&grid=true" if completed_task.task.task_type == 'G' else "") + \
                  ("&alwaysShowChat=true" if completed_task.task.chat_enabled else "&showChat=false")
    template_vars = {
        'version': VERSION,
        'subject_external_id': seid,
        'completed_task': completed_task,
        'private_information': _get_private_information(completed_task, seid),
        # TODO: whack this assuming it is as superfluous as it looks 
        'task_type': completed_task.task.task_type,
        'iframe_src': iframe_src,
        # Countdown-related vars
        'next_url': _completed_task_next_url(completed_task, seid),
        'begin_after': completed_task.preplay_seconds_remaining(),
        'count_from': completed_task.workspace_seconds_remaining(),
        'checkin_url': reverse(workspace_checkin, kwargs={ "ctid": ctid, "seid": seid }),
        # Keys used only by Concentration-type Tasks
        'preplay_count_from': completed_task.preplay_seconds_remaining(),
        'preplay_checkin_url': reverse(preplay_checkin, kwargs={ "ctid": ctid, "seid": seid }),
        'preplay_countdown_sublabel': completed_task.task.preplay_countdown_sublabel,
        'video': completed_task.session.video_enabled,
        'domain': MCI_BASE_URL,
        'no_header_timer': completed_task.task.task_type in ['C', 'I'],
        'timerDebug': "false",
        'sid': subject.id,
        'display_name': subject.display_name,
        'realtime_game_host': MCI_CONCENTRATION_BASE_URL,
        #'opentok_session_id': completed_task.session.opentok_session_id,
        #'opentok_token': subject.opentok_token,
        'video_height': 80,
        'video_width': 130,
        'seconds_between_rounds': completed_task.task.time_between_rounds,
        # Keys used only for Squares-type tasks
        'squares_set_width': squares_set_width,
        'squares_set_height': squares_set_height, 
        'board_area_border_thickness': board_area_border_thickness,
        # Load testing
        'load_test': completed_task.session.load_test,
        'mousemove_interval': completed_task.task.mousemove_interval 
      , 'scribe_author_id' : completed_task.scribe().etherpad_author_id if completed_task.scribe() else None
      , 'scribe_display_name' : completed_task.scribe().display_name if completed_task.scribe() else None
      , 'user_author_id'   : subject.etherpad_author_id
      , 'subject_can_edit': subject.is_scribe_or_scribe_disabled(completed_task)
    }
    if completed_task.session.has_realtimegame_task():
        if completed_task.solo_subject: 
            avatars = Avatar.objects.filter(viewer=subject, viewed=subject)
        else:
            avatars = Avatar.objects.filter(viewer=subject).order_by('viewed__id')
        template_vars['avatars_list'] = _avatars_list(avatars)
        template_vars['avatars_json'] = json.dumps(_avatars_dict(avatars))
    resp = render_to_response(
        'mci/task_workspace.html',
        template_vars,
        context_instance=RequestContext(request))
    resp.delete_cookie("token")
    resp.set_cookie( "sessionID"
                   , value=subject.etherpad_session_id
                   , path="/"
                   , domain=MCI_DOMAIN
                   )
    patch_cache_control(resp, no_cache=True, no_store=True, must_revalidate=True)
    return resp
    

@never_cache
def preplay_checkin(request, ctid, seid):
    try:
        completed_task = CompletedTask.objects.get(pk=ctid)
    except CompletedTask.DoesNotExist:
        _log_completedtask_dne(request, ctid, seid, "Preplay Checkin URL")
        return _error_response(request)
    response_data = {
        'count_from': completed_task.preplay_seconds_remaining(),
    }
    return HttpResponse(json.dumps(response_data), content_type="application/json")

@never_cache
def workspace_checkin(request, ctid, seid):
    try:
        completed_task = CompletedTask.objects.get(pk=ctid)
    except CompletedTask.DoesNotExist:
        _log_completedtask_dne(request, ctid, seid, "Workspace Checkin URL")
        return _error_response(request=request)
    response_data = {
        'next_url': _completed_task_next_url(completed_task, seid),
        'begin_after': completed_task.preplay_seconds_remaining(),
        'count_from': completed_task.workspace_seconds_remaining(),
    }
    return HttpResponse(json.dumps(response_data), content_type="application/json")


def workspace_popup(request, task_id):
  try:
    task = Task.objects.get(pk=task_id)
  except Task.DoesNotExist:
    return _error_response(request=request)
  return render_to_response('mci/task_workspace_popup.html', {
        'version': VERSION,
        'task' : task,
    }, context_instance=RequestContext(request))


def workspace_results(request, completed_task_id):
  """View the results of a task by viewing the completed workspace"""
  try:
    completed_task = CompletedTask.objects.get(pk=completed_task_id)
  except CompletedTask.DoesNotExist:
    return _error_response(request=request)

  iframe_src = completed_task.etherpad_workspace_url + \
                "?showLineNumbers=false" + \
                ("&grid=true" if completed_task.task.task_type == 'G' else "") + \
                ("&showChat=true" if completed_task.task.chat_enabled else "")

  resp = render_to_response('mci/task_workspace.html', {
    'version': VERSION,
    'completed_task' : completed_task,
    'view_results_only' : True,
    'iframe_src': iframe_src,
    'timerDebug': "false",
    }, context_instance=RequestContext(request))
  resp.delete_cookie("token")
  s = completed_task.session
  if s.etherpad_group_id and s.etherpad_admin_session_id:
      resp.set_cookie( "sessionID"
                     , value=s.etherpad_admin_session_id
                     , path="/"
                     , domain=MCI_DOMAIN
                     )
  patch_cache_control(resp, no_cache=True, no_store=True, must_revalidate=True)
  return resp
  


def opentok_subscribed_to_stream(request, sub_seid, pub_seid):
    _log.debug("Subject %s subscribed to subject %s's video stream." %
        (sub_seid, pub_seid))
    return HttpResponse('')

def opentok_published_stream(request, pub_seid):
    _log.debug("Subject %s published a video stream." % pub_seid)
    return HttpResponse('')

def workspace_preview(request, task_id):
    """Preview the workspace view for an Etherpad-based task, and edit the 
        underlying Etherpad instance for that task"""
    from workspace import workspace
    try:
        task = Task.objects.get(pk=task_id)
    except CompletedTask.DoesNotExist:
        return _error_response(request=request)
    completed_task = CompletedTask()
    completed_task.task = task
    completed_task.etherpad_workspace_url = workspace.pad_url_for_pad_id(
        task.etherpad_template)
    # TODO what does the 'client' param even do?
    iframe_src = completed_task.etherpad_workspace_url + \
                  "?client=true" + \
                  "&showLineNumbers=false" + \
                  ("&grid=true" if completed_task.task.task_type == 'G' else "") + \
                  ("&showChat=true" if completed_task.task.chat_enabled else "")
    resp = render_to_response('mci/task_workspace.html', {
        'version': VERSION,
        'completed_task': completed_task,
        'iframe_src': iframe_src,
    }, context_instance=RequestContext(request))
    patch_cache_control(resp, no_cache=True, no_store=True, must_revalidate=True)
    return resp    

def go_to_current_task(request, seid):
    try:
        subject = Subject.objects.get(external_id=seid)
    except (Subject.DoesNotExist, CompletedTask.DoesNotExist):
        return _error_response(request=request)
    session = subject.session
    buffer = 0
    now = datetime.today()
    solo_cts = CompletedTask.objects.filter(
        session__id=session.id,
        solo_subject=subject,
        expected_start_time__lt=now,
        expected_finish_time__gt=now)
    if solo_cts.count() > 0:
        if solo_cts.count() > 1:
            return _error_response(request=request)
        ct = solo_cts[0]
    else:
        group_cts = CompletedTask.objects.filter(
            session__id=session.id,
            session_group=subject.session_group,
            expected_start_time__lt=now,
            expected_finish_time__gt=now)
        if group_cts.count() == 0:
            group_cts = CompletedTask.objects.filter(
                session__id=session.id,
                session_group=subject.session_group,
                expected_finish_time__gt=now)
            return _message_response("Your session has ended!", request)
        if group_cts.count() > 1:
            _log.error("Found more than one current Completed Task")
            return _error_response(request=request)
        ct = group_cts[0]
    tdi = timedelta(seconds = ct.task.instructions_time - buffer)
    if now < ct.expected_start_time + tdi:
        mode = "I"
    else:
        tdp = timedelta(seconds=(ct.task.instructions_time \
                + ct.task.primer_time \
                - buffer))
        if ct.task.primer and now < ct.expected_start_time + tdp:
            mode = "P"
        else:
            mode = "W"
    url = _get_base_task_url(ct.id, seid, mode)
    return redirect(url)

def done(request, seid):
    try:
        subject = Subject.objects.get(external_id=seid)
        audit.audit_log("Done",request=request,subject=subject)
    except Subject.DoesNotExist:
        return _error_response(request=request)  
    if subject.session.done_redirect_url:
        return render_to_response('mci/message.html', {
            'version': VERSION,
            'timer' : True,
            'timerDebug': "false",
            'message' : subject.session.done_text,
            'count_from': subject.session.done_seconds_remaining(),
            'next_url' : subject.session.done_redirect_url,
        }, context_instance=RequestContext(request))
    return _message_response(subject.session.done_text,request)

# TODO: delete these, view and URL mapping both
@transaction.atomic
def _rollbacktest():
    Region.objects.create(name="daffy")
    raise Exception

def rollbacktest(request):
    from mci.models import Region
    try:
        _rollbacktest()
    except:
        pass
    return HttpResponse(Region.objects.all())

def bandwidthtest(request):
    return render_to_response('mci/bandwidthtest.html',{}, context_instance=RequestContext(request))


def configure_next_round(request, ctid):
    try:
        completed_task = CompletedTask.objects.get(pk=ctid)
    except CompletedTask.DoesNotExist:
        _log_completedtask_dne(request, ctid, seid, "'Configure Next Round'")
        return HttpResponse(json.dumps({ 'error': 'bad ctid' }))
    try:
        new_rnd_index = completed_task.configure_next_round()
    except:
        return HttpResponse(json.dumps({ 'error': 'round not configured' }))
    return HttpResponse(json.dumps({ 'round': new_rnd_index } ))
