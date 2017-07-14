import json
import traceback
import re
import uuid
from django.db import models
from datetime import datetime, timedelta
import time
import django.db.models.options as options
from django.db import transaction, IntegrityError
from urllib2 import quote
from django.db.models.signals import pre_save
from settings import MCI_REDIS_SERVER         \
                   , MCI_REDIS_PORT           \
                   , MCI_OPENTOK_API_KEY      \
                   , MCI_OPENTOK_API_SECRET   \
                   , game_board_width         \
                   , game_board_height        \
                   , squares_set_width        \
                   , squares_set_height       \
                   , MCI_ETHERPAD_API_URL     \
                   , MCI_ETHERPAD_API_KEY     \
                   , MCI_ETHERPAD_USING_REDIS \
                   , MCI_ETHERPAD_REDIS_CONF
from django.db.models import Q
from django.db.models.query import QuerySet
import OpenTokSDK
from django.core.urlresolvers import reverse
from itertools import combinations
from math import ceil
from operator import attrgetter
from pprint import pformat, pprint
from mci.workspace.py_etherpad import *
from mci.workspace.squares_pieces import random_n_length_sublists_unique_on_attribute
from mci.workspace.workspace import pad_url_for_pad_id
from random import choice, shuffle
import math
import redis
from operator import or_
from mci.util.summaries import listWithTotalsLast
import logging
_log       = logging.getLogger("cci")
_cards_log = logging.getLogger("concentration_cards")
from collections import namedtuple
PseudonymReq = namedtuple('PseudonymReq',
    'region, fem, num, session_template, session, session_builder')
from south.modelsinspector import add_introspection_rules
from django.contrib.auth.models import User
from django.db.models.signals import post_save

options.DEFAULT_NAMES = options.DEFAULT_NAMES + ('in_db',)

class QuerySetWithPermissions(QuerySet):
    def owned_by_virtue_of_ug_membership(self, user, ugs):
        shares_any_usergroup = reduce(or_, [Q(usergroups=ug) for ug in ugs])
        return shares_any_usergroup
    def permitted_in_change_list(self, user):
        if user.is_superuser:
            return self
        if user.userprofile.owns_all_owned_objects:
            return self
        ugs = user.ugroups.all()
        if not ugs:
            return self.none()
        qs = self.filter(self.owned_by_virtue_of_ug_membership(user, ugs)).distinct()
        return qs
    def permitted_in_change_list_or_selected(self, user, existing_selection):
        if user.is_superuser:
            return self
        if user.userprofile.owns_all_owned_objects:
            return self
        ugs = user.ugroups.all()
        if not ugs:
            return self.none()
        owned = self.owned_by_virtue_of_ug_membership(user, ugs)
        in_existing_selection = Q(pk__in=existing_selection)
        qs = self.filter(Q(owned | in_existing_selection)).distinct()
        return qs

class ManagerWithPermissions(models.Manager):
    def get_queryset(self):
        return QuerySetWithPermissions(self.model, using=self._db)
    def permitted_in_change_list(self, user):
        return self.get_queryset().permitted_in_change_list(user)
    def permitted_in_change_list_or_selected(self, user, existing_selection):
        return self.get_queryset().permitted_in_change_list_or_selected(user, existing_selection)

def event_cmp(x, y):
    _cmp = cmp(x.timestamp, y.timestamp)
    if _cmp == 0:
        if '| setup' in x.data and '| match' in y.data:
            return -1
        if '| match' in x.data and '| setup' in y.data:
            return 1
    return _cmp

def _format_datetime(dt):
    return dt.strftime("%Y-%m-%d-%H-%M-%S")

def counter(counts, item):
    counts[item] = counts.get(item, 0) + 1
    return counts

class AheadOfSchedule(Exception):
    pass

def _seconds_remaining(start_time, end_time):
    """Return the number of seconds in the timedelta, but 0 if the timedelta is
        negative"""
    try:
        current_time = datetime.now()
        if current_time < start_time:
            raise AheadOfSchedule
    except AheadOfSchedule:
        #_log.error("AheadOfSchedule encountered in _seconds_remaining.")
        pass
    time_remaining = end_time - max(current_time, start_time)
    return time_remaining.seconds if time_remaining > timedelta() else 0


class Text(models.Model):
    """Configurable text strings that can be displayed throughout the application"""
    key = models.CharField(max_length=32)
    text = models.TextField()

    def __unicode__(self):
        return unicode(self.key)

class DateTimeFractionField(models.DateTimeField):
    description = "Datetimefield with fraction second. Requires MySQL 5.4.3 or greater"

    def __init__(self, *args, **kwargs):
        super(DateTimeFractionField, self).__init__(*args, **kwargs)

    def db_type(self, connection):
        return 'DATETIME(%s)' % 6

    add_introspection_rules([], ["^mci\.models\.DateTimeFractionField"])

class EventLog(models.Model):
    event = models.CharField(max_length=64)
    data = models.TextField(default='',blank=True)
    chat_name = models.TextField(default='',blank=True)
    subject = models.ForeignKey('Subject', null=True)
    session = models.ForeignKey('Session', null=True)
    session_group = models.IntegerField(null=True)
    completed_task = models.ForeignKey('CompletedTask', null=True)
    ip_address = models.IPAddressField(null=True)
    timestamp = DateTimeFractionField()

class EtherpadLiteRecordManager(models.Manager):

    key_of_set_author_records = "ueberDB:keys:globalAuthor"
    key_of_set_mapper_records = "ueberDB:keys:mapper2author"

    def clear_querysets(self):
        self.author_records = []
        self.mapper_records = []
        self.authors = {}
        self.chat_records_by_completed_task = {}
        self.edit_records_by_completed_task = {}

    def __init__(self, *args, **kwargs):
        super(EtherpadLiteRecordManager, self).__init__(*args, **kwargs)
        self.clear_querysets()

    def key_of_set_edits(self, pad_id):
        return "pad:%s:revs" % pad_id

    def key_of_set_chats(self, pad_id):
        return "pad:%s:chat" % pad_id

    def fetch_author_queryset(self):
        raise NotImplementedError

    def fetch_mapper_queryset(self):
        raise NotImplementedError

    def fetch_chat_querysets(self, cts):
        raise NotImplementedError

    def fetch_edit_querysets(self, cts):
        raise NotImplementedError

    def fetch_querysets(self, ct, full_session):
        if not self.author_records:
            self.author_records = self.fetch_author_queryset()
        if not self.mapper_records:
            self.mapper_records = self.fetch_mapper_queryset()

        el_cts = ct.session.completedtask_set.filter(task__task_type__in=['T','G'])
        cts = el_cts if full_session else [ct]

        cts_with_unfetched_chat_querysets = [ct for ct in cts
                                                if not ct.pk in self.chat_records_by_completed_task]
        if cts_with_unfetched_chat_querysets:
            ctids_by_pad_id = dict([(ct.pad_id(), ct.pk) for ct in cts_with_unfetched_chat_querysets])
            records = list(self.fetch_chat_querysets(cts_with_unfetched_chat_querysets))
            for record in records:
                pad_id = (record.key.split(":")[1],)
                ctid = ctids_by_pad_id[pad_id]
                if not ctid in self.chat_records_by_completed_task:
                    self.chat_records_by_completed_task[ctid] = []
                self.chat_records_by_completed_task[ctid].append(record)

        cts_with_unfetched_edit_querysets = [ct for ct in cts
                                                if not ct.pk in self.edit_records_by_completed_task]
        if cts_with_unfetched_edit_querysets:
            ctids_by_pad_id = dict([(ct.pad_id(), ct.pk) for ct in cts_with_unfetched_edit_querysets])
            records = list(self.fetch_edit_querysets(cts_with_unfetched_edit_querysets))
            for record in records:
                pad_id = (record.key.split(":")[1],)
                ctid = ctids_by_pad_id[pad_id]
                if not ctid in self.edit_records_by_completed_task:
                    self.edit_records_by_completed_task[ctid] = []
                self.edit_records_by_completed_task[ctid].append(record)

    def mapperForAuthorId(self, etherpadAuthorId):
        #_log.info("mapperForAuthorId >> etherpadAuthorId: %s" % etherpadAuthorId)
        mapper_record = next(r for r in self.mapper_records if r.value_raw == ("\"%s\"" % etherpadAuthorId))
        matches = re.search('mapper2author:(.*)', mapper_record.key)
        mapper = matches.group(1)
        #print "mapper: %r" % mapper
        return mapper

    def authorData(self, etherpadAuthorId):
        #_log.info("authorData >> etherpadAuthorId: %s" % etherpadAuthorId)
        if etherpadAuthorId in self.authors:
            (authorData, subject_id) = self.authors[etherpadAuthorId]
        else:
            author_record = next(r for r in self.author_records if r.key == ("globalAuthor:%s" % etherpadAuthorId))
            authorData = json.loads(author_record.value_raw)
            try:
                subject_id = self.mapperForAuthorId(etherpadAuthorId)
            # Not every etherpadAuthorId is mapped to a subject, because we weren't
            # using EL's user mgmt featues until Summer 2014.  So we need to fail gracefully.
            except StopIteration:
                subject_id = None
            self.authors[etherpadAuthorId] = (authorData, subject_id)
        return (authorData, subject_id)

    def chats(self,completed_task, full_session=False):
        _log.info("mci.models.EtherpadLiteRecordManager.chats >> entering (ct %s)" % completed_task.pk)
        d = datetime.now()

        self.fetch_querysets(completed_task, full_session)

        records = self.chat_records_by_completed_task.get(completed_task.pk, [])
        for item in records:
            item.value = json.loads(item.value_raw)
            item.event = 'Chat'
            item.data = item.value['text']
            item.time = datetime.fromtimestamp(item.value['time'] / 1000.0)
            item.etherpadAuthorValue = None
            if 'userId' in item.value and item.value['userId']:
                etherpadAuthorId = item.value['userId']
                #_log.info("mci.models.EtherPadLiteManager.chats >> about to call authorData for item %s (etherpadAuthorId %s)"
                #            % (item.pk, etherpadAuthorId))
                (item.etherpadAuthorValue, item.subject_id) = self.authorData(etherpadAuthorId)
                item.chat_name = item.etherpadAuthorValue.get('name')
            item.completed_task = completed_task

        elapsed = datetime.now() - d
        _log.info("mci.models.EtherpadLiteRecordManager.chats >> done in %f" % (elapsed.seconds + elapsed.microseconds / 1000000.0))

        return filter(None,records)

    def edits(self,completed_task, full_session=False):
        _log.info("mci.models.EtherpadLiteRecordManager.edits >> entering (ct %s)" % completed_task.pk)
        d = datetime.now()

        self.fetch_querysets(completed_task, full_session)

        records = self.edit_records_by_completed_task.get(completed_task.pk, [])
        for item in records:
            item.value = json.loads(item.value_raw)
            item.event = 'Edit pad'
            item.time = datetime.fromtimestamp(item.value['meta']['timestamp'] / 1000.0)
            item.etherpadAuthorValue = None
            if 'author' in item.value['meta'] and item.value['meta']['author']:
                etherpadAuthorId = item.value['meta']['author']
                #print "edits >> etherpadAuthorId: %s" % etherpadAuthorId
                #_log.info("mci.models.EtherPadLiteManager.edits >> about to call authorData for item %s (etherpadAuthorId %s)" % (item.pk, etherpadAuthorId))
                (item.etherpadAuthorValue, item.subject_id) = self.authorData(etherpadAuthorId)
                item.chat_name = item.etherpadAuthorValue['name']
            item.completed_task = completed_task

        elapsed = datetime.now() - d
        _log.info("mci.models.EtherpadLiteRecordManager.edits >> done in %f" % (elapsed.seconds + elapsed.microseconds / 1000000.0))

        return filter(None,records)


class EtherpadLiteRecordManagerRedis(EtherpadLiteRecordManager):

    def __init__(self, redis_conf, *args, **kwargs):
        super(EtherpadLiteRecordManagerRedis, self).__init__(*args, **kwargs)
        self.redis_conn = redis.Redis( host = redis_conf['host']
                                     , port = redis_conf['port']
                                     , db   = redis_conf['database']
                                     )

    def rc_get_or_None(self, key):
        #print ("rc_get_or_None >> key: %s" % key)
        value_raw = self.redis_conn.get(key)
        return EtherpadLiteRecord(key=key, value_raw=value_raw)

    def rc_kvs_or_null(self, key_of_set):
        _log.debug("rc_kvs_or_null >> calling SMEMBERS with key: %s" % key_of_set)
        d = datetime.now()
        keys = self.redis_conn.smembers(key_of_set)
        e = datetime.now() - d
        _log.debug("rc_kvs_or_null >> called SMEMBERS, elapsed: %s" % e)
        if not keys:
            _log.debug("We did not get any members for: %s" % key_of_set)
            return []
        _log.debug("rc_kvs_or_null >> calling MGET with key count: %d" % (len(keys)))
        d = datetime.now()
        vals = self.redis_conn.mget(keys)
        e = datetime.now() - d
        _log.debug("rc_kvs_or_null >> called MGET, val count: %d.  elapsed: %s" % (len(vals), e))
        #print("rc_kvs_or_null >> vals: \n%s" % pformat(vals))
        return [EtherpadLiteRecord(key=k, value_raw=v) for (k, v) in zip(keys, vals)]

    def fetch_author_queryset(self):
        return self.rc_kvs_or_null(self.key_of_set_author_records)

    def fetch_mapper_queryset(self):
        return self.rc_kvs_or_null(self.key_of_set_mapper_records)

    def fetch_chat_querysets(self, cts):
        _log.info("EtherpadLiteRecordManagerRedis.fetch_chat_querysets >> entering.  cts: %s" % cts)
        d = datetime.now()
        result = []
        for ct in cts:
            pad_id = ct.pad_id()
            result.extend(self.rc_kvs_or_null(self.key_of_set_chats(pad_id)))

        elapsed = datetime.now() - d
        _log.info("EtherpadLiteRecordManagerRedis.fetch_chat_querysets >> done in %f" % (elapsed.seconds + elapsed.microseconds / 1000000.0))

        return result

    def fetch_edit_querysets(self, cts):
        _log.info("EtherpadLiteRecordManagerRedis.fetch_edit_querysets >> entering.  cts: %s" % cts)
        d = datetime.now()
        result = []
        for ct in cts:
            pad_id = ct.pad_id()
            result.extend(self.rc_kvs_or_null(self.key_of_set_edits(pad_id)))

        elapsed = datetime.now() - d
        _log.info("EtherpadLiteRecordManagerRedis.fetch_edit_querysets >> done in %f" % (elapsed.seconds + elapsed.microseconds / 1000000.0))

        return result

class EtherpadLiteRecordManagerMySQL(EtherpadLiteRecordManager):

    def __init__(self, *args, **kwargs):
        _log.info("EtherpadLiteRecordManagerMySQL.__init__ >> entering...")
        super(EtherpadLiteRecordManagerMySQL, self).__init__(*args, **kwargs)

    def fetch_author_queryset(self):
        return super(EtherpadLiteRecordManager,self).filter(key__startswith=self.key_of_set_author_records)

    def fetch_mapper_queryset(self):
        return super(EtherpadLiteRecordManager,self).filter(key__startswith=self.key_of_set_mapper_records)

    def fetch_chat_querysets(self, cts):
        condition = reduce(or_, [Q(key__startswith=self.key_of_set_chats(ct.pad_id())) for ct in cts])
        return super(EtherpadLiteRecordManager,self).filter(condition)

    def fetch_edit_querysets(self, cts):
        condition = reduce(or_, [Q(key__startswith=self.key_of_set_edits(ct.pad_id())) for ct in cts])
        return super(EtherpadLiteRecordManager,self).filter(condition)

class EtherpadLiteRecord(models.Model):
    """ Readonly view of the Etherpad Lite database    """

    def __unicode__(self):
        return ''.join([ "EtherpadLiteRecord >>"
                       , "\n\tKey:        %s" % self.key
                       , "\n\tRaw value:  %s" % self.value_raw
                       , "\n\tSubject ID: %s" % self.subject_id
                       , "\n\tChat name:  %s" % self.chat_name
                       , "\n\tTimestamp:  %s" % str(self.time)
                       ])

    key = models.TextField(max_length=100,primary_key=True)
    value_raw = models.TextField(db_column='value')
    value = {}
    event               = None
    etherpadAuthorValue = None
    subject_id          = None
    time                = None
    data                = None
    completed_task      = None
    chat_name           = None

    objects = EtherpadLiteRecordManagerRedis(MCI_ETHERPAD_REDIS_CONF) \
                  if MCI_ETHERPAD_USING_REDIS else EtherpadLiteRecordManagerMySQL()

    class Meta:
        managed = False
        db_table = "store"
        in_db = "etherpad-lite"
        ordering = ["key"]

    def event_log_entry(self, session=None, session_group=None, subs={}, cache_subjects=False):
        if self.etherpadAuthorValue:
            #print "event_log_entry >> self.event: %s" % self.event
            if self.subject_id:
                #print "event_log_entry >> self.subject_id: %s" % self.subject_id
                if "sessionAdmin" in self.subject_id:
                    subject = Subject( external_id=""
                                     , session=session if session else self.completed_task.session
                                     , session_group=session_group
                                     )
                else:
                    if cache_subjects:
                        try:
                            subject = subs[self.subject_id]
                        except KeyError:
                            _log.info("Subject %s not found in subs, adding" % self.subject_id)
                            subject = Subject.objects.get(pk=self.subject_id)
                            subs[self.subject_id] = subject
                    else:
                        subject = Subject.objects.get(pk=self.subject_id)
            else:
                if 'externalId' in self.etherpadAuthorValue:
                    external_id = self.etherpadAuthorValue['externalId']
                elif 'name' in self.etherpadAuthorValue:
                    external_id = self.etherpadAuthorValue['name']
                else:
                    external_id = ""
                subject = Subject(
                    external_id=external_id,
                    session=session if session is not None else self.completed_task.session,
                    session_group=session_group,
                )
            #print "event_log_entry >> self.subject.external_id: %s" % subject.external_id
            return EventLog( event          = self.event
                           , data           = self.data      if self.data      is not None else ""
                           , chat_name      = self.chat_name if self.chat_name is not None else ""
                           , timestamp      = self.time
                           , subject        = subject
                           , session        = session
                           , session_group  = session_group
                           , completed_task = self.completed_task
                           )

    def save(self, *args, **kwargs):
        raise NotImplementedError

    def delete(self, *args, **kwargs):
        if "yes, really" in args:
            return super(EtherpadLiteRecord, self).delete()
        else:
            raise NotImplementedError

