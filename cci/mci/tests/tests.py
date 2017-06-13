from datetime import timedelta, datetime
from django.test import TestCase
from mci.models import SessionBuilder           \
                     , Session                  \
                     , SessionTemplate          \
                     , SessionTemplateFrequency \
                     , SI_SB_Status             \
                     , Subject                  \
                     , SubjectIdentity          \
                     , TaskPrivateInformation   \
                     , TaskGridItem             \
                     , CompletedTaskGridItem    \
                     , UserGroup
from django.contrib.auth.models import User
from mci.views import _setup_participants, _configure_session
from pprint import pformat

# Run tests from related applications
from mci.workspace.tests import *
import settings

class Util:
	def setup_test_participants(self, session):
		participants = session.subject_set.all()
		for p in list(participants):
			p.in_waiting_room = True
			p.save()
		_setup_participants(session)
		return session


class SessionTest(TestCase):
  fixtures = ['test', 'users']

  def test_not_too_early(self):
    session = Session.objects.get(pk=1)
    session.start_datetime = datetime.today() + timedelta(minutes=10)
    self.assertFalse(session.too_early())

  def test_too_early(self):
    session = Session.objects.get(pk=1)
    session.start_datetime = datetime.today() + timedelta(minutes=session.waiting_room_time + 1)
    self.assertTrue(session.too_early())

  def test_participants_none_ready(self):
    session = Session.objects.get(pk=1)
    _setup_participants(session)

    participants = session.subject_set.all()
    for p in list(participants):
      self.assertEqual(p.session_group, None)

  def test_participants_all_ready(self):
    """ Test data has 5 participants and group size from 3 to 4"""
    session = Session.objects.get(pk=1)
    session = Util().setup_test_participants(session=session)

    groups = map(lambda x:x.session_group,list(session.subject_set.all()))
    self.assertEqual(4,groups.count(1))
    self.assertEqual(1,groups.count(0))

#  def test_setup_tasks(self):
#    session = Session.objects.get(pk=1)
#    participants = session.subject_set.all()
#    for p in list(participants):
#      p.in_waiting_room = True
#      p.save()
#    _setup_participants(session)
#    _setup_tasks(session)


class TaskTest(TestCase):
	fixtures = ['test']

	def _setup_private_information_test(self):
		session = Session.objects.get(pk=1)
		session = Util().setup_test_participants(session)
		task = Task.objects.get(id=4)
		return session, task

	def test_no_private_information(self):
		from mci.views import _get_private_information
		session, task = self._setup_private_information_test()
		self.assertIsNone(_get_private_information(task,session,"rabbit"))

	def test_one_private_information(self):
		from mci.views import _get_private_information
		session, task = self._setup_private_information_test()
		tpi = TaskPrivateInformation(task_id=4,information="This is our private information")
		tpi.save()
		self.assertEquals(_get_private_information(task,session,"rabbit")[0],"This is our private information")

	def test_two_private_information_five_participants(self):
		"""Make sure that everyone has a piece of information, even if some are duplicated
		Subjects are: bird, donkey, fish, hamster, rabbit
		"""
		from mci.views import _get_private_information
		session, task = self._setup_private_information_test()
		tpi1 = TaskPrivateInformation(task_id=4,information="A-This is our private information")
		tpi1.save()
		tpi2 = TaskPrivateInformation(task_id=4,information="B-Second piece of information")
		tpi2.save()
		self.assertEquals(_get_private_information(task,session,"bird")[0],"A-This is our private information")
		self.assertEquals(_get_private_information(task,session,"donkey")[0],"B-Second piece of information")
		self.assertEquals(_get_private_information(task,session,"rabbit")[0],"A-This is our private information")

	def test_more_information_than_participants(self):
		"""Make sure that all pieces of information are distributed, even if there are fewer people than pieces of information
		Subjects are: bird, donkey, fish, hamster, rabbit
		"""
		from mci.views import _get_private_information
		session, task = self._setup_private_information_test()
		for i in range(1,8):
			tpi = TaskPrivateInformation(task_id=4,information="This is information #" + str(i))
			tpi.save()
		self.assertEquals(_get_private_information(task,session,"bird")[0],"This is information #1")
		self.assertEquals(_get_private_information(task,session,"bird")[1],"This is information #6")
		self.assertEquals(_get_private_information(task,session,"donkey")[0],"This is information #2")
		self.assertEquals(_get_private_information(task,session,"donkey")[1],"This is information #7")
		self.assertEquals(_get_private_information(task,session,"fish")[0],"This is information #3")
		self.assertEquals(_get_private_information(task,session,"rabbit")[0],"This is information #5")