class DisguiseSelection(models.Model):
    def __unicode__(self):
        return unicode("Position %d for %s: %s/%s" % (
            self.position,
            unicode(self.session if self.session else self.session_template),
            unicode(self.region),
            unicode("Feminine" if self.feminine else "Masculine"),
        ))
    session_template = models.ForeignKey(
        'SessionTemplate',
        null=True,
        blank=True,
        related_name='disguise_selections')
    session = models.ForeignKey(
        'Session',
        null=True,
        blank=True,
        related_name='disguise_selections')
    region = models.ForeignKey(
        'Region',
        related_name='disguise_selections')
    feminine = models.BooleanField(default=True)
    # TODO: Make sure this 'position' bit works with Grappelli, and that
    #       DSs get READ in this order, both for purposes of REPORTING
    #       REQUIREMENTS and for actually selecting disguises.
    position = models.SmallIntegerField('Position')
    position.verbose_name=""

def _reqs_from_disguise_selections(dss, sb, st, s):
    def _counter(counts, disguise_selection):
        region_pk = disguise_selection.region.pk
        fem = disguise_selection.feminine
        if not region_pk in counts:
            counts[region_pk] = { True: 0, False: 0, }
        counts[region_pk][fem] += 1
        return counts
    counts = reduce(_counter, dss, {})
    reqs = [
        PseudonymReq(
            session=s,
            session_template=st,
            session_builder=sb,
            region=Region.objects.get(pk=region_pk),
            fem=fem,
            num=counts[region_pk][fem],
        ) for region_pk in counts
          for fem in [True, False]
          if counts[region_pk][fem] > 0
    ]
    return reqs

class SessionBase(models.Model):
    name = models.CharField(max_length=64)
    scribe_enabled = models.BooleanField(
        default=False,
        verbose_name="Require a scribe")
    confirmation_required = models.BooleanField(
        default=False,
        verbose_name="Require confirmation before starting session")
    subjects_disguised = models.BooleanField(
        default=False,
        verbose_name="Deception",
        help_text="""If this is checked, Subjects in game-type tasks will see
        fake names and flags for other Subjects.  Further down this page, under
        'Disguise Types to be Used', you can indicate the regions from which
        the fake name/flag pairs will be chosen.""")
    video_enabled = models.BooleanField(
        default=False,
        verbose_name="Video",
        help_text="""If video is enabled, Subjects in game-type tasks will see
        video of other Subjects.  (Note that this is only intended for Sessions
        with up to 6 participating Subjects.""")
    disguise_regions = models.ManyToManyField(
        'Region',
        through='DisguiseSelection')
    solo_task_group_start = models.ForeignKey(
        'TaskGroup',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='+')
    solo_task_group_start.verbose_name = "Solo task group at start of session"
    solo_task_group_end = models.ForeignKey(
        'TaskGroup',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='+')
    initial_task_group = models.ForeignKey(
        'TaskGroup',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='+')
    solo_task_group_end.verbose_name = "Solo task group at end of session"
    task_groups = models.ManyToManyField("TaskGroup", verbose_name="Main Task Groups")
    introduction_text = models.TextField(default="Some default text.")
    introduction_time = models.PositiveIntegerField(
        verbose_name="Introduction time",
        help_text="Time to display introduction (seconds)",
        default=15)
    done_text = models.TextField(default="Some default text.")
    done_time = models.PositiveIntegerField(
        verbose_name="Done time",
        help_text="Time to display final message before redirecting (seconds)",
        default=15)
    done_redirect_url = models.CharField(
        max_length=256,
        default="http://www.google.com")
    load_test = models.BooleanField(
        default=False,
        help_text=""" If this is True, each Subjects's browser will
                      emit a stream of fake cursor movements and clicks (in a
                      way that emulates real, if brainless, Concentration or
                      Tiles gameplay).
                  """)

    display_name_page = models.BooleanField(
        default=True,
        verbose_name="Ask for Display Name",
        help_text=""" If this is True, each Subject will see a 'Display Name' form
                      after the session's Introduction page and before its
                      Roster page (or its first task's Instructions page, if it
                      doesn't have the Roster page enabled).
                  """
    )
    display_name_time = models.PositiveIntegerField(
        default=15,
        help_text=""" Number of seconds to wait on the Display Name form. """
    )
    roster_page = models.BooleanField(
        default=True,
        verbose_name="Show Roster Page",
        help_text=""" If this is True, each Subject will see a 'roster' page
                      after the session's Display Name form (or its
                      Introduction page, if it doesn't have the Display Name
                      form enabled) and before the first task's Instructions
                      page.  If deception is disabled for the session, the
                      roster page will list the real names and flags of the
                      session participants.  If deception is enabled then the
                      version of the roster page shown to a given participant
                      will list the same false names and flags that that
                      participant will later see in the workspace.
                  """
    )
    roster_time = models.PositiveIntegerField(
        default=10,
        help_text=""" Number of seconds to display the Roster page. """
    )

    # MESSAGES
    msg_err_cannot_form_group = models.TextField(
        null=True,
        blank=True,
        verbose_name="'Could not assign to group' error message")

    class Meta:
        abstract = True

    def has_task_of_type(self, task_type):
        if self.status == 'S':
            tasks = [ct.task for ct in self.completedtask_set.all()]
            return any([task.is_of_type(task_type) for task in tasks])
        else:
            if not self.pk:
                return False
            return any([task.is_of_type(task_type)
                          for task_group in ( list(self.task_groups.all())
                                            + ([self.solo_task_group_start] if self.solo_task_group_start else [])
                                            + ([self.solo_task_group_end]   if self.solo_task_group_end   else [])
                                            + ([self.initial_task_group]    if self.initial_task_group    else [])
                                            )
                          for task in task_group.task_set.all()])

    def has_realtimegame_task(self):
        return any([self.has_task_of_type(t) for t in ['C', 'I', 'S']])

    def has_etherpad_lite_task(self):
        return any([self.has_task_of_type(t) for t in ['T', 'G']])

    def task_groups_list(self):
        return ", ".join([x.name for x in self.task_groups.all()])


    # NOTE: This is useful when VALIDATING a Session or SessionTemplate.
    def nym_shortfalls(self, dss=None):
        if type(self) == SessionTemplate:
            reqs = self.nym_reqs_for_session_template(dss)
        else:
            reqs = self.nym_reqs_for_session(dss)
        return [r for r in reqs if not r.region.satisfies_req(r)]

    # NOTE: This is useful when VALIDATING a Session or SessionTemplate.
    def nym_shortfall_reports(self, dss=None):
        report_st = """Session Builder %s, when building a session using
            Session Template %s,"""
        report_sesh = "Session %s"
        base_report = "%s would expect Region %s to have at least %d %s Pseudonym%s"
        unmet_reqs = self.nym_shortfalls(dss)
        return '.  Also: '.join([
            base_report % (
                (report_st % (
                    '<a href="%s">%s</a>' % (
                        reverse(
                            'admin:mci_sessionbuilder_change',
                            args=(req.session_builder.id,)),
                        req.session_builder),
                    '<a href="%s">%s</a>' % (
                        reverse(
                            'admin:mci_sessiontemplate_change',
                            args=(req.session_template.id,)),
                        req.session_template),
                )) if req.session_template else
                (report_sesh % (
                    '<a href="%s">%s</a>' % (
                        reverse(
                            'admin:mci_session_change',
                            args=(req.session.id,)),
                        req.session),
                )),
                '<a href="%s">%s</a>' % (
                    reverse(
                        'admin:mci_region_change',
                        args=(req.region.id,)),
                    req.region),
                req.num,
                "feminine" if req.fem else "masculine",
                "" if req.num == 1 else "s"
            ) for req in unmet_reqs
        ])


    # NOTE: This is useful when VALIDATING a SessionTemplate.
    def unmet_ds_requirement_reports(self, num_dss):
        if not self.pk:
            return []
        stfs = self.freqs_visavis_session_builders.all()
        sbs = [stf.session_builder for stf in stfs]
        unsatisfied_sbs = [sb for sb in sbs
                               if sb.subjects_per_session - 1 > num_dss]
        base_report = """Session Builder %s might use up to %d disguise%s"""
        return '.  Also: '.join([
            base_report % (
                '<a href="%s">%s</a>' % (
                    reverse(
                        'admin:mci_sessionbuilder_change',
                        args=(sb.id,)),
                    sb),
                sb.subjects_per_session - 1,
                "" if sb.subjects_per_session - 1 == 1 else "s"
            )
            for sb in unsatisfied_sbs
        ])

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.subjects_disguised and self.video_enabled:
              raise ValidationError("You may not enable both video and deception.")


class SessionTemplate(SessionBase):
    def __unicode__(self):
        return unicode(self.name)
    objects = ManagerWithPermissions()

    usergroups = models.ManyToManyField('UserGroup', help_text="To see/edit this Session Template, a User must belong to one of these User Groups.")

    # NOTE: This is useful in 2 different scenarios:
    #       1.  When we are VALIDATING a SB.  It assumes that:
    #           - Self is a SessionTemplate, not a Session.
    #           - We are only interested in the DisguiseSelections that are
    #             actually related to this SessionTemplate, not some set of
    #             unsaved DSs instantiated using inline forms that are being
    #             validated.
    #           - We are only interested in the PseudonymReqs imposed through
    #             this ST by the SB 'sb'.
    #           We assume this scenario when 'not dss == True'.
    #       2.  As a utility function for self.nym_reqs_for_session_template.
    def nym_reqs_for_session_template_given_sb(self, sb, dss=None):
        if not dss:
            dss = self.disguise_selections.all()
        dss_slice = dss[:(sb.subjects_per_session - 1)]
        return _reqs_from_disguise_selections(dss_slice, sb=sb, st=self, s=None)

    # NOTE: This is useful in 2 different scenarios:
    #       1.  When we are VALIDATING a ST.  It assumes that:
    #           - Self is a SessionTemplate, not a Session.
    #           - We are interested in the DisguiseSelections 'dss', not those
    #             which are currently related to this SessionTemplate.
    #           - We are interested in ALL of the PseudonymReqs imposed through
    #             this ST by ALL of the SessionBuilders that are actually related
    #             to it.
    #           We assume this scenario when 'not dss == False'.
    #       2.  When we are VALIDATING a Region.  It assumes that:
    #           - Self is a SessionTemplate, not a Session.
    #           - We are only interested in the DisguiseSelections that are
    #             actually related to this SessionTemplate, not some set of
    #             unsaved DSs instantiated using inline forms that are being
    #             validated.
    #           - We are interested in ALL of the PseudonymReqs imposed through
    #             this ST by ALL of the SessionBuilders that are actually related
    #             to it.
    def nym_reqs_for_session_template(self, dss=None):
        stfs = self.freqs_visavis_session_builders.all()
        sbs = [stf.session_builder for stf in stfs]
        req_lists = [self.nym_reqs_for_session_template_given_sb(sb, dss)
                        for sb in sbs]
        return [req for req_list in req_lists for req in req_list]

    # NOTE: This is useful when VALIDATING a SB.
    def unmet_nym_reqs_for_session_template_given_sb(self, sb):
        reqs = self.nym_reqs_for_session_template_given_sb(sb)
        return [r for r in reqs if not r.region.satisfies_req(r)]

    def unmet_nym_req_reports_for_session_template_given_sb(self, sb):
        report = """Session Template '%s' would need Region '%s' to have at
        least %d %s Pseudonym%s"""
        return ".  Also: ".join([
            report % (
                '<a href="%s">%s</a>' % (
                    reverse(
                        'admin:mci_sessiontemplate_change',
                        args=(req.session_template.id,)),
                    req.session_template),
                '<a href="%s">%s</a>' % (
                    reverse(
                        'admin:mci_region_change',
                        args=(req.region.id,)),
                    req.region),
                req.num,
                "feminine" if req.fem else "masculine",
                "" if req.num == 1 else "s")
            for req in self.unmet_nym_reqs_for_session_template_given_sb(sb)
        ])

    def nym_req_reports_by_region(self, sb):
        outer_li = '<li><span class="region">%s: </span>' + \
            '<span class="req-list">%s</span></li>'
        dss = self.disguise_selections.all()
        li_contents = ''.join([
            outer_li % (
                '<a href="%s">%s</a>' % (
                    reverse('admin:mci_region_change', args=(ds.region.id,)),
                    ds.region.name),
                ', '.join([
                    '%d %s (has %d)' % (
                        req.num,
                        'Feminine' if req.fem else 'Masculine',
                        ds.region.pseudonym_set.filter(feminine=req.fem).count(),
                    ) for req in ds.nym_reqs_for_session_builder(sb)
                ])
            ) for ds in dss
        ])
        return '<ul>%s</ul>' % li_contents


class SessionSetup(models.Model):
    session = models.ForeignKey('Session', unique=True)

class Session(SessionBase):
    def __unicode__(self):
        return unicode(self.name)
    objects = ManagerWithPermissions()

    # These fields aren't used by SessionTemplate, since SessionBuilders always
    # set them based on the actual number of subjects being assigned to the
    # Session.
    min_group_size = models.PositiveSmallIntegerField(
        verbose_name="Minimum group size",
        help_text="""
        If a group would be smaller than the minimum size, the group will not run. Even if
        group sizes are set explicitly (for example, using the Group Creation Matrix), each group
        must be larger than the minimum group size. Note that group sizes are based on
        the number of confirmed members of a group, which may be less than the number originally
        requested.
        """)
    max_group_size = models.PositiveSmallIntegerField(verbose_name="Maximum group size")
    # This field isn't used by SessionTemplate because SessionBuilders always
    # set it to 'F'.
    group_creation_method = models.CharField(
        max_length=1,
        choices=(
            ('M', "Create as many groups as possible"),
            ('F', "Create as few groups as possible"),
            ('X', "Create groups based on matrix")),
        default="F")
    group_creation_matrix = models.TextField(
        verbose_name="Group Creation Matrix",
        help_text="""
        Enter a matrix into this text field, one row per line, with values separated by commas.
        The first column in each row represents the number of people in the cohort. Subsequent
        columns represent the groups to be created, with the number in the column indicating the number
        of people in each group. For example, the row "5,2,3" indicates that a cohort of five
        participants should be split into one group of two and one group of three.
        """,
        blank=True,
        null=True)
    # This field isn't used by SessionTemplate because SessionBuilders always
    # set it to the same value.
    waiting_room_time = models.PositiveIntegerField(
        verbose_name="Waiting room time",
        help_text="""How long before the scheduled start time people can
                  register (in minutes)""",
        default=900)
    # These fields don't appear on SessionTemplate because they are specific to
    # each Session instance.
    start_datetime = models.DateTimeField(verbose_name="Start time")
    confirmation_deadline_datetime = models.DateTimeField(verbose_name="Confirmation Deadline", null=True)
    status = models.CharField(
        max_length=1,
        choices=(
            ('P', "Not Started"),
            ('C', "Configuring"),
            ('E', "Error"),
            ('S', "Started")))
    opentok_session_id = models.CharField(
        max_length=200,
        blank=True,
        null=True)
    session_template_frequency = models.ForeignKey(
        'SessionTemplateFrequency',
        blank=True,
        null=True)
    etherpad_group_id = models.CharField( max_length=200
                                        , blank=True
                                        , null=True
                                        )
    etherpad_admin_author_id = models.CharField( max_length=200
                                               , blank=True
                                               , null=True
                                               )
    etherpad_admin_session_id = models.CharField( max_length=200
                                                , blank=True
                                                , null=True
                                                )
    usergroups = models.ManyToManyField('UserGroup', help_text="To see/edit this Session and its Completed Tasks and Subjects, a User must belong to one of these User Groups.")

    class Meta(SessionBase.Meta):
        ordering = ['-start_datetime']

    def __unicode__(self):
      return unicode(self.name)

    def __deepcopy__(self, memo):
      import copy
      result = copy.copy(self)
      result.id = None
      result.name += " copy"
      result.status = 'P'
      result.save()
      result.usergroups = self.usergroups.all()
      result.solo_task_group_start = self.solo_task_group_start
      result.solo_task_group_end = self.solo_task_group_end
      result.initial_task_group = self.initial_task_group
      for obj in self.task_groups.all():
        result.task_groups.add(obj)
      return result

    def subject_count(self):
      return len(self.subject_set.all())

    def _time_to_start(self):
      return self.start_datetime - datetime.today()

    def total_seconds_to_start(self):
      delta = self._time_to_start()
      return delta.days * 3600 * 24 + delta.seconds

    def time_to_waiting_room_opens(self):
      return self._time_to_start() - timedelta(minutes=self.waiting_room_time)

    def too_early(self):
      return self._time_to_start() > timedelta(minutes=self.waiting_room_time)

    def too_late(self):
      return datetime.today() > self.start_datetime

    def ready_to_start(self):
      return self.too_late()

    def start_now(self):
      # When this is 30, other participants (other than the one who sets up a
      # Concentration-containing Session) only see it for about 10 seconds.
      self.start_datetime = datetime.today() + timedelta(seconds = 25)

    def intro_end_time(self):
        return self.start_datetime + timedelta(seconds=self.introduction_time)

    def intro_seconds_remaining(self):
      return _seconds_remaining(datetime.now(), self.intro_end_time())

    def display_name_end_time(self):
        scnds = self.display_name_time if self.display_name_page else 0
        return self.intro_end_time() + timedelta(seconds=scnds)

    def display_name_seconds_remaining(self):
      return _seconds_remaining(datetime.now(), self.display_name_end_time())


    def roster_end_time(self):
        scnds = self.roster_time if self.roster_page else 0
        return self.display_name_end_time() + timedelta(seconds=scnds)

    def roster_seconds_remaining(self):
      return _seconds_remaining(datetime.now(), self.roster_end_time())

    # NOTE: this returns the same number of seconds no matter when you request it
    def done_seconds_remaining(self):
      return self.done_time

    def should_configure(self):
        try:
            SessionSetup.objects.create(session=self)
            return True
        except IntegrityError:
            return False

    def started(self):
        return self.id \
           and (CompletedTask.objects.filter(session__id = self.id)
            or  self.status != 'P')

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.min_group_size > self.max_group_size:
            raise ValidationError("""
                Minimum group size must be less than or equal to maximum group
                size.
            """)
        if self.started():
            raise ValidationError("""
                It appears that this session may already have been run, since
                it has associated Completed Tasks. To avoid changing or
                overwriting past results it cannot be changed.  If you want to
                change this Session, first reset it and then try again.  Note
                that resetting the Session will delete all data associated
                with its Completed Tasks.
            """)
        if self.group_creation_method == 'X':
            if not self.group_creation_matrix:
                raise ValidationError("""
                    The Group Creation Matrix must be filled out in order to
                    create groups based on a matrix""")
            else:
                for row in self.group_creation_matrix.split("\n"):
                    if not row.strip():
                        continue
                    if not self.check_matrix_text(row):
                        raise ValidationError("Invalid input in group matrix row: %s" % row)
                    cols = row.split(",")
                    if len(cols) < 2:
                        raise ValidationError("Invalid row in group creation matrix: %s" % row)
                    if int(cols[0]) < sum([int(x) for x in cols[1:]]):
                        raise ValidationError("Invalid row in group creation matrix: %s. \
                            The sum of people assigned to groups is greater than the cohort size" % row )

        super(Session, self).clean()

    # We need this method to make sure that there have not been
    # any errors inserted into the individual lines. After the
    # strip is called, there should only be numbers and commas,
    # nothing else.
    def check_matrix_text(self, line):

        # We need a regular expression that matches only
        # number,number,number
        # It needs to fail on having extra commas anywhere
        #
        # The regex that does this is:
        # ^([0-9]+,)+[0-9]+$

        regex = r"([0-9]+,)+[0-9]+"
        return re.search(regex, line)


    def nym_reqs_for_session__for_reporting(self):
        outer_li = """
            <li>
                <span class="region"><a href="%s">%s</a>: </span>
                <span class="gender-number">%d %s</span>
            </li>
        """
        reqs = self.nym_reqs_for_session()
        li_contents = ''.join([
            outer_li % (
                reverse('admin:mci_region_change', args=(req.region.id,)),
                req.region.name,
                req.num,
                'Feminine' if req.fem else 'Masculine',
            ) for req in reqs
        ])
        return '<ul>%s</ul>' % li_contents

    def reset(self):
        self.status = "P"
        self.etherpad_group_id = None
        self.etherpad_admin_author_id = None
        self.etherpad_admin_session_id = None
        self.eventlog_set.all().delete()
        self.subject_set.all().update( in_waiting_room=False
                                     , session_group=None
                                     , etherpad_session_id=None
                                     , etherpad_author_id=None
                                     , scribe='U' # "Unconfirmed"
                                     )
        for subject in self.subject_set.all():
            subject.avatars_for.all().delete()
        for setup_lock in self.sessionsetup_set.all():
            setup_lock.delete()
        # Delete each CompletedTask's Redis keys before deleting the CT itself.
        import redis
        rc = redis.Redis(host=MCI_REDIS_SERVER, port=MCI_REDIS_PORT)
        for ct in self.completedtask_set.all():


            # TODO: make sure to reset all the new, Tiles-oriented keys as well.

            _log.debug("Deleting redis hash %s" % ct.keyname_vars())
            rc.delete(ct.keyname_vars())
            _log.debug("Deleting redis key %s" % ct.keyname_points_global())
            rc.delete(ct.keyname_points_global())
            _log.debug("Deleting redis hash %s" % ct.hashname_users())
            rc.delete(ct.hashname_users())
            for hn in ct.hashnames_cards_rounds():
                _log.debug("Deleting redis hash %s" % hn)
                rc.delete(hn)
            ct.delete()
        self.start_datetime = datetime.now() + timedelta(seconds=30)
        self.save()

    # NOTE: This is useful in 2 different scenarios:
    #       1.  When we are CONFIGURING a Session, i.e. the intended
    #           client is self.disguises.  It assumes that:
    #           - Self is a Session, not a SessionTemplate.
    #           - We know ('disguises_needed') how many Subjects are present.
    #           - We are only interested in the DisguiseSelections that are
    #             actually related to this Session, not some set of unsaved DSs
    #             instantiated using inline forms that are being validated.
    #           We assume this scenario when 'not dss == True'.
    #       2.  As a utility function for self.nym_reqs_for_session.
    def nym_reqs_for_session_given_disguise_count(self, disguise_count, dss=None):
        if not dss:
            dss = self.disguise_selections.all().order_by('position')
        dss_slice = dss[:disguise_count]
        return _reqs_from_disguise_selections(dss_slice, sb=None, st=None, s=self)

    # NOTE: This is useful in 2 different scenarios:
    #       1.  When we are VALIDATING a Session.  It assumes that:
    #           - Self is a Session, not a SessionTemplate.
    #           - We are interested in the DisguiseSelections 'dss', not those
    #             which are currently related to this Session.
    #           - We are going to derive our 'disguise count' from
    #             self.max_group_size.
    #           We assume this scenario when 'not dss == False'.
    #       2.  When we are VALIDATING a Region.  It assumes that:
    #           - Self is a Session, not a SessionTemplate.
    #           - We are only interested in the DisguiseSelections that are
    #             actually related to this Session, not some set of
    #             unsaved DSs instantiated using inline forms that are being
    #             validated.
    #           - We are going to derive our 'disguise count' from
    #             self.max_group_size.
    def nym_reqs_for_session(self, dss=None):
        ct = self.max_group_size - 1
        return self.nym_reqs_for_session_given_disguise_count(ct, dss)

    # NOTE: This is useful when CONFIGURING a Session.
    def disguises(self, disguise_count):
        reqs = self.nym_reqs_for_session_given_disguise_count(disguise_count)
        disguise_lists = [r.region.random_disguises(r) for r in reqs]
        disguises = [disguise for disguise_list in disguise_lists
                              for disguise in disguise_list]
        return disguises

    def group_cts(self):
        return self.completedtask_set.filter(solo_subject__isnull=True)

    def per_subject_metrics(self, t, session_group):
        if t == 'C':
            return [ ('clicks'                        , 'Card Clicks')
                   , ('score'                         , 'Score')
                   ]
        elif t == 'I':
            return [ ('clicks'                        , 'Tile Clicks')
                   , ('netScore'                      , 'Net Score')
                   , ('uniqueTilesCorrectlyClicked'   , 'Unique Tiles Correctly Clicked')
                   , ('uniqueTilesIncorrectlyClicked' , 'Unique Tiles Incorrectly Clicked')
                   , ('correctCorrections'            , 'Correct Corrections of Others')
                   , ('incorrectCorrections'          , 'Incorrect Corrections of Others')
                   , ('timesCorrectlyCorrected'       , 'Correct Corrections by Others')
                   , ('timesIncorrectlyCorrected'     , 'Incorrect Corrections by Others')
                   , ('correctSubmitClicks'           , 'Correct Submit Clicks')
                   , ('incorrectSubmitClicks'         , 'Incorrect Submit Clicks')
                   ]
        elif t == 'S':
            return [ ('moves'                         , 'Moves')
                   , ('partialMatches'                , 'Partial')
                   , ('completeMatches'               , 'Complete')
                   , { 'category': 'interactions'
                     , 'names': [str(sub.pk) for sub in self.subjects_in_group(session_group)]
                     }
                   ]

    def assign_etherpad_lite_group_id(self, pad_client):
        group_id_resp_dict = pad_client.createGroupIfNotExistsFor(self.pk)
        self.etherpad_group_id = group_id_resp_dict['groupID']
        self.save()

    def assign_admin_el_identity(self, pad_client):
        adminAuthorMapper = "sessionAdmin%s" % str(self.pk)
        author_id_resp_dict = pad_client.createAuthorIfNotExistsFor(adminAuthorMapper, "Session Admin")
        self.etherpad_admin_author_id = author_id_resp_dict['authorID']
        valid_until = int(time.time()) + (1000 * 365 * 24 * 60 * 60)
        session_id_resp_dict = pad_client.createSession( self.etherpad_group_id
                                                       , self.etherpad_admin_author_id
                                                       , valid_until
                                                       )
        self.etherpad_admin_session_id = session_id_resp_dict['sessionID']
        self.save()

    def get_pad_client(self):
        return EtherpadLiteClient(MCI_ETHERPAD_API_KEY,MCI_ETHERPAD_API_URL)

    def configure_etherpad_lite_user_mgmt(self):
        pad_client = self.get_pad_client()
        self.assign_etherpad_lite_group_id(pad_client)
        self.assign_admin_el_identity(pad_client)

    def retrieve_scribeless_group_ids(self):
        # This method will return a list of group ids
        # where nobody in the group is a scribe, AND everyone is an 'X'
        # This method will be used to determine if other groups should wait
        # for others to find scribes
        _log.debug("Getting scribeless groups ids")

        scribeless_groups = list()

        all_session_groups = self.session_groups()
        _log.debug("There are %d groups." % len(all_session_groups))

        # We need to go through each group,
        for candidate_group in all_session_groups:
            # Let us get the subjects who are not zero
            all_group_subjects = self.subject_set.filter(session_group=candidate_group).exclude(scribe='X')

            # If this is none, then this is a bad group
            if not all_group_subjects:
                _log.debug("Group with all X-es.")
                scribeless_groups.append(candidate_group)
            else:
                _log.debug("There are %d subjects." % len(all_group_subjects))
                _log.debug("Group was OK.")

        return scribeless_groups

    def select_scribes(self):
        from django.core.exceptions import ObjectDoesNotExist
        from random import choice
        for session_group in self.session_groups():
            # Check to see if there is an existing scribe, and select a new one if not
            _log.debug("Selecting scribe for group %d" % (session_group))
            log_data = self.subject_set.filter(session_group=session_group)
            if log_data:
                for d in log_data:
                    _log.error("User %s in group %d and session %s with scribe_status %s going into the scribe selection process" % (d.external_id, session_group, self.id, d.scribe))
            try:
                existing_scribe = self.subject_set.get(session_group=session_group, scribe='S')
                _log.debug("User (%s) already set as scribe for group %d in session %s" % (existing_scribe.external_id, session_group, self.id))
            except ObjectDoesNotExist:
                subs = self.subject_set.filter(session_group=session_group).exclude(scribe='X')
                if subs:
                    # Use the random.choice method to get a random person in the group
                    # and set them as a requested scribe
                    scribe = choice(subs)
                    scribe.scribe = 'R' # Requested that this person be the scribe
                    _log.debug("Selecting user %s as scribe for group %d in session %s" % (scribe.external_id, session_group, self.id))
                    scribe.save()
                else:
                    # log_data = self.subject_set.filter(session_group=session_group)
                    # if log_data:
                    #     for d in log_data:
                    #         _log.error("User %d in group %d and session %s with scribe_status %s not selected as scribe" % (d.external_id, session_group, self.id, d.scribe))

                    # So we cannot find someone to be a scribe here. It would be great to mark this
                    # somewhere, but we will have to leave this task to the method retrieve_scribeless_group_ids()
                    _log.error("Could not select scribe for group %d in session %s" % (session_group, self.id))

    def matrix_group_sizes(self, participant_count):
        for row in self.group_creation_matrix.split("\n"):
            if not row.strip():
                continue
            cols = row.split(",")
            if int(cols[0]) == participant_count:
                return [int(x) for x in cols[1:]]
        return None # If no match found

    def session_groups(self):
        # This is where we return a list of session groups
        # Note that a session group is not an object, but merely
        # an identifier for each subject

        # Get all the subjects
        group_subs = self.subject_set.filter( ~Q(session_group=0)
                                            , session_group__isnull=False
                                            )

        # Return a list of unique group ids
        return list(set([sub.session_group for sub in group_subs]))

    def completed_tasks_for_session_group(self, session_group):
        return self.completedtask_set.filter(session_group=session_group)

    def subjects_in_group(self, session_group):
        return self.subject_set.filter(session_group=session_group)

    def log_summary_for_task_type(self, task_type, session_group):
        def reduceTaskMetrics(metrics):
            metrics = [m[0] if type(m) != dict else m for m in metrics]
            def add_task_summaries(sessionSummary, taskSummary):
                for seid in taskSummary:
                    # Initialize sessionSummary's key for this seid.
                    if seid not in sessionSummary:
                        sessionSummary[seid] = {}

                    for m in metrics:
                        if type(m) == dict:
                            # Ignore this metric/Subject pair if the 'Subject' doesn't
                            # have this category of metrics.
                            if m['category'] in taskSummary[seid]:

                                # Initialize sessionSummary[seid]'s key for this
                                # category of metrics.
                                if m['category'] not in sessionSummary[seid]:
                                    sessionSummary[seid][m['category']] = {}

                                for submetric in m['names']:

                                    if submetric in taskSummary[seid][m['category']]:

                                        # Initialize key for this submetric.
                                        if submetric not in sessionSummary[seid][m['category']]:
                                            sessionSummary[seid][m['category']][submetric] = 0

                                        sessionSummary[seid][m['category']][submetric] += float(taskSummary[seid][m['category']][submetric])
                        else:
                            # Ignore this metric/Subject pair if the 'Subject' doesn't
                            # have this metric -- e.g. if the 'Subject' is 'Totals'.
                            if m in taskSummary[seid]:
                                # Initialize sessionSummary[seid]'s key for this metric.
                                if m not in sessionSummary[seid]:
                                    sessionSummary[seid][m] = 0

                                sessionSummary[seid][m] += float(taskSummary[seid][m])

                return sessionSummary
            return add_task_summaries
        summaries = [ct.summary() for ct in self.completed_tasks_for_session_group(session_group)
                                   if ct.task.task_type == task_type
                    ]
        return reduce( reduceTaskMetrics(self.per_subject_metrics(task_type, session_group))
                     , summaries
                     , {}
                     )
    def log_summary_with_totals_for_task_type(self, task_type, session_group):
        summ = self.log_summary_for_task_type(task_type, session_group)
        subs = self.subjects_in_group(session_group)
        return listWithTotalsLast(summ, task_type, subs)

    def set_up_completed_tasks(self):
        _log.debug("Setting up completed tasks for session %s" % (self.id))
        task_groups = list(self.task_groups.all())
        shuffle(task_groups)

        if self.initial_task_group:
            task_groups = [i for i in task_groups
                              if i.id != self.initial_task_group.id]
            task_groups.insert(0,self.initial_task_group)
        for session_group in self.session_groups():
            index = 0
            roster_seconds = self.roster_time if self.roster_page else 0
            time_mark = self.start_datetime + \
                        timedelta(seconds=self.introduction_time) + \
                        timedelta(seconds=roster_seconds)
            def create_and_configure(index, task, time_mark, finish_time, solo_sub=None):
                ct = CompletedTask.objects.create( task                 = task
                                                 , session              = self
                                                 , session_group        = session_group
                                                 , completed_task_order = index
                                                 , expected_start_time  = time_mark
                                                 , expected_finish_time = finish_time
                                                   # The critical variable
                                                 , solo_subject         = solo_sub
                                                 )
                ct.configure()
            if self.solo_task_group_start:
                for task in list(self.solo_task_group_start.task_set.all()):
                    finish_time = time_mark + timedelta(seconds = task.total_duration())
                    for solo_sub in self.subjects_in_group(session_group):
                        create_and_configure(index, task, time_mark, finish_time, solo_sub)
                    index += 1
                    time_mark = finish_time

            for task_group in task_groups:
                for task in list(task_group.task_set.all()):
                    finish_time = time_mark + timedelta(seconds = task.total_duration())
                    create_and_configure(index, task, time_mark, finish_time)
                    index += 1
                    time_mark = finish_time

            if self.solo_task_group_end:
                for task in list(self.solo_task_group_end.task_set.all()):
                    finish_time = time_mark + timedelta(seconds = task.total_duration())
                    for solo_sub in self.subjects_in_group(session_group):
                        create_and_configure(index, task, time_mark, finish_time, solo_sub)
                    index += 1
                    time_mark = finish_time

    def build_session_log(self, session_group, full_session=True, cache_subjects=True):
        log = []
        EtherpadLiteRecord.objects.clear_querysets()
        group_cts = self.completed_tasks_for_session_group(session_group)
        for ct in group_cts.filter(solo_subject__isnull = True):
            log.extend(ct.build_log(full_session=full_session, cache_subjects=cache_subjects))
        log.extend(list(EventLog.objects.select_related( 'subject'
                                                       , 'completed_task'
                                                       , 'completed_task__task'
                                                       ).filter( ( Q(subject__session_group=session_group)
                                                                 | Q(subject__session_group__isnull=True)
                                                                 )
                                                               , session                = self
                                                               , completed_task__isnull = True
                                                               )))
        log = filter(None, log)
        log.sort(cmp=event_cmp)
        return log