class CompletedTaskGridItemTest(TestCase):

	def test_blank(self):
		task_grid_item = TaskGridItem(correct_answer="yes")
		completed = CompletedTaskGridItem(task_grid_item=task_grid_item,answer="")
		self.assertFalse(completed.correct())

	def test_single(self):
		task_grid_item = TaskGridItem(correct_answer="yes")
		completed = CompletedTaskGridItem(task_grid_item=task_grid_item,answer="yes")
		self.assertTrue(completed.correct())

	def test_single_capitalization(self):
		task_grid_item = TaskGridItem(correct_answer="yes")
		completed = CompletedTaskGridItem(task_grid_item=task_grid_item,answer="Yes")
		self.assertTrue(completed.correct())

	def test_single_whitespace(self):
		task_grid_item = TaskGridItem(correct_answer="yes")
		completed = CompletedTaskGridItem(task_grid_item=task_grid_item,answer="  yes  ")
		self.assertTrue(completed.correct())

	def test_single_correct_whitespace(self):
		task_grid_item = TaskGridItem(correct_answer="yes ")
		completed = CompletedTaskGridItem(task_grid_item=task_grid_item,answer="  yes  ")
		self.assertTrue(completed.correct())

	def test_multiple_incorrect(self):
		task_grid_item = TaskGridItem(correct_answer="yes,no,maybe ")
		completed = CompletedTaskGridItem(task_grid_item=task_grid_item,answer="hahaha")
		self.assertFalse(completed.correct())

	def test_multiple_correct(self):
		task_grid_item = TaskGridItem(correct_answer="yes,no,maybe ")
		completed = CompletedTaskGridItem(task_grid_item=task_grid_item,answer="no ")
		self.assertTrue(completed.correct())

class SessionBuilderSurveyTestCase(TestCase):
    def setUp(self):
        now = datetime.now()
        sb = SessionBuilder.objects.create( name                 = "Test SB"
                                          , mturk                = True
                                          , waiting_room_opens   = now - timedelta(hours=1)
                                          , waiting_room_closes  = now + timedelta(hours=1)
                                          , subjects_per_session = 4
                                          )
        st = SessionTemplate.objects.create(name = "Test ST")
        tg = st.task_groups.create(name = "Test TG")
        tg.task_set.create( name      = "Test Task"
                          , task_type = "T"
                          )
        SessionTemplateFrequency.objects.create( session_template = st
                                               , session_builder  = sb
                                               )


    def test__build_session_basic_functionality(self):
        num_subs = 4

        sb = SessionBuilder.objects.get(name="Test SB")
        arrival = datetime.now() - timedelta(seconds=1)
        for i in range(num_subs):
            n = "There are a few movies out that I'd like to see %d" % i
            si = SubjectIdentity.objects.create( mturk_id     = n
                                               , display_name = n[:11]
                                               )
            SI_SB_Status.objects.create( sessionbuilder            = sb
                                       , arrival_time              = arrival
                                       , subject_identity          = si
                                       , last_waiting_room_checkin = arrival
                                       )

        sb.survey()
        self.assertEqual(Session.objects.count(), 1)

    def test__build_session_honors_sb_group_ids(self):

        sb = SessionBuilder.objects.get(name="Test SB")
        arrival = datetime.now() - timedelta(seconds=1)
        n = "There are a few movies out that I'd like to see %d"
        for i in range(4):
            name = n % i
            si = SubjectIdentity.objects.create( mturk_id     = name
                                               , display_name = name[:11]
                                               )
            SI_SB_Status.objects.create( sessionbuilder            = sb
                                       , arrival_time              = arrival
                                       , subject_identity          = si
                                       , last_waiting_room_checkin = arrival
                                       , sb_group_id               = None if i == 3 else str(3)
                                       )
        sb.survey()
        self.assertEqual(Session.objects.count(), 0)

        for i in range(4,7):
            name = n % i
            si = SubjectIdentity.objects.create( mturk_id     = name
                                               , display_name = name[:11]
                                               )
            SI_SB_Status.objects.create( sessionbuilder            = sb
                                       , arrival_time              = arrival
                                       , subject_identity          = si
                                       , last_waiting_room_checkin = arrival
                                       )
        sb.survey()
        self.assertEqual(Session.objects.count(), 1)

        name = n % 7
        si = SubjectIdentity.objects.create( mturk_id     = name
                                           , display_name = name[:11]
                                           )
        SI_SB_Status.objects.create( sessionbuilder            = sb
                                   , arrival_time              = arrival
                                   , subject_identity          = si
                                   , last_waiting_room_checkin = arrival
                                   , sb_group_id               = str(3)
                                   )

        sb.survey()
        self.assertEqual(Session.objects.count(), 2)

        stats = SI_SB_Status.objects.all()
        subs_group_3    = [stat.subject for stat in stats if stat.sb_group_id == str(3)]
        subs_group_None = [stat.subject for stat in stats if not stat.sb_group_id]
        self.assertEqual(len(set([sub.session for sub in subs_group_3])), 1)
        self.assertEqual(len(set([sub.session for sub in subs_group_None])), 1)


    def test__build_session__correct_user_groups(self):
        num_subs = 4

        sb = SessionBuilder.objects.get(name="Test SB")
        ug = sb.usergroups.create(name="Test UG")
        sb.usergroups.create(name="Test UG for SB only")
        for (i, st) in enumerate(sb.session_templates.all()):
            st.usergroups.add(ug)
            st.usergroups.create(name="UG for ST %d" % i)
        arrival = datetime.now() - timedelta(seconds=1)
        for i in range(num_subs):
            n = "There are a few movies out that I'd like to see %d" % i
            si = SubjectIdentity.objects.create( mturk_id     = n
                                               , display_name = n[:11]
                                               )
            SI_SB_Status.objects.create( sessionbuilder            = sb
                                       , arrival_time              = arrival
                                       , subject_identity          = si
                                       , last_waiting_room_checkin = arrival
                                       )

        sb.survey()
        sesh = Session.objects.get(session_template_frequency__session_builder=sb)
 
        self.assertListEqual([ug], list(sesh.usergroups.all()))