# Make sure both Sessions and SessionBuilders have an OpenTok session set up for it.
def opentok_session_setup(sender, instance, *args, **kwargs):
    if not instance.opentok_session_id:
        opentok = OpenTokSDK.OpenTokSDK(MCI_OPENTOK_API_KEY, MCI_OPENTOK_API_SECRET)
        session_properties = { OpenTokSDK.SessionProperties.p2p_preference: "disabled" }
        opentok_session = opentok.create_session(None, session_properties)
        instance.opentok_session_id = opentok_session.session_id
        _log.debug("%s %s's OpenTok Session ID: %s" %
                    (instance.__class__.__name__, instance.id,
                    opentok_session.session_id))
#pre_save.connect(opentok_session_setup, sender=Session)

class SessionTemplateFrequency(models.Model):
    def __unicode__(self):
        return unicode("Frequency using %s" % unicode(self.session_template.name))
    session_template = models.ForeignKey(
        'SessionTemplate',
        related_name='freqs_visavis_session_builders')
    session_builder = models.ForeignKey(
        'SessionBuilder',
        related_name='session_template_freqs')
    frequency = models.FloatField(default=1.0)

class SessionBuilderSurvey(models.Model):
    sessionbuilder = models.ForeignKey('SessionBuilder', unique=True)

class SessionBuilder(models.Model):
    def __unicode__(self):
        return unicode(self.name)
    objects = ManagerWithPermissions()

    name = models.CharField(max_length=200)
    mturk = models.BooleanField(
        default=False,
        verbose_name = "Allow Non-Email ID",
    )
    custom_id_label = models.CharField(
        max_length=200,
        default="Username (e.g. Mturk ID)",
        verbose_name="Non-Email ID Field Label",
    )
    waiting_room_opens = models.DateTimeField()
    waiting_room_closes = models.DateTimeField()
    session_templates = models.ManyToManyField(
        'SessionTemplate',
        through='SessionTemplateFrequency')
    last_survey_time = models.DateTimeField(null=True,blank=True)

    # Session formation rules
    previous_play_required = models.BooleanField(
        default=False,
        help_text=""" If this is checked, this SessionBuilder will only form
                      Sessions with Subjects who HAVE been in a Session
                      together before. (Not compatible with 'Previous
                      Play Forbidden', obviously.)""")
    previous_play_forbidden = models.BooleanField(
        default=False,
        help_text=""" If this is checked, this SessionBuilder will only form
                      Sessions with Subjects who have NOT been in a Session
                      together before. (Not compatible with 'Previous
                      Play Required', obviously.)""")
    subjects_per_session = models.PositiveSmallIntegerField()
    javascript_test_explanation = models.TextField(
        default="""We are testing Javascript in your browser.  If this message
        does not go away, Javascript is disabled or broken in your browser.
        You must have Javascript working in order to continue.""",
    )
    error_connecting_to_game_server_msg = models.TextField(
        default="""Your browser is Javascript-enabled but for some reason
        cannot connect to our real-time game server.  We have logged this and
        will do our best to improve compatibility in the future.""",
        verbose_name="'Error Connecting to Game Server' Message",
    )
    usergroups = models.ManyToManyField('UserGroup', help_text="To see/edit this Session Builder, a User must belong to one of these User Groups.")
    ask_for_group_id = models.BooleanField(
        default=False,
        verbose_name="Ask for Group ID",
        help_text="""Show arriving Subjects a 'Group ID' field so they can indicate membership in predetermined groups.""")

    def __deepcopy__(self, memo):
      import copy
      result = copy.copy(self)
      result.id = None
      result.name += " copy"
      result.save()
      for stf in self.session_template_freqs.all():
          # TODO: use 'deepcopy' on the STF model
          new_stf = SessionTemplateFrequency(
              session_template=stf.session_template,
              session_builder=stf.session_builder,
              frequency=stf.frequency)
          result.session_template_freqs.add(new_stf)
      for srq in self.sessionregionquota_set.all():
          # TODO: use 'deepcopy' on the SRQ model
          new_srq = SessionRegionQuota(
              sessionbuilder=srq.sessionbuilder,
              region=srq.region,
              subjects=srq.subjects)
          result.sessionregionquota_set.add(new_srq)
      return result

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.previous_play_required and self.previous_play_forbidden:
            msg = """ You cannot both require and forbid that Subjects
                      have been in a Session together before. """
            raise ValidationError(msg)

    def unmet_ds_requirement_report_for_st(self, st):
        if st.subjects_disguised:
            ct = st.disguise_selections.count()
            if self.subjects_per_session - 1 > ct:
                base_report = """For Session Template %s you have only specified
                    %d disguise%s"""
                return base_report % (
                    '<a href="%s">%s</a>' % (
                        reverse(
                            'admin:mci_sessiontemplate_change',
                            args=(st.id,)),
                        st),
                    ct,
                    "" if ct == 1 else "s"
                )
        return ""

    # TODO: check that this function documentation is accurate.
    # Return True in any of the following cases:
    #   - There is not currently a lock row indicating that there is a survey in
    #     progress, AND either:
    #       - More than 10 seconds have passed since the last survey timestamp.
    #       - Parameter 'force' == True.
    #   - More than 30 seconds have passed since the last survey timestamp.
    def should_survey(self, force):
        try:
            t = self.last_survey_time
            if force or (not t) or t <= datetime.now()-timedelta(seconds=10):
                SessionBuilderSurvey.objects.create(sessionbuilder=self)
                return True
        except IntegrityError:
            if t <= datetime.now() - timedelta(seconds=30):
                return True
            pass
        return False

    def survey(self):
        self.last_survey_time = datetime.now()
        self.save()
        _log.info("SessionBuilder.survey >> entering.  SessionBuilder: %s (%s)" % (self, self.pk))
        survey_tag = uuid.uuid4()
        # In order of arrival, take subjects and assign them to groups that are
        # as close as possible to complete.  These groups are only real if they
        # are in fact complete.  Otherwise their only purpose is to provide the
        # 'waiting for' value for an individual subject.
        # NOTE: Apart from sorting by arrival time, there is no optimization
        # here.  True optimization would involve the selection of the best of
        # all partitions of the set of waiting subjects in terms of the sum of
        # their parts' distances from completeness.  That's a factorially
        # complex algorithm -- not gonna happen.
        def _survey():
            ago = datetime.now() - timedelta(seconds=15)
            # TODO: move to an algorithm where we don't repeat
            #       the database query on every recursion, but rather
            #       just remove items from our starting list.
            statuses_qs = self.subject_identity_statuses.filter(
                ~Q(survey_tag=survey_tag),
                arrival_time__isnull=False,
                dispatch_time__isnull=True,
                rejected=False,
                last_waiting_room_checkin__gte=ago)
            statuses = sorted(statuses_qs, key=lambda s: s.arrival_time)
            if len(statuses) == 0:
                return
            for status in statuses:
                for k in range(self.subjects_per_session):
                    subsets = [list(xs) for xs in combinations(
                        statuses,
                        self.subjects_per_session - k)]
                    relevant_subsets = sorted([s for s in subsets if status in s])
                    for subset in relevant_subsets:
                        if self.valid_status_set(subset, k):
                            # NOTE: We always hit this, because a subset
                            #       of size 1 always validates.  There's only
                            #       one corner case: it's
                            #       when the status 'on behalf of which' we're
                            #       doing the current scan is the status of an
                            #       SI whose country isn't in one of the quota'd
                            #       Regions, and the quotas cover all the
                            #       spots in the session.  In that case we fall
                            #       through / fall out of this loop.
                            should_set_waiting_for = True
                            if k == 0:
                                # If build_session raises _any_ exception, it
                                # should have been completely rolled back.  Thus
                                # if we need to reject any Statuses, it needs
                                # to be done here.
                                # We use .update() for updates that take place
                                # after build_session so as to avoid stomping on
                                # any model object changes made during that call.
                                # This really isn't necessary within the exception
                                # cases, since the call's changes will have been
                                # rolled back... but it feels cleaner.  It IS
                                # necessary in the lines following the try-except
                                # block.
                                try:
                                    self.build_session(subset)
                                except self.SubjectNotCreatedError as e:
                                    SI_SB_Status.objects.filter(pk=e.bad_status.pk).update(
                                        rejected=True,
                                        rejection_reason="Failed Subject Creation")
                                    should_set_waiting_for = False
                                except self.StatusSubjectNotAssignedError as e:
                                    SI_SB_Status.objects.filter(pk=e.bad_status.pk).update(
                                        rejected=True,
                                        rejection_reason="Failed Subject Connection")
                                    should_set_waiting_for = False
                            if should_set_waiting_for:
                                pks = [st.pk for st in subset]
                                SI_SB_Status.objects.filter(pk__in=pks).update(
                                    survey_tag=survey_tag,
                                    waiting_for=k)
                            return _survey()
                # This only happens when we've fallen through; see note above.
                _log.info(("Status %s is not a member of any possible valid "
                    "status set.  Rejecting.") % status)
                status.rejected = True
                status.rejection_reason = "Excluded by quotas"
                status.save()
        try:
            _survey()
        except:
            _log.info( "SessionBuilder.survey >> Exception raised."
                       "\n\tSessionBuilder: %s (%s)"
                       "\n\tTraceback:\n%s"
                       % (self, self.pk, traceback.format_exc())
                     )
            SessionBuilderSurvey.objects.filter(sessionbuilder=self).delete()
            raise
        SessionBuilderSurvey.objects.filter(sessionbuilder=self).delete()
        _log.info("SessionBuilder.survey >> exiting.  SessionBuilder: %s (%s)" % (self, self.pk))

    def valid_status_set(self, statuses, k):
        triples = [( stat.subject_identity.pk, stat.subject_identity.mturk_id, stat.sb_group_id) for stat in statuses]
        _log.debug("Statuses being checked for validity as a set: \n%s" % pformat(triples, indent=8))
        # Group IDs the same
        idents = [status.subject_identity for status in statuses]
        if not len(set([stat.sb_group_id for stat in statuses])) == 1:
            return False
        # Previous play forbidden
        if self.previous_play_forbidden:
            previous_sessions = [
                stat.subject.session
                for ident in idents
                for stat in ident.sessionbuilder_statuses.all()
                 if stat.subject
            ]
            if len(previous_sessions) != len(set(previous_sessions)):
                return False
        # Previous play required
        def _dispatched_to_same_session(status_a, status_b):
            _log.debug("Seeing whether %s and %s dispatched to the same Session"
                % (status_a, status_b))
            if not status_a.subject or not status_b.subject:
                return False
            return status_a.subject.session == status_b.subject.session
        def _status_session_is_among_identity_sessions(status_a, identity_b):
            bs = [_dispatched_to_same_session(status_a, status_b)
                    for status_b in identity_b.sessionbuilder_statuses.all()]
            _log.debug("Is %s's Session among %s's Subject Sessions? %s" %
                (status_a, identity_b, bs))
            return any(bs)
        if self.previous_play_required:
            if len(idents) > 1:
                # For at least one of Identity A's Statuses...
                if not any([
                    # ... it should be true for *every* Identity B...
                    all([
                        # ... that the Status's Subject's Session is among
                        # Identity B's Status Subject Sessions.
                        _status_session_is_among_identity_sessions(status_a, identity_b)
                            for identity_b in idents
                    ])
                    for status_a in idents[0].sessionbuilder_statuses.all()
                ]):
                    return False
        # Regional quotas
        #     We check whether all the quotas in *any* k-length combo of the
        #     quota set are met.  For these purposes we consider 'the quota
        #     set' to be a set of single-Subject requirements; i.e. a quota
        #     of 2 for Jordan would be represented as 2 quotas for Jordan,
        #     either of which we could exclude from a k-sized combo while
        #     including the other.
        quotas_flattened = [q.region for q in self.sessionregionquota_set.all()
                            for _ in range(q.subjects)]
        combo_length = max(0, len(quotas_flattened) - k)
        combos = [list(xs) for xs in combinations(quotas_flattened, combo_length)]
        if not any([all([len([si for si in idents if si.country in r.countries.all()]) >= q
                         for (r, q) in reduce(counter, combo, {}).items()])
                    for combo in combos]):
            return False
        return True

    class StatusSubjectNotAssignedError(Exception):
        def __init__(self, status):
            self.bad_status = status
    class SubjectNotCreatedError(Exception):
        def __init__(self, status):
            self.bad_status = status

    def next_session_template_frequency(self):
        # \ the Sessions that we have built so far. \
        sessions = Session.objects.filter(
            session_template_frequency__session_builder=self)
        # \ the SessionTemplateFrequencies that are linked to by the
        #   Sessions we've actually built so far. \
        sesh_stf_pks = [s.session_template_frequency.pk for s in sessions]
        # \ the full list of SessionTemplateFrequencies that we're supposed to
        #   maintain. \
        stfs = self.session_template_freqs.all()
        # \ a dictionary.  keys are the pks of the SessionTemplateFrequencies
        #   we're supposed to maintain.  for each key, value is the % of the
        #   Sessions we build that are supposed to use that STF. \
        desired_stf_freqs = dict([(stf.pk, stf.frequency) for stf in stfs])
        # \ a dictionary.  keys are, again, the pks of the STFs we're supposed
        #   to maintain.  for each key, value is the number of Sessions
        #   we've built so far that have used that STF. \
        current_stf_counts = reduce(
            counter,
            sesh_stf_pks,
            dict([(stf.pk, 0) for stf in stfs]))
        stf_count = len(sesh_stf_pks)
        # \ a dictionary.  keys are, again, the pks of the STFs we're supposed
        #   to maintain.  for each key, value is what % of the Sessions
        #   we've built so far have used that STF.
        current_stf_freqs = dict([
            (pk, (float(ct)/stf_count) if stf_count else 0.0)
            for pk, ct in current_stf_counts.items()])
        # \ a dictionary.  keys are, again, the pks of the STFs we're supposed
        #   to maintain.  for each key, value is the distance between the
        #   current % and the desired %. \
        stf_freq_shortfalls = dict([
            (pk, desired_stf_freqs[pk] - current_stf_freqs[pk])
            for pk in current_stf_freqs])
        # \ the SessionTemplateFrequency whose distance is greatest, according
        # to stf_freq_shortfalls. \
        return SessionTemplateFrequency.objects.get(
            pk=max(stf_freq_shortfalls, key=stf_freq_shortfalls.get))


    @transaction.atomic
    def build_session(self, statuses):
        stf = self.next_session_template_frequency()
        st = stf.session_template
        subject_identities = [stat.subject_identity for stat in statuses]
        _log.debug( "SessionBuilder.build_session >> SB '%s' building a Session"
                    "\n\tSubject Identities:\n%s"
                    "\n\tSessionTemplateFrequency: %s"
                    "\n\tSessionTemplate:          %s"
                    "\n\tST DisguiseSelections:\n%s"
                    % ( self
                      , pformat(subject_identities, indent=8)
                      , stf
                      , st
                      , pformat(st.disguise_selections.all(), indent=8)
                      )
                  )
        # Create the new Session.  All the fields on SessionTemplate
        # 'st' (which we just identified) get copied to the Session.
        session_ct = Session.objects.filter(
            session_template_frequency__session_builder=self).count()
        sesh = Session.objects.create(
            name=self.name + " -- Session " + str(session_ct + 1),
            load_test=st.load_test,
            start_datetime=datetime.now() + timedelta(seconds=40),
            min_group_size=2,
            max_group_size=self.subjects_per_session,
            group_creation_method='F',
            status='P',
            waiting_room_time=600,
            subjects_disguised=st.subjects_disguised,
            video_enabled=st.video_enabled,
            session_template_frequency=stf,
            solo_task_group_start=st.solo_task_group_start,
            solo_task_group_end=st.solo_task_group_end,
            initial_task_group=st.initial_task_group,
            introduction_text=st.introduction_text,
            introduction_time=st.introduction_time,
            display_name_page=st.display_name_page,
            display_name_time=st.display_name_time,
            roster_time=st.roster_time,
            roster_page=st.roster_page,
            done_text=st.done_text,
            done_time=st.done_time,
            done_redirect_url=st.done_redirect_url,
            msg_err_cannot_form_group=st.msg_err_cannot_form_group,
        )
        sesh.usergroups = self.usergroups.all()

        _log.debug("Created a Session: %s." % sesh)
        for ds in st.disguise_selections.all():
            DisguiseSelection.objects.create(
                # I include the following line just for clarity
                session_template=None,
                session=sesh,
                region=ds.region,
                feminine=ds.feminine,
                position=ds.position,
            )
            _log.debug("Added a DS to this new Session.  Its DSs: %s" %
                sesh.disguise_selections.all())
        for tg in st.task_groups.all():
            sesh.task_groups.add(tg)
        for status in statuses:
            si = status.subject_identity
            # Make sure external_id will be globally unique.
            # TODO: Beef this up.  Right now we can only increment up to 10!  It
            #       is surely a corner case, but we should be able to handle
            #       any number of clashing external_id values.
            sb_tag = "(SB " + str(self.id) + ")"
            ext_id_basis = si.mturk_id if self.mturk else si.email
            sub_field_max_len = Subject._meta.get_field('external_id').max_length
            max_len = sub_field_max_len - len(sb_tag) - 1 # the final `1` is for the digit we may add as a way to disambiguate
            external_id = ext_id_basis[:max_len] + sb_tag
            if Subject.objects.filter(external_id=external_id).count():
                greatest = Subject.objects.filter(
                    external_id__contains=external_id).order_by(
                        '-external_id')[0].external_id
                last_char = greatest[-1]
                if last_char.isdigit():
                    external_id = greatest[:-1] + str(int(last_char) + 1)
                else:
                    external_id = greatest + str(int(1))
            # Make sure display_name will be unique within this Session.
            display_name = si.display_name
            if sesh.subject_set.filter(display_name=si.display_name).count():
                greatest = sesh.subject_set.filter(
                    display_name__contains=si.display_name).order_by(
                        '-display_name')[0].display_name
                last_char = greatest[-1]
                if last_char.isdigit():
                    display_name = greatest[:-1] + str(int(last_char) + 1)
                else:
                    display_name = greatest + str(int(1))
            # Create the Subject
            try:
                sub = Subject.objects.create(
                    session=sesh,
                    external_id=external_id,
                    display_name=display_name,
                    country=si.country,
                    consent_and_individual_tests_completed=True,
                    in_waiting_room=False)
            except IntegrityError:
                _log.error(("IntegrityError while creating Subject (Status %s).  Traceback:\n%s") % (status, traceback.format_exc()))
                raise self.SubjectNotCreatedError(status)
            # Update the Status
            SI_SB_Status.objects.filter(pk=status.id).update(
                dispatch_time=datetime.now(),
                subject=sub)
            _status = SI_SB_Status.objects.get(pk=status.id)
            _log.debug( "SessionBuilder.build_session >> Linked SI_SB_Status to Subject!"
                        "\n\tSI_SB_Status:  %s"
                        "\n\tSubject:       %s"
                        "\n\tDispatch time: %s"
                        "\n\tRejected:      %s"
                        % (_status, _status.subject, _status.dispatch_time, _status.rejected)
                      )
        for status in statuses:
            _st = SI_SB_Status.objects.get(pk=status.id)
            if not _st.subject:
                _log.error( "SessionBuilder.build_session >> Attempt to build Session resulted in StatusSubjectNotAssignedError."
                            "\n\t`SI_SB_Status`es:  %s"
                            "\n\tBad SI_SB_Status: %s"
                            % (pformat(statuses, indent=8), _st)
                          )
                raise self.StatusSubjectNotAssignedError(_st)

class SessionRegionQuota(models.Model):
    sessionbuilder = models.ForeignKey('SessionBuilder')
    region = models.ForeignKey('Region')
    subjects = models.PositiveSmallIntegerField(
        verbose_name="# Subjects who must come from this Region")

class SI_SB_Status(models.Model):

    def __unicode__(self):
        return unicode(self.subject_identity)

    sessionbuilder = models.ForeignKey(
        'SessionBuilder',
        related_name='subject_identity_statuses')
    subject_identity = models.ForeignKey(
        'SubjectIdentity',
        related_name='sessionbuilder_statuses')
    arrival_time = models.DateTimeField(null=True, blank=True)
    dispatch_time = models.DateTimeField(null=True, blank=True)
    subject = models.ForeignKey('Subject', null=True, blank=True, unique=True)
    sb_group_id = models.CharField(max_length=32, blank=True, null=True)
    survey_tag = models.CharField(
        max_length=256,
        blank=True,
        null=True)
    waiting_for = models.IntegerField(
        default=-1)
    last_waiting_room_checkin = models.DateTimeField(
        default=lambda: datetime.now())
    rejected = models.BooleanField(default=False)
    rejection_reason = models.CharField(
        max_length=256,
        null=True, blank=True)

    def __cmp__(self, other):
        return cmp(self.arrival_time, other.arrival_time)

    def get_waiting_for(self):
        if self.waiting_for == -1:
            return self.sessionbuilder.subjects_per_session - 1
        return self.waiting_for
    get_waiting_for.verbose_name = "Waiting for"

class SubjectIdentityQuerySet(QuerySetWithPermissions):
    def owned_by_virtue_of_ug_membership(self, user, ugs):
        shares_any_usergroup_with_session = reduce(or_, [Q(sessionbuilders__usergroups=ug) for ug in ugs])
        return shares_any_usergroup_with_session

class SubjectIdentityManager(ManagerWithPermissions):
    def get_queryset(self):
        return SubjectIdentityQuerySet(self.model, using=self._db)

class SubjectIdentity(models.Model):
    def __unicode__(self):
        return unicode(self.email if self.email else self.mturk_id)
    objects = SubjectIdentityManager()

    sessionbuilders = models.ManyToManyField(
        'SessionBuilder',
        through='SI_SB_Status',
        related_name='subject_identities')
    email = models.EmailField(unique=True, blank=True, null=True)
    mturk_id = models.CharField(
        unique=True,
        max_length=200,
        blank=True,
        null=True)
    display_name = models.CharField(max_length=12, blank=True, null=True)
    country = models.ForeignKey('SubjectCountry', blank=True, null=True)
    opentok_token = models.CharField(max_length=512, blank=True, null=True)

    class Meta:
        verbose_name_plural = "Subject Identities"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.pk:
            sbs_are_mturk = [sb.mturk for sb in self.sessionbuilders.all()]
            if any(sbs_are_mturk) and not self.mturk_id:
                    msg = """ Since this Subject Identity is associated with an
                              MTurk Session Builder, it must have an MTurk ID. """
                    raise ValidationError(msg)
            if not all(sbs_are_mturk) and not self.email:
                    msg = """ Since this Subject Identity is associated with a
                              non-MTurk Session Builder, it must have a valid
                              email address. """
                    raise ValidationError(msg)

class TaskGroup(models.Model):
    def __unicode__(self):
        return unicode(self.name)
    objects = ManagerWithPermissions()

    name = models.CharField(max_length=64)
    usergroups = models.ManyToManyField('UserGroup', help_text="To see/edit this Task Group and its associated Tasks, a User must belong to one of these User Groups.")

class TaskQuerySet(QuerySetWithPermissions):
    def owned_by_virtue_of_ug_membership(self, user, ugs):
        shares_any_usergroup_with_taskgroup = reduce(or_, [Q(task_group__usergroups=ug) for ug in ugs])
        return shares_any_usergroup_with_taskgroup

class TaskManager(ManagerWithPermissions):
    def get_queryset(self):
        return TaskQuerySet(self.model, using=self._db)

class Task(models.Model):
  def __unicode__(self):
      return unicode(self.name)
  objects = TaskManager()

  name = models.CharField(max_length=64)
  task_group = models.ForeignKey('TaskGroup')
  task_order = models.PositiveSmallIntegerField(
      blank=True,
      null=True,)
  task_type = models.CharField(
      max_length=1,
      choices=( ('T', "Text")
              , ('G', "Grid")
              , ('C', "Concentration")
              , ('I', "Tiles")
              , ('S', "Squares")
              )
  )
  time_before_play = models.PositiveSmallIntegerField(
      default=0,
      help_text=""" Number of seconds of 'Game begins in...' time before
                    gameplay begins.""")
  preplay_countdown_sublabel = models.CharField(
      null=True,
      blank=True,
      max_length=256,
      help_text=""" This text will appear below the 'Game begins in...'
                    countdown.""")
  time_between_rounds = models.PositiveSmallIntegerField(
      default=5,
      help_text=""" Number of seconds for which the game should pause between
                    rounds.""")
  time_between_rounds.verbose_name = 'Time between Rounds'
  time_unmatched_pairs_remain_faceup = models.FloatField(
      default=1,
      help_text=""" Number of seconds for which unmatched Concentration card
                    pairs should remain faceup.""")
  time_unmatched_pairs_remain_faceup.verbose_name = """
      Time Unmatched Cards Remain Faceup """
  pairs_in_generated_round = models.PositiveSmallIntegerField(
      default=16,
      help_text=""" Number of pairs in a randomly-generated Concentration Round.
                    Note that admin-defined Rounds will use whatever number of
                    of pairs the admin has specified; this field only defines the
                    number of pairs to be included in each *randomly* generated
                    Round. """)
  starting_width = models.PositiveSmallIntegerField(default=3)
  starting_height = models.PositiveSmallIntegerField(default=2)
  pct_tiles_on = models.FloatField(
      default=0.3,
      verbose_name="""Percent of Tiles that are 'on' in the Pattern.""")
  tiles_preview_seconds = models.FloatField(
      default=2.0,
      verbose_name="""How many seconds Subjects can study the Pattern.""")
  instructions = models.TextField(
      help_text="""Text to be displayed on the Instructions page before the
                   test, and also available on top of the workspace""",
      default="""This is default text.""")
  instructions_time = models.PositiveSmallIntegerField(
      help_text="""Number of seconds for which the instructions should be
                   displayed""",
      default=10)
  instructions_width = models.IntegerField(
      blank=True,
      null=True,
      help_text="""Starting width (in pixels) for the instructions pane
                   displayed to the left of the workspace. Optional.""")
  primer = models.TextField(
      blank=True,
      help_text="""Text to be displayed on the Primer page before the
                   test. If blank, no primer will be displayed""")
  primer_sidebar_text = models.TextField(
      blank=True,
      help_text="""Text to be displayed in the left sidebar of the Primer page
                   If blank, no sidebar will be displayed""")
  primer_time = models.PositiveSmallIntegerField(
      default=15,
      help_text="""Number of seconds for which the primer should
                   be displayed""")
  interaction_instructions = models.TextField(
      help_text="""Instructions displayed on the left side of the workspace
                   during the test""",
      default="""This is default text.""")
  etherpad_template = models.CharField(
      max_length=256,
      blank=True,
      null=True,
      help_text="""A unique string of characters identifying the Etherpad
                   workspace template for this task""")
  interaction_time = models.PositiveSmallIntegerField(
      help_text="""Time in seconds that the team will have to work in the
                   workspace""",
      default=60)
  grid_header_instructions = models.TextField(
      blank=True,
      null=True,
      help_text="""Only for grid tasks - text displayed immediately above
                   the grid""")
  grid_css = models.TextField(
      blank=True,
      null=True,
      help_text="""Custom CSS to be applied to the grid. Contents will be
                   added within &lt;style type='text/css'&gt; tags""")
  chat_enabled = models.BooleanField(
      default=True,
      help_text="""Enable chat for this task.  If you select Task Type
                   'Concentration' above, your input here will be overridden
                   with a value of 'False'.""")
  mousemove_interval = models.PositiveSmallIntegerField(
      default=100,
      help_text="""During a load test, this is the # of milliseconds
                    each client will wait between reports of new cursor coordinates.
                    When 'Load Test' is False, this field is not used.""")

  class Meta:
    ordering = ['task_group', 'task_order']

  def clean(self):
    if not self.etherpad_template and self.task_type in ['T', 'G']:
      self.etherpad_template = uuid.uuid4()

  def __unicode__(self):
    return unicode(self.name)

  def pretty_interaction_time(self):
    if not self.interaction_time % 60:
      return "%d minutes" % (self.interaction_time / 60)
    else:
      return "%d seconds" % self.interaction_time

  def total_duration(self):
    return   self.instructions_time \
           + (self.primer_time if (self.primer_time and self.primer) else 0) \
           + self.time_before_play \
           + self.interaction_time

  def grid_items(self):
    grid_items = self.taskgriditem_set.all()
    if grid_items:
      row_count = max(map(lambda x:x.row,grid_items))
      column_count = max(map(lambda x:x.column,grid_items))
      complete_grid = []
      for i in range(1,row_count + 1):
        row = []
        for j in range(1,column_count + 1):
          k = [x for x in grid_items if x.column == j and x.row == i]
          row.append(k[0] if k else [])
        complete_grid.append(row)
      return complete_grid
    else:
      return None

  def is_of_type(self, task_type):
      result = self.task_type == task_type
      return result

  def uses_etherpad(self):
      return any([self.is_of_type(t) for t in ['T', 'G']])

  def uses_realtimegame(self):
      return any([self.is_of_type(t) for t in ['C', 'I', 'S']])

# Although we give the Task model's 'chat_enabled' field a database default
# of 'True', it would be confusing to give any Task of type 'Concentration'
# a value of True.  We enforce False.
def concentration_defaults(sender, instance, *args, **kwargs):
    if instance.task_type == 'C':
        instance.chat_enabled = False
pre_save.connect(concentration_defaults, sender=Task)


class TaskPrivateInformation(models.Model):
    task = models.ForeignKey('Task')
    information = models.TextField(blank=True)

    class Meta:
        ordering = ['information']
        verbose_name_plural = "Private Information items"

class TaskGridItemQuerySet(QuerySetWithPermissions):
    def owned_by_virtue_of_ug_membership(self, user, ugs):
        shares_any_ug_with_taskgroup_of_task = reduce(or_, [Q(task__task_group__usergroups=ug) for ug in ugs])
        return shares_any_ug_with_taskgroup_of_task

class TaskGridItemManager(ManagerWithPermissions):
    def get_queryset(self):
        return TaskGridItemQuerySet(self.model, using=self._db)

class TaskGridItem(models.Model):
    def __unicode__(self):
        return unicode(self.name)
    objects = TaskGridItemManager()

    task = models.ForeignKey('Task')
    row = models.PositiveSmallIntegerField()
    column = models.PositiveSmallIntegerField()
    text_label = models.CharField(max_length=256, blank=True)
    image_label = models.ImageField(upload_to='tasks', blank=True)
    field_width = models.PositiveSmallIntegerField(max_length=256, blank=True, null=True)
    correct_answer = models.CharField(max_length=256, blank=True)
    readonly = models.BooleanField()

    def image_label_url(self):
        return self.image_label.url if self.image_label else False

    def __unicode__(self):
        return unicode("%s [%s,%s]" % (unicode(self.task.name), self.row, self.column))

class SubjectCountry(models.Model):
    def __unicode__(self):
        return unicode(self.name)

    name = models.CharField(max_length=200)
    flag = models.ImageField(upload_to="flags")
    list_priority = models.PositiveSmallIntegerField(null=True, blank=True)

    def thumbnail(self):
        return '<img src="%s" />' % self.flag.url
    thumbnail.allow_tags = True

    class Meta:
        verbose_name_plural = 'Subject Countries'
        ordering = ['-list_priority', 'flag']

class Region(models.Model):
    def __unicode__(self):
        return unicode(self.name)

    name = models.CharField(max_length=200, unique=True)
    countries = models.ManyToManyField('SubjectCountry')

    def random_disguises(self, req):
        from random import sample, choice
        pool = [n for n in self.pseudonym_set.all() if n.feminine == req.fem]
        selected = sample(pool, req.num)
        return [{
            'display_name': nym,
            'country': choice(self.countries.all())
        } for nym in selected]

    def satisfies_req(self, req):
        nyms = self.pseudonym_set.all()
        return len([n for n in nyms if n.feminine == req.fem]) >= req.num

    # NOTE: This is useful when we are VALIDATING a Region.  It assumes that:
    #       - We are only interested in the DisguiseSelections that are
    #         actually related to this Region, not some set of unsaved DSs
    #         instantiated using inline forms that are being validated.
    def nym_reqs(self):
        dss = self.disguise_selections.all()
        sts = set([ds.session_template for ds in dss if ds.session_template])
        reqs_from_sts = [st.nym_reqs_for_session_template() for st in sts]
        sessions = set([ds.session for ds in dss if ds.session])
        reqs_from_sessions = [s.nym_reqs_for_session() for s in sessions]
        return [req for req_list in reqs_from_sts + reqs_from_sessions
                    for req in req_list
                     if req.region == self]

    def unmet_nym_reqs_given_new_counts(self, new_f_ct, new_m_ct):
        return [req for req in self.nym_reqs()
                    if (req.num > new_f_ct if req.fem else req.num > new_m_ct)]

    def unmet_nym_req_reports_given_new_counts(self, new_f_ct, new_m_ct):
        report_st = """Session Builder %s, when building a session using
            Session Template %s,"""
        report_sesh = "Session %s"
        base_report = "%s expects this Region to have at least %d %s Pseudonym%s"
        unmet_reqs = self.unmet_nym_reqs_given_new_counts(new_f_ct, new_m_ct)
        return '.  Also: '.join([
            base_report % (
                (report_st % (
                    '<a href="%s">%s</a>' % (
                        reverse(
                            'admin:mci_sessionbuilder_change',
                            args=(req.session_builder.id,)),
                        req.session_builder),
                    '<a href="%s">%s</a>' % (
                        reverse(
                            'admin:mci_sessiontemplate_change',
                            args=(req.session_template.id,)),
                        req.session_template),
                )) if req.session_template else
                (report_sesh % (
                    '<a href="%s">%s</a>' % (
                        reverse(
                            'admin:mci_session_change',
                            args=(req.session.id,)),
                        req.session),
                )),
                req.num,
                "feminine" if req.fem else "masculine",
                "" if req.num == 1 else "s"
            ) for req in unmet_reqs
        ])

class SubjectQuerySet(QuerySetWithPermissions):
    def owned_by_virtue_of_ug_membership(self, user, ugs):
        shares_any_usergroup_with_session = reduce(or_, [Q(session__usergroups=ug) for ug in ugs])
        return shares_any_usergroup_with_session

class SubjectManager(ManagerWithPermissions):
    def get_queryset(self):
        return SubjectQuerySet(self.model, using=self._db)

class Subject(models.Model):
    def __unicode__(self):
        return unicode(self.external_id)
    objects = SubjectManager()

    session = models.ForeignKey('Session')
    external_id = models.CharField(max_length=32, unique=True)
    display_name = models.CharField(max_length=12, blank=True, null=True)
    display_name.verbose_name="Display\n Name"
    country = models.ForeignKey('SubjectCountry', blank=True, null=True)
    consent_and_individual_tests_completed = models.BooleanField(default=True)
    consent_and_individual_tests_completed.verbose_name = "Consent & tests"
    in_waiting_room = models.BooleanField()
    session_group = models.PositiveSmallIntegerField(blank=True, null=True)
    opentok_token = models.CharField(max_length=512, blank=True, null=True)
    etherpad_author_id = models.CharField( max_length=200
                                         , blank=True
                                         , null=True
                                         )
    etherpad_session_id = models.CharField( max_length=200
                                          , blank=True
                                          , null=True
                                          )
    scribe = models.CharField(
        max_length=1,
        default='U',
        choices=(
            ('U', "Unconfirmed"),
            ('C', "User confirmed"),
            ('R', "Scribe requested"),
            ('S', "Scribe confirmed")))


    def clean(self):
        from django.core.exceptions import ValidationError
        if self.session.has_task_of_type('C'):
            if not self.country:
                msg = """Session includes a Concentration task, so each Subject
                          must be assigned a Country."""
                raise ValidationError(msg)
            if not self.display_name:
                msg = """Session includes a Concentration task, so each Subject
                          must be assigned a Display Name."""
                raise ValidationError(msg)

    def etherpad_lite_identity_assigned(self):
        return self.etherpad_author_id and self.etherpad_session_id

    def assign_etherpad_lite_identity(self, pad_client):
        author_id_resp_dict = pad_client.createAuthorIfNotExistsFor(self.pk, self.display_name)
        self.etherpad_author_id = author_id_resp_dict['authorID']
        valid_until = int(time.time()) + (1000 * 365 * 24 * 60 * 60)
        session_id_resp_dict = pad_client.createSession( self.session.etherpad_group_id
                                                       , self.etherpad_author_id
                                                       , valid_until
                                                       )
        self.etherpad_session_id = session_id_resp_dict['sessionID']
        self.save()

    def is_scribe_or_scribe_disabled(self, ct):
        return not self.session.scribe_enabled or self.scribe == 'S'

class Avatar(models.Model):
    viewed = models.ForeignKey(
        'Subject',
        related_name='avatars_of')
    viewer = models.ForeignKey(
        'Subject',
        related_name='avatars_for')
    display_name = models.CharField(
        max_length=256,
        blank=True,
        null=True)
    country = models.ForeignKey(
        'SubjectCountry',
        blank=True,
        null=True)

class Pseudonym(models.Model):
    def __unicode__(self):
        return unicode(self.pseudonym)
    pseudonym = models.CharField(max_length=200)
    region = models.ForeignKey(
        'Region',
        default=lambda: Region.objects.get_or_create(name='Default Region')[0].pk)
    feminine = models.BooleanField(default=False)

class CompletedTaskQuerySet(QuerySetWithPermissions):
    def owned_by_virtue_of_ug_membership(self, user, ugs):
        shares_any_usergroup_with_session = reduce(or_, [Q(session__usergroups=ug) for ug in ugs])
        return shares_any_usergroup_with_session

class CompletedTaskManager(ManagerWithPermissions):
    def get_queryset(self):
        return CompletedTaskQuerySet(self.model, using=self._db)

class CompletedTask(models.Model):
  def __unicode__(self):
      return unicode(self.name)
  objects = CompletedTaskManager()

  task = models.ForeignKey('Task')
  session = models.ForeignKey('Session')
  session_group = models.IntegerField()
  completed_task_order = models.PositiveSmallIntegerField()
  start_time = models.DateTimeField(blank=True, null=True)
  # TODO: add 'end_time' so we get actual end times
  expected_start_time = models.DateTimeField(blank=True, null=True)
  expected_finish_time = models.DateTimeField(blank=True, null=True)
  # Only for tasks of type Text or Grid
  etherpad_workspace_url = models.URLField(blank=True)
  solo_subject = models.ForeignKey(
      'Subject',
      blank=True,
      null=True,
      related_name='+')
  num_rounds = models.IntegerField(default=10)
  # Only used in Squares-type tasks.
  board_area_width = models.IntegerField(default=game_board_width/3)
  board_area_height = models.IntegerField(default=game_board_height/3)

  class Meta:
    ordering = ['-expected_start_time']

  def grid_total(self):
    if self.task.task_type == "G":
      return self.task.taskgriditem_set.filter(readonly__exact=False).count()

  def grid_blank_count(self):
    if self.task.task_type == "G":
      return self.grid_total() - \
             self.completedtaskgriditem_set.exclude(answer__exact = "").count()

  def grid_correct_count(self):
    if self.task.task_type == "G":
      completed_items = map(
          lambda x:x.correct(),
          list(self.completedtaskgriditem_set.all()))
      return completed_items.count(True)

  def grid_incorrect_count(self):
    if self.task.task_type == "G":
      completed_items = map(
          lambda x:x.correct(),
          list(self.completedtaskgriditem_set.all()))
      return completed_items.count(False)

  def grid_percent_correct(self):
    if self.task.task_type == "G" and self.grid_total() > 0:
      return "%.2f%%" % (
          float(self.grid_correct_count()) / float(self.grid_total()) * 100)

  def __unicode__(self):
    return unicode("%s-%s-%s" % (unicode(self.session.name), unicode(self.task.name), unicode(self.session_group)))

  def instructions_end_time(self):
    return self.expected_start_time + \
           timedelta(seconds=self.task.instructions_time)

  def instructions_seconds_remaining(self):
      return _seconds_remaining(
          self.expected_start_time,
          self.instructions_end_time())

  def primer_end_time(self):
    pt = self.task.primer_time if (self.task.primer and self.task.primer_time) else 0
    return self.instructions_end_time() + timedelta(seconds=pt)

  def primer_seconds_remaining(self):
      return _seconds_remaining(self.instructions_end_time(), self.primer_end_time())

  def preplay_end_time(self):
    rv = self.primer_end_time() + timedelta(seconds=self.task.time_before_play)
    return rv

  def preplay_seconds_remaining(self):
      return _seconds_remaining(self.primer_end_time(), self.preplay_end_time())

  def workspace_seconds_remaining(self):
      return _seconds_remaining(self.preplay_end_time(), self.expected_finish_time)

  def next_completed_task(self, seid=None):
      if seid:
          solo_cts = CompletedTask.objects.filter(
              completed_task_order=self.completed_task_order+1,
              solo_subject=Subject.objects.get(external_id=seid))
          if solo_cts.count() > 0:
              return solo_cts[0]
      return CompletedTask.objects.get(
          completed_task_order=self.completed_task_order+1,
          session_group=self.session_group,
          session__id=self.session.id,
          solo_subject__isnull=True)

  def keyname_vars(self):
      return 'ct_%d_vars' % (self.pk)
  def keyname_points_global(self):
      return 'ct_%d_points_global' % (self.pk)
  def hashname_users(self):
      return 'ct_%d_users' % (self.pk)
  def hashname_cards_round(self, i):
      return 'ct_%d_cards_round_%s' % (self.pk, i)
  def hashnames_cards_rounds(self):
      return [self.hashname_cards_round(i) for i in range(self.num_rounds)]
  def hashname_vars_round(self, i):
      return 'ct_%d_vars_round_%s' % (self.pk, i)
  def keyname_current_round(self):
      return 'ct_%d_current_round' % (self.pk)
  def queuename_card_clicks(self):
      return 'ct_%d_card_clicks' % self.pk
  # Only used in Tiles-type tasks
  def queuename_submit_clicks(self):
      return 'ct_%d_submit_clicks' % self.pk
  # Only used in Squares-type tasks
  def queuename_squares_moves(self):
      return 'ct_%d_squares_moves' % self.pk

  def configure_next_round(self):
      _log.debug("Configuring next round for CT %d" % self.pk)
      try:
          import redis
          rc = redis.Redis(host=MCI_REDIS_SERVER, port=MCI_REDIS_PORT)

          current_round = rc.get(self.keyname_current_round())

          current_outcome = rc.hget(self.hashname_vars_round(current_round), 'outcome')
          if current_outcome == 'not_finished':
              raise Exception

          increment = 1 if current_outcome == 'success' else -1

          current_w = int(rc.hget(self.hashname_vars_round(current_round), 'w'))
          proviz_w = current_w + increment
          proviz_w_is_valid = proviz_w > self.task.starting_width and proviz_w <= 10
          new_w = proviz_w if proviz_w_is_valid else current_w

          current_h = int(rc.hget(self.hashname_vars_round(current_round), 'h'))
          proviz_h = current_h + increment
          proviz_h_is_valid = proviz_h > self.task.starting_height and proviz_h <= 4
          new_h = proviz_h if proviz_h_is_valid else current_h

          return self.configure_round(rc, int(current_round) + 1, new_w, new_h)
      except:
          _log.error(traceback.format_exc())
          raise

  # Note that we pass in a py-redis connection; otherwise we'd be connecting
  # multiple times when this function is called from workspace.py.
  # Also note that, at present, this method is only used to configure
  # TILES rounds.  That should probably be reflected in its name.  (It's
  # only used for Tiles rounds because Tiles is the only task type where
  # the setup of round n+1 depends on the outcome of round n.)
  def configure_round(self, rc, i, w, h):
      from random import sample
      l = w * h
      pattern = sample(range(l), int(l * self.task.pct_tiles_on) or 1)
      try:
          rc.hset(self.hashname_vars_round(i), 'w', w)
          rc.hset(self.hashname_vars_round(i), 'h', h)
          rc.hset(self.hashname_vars_round(i), 'outcome', 'not_finished')
      except:
          _log.error(
              "Failed configuring variables for Round %d of Tiles CT %d" % (i, self.pk))
          raise
      tile_dicts = [ ( j
                     , { 'in_selection': 'off'
                       , 'in_pattern': 'on' if m in pattern else 'off'
                       , 'clear_left': j % w == 0
                       }
                     ) for j, m in enumerate(range(l))
                   ]
      for j, td in tile_dicts:
          try:
              rc.hset(self.hashname_cards_round(i), str(j), json.dumps(td, indent=4))
          except:
              _log.error("Failed storing Card %d for Round %d of Tiles CT %d"
                            % (j, i, self.pk))
              raise
          _log.debug("Stored Card %d for Round %d of Tiles CT %d" % (j, i, self.pk))
      rc.set(self.keyname_current_round(), i)
      _log.debug("Finished configuring Round %d of Tiles CT %d" % (i, self.pk))
      return i

  def import_redis_submit_clicks(self):
      msg = 'Round %s | Outcome: %s | Team Score Change : %s | New Team Score: %s' \
            ' | Tiles in Round: %s'
      fn = lambda e: msg % (e['round'], e['outcome'], e['teamScoreChange'],
                            e['newTeamScore'], e['tiles'])
      self.import_redis_events('Submit', self.queuename_submit_clicks, fn)

  def import_redis_squares_moves(self):
      msg = "Round %s | Piece : %s | Receiver: %s | Status: %s | " \
            "Pieces Per Subject: %s"
      def msgFn(e):
          sidCtPairs = e['piecesPerSubject'].items()
          seidCtPairs = [( Subject.objects.get(pk=sid).external_id
                         , ct ) for (sid, ct) in sidCtPairs]
          scpsSorted = sorted(seidCtPairs, key=lambda p: p[0])
          scpsString = ', '.join(["%s: %s" % (seid, ct) for (seid, ct) in scpsSorted])
          return msg % (e['round'], e['pieceId'], Subject.objects.get(pk=e['receiverSid']),
                            e['outcome'], scpsString)
      self.import_redis_events('Move', self.queuename_squares_moves, msgFn)

  def import_redis_card_clicks(self):
      if self.task.task_type == 'C':
          def fn(e):
              msg = 'Round %s | Card %s | %s'
              return msg % (e['round'], e['index'], e['outcome'])
      elif self.task.task_type == 'I':
          msg = 'Round %s | Tile %s | Correct: %s | New Selection: %s ' \
                    '| Pattern: %s | Corrected Subject: %s'
          def fn(e):
              cKey = 'corrected'
              if cKey in e:
                  correctedSid = e[cKey]
                  try:
                      sub = Subject.objects.get(pk=correctedSid)
                  except Subject.DoesNotExist:
                      sub = "(bad ID for Corrected Subject: %s)" % correctedSid
              else:
                  sub = "(none)"
              vs = (e['round'], e['index'], e['correct'], e['selection'],
                    e['pattern'], sub)
              return msg % vs
      self.import_redis_events('Click', self.queuename_card_clicks, fn)

  def import_redis_events(self, eventType, queuenameFn, dataFn):
      # Empty the specified queue of records for this Completed Task, creating
      # an EventLog for each record.
      import redis
      rc = redis.Redis(host=MCI_REDIS_SERVER, port=MCI_REDIS_PORT)
      empty = False
      while not empty:
          event_json = rc.lpop(queuenameFn())
          if event_json:
              event = json.loads(event_json)
              try:
                  sub=Subject.objects.get(pk=event['sid'])
                  EventLog.objects.create(
                      timestamp=datetime.fromtimestamp(int(event['timestamp']) / 1000.0),
                      subject=sub,
                      session=sub.session,
                      session_group=sub.session_group,
                      completed_task=self,
                      event=eventType,
                      data=dataFn(event)
                  )
              except:
                  rc.lpush(queuenameFn(), event_json)
                  raise
          else:
              empty = True

  def tiles_summary_with_totals(self):
      summ = self.tiles_summary()
      subs = self.session.subjects_in_group(self.session_group)
      return listWithTotalsLast(summ, 'I', subs)

  def tiles_summary(self):
      if self.task.task_type != 'I':
          return None
      subs = [self.solo_subject] if self.solo_subject else \
             self.session.subject_set.filter(session_group=self.session_group)
      import redis
      rc = redis.Redis(host=MCI_REDIS_SERVER, port=MCI_REDIS_PORT)
      def stats_pair(sub):
          _log.debug("self.hashname_users(): " + self.hashname_users())
          _log.debug("self.pk: %d" % self.pk)
          hn = self.hashname_users()
          spk = sub.pk
          v = rc.hget(hn, spk)
          jv = json.loads(v)
          return (sub.external_id, jv)
      stats_pairs = [stats_pair(sub) for sub in subs]
      def uniqueTilesClicked(utcRecord):
          # Case 1 is to gracefully handle Tiles sessions that were run before
          # we fixed the way we log uniqueTilesClicked.  I.e. any reporting
          # that needs to make sure of Case 1 is flawed in terms of the data --
          # we just want to avoid failing ungracefully in those cases, since
          # some of them are still in the system.
          def utcCt(r):
              # Case 1
              if type(utcRecord[r]) == bool:
                  return int(utcRecord[r])
              # Case 2
              return len(utcRecord[str(r)])
          return sum([utcCt(rnd) for rnd in utcRecord])

      # A dictionary d:
      stats = dict(
          # d contains a k+v for each pair in this list:
          [ ( sid
              # A dictionary d':
            , dict(
                  # d' contains a k+v for each pair in this list:
                  [ ( metric
                    , uniqueTilesClicked(data[metric])
                          if metric in [ 'uniqueTilesCorrectlyClicked'
                                       , 'uniqueTilesIncorrectlyClicked' ]
                          else data[metric]
                    ) for metric in data
                  ]
                  # d' also includes every k+v in the following dict:
                  , **{ 'totals': False }
              )
            ) for (sid, data) in stats_pairs
          ]
      )

      def blah(m):
          def blech(memo, new):
              return memo + float(new[m])
          return ( m
                 , reduce(blech, stats.values(), 0)
                 )

      totals = dict([
          ( 'Totals'
          , dict( [ blah(m[0]) for m in self.per_subject_metrics()
                       if m not in [ 'timesCorrectlyCorrected'
                                   , 'timesIncorrectlyCorrected' ] ]
                , **{ 'totals': True }
                )
          )
      ])
      return dict(stats, **totals)

  def seconds_to_first_tiles_correction(self):
      if self.task.task_type != 'I':
          return 'N/A'
      corrections = self.eventlog_set.filter(
          (~Q(data__contains='Corrected Subject: (none)')),
          event='Click',
          data__contains='Corrected Subject:')
      if not corrections:
          return 'No cross-subject correction occurred'
      first = sorted(corrections, key=lambda c: c.timestamp)[0].timestamp
      stamp_string = first.strftime("%H:%M:%S")
      h, remainer = divmod((first - self.start_time).seconds, 3600)
      m, s = divmod(remainer, 60)
      elapsed_string = '%02d:%02d:%02d' % (h, m, s)
      return "%s (Click Timestamp: %s)" % (elapsed_string, stamp_string)

  def team_tiles_score(self):
      if self.task.task_type != 'I':
          return 0
      import redis
      rc = redis.Redis(host=MCI_REDIS_SERVER, port=MCI_REDIS_PORT)
      return float(rc.get(self.keyname_points_global()))


  def build_log(self, full_session=False, cache_subjects=False):
      if self.task.task_type in ['C', 'I']:
          self.import_redis_card_clicks()
          if self.task.task_type == 'I':
              self.import_redis_submit_clicks()
      elif self.task.task_type == 'S':
          self.import_redis_squares_moves()
      log = list(EventLog.objects.select_related('task','subject').filter(
          completed_task=self))

      subs = {}
      def _event_log_entry(record):
          return record.event_log_entry ( session         = self.session
                                        , session_group   = self.session_group
                                        , subs            = subs
                                        , cache_subjects  = cache_subjects
                                        )

      chats = map(_event_log_entry, EtherpadLiteRecord.objects.chats(self, full_session))
      log.extend(chats)

      edits = map(_event_log_entry, EtherpadLiteRecord.objects.edits(self, full_session))
      editsSorted = sorted(filter(None, edits), key=lambda e: e.timestamp)
      def withRevNum((i, e)):
          e.event = e.event + (" (rev %d)" % i)
          return e
      editsWithRevNums = map(withRevNum, enumerate(editsSorted))
      log.extend(editsWithRevNums)

      log = filter(None, log)
      log.sort(key=attrgetter("timestamp"))
      return log

  def conc_summary_with_totals(self):
      summ = self.conc_summary()
      subs = self.session.subjects_in_group(self.session_group)
      return listWithTotalsLast(summ, 'C', subs)

  def conc_summary(self):
      if self.task.task_type != 'C':
          return None

      EtherpadLiteRecord.objects.clear_querysets()
      log = self.build_log()
      subs = self.session.subjects_in_group(self.session_group)
      clicks = [item for item in log
                     if  item.subject and "Click" in item.event]
      # _scores consumes the list of clicks
      def _scores(clicks, scores):
          if len(clicks) == 0:
              return scores
          def _assister(clicks, card_index):
              if len(clicks) == 0:
                  return None
              if '| setup' in clicks[0].data and str(card_index) in clicks[0].data:
                  return clicks[0].subject.external_id
              return _assister(clicks[1:], card_index)
          if "| match" in clicks[0].data:
              clicker = clicks[0].subject.external_id
              scores[clicker] += 0.5
              round_index = int(re.findall("Round (\d+) |", clicks[0].data)[0])
              card_index = int(re.findall("Card (\d+)", clicks[0].data)[0])
              rnd = ConcentrationRound.objects.get(
                  completed_task=self,
                  position=round_index)
              crps = rnd.concentrationroundposition_set.all()
              clicked_crp = crps.get(position=card_index)
              crps_with_same_card = [crp for crp in crps if crp.card == clicked_crp.card]
              crps_with_same_card.remove(clicked_crp)
              setup_crp = crps_with_same_card[0]
              mAssister = _assister(clicks, setup_crp.position)
              if mAssister:
                  scores[mAssister] += 0.5
                  _log.debug("Giving %s 0.5 points for the assist (%s)" % (mAssister, setup_crp.card))
              else:
                  _log.info("Found no assister for click on card at index " + str(card_index) + ".  Likely concurrency issue during gameplay.")
          return _scores(clicks[1:], scores)
      def subject_clicks(sub):
          return [click for click in clicks
                        if  click.subject.external_id == sub.external_id]
      _scores = _scores(
          list(reversed(clicks)),
          dict([(sub.external_id, 0) for sub in subs]))
      stats = dict([(sub.external_id, {
          'score': _scores[sub.external_id],
          'clicks': len(subject_clicks(sub)),
          'totals': False,
      }) for sub in subs])
      stats['Totals'] = {
          'score': reduce(lambda memo, new: memo + new['score'], stats.values(), 0),
          'clicks': reduce(lambda memo, new: memo + new['clicks'], stats.values(), 0),
          'totals': True,
      }
      return stats

  def squares_summary_with_totals(self):
      summ = self.squares_summary()
      subs = self.session.subjects_in_group(self.session_group)
      return listWithTotalsLast(summ, 'S', subs)


  def squares_summary(self):
      if self.task.task_type != 'S':
          return None
      subs = [self.solo_subject] if self.solo_subject else self.session.subjects_in_group(self.session_group)
      rc = redis.Redis(host=MCI_REDIS_SERVER, port=MCI_REDIS_PORT)
      stats_pairs = [( sub.external_id
                     , json.loads(rc.hget(self.hashname_users(), sub.pk))
                     ) for sub in subs]
      _log.debug("stats_pairs: %s" % pformat(stats_pairs))

      # A dictionary d:
      stats = dict(
          # d contains a k+v for each pair in this list:
          [ ( sid
              # A dictionary d':
            , dict(
                  # d' contains a k+v for each pair in this list:
                  [ ( metric
                    , data[metric]
                    ) for metric in data
                  ]
                  # d' also includes every k+v in the following dict:
                  , **{ 'totals': False }
              )
            ) for (sid, data) in stats_pairs
          ]
      )

      def blah(m):
          def blech(memo, new):
              return memo + float(new[m])
          return ( m
                 , reduce(blech, stats.values(), 0)
                 )

      totals = dict([
          ( 'Totals'
          , dict( [blah(m[0]) for m in self.per_subject_metrics()
                               if type(m) is not dict]
                , **{ 'totals': True }
                )
          )
      ])
      return dict(stats, **totals)

  def summary(self, *args, **kwargs):
      if self.task.task_type == 'C':
          return self.conc_summary(*args, **kwargs)
      elif self.task.task_type == 'I':
          return self.tiles_summary(*args, **kwargs)
      elif self.task.task_type == 'S':
          return self.squares_summary(*args, **kwargs)

  def per_subject_metrics(self):
      return self.session.per_subject_metrics(self.task.task_type, self.session_group)

  def create_el_pad(self):
      pad_client = EtherpadLiteClient(MCI_ETHERPAD_API_KEY,MCI_ETHERPAD_API_URL)

      if self.task.etherpad_template:
          try:
              source_text = pad_client.getText(padID = self.task.etherpad_template)
          except Exception as e:
              _log.debug(("Received error response from Etherpad Lite server: '%s'.\n\t... We'll assume that Task %s's pad template was never set up (which is totally normal).") % (e, self.task.pk))
              source_text = {'text' : " "}
      else:
          source_text = {'text' : " "}

      try:
          new_pad_name = uuid.uuid4().hex
          pad_id_resp_dict = pad_client.createGroupPad(
              groupID = self.session.etherpad_group_id
            , padName = new_pad_name
            , text    = source_text['text']
            )
          new_pad_id = pad_id_resp_dict['padID']
          self.etherpad_workspace_url = pad_url_for_pad_id(new_pad_id)
          self.save()
      except Exception:
          _log.error("Could not create pad for CompletedTask: %s.  Traceback follows:" % self.pk)
          _log.error(traceback.format_exc())
          raise

  def pad_id(self):
      result = re.search(r'.*/p/(.*)',self.etherpad_workspace_url)
      return result.groups(0) if result else None

  def scribe(self):
      from django.core.exceptions import ObjectDoesNotExist
      try:
          return self.session.subject_set.get(session_group=self.session_group, scribe="S")
      except ObjectDoesNotExist:
          return None

  def assign_scribe(self):
      scribe = self.scribe()
      if scribe and not scribe.etherpad_lite_identity_assigned():
          scribe.assign_etherpad_lite_identity(self.session.get_pad_client())

  def configure(self):
      ct   = self
      task = self.task
      now  = datetime.now()

      if self.task.uses_etherpad():
          self.create_el_pad()
          if self.session.scribe_enabled:
              self.assign_scribe()

      elif self.task.uses_realtimegame():
          rc = redis.Redis(host=MCI_REDIS_SERVER, port=MCI_REDIS_PORT)
          bak_tag = '_clash_bak_%s' % datetime.now()

          # Back up any existing keys/hashes whose names clash with the names
          # we'll use.
          if rc.get(ct.keyname_vars()):
              _log.debug("Renaming redis key %s" % ct.keyname_vars())
              rc.rename(ct.keyname_vars(), ct.keyname_vars() + bak_tag)
          if rc.get(ct.keyname_points_global()):
              _log.debug("Renaming redis key %s" % ct.keyname_points_global())
              rc.rename(ct.keyname_points_global(), ct.keyname_points_global() + bak_tag)
          if rc.get(ct.keyname_current_round()):
              _log.debug("Renaming redis key %s" % ct.keyname_current_round())
              rc.rename(ct.keyname_current_round(), ct.keyname_current_round() + bak_tag)
          if rc.hkeys(ct.hashname_users()):
              _log.debug("Renaming redis hash %s" % ct.hashname_users())
              rc.rename(ct.hashname_users(), ct.hashname_users() + bak_tag)
          for hn in ct.hashnames_cards_rounds():
              if rc.hkeys(hn):
                  _log.debug("Renaming redis hash %s" % hn)
                  rc.rename(hn, hn + bak_tag)

          # Store an initial global score of '0'.
          rc.set(ct.keyname_points_global(), '0')

          # For each Subject associated with 'ct', store a JSON dict
          # in a Redis hash.
          if ct.solo_subject:
              subjects = [ct.solo_subject]
          else:
              subjects = [s for s in ct.session.subject_set.all().order_by('id')
                             if s.session_group == ct.session_group]

          areas_wide = 3 if len(subjects) >= 3 else len(subjects)
          areas_tall = int(math.ceil(float(len(subjects)) / areas_wide))
          ct.board_area_width = game_board_width / areas_wide
          ct.board_area_height = game_board_height / areas_tall
          ct.squares_set_width = squares_set_width
          ct.squares_set_height = squares_set_height
          ct.save()
          naive_piece_positions = [ ( (ct.board_area_width  * 1 / 3)
                                    , (ct.board_area_height * 1 / 3)
                                    )
                                  , ( (ct.board_area_width  * 2 / 3)
                                    , (ct.board_area_height * 1 / 3)
                                    )
                                  , ( (ct.board_area_width  * 1 / 2)
                                    , (ct.board_area_height * 2 / 3)
                                    )
                                  ]
          max_areas_wide = 3
          def board_area_offset_x(i):
              index_x = i % max_areas_wide
              offset = index_x * ct.board_area_width
              return offset
          def board_area_offset_y(i):
              index_y = i / max_areas_wide
              offset = index_y * ct.board_area_height
              return offset

          # Store attributes of the Task
          ctVars = { 'seconds_between_rounds': ct.task.time_between_rounds
                     # Only used in Concentration.
                   , 'seconds_unmatched_faceup': ct.task.time_unmatched_pairs_remain_faceup
                     # Might be better named 'task_start_time'.
                   , 'play_start_time': _format_datetime(ct.preplay_end_time())
                   , 'play_end_time': _format_datetime(ct.expected_finish_time)
                     # Only used in Tiles.
                   , 'tiles_preview_seconds': ct.task.tiles_preview_seconds
                   , 'team_score': 0
                   , 'task_type': task.task_type
                   , 'board_area_width': ct.board_area_width
                   , 'board_area_height': ct.board_area_height
                   , 'squares_set_width': ct.squares_set_width
                   , 'squares_set_height': ct.squares_set_height
                   }
          def ith_board_area(i):
              ox = board_area_offset_x(i)
              oy = board_area_offset_y(i)
              return { 'tl': { 'x': ox
                             , 'y': oy
                             }
                     , 'br': { 'x': ox + ct.board_area_width
                             , 'y': oy + ct.board_area_height
                             }
                     }
          board_areas = dict([(s.pk, ith_board_area(i))
                                for (i, s) in enumerate(subjects)])
          ctVars = dict(ctVars, **{ 'board_areas': json.dumps(board_areas)
                                  }) if task.task_type == 'S' else ctVars
          rc.set(ct.keyname_vars(), json.dumps(ctVars))

          for s in subjects:
              sd = { 'sid': s.pk
                   , 'x': -1
                   , 'y': -1
                   , 'clicks': '0'
                   }
              if task.task_type == 'I':
                  sd['netScore'] = '0'
                  sd['uniqueTilesCorrectlyClicked'] = {}
                  sd['uniqueTilesIncorrectlyClicked'] = {}
                  sd['correctCorrections'] = '0'
                  sd['incorrectCorrections' ] = '0'
                  sd['timesCorrectlyCorrected'] = '0'
                  sd['timesIncorrectlyCorrected' ] = '0'
                  sd['correctSubmitClicks' ] = '0'
                  sd['incorrectSubmitClicks' ] = '0'
              elif task.task_type == 'C':
                  sd['score'] = '0'
              elif task.task_type == 'S':
                  sd['completeMatches'] = '0'
                  sd['partialMatches'] = '0'
                  sd['interactions'] = dict([(_s.pk, 0) for _s in subjects])
                  sd['moves'] = '0'
              rc.hset(ct.hashname_users(), str(s.pk), json.dumps(sd, indent=4))
              _log.debug("Stored user dict for Subject %d in %s" %
                  (s.pk, ct.hashname_users()))

          if task.task_type == 'I':

              # Configure the starting round (using the same mechanism we use to
              # configure later rounds).
              ct.configure_round(rc, 0, task.starting_width, task.starting_height)

          elif task.task_type == 'S':

              # For each of the SquaresRoundTemplates we've defined for this Task,
              # store a JSON array (of x,y pairs) representing each of the
              # SRT's SquaresPieces.

              def repeat_to_length(list_to_expand, length):
                  return (list_to_expand * ((length/len(list_to_expand))+1))[:length]
              templates = repeat_to_length(list(ct.task.squares_round_template_indices.all()), 10)
              for (i, srti) in enumerate(templates):
                  srt = srti.rnd_template
                  sr = ct.squaresround_set.create(position=i)
                  # Take each of the SquaresSets associated with SquaresRoundTemplate
                  # 'srt' and associate it with the new SquaresRound 'sr' at the same
                  # 'position'.
                  for (j, squares_set) in list(enumerate(srt.squares_sets.all()))[:len(subjects)]:
                      SquaresRoundSquaresSetThrough.objects.create(
                          squares_round=sr,
                          squares_set=squares_set,
                          position=j)
                  def squares_piece_dict(piece):
                      vertex_pairs = [ (piece.v0_x, piece.v0_y)
                                     , (piece.v1_x, piece.v1_y)
                                     , (piece.v2_x, piece.v2_y)
                                     , (piece.v3_x, piece.v3_y)
                                     , (piece.v4_x, piece.v4_y)
                                     , (piece.v5_x, piece.v5_y)
                                     , (piece.v6_x, piece.v6_y)
                                     ]
                      vs = [{ 'x': x
                            , 'y': y
                            } for (x, y) in vertex_pairs
                              if  x is not None and y is not None]
                      return { 'piece_id': piece.pk
                             , 'set_id': piece.squares_set.pk
                             , 'vertices': vs
                             , 'avg_vertex': { 'x': sum([v['x'] for v in vs]) / len(vs)
                                             , 'y': sum([v['y'] for v in vs]) / len(vs)
                                             }
                             , 'drag_mode': False
                             , 'match_ready': False
                             , 'matched': False
                             }
                  piece_dicts_without_positions = [squares_piece_dict(sp)
                            for ss in sr.squares_sets.all()
                            for sp in ss.squarespiece_set.all()]
                  piece_dict_sublists_without_positions = random_n_length_sublists_unique_on_attribute(
                      piece_dicts_without_positions, 3, lambda d: d['set_id'], len(subjects))
                  # Adjusted so we're positioning each piece so the average of
                  # its vertices is at the abstract centerpoint, rather than its
                  # set's top left corner being there (at the abstract
                  # centerpoint).
                  def piece_positions_normalized_by_avg_vertex(piece_dicts):
                      def adjusted(j, x, y):
                          avg_v = piece_dicts[j]['avg_vertex']
                          return (x - avg_v['x'], y - avg_v['y'])
                      return [adjusted(j, x, y)
                                for (j, (x, y)) in enumerate(naive_piece_positions)]
                  piece_position_sublists = [piece_positions_normalized_by_avg_vertex(piece_dict_sublist)
                                              for piece_dict_sublist in piece_dict_sublists_without_positions]
                  # Adjusted so we're positioning each piece in the board
                  # area where it belongs, rather than positioning them
                  # all in the 1st board area.
                  def in_correct_board_area(board_area_index, piece_position_list):
                      return [( x + board_area_offset_x(board_area_index)
                              , y + board_area_offset_y(board_area_index)
                              ) for (x, y) in piece_position_list]
                  piece_position_sublists_in_correct_board_areas = [
                      in_correct_board_area(j, piece_position_sublist)
                      for (j, piece_position_sublist) in enumerate(piece_position_sublists)
                  ]
                  def merged_dicts(piece_dicts, piece_positions):
                      def merged_dict(piece_dict, piece_position):
                          pos_dict = {'x': piece_position[0], 'y': piece_position[1]}
                          new_dict = piece_dict
                          new_dict['position'] = pos_dict
                          new_dict['return_position'] = pos_dict
                          return new_dict
                      return [merged_dict(pd, pp)
                                for (pd, pp) in zip(piece_dicts, piece_positions)]
                  piece_dict_sublists_with_positions = \
                      [merged_dicts(pd_sublist, pp_sublist)
                          for (pd_sublist, pp_sublist)
                            in zip(piece_dict_sublists_without_positions,
                                   piece_position_sublists_in_correct_board_areas)]
                  piece_dicts_with_positions = [item
                      for sublist in piece_dict_sublists_with_positions
                      for item in sublist]
                  for pdwp in piece_dicts_with_positions:
                      _log.debug("Storing Piece: %r" % pdwp)
                      rc.hset(ct.hashname_cards_round(i), str(pdwp['piece_id']), json.dumps(pdwp, indent=4))
                  _log.debug("Exiting setup of Squares Round %d" % i)

          elif task.task_type == 'C':

              # For each of 10 rounds, for each of the round's cards, store a JSON
              # dict representing the card.
              # Generate each round from the ConcentrationRoundTemplate that either
              # is pre-defined on the Task or, in the absence of a predefined one,
              # is generated randomly.
              # NOTE: Pre-defined ConcentrationRoundTemplates can have as few or many
              #       positions as the admin wants.  Generated CRTs have num_rounds
              #       positions.
              css = list(ConcentrationCardSet.objects.all())
              if len(css) == 0:
                  _log.error("No Concentration Card Sets defined!")
                  raise Exception
              shuffle(css)

              random_rnd_tpl_length = ct.task.pairs_in_generated_round

              def random_round_template():
                  chars = [chr(n + ord('a')) for n in range(random_rnd_tpl_length)]
                  chars += chars
                  shuffle(chars)
                  return ConcentrationRoundTemplate(positions=','.join(chars))

              for i in range(ct.num_rounds):
                  conc_round = ct.concentrationround_set.create(
                                  position=i)
                  templates = [tcrti.rnd_template for tcrti in
                                  task.taskconcentrationroundtemplateindex_set.filter(
                                      position=i)]
                  tpl = templates[0] if templates else random_round_template()
                  chars = tpl.positions.split(',')
                  _cards_log.debug("Split the template's positions into a list")
                  cardsets = list(css)
                  if tpl.card_set:
                      itcs = cardsets.index(tpl.card_set)
                      cardsets[itcs], cardsets[-1] = cardsets[-1], cardsets[itcs]
                  card_set = None
                  _cards_log.debug("Entering the 'find a card set' loop")
                  while not card_set:
                      try:
                          _cards_log.debug("About to pop a card set off the list")
                          card_set = cardsets.pop()
                      except IndexError:
                          _log.error(("No ConcentrationCardSets with enough cards for "
                              "Round %d") % i)
                          raise IndexError
                      if not card_set.cards.count() >= len(chars) / 2:
                          _cards_log.debug(("Selected card set doesn't have enough "
                              "cards.  Discarding it."))
                          card_set = None
                  _cards_log.debug("Using card set %s for round %d" % (card_set, i))
                  set_cards = list(card_set.cards.all())
                  shuffle(set_cards)
                  card_map = dict([(char, set_cards.pop()) for char in list(set(chars))])
                  cards = [card_map[char] for char in chars]
                  for j in range(len(cards)):
                      conc_round.concentrationroundposition_set.create(
                          position=j,
                          card=cards[j])

                  # For each ConcentrationCard in our list, store a JSON dict in a
                  # Redis hash representing this Round.
                  card_dicts = [{ 'url': card.image.url,
                                  'state': 'facedown' } for card in cards]
                  for j, cd in enumerate(card_dicts):
                      rc.hset(ct.hashname_cards_round(i), str(j), json.dumps(cd, indent=4))
                  _log.debug("Exiting setup of Concentration Round %d" % i)

class CompletedTaskGridItemQuerySet(QuerySetWithPermissions):
    def owned_by_virtue_of_ug_membership(self, user, ugs):
        shares_any_usergroup_with_session_of_ct = reduce(or_, [Q(completed_task__session__usergroups=ug) for ug in ugs])
        return shares_any_usergroup_with_session_of_ct

class CompletedTaskGridItemManager(ManagerWithPermissions):
    def get_queryset(self):
        return CompletedTaskGridItemQuerySet(self.model, using=self._db)

class CompletedTaskGridItem(models.Model):
    def __unicode__(self):
        return unicode(self.name)
    objects = CompletedTaskGridItemManager()

    task_grid_item = models.ForeignKey('TaskGridItem')
    completed_task = models.ForeignKey('CompletedTask')
    answer = models.CharField(max_length=256)
    subject = models.ForeignKey('Subject', null=True)

    def correct(self):
        answers = map(lambda x:x.strip(),self.task_grid_item.correct_answer.lower().split(","))
        return self.answer.lower().strip() and self.answer.lower().strip() in answers


###########
# SQUARES #
###########

class SquaresSet(models.Model):
    """ A square.  Pretty straightforward.  """

    def __unicode__(self):
        return unicode(self.name)

    name = models.CharField(max_length=200, blank=True, null=True)

    # TODO use admin form validation to ensure there are exactly 3 pieces per Square.

class SquaresPiece(models.Model):
    """ A piece of a Squares set.  """

    squares_set = models.ForeignKey('SquaresSet')

    v0_x = models.PositiveSmallIntegerField(
        verbose_name="x0",
        blank=True,
        null=True)
    v0_y = models.PositiveSmallIntegerField(
        verbose_name="y0",
				blank=True,
				null=True)
    v1_x = models.PositiveSmallIntegerField(
        verbose_name="x1",
        blank=True,
        null=True)
    v1_y = models.PositiveSmallIntegerField(
        verbose_name="y1",
				blank=True,
				null=True)
    v2_x = models.PositiveSmallIntegerField(
        verbose_name="x2",
        blank=True,
        null=True)
    v2_y = models.PositiveSmallIntegerField(
        verbose_name="y2",
				blank=True,
				null=True)
    v3_x = models.PositiveSmallIntegerField(
        verbose_name="x3",
        blank=True,
        null=True)
    v3_y = models.PositiveSmallIntegerField(
        verbose_name="y3",
				blank=True,
				null=True)
    v4_x = models.PositiveSmallIntegerField(
        verbose_name="x4",
        blank=True,
        null=True)
    v4_y = models.PositiveSmallIntegerField(
        verbose_name="y4",
				blank=True,
				null=True)
    v5_x = models.PositiveSmallIntegerField(
        verbose_name="x5",
        blank=True,
        null=True)
    v5_y = models.PositiveSmallIntegerField(
        verbose_name="y5",
				blank=True,
				null=True)
    v6_x = models.PositiveSmallIntegerField(
        verbose_name="x6",
        blank=True,
        null=True)
    v6_y = models.PositiveSmallIntegerField(
        verbose_name="y6",
				blank=True,
				null=True)
    # TODO use admin form validation to ensure there are at least 3 vertices per Piece

    def clean(self):
        from django.core.exceptions import ValidationError
        for x in [self.v0_x, self.v1_x, self.v2_x, self.v3_x, self.v4_x, self.v5_x, self.v6_x]:
            if x > squares_set_width:
                raise ValidationError("Vertex's x position cannot exceed %d." % squares_set_width)
        for y in [self.v0_y, self.v1_y, self.v2_y, self.v3_y, self.v4_y, self.v5_y, self.v6_y]:
            if y > squares_set_height:
                raise ValidationError("Vertex's y position cannot exceed %d." % squares_set_height)

class SquaresRound(models.Model):
    """
        Each SquaresRound is associated with a CompletedTask and has
        associated with it a list of SquaresSets.
    """
    def __unicode__(self):
        return unicode(self.id)

    completed_task = models.ForeignKey('CompletedTask')
    # Intentionally not inheriting from Grappelli's 'Position' class
    position = models.SmallIntegerField(
        verbose_name="""The index of this SquaresRound in the sequence of
            SquaresRounds that make up this CompletedTask.""")
    squares_sets = models.ManyToManyField(
        'SquaresSet',
        through='SquaresRoundSquaresSetThrough')

class SquaresRoundSquaresSetThrough(models.Model):
    """ Through/joint table helping to model the (*ordered*) many-to-many
        relationship between SquaresRound and SquaresSet. """
    squares_round = models.ForeignKey('SquaresRound')
    squares_set = models.ForeignKey('SquaresSet')
    position = models.PositiveSmallIntegerField("Position")
    class Meta:
        verbose_name = "Set Used in this Squares Round"
        verbose_name_plural = "Sets Used in this Squares Round"

class SquaresRoundTemplate(models.Model):

    def __unicode__(self):
        return unicode(self.name)

    name = models.CharField(
        max_length=200,
        blank=True,
        null=True)
    class Meta:
        verbose_name = "Squares Round"
        verbose_name_plural = "Squares Rounds"
    squares_sets = models.ManyToManyField(
        'SquaresSet',
        through='SquaresRoundTemplateSquaresSetThrough')

class SquaresRoundTemplateSquaresSetThrough(models.Model):
    """ Through/joint table helping to model the (ordered) many-to-many
        relationship between SquaresRoundTemplate and SquaresSet. """

    squares_round_template = models.ForeignKey('SquaresRoundTemplate')
    squares_set = models.ForeignKey('SquaresSet')
    position = models.PositiveSmallIntegerField("Position")
    class Meta:
        verbose_name = "Set Used in this Squares Round Template"
        verbose_name_plural = "Sets Used in this Squares Round Template"

class TaskSquaresRoundTemplateIndex(models.Model):
    """
        Through/joint table helping to represent the (ordered) many-to-many
        relationship between Task and SquaresRoundTemplate.
        Each Squares-type Task has 0 or more SquaresRoundTemplates
        associated with it.  They are associated with it in a defined order,
        so we use this custom joint model rather than the orderless relation of
        the ManyToManyField.
    """
    def __unicode__(self):
        return 'SquaresRoundTemplate at position %i in %s' % (self.position, unicode(self.task))

    task = models.ForeignKey(
        'Task',
        related_name='squares_round_template_indices')
    rnd_template = models.ForeignKey(
        'SquaresRoundTemplate',
        related_name='task_joints')
    rnd_template.verbose_name = "Round Template"
    position = models.SmallIntegerField('Position')


#################
# CONCENTRATION #
#################

class ConcentrationCard(models.Model):
    """
        A card.  Pretty straightforward.
    """

    def __unicode__(self):
        return unicode(self.name if self.name else self.image.name.split('/')[1])

    name = models.CharField(max_length=200, blank=True, null=True)
    image = models.ImageField(upload_to='card_images')

    def thumbnail(self):
        return '<img src="%s" />' % self.image.url
    thumbnail.allow_tags = True

class ConcentrationRoundTemplate(models.Model):
    """
        A ConcentrationRoundTemplate represents an arrangement of pairs.
        Its 'positions' field is a comma-delimited character list.  Each of the
        list's members is a character other than ','.  Any character that
        appears in the list must appear exactly twice.

        The two list positions of each appearing character represent the two
        board positions of a pair of cards in a Concentration game.  This data
        structure does not specify which ConcentrationCard will instantiate the
        pair in a given CompletedTask.
    """

    def __unicode__(self):
        return unicode(self.name if self.name else self.id)

    name = models.CharField(
        max_length=200,
        blank=True,
        null=True)
    positions = models.CharField(
        max_length=200,
        help_text="""
            One character for each card in your desired game board, and each
            character you use must appear exactly twice.  E.g.:
            'a,a,b,b,c,c,d,d,e,e,f,f,g,g,h,h,i,i,j,j,k,k,l,l,m,m,n,n,o,o,p,p'.
        """)
    card_set = models.ForeignKey(
        'ConcentrationCardSet',
        blank=True,
        null=True,
        help_text="""
            OPTIONAL.  If you omit this, a random Card Set will be selected
            each time this ConcentrationRoundTemplate is used to create a Session.
        """)

    def clean(self):
        from django.core.exceptions import ValidationError
        positions = self.positions.split(',')
        for pos in positions:
            if len([p for p in positions if p == pos]) != 2:
                msg = "Each member of 'positions' must appear in the list " + \
                      "exactly twice."
                raise ValidationError(msg)

    class Meta:
        verbose_name = "Concentration Round"
        verbose_name_plural = "Concentration Rounds"


class ConcentrationCardSet(models.Model):
    """
        A usable ConcentrationCardSet has n (n >= 16) ConcentrationCards
        associated with it.  Each ConcentrationRoundTemplate has, in addition
        to its 'positions' list, an optional relation to a
        ConcentrationCardSet; if the relation is present all the cards selected
        for ConcentrationRounds based on the ConcentrationRoundTemplate will
        be selected from that ConcentrationCardSet.
    """
    def __unicode__(self):
        return unicode(self.name if self.name else self.id)

    name = models.CharField(max_length=200, blank=True, null=True)
    cards = models.ManyToManyField('ConcentrationCard')

    def thumbnails(self):
        return json.dumps([{ 'id': cc.id, 'thumbnail': cc.image.url }
                              for cc in ConcentrationCard.objects.all()])

class TaskConcentrationRoundTemplateIndex(models.Model):
    """
        Each Concentration-type Task has 0 or more ConcentrationRoundTemplates
        associated with it.  They are associated with it in a defined order,
        so we use this custom joint model rather than the orderless relation of
        the ManyToManyField.
    """
    def __unicode__(self):
        return unicode('ConcentrationRoundTemplate')

    task = models.ForeignKey('Task')
    rnd_template = models.ForeignKey('ConcentrationRoundTemplate')
    rnd_template.verbose_name = "Round Template"
    position = models.SmallIntegerField('Position')

class ConcentrationRound(models.Model):
    """
        Each ConcentrationRound is associated with a CompletedTask and has
        associated with it 32 ConcentrationRoundPositions.
    """
    def __unicode__(self):
        return unicode(self.id)

    completed_task = models.ForeignKey('CompletedTask')
    # Intentionally not inheriting from Grappelli's 'Position' class
    position = models.SmallIntegerField()
    started = models.BooleanField(default=False)


class ConcentrationRoundPosition(models.Model):
    def __unicode__(self):
        return unicode("%i: %s" % (self.position, unicode(self.card.image.url)))

    rnd = models.ForeignKey('ConcentrationRound')
    card = models.ForeignKey('ConcentrationCard')
    # Intentionally not inheriting from Grappelli's 'Position' class
    position = models.PositiveSmallIntegerField()

class UserGroupQuerySet(QuerySetWithPermissions):
    def owned_by_virtue_of_ug_membership(self, user, ugs):
        has_user_as_member = Q(pk__in=[ug.pk for ug in ugs])
        return has_user_as_member
    def permitted_in_change_list(self, user):
        if user.is_superuser:
            return self
        if user.has_perm('mci.manage_usergroups'):
            return self
        ugs = user.ugroups.all()
        if not ugs:
            return self.none()
        qs = self.filter(self.owned_by_virtue_of_ug_membership(user, ugs)).distinct()
        return qs
    def permitted_in_change_list_or_selected(self, user, existing_selection):
        if user.is_superuser:
            return self
        if user.has_perm('mci.manage_usergroups'):
            return self
        ugs = user.ugroups.all()
        if not ugs:
            return self.none()
        owned = self.owned_by_virtue_of_ug_membership(user, ugs)
        in_existing_selection = Q(pk__in=existing_selection)
        qs = self.filter(Q(owned | in_existing_selection)).distinct()
        return qs

class UserGroupManager(ManagerWithPermissions):
    def get_queryset(self):
        return UserGroupQuerySet(self.model, using=self._db)

class UserGroup(models.Model):
    def __unicode__(self):
        return unicode(self.name)
    objects = UserGroupManager()

    name = models.CharField(max_length=128, blank=False, null=False)
    users = models.ManyToManyField(User, related_name="ugroups")

    class Meta:
        permissions = [('manage_usergroups', "Can see and edit every User Group, even if not a member")]

class UserProfile(models.Model):
    user = models.OneToOneField(User)
    owns_all_owned_objects = models.BooleanField(
        default=False,
        verbose_name="Can View and Edit All Objects")

def ensure_profile_exists(sender, **kwargs):
    if kwargs.get('created', False):
        UserProfile.objects.get_or_create(user=kwargs.get('instance'))

post_save.connect(ensure_profile_exists, sender=User)
