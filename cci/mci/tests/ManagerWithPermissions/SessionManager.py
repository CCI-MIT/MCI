from django.test import TestCase
from mci.models import Session, SessionBuilder, SessionTemplate, SessionTemplateFrequency, UserGroup
from django.contrib.auth.models import User
from pprint import pformat

class UserType(object):
    def prepare_user_groups(self):
        raise NotImplementedError
class SessionUGPossession(object):
    def prepare_session(self, ug):
        raise NotImplementedError
class TaskGroupUGPossession(object):
    def prepare_task_groups(self, ug, s):
        raise NotImplementedError
class SessionBuilderExistenceAndPermittedness(object):
    def maybe_prepare_sessionbuilder(self, ug, sesh):
        raise NotImplementedError

class Test_SessionManager(UserType, SessionUGPossession, TaskGroupUGPossession):
    fixtures = ['test', 'users']
    def test_permitted(self):
        (u, ug) = self.prepare_user_groups()
        sesh = self.prepare_session(ug)
        self.prepare_task_groups(ug, sesh)
        self.maybe_prepare_sessionbuilder(ug, sesh)
        try:
            self.assertEqual( Session.objects.permitted(u).filter(pk=sesh.pk).exists()
                            , self.should_permit()
                            )
        except AssertionError as e:
            print "\n\n\n\nCaught AssertionError!"
            print "User UserGroup:                   \n%s" % pformat(ug)
            print "Session's Usergroups:             \n%s" % pformat(sesh.usergroups.all())
            print "Session's TaskGroup's UserGroups: \n%s" % pformat([(tg, tg.usergroups.all()) for tg in sesh.task_groups.all()])
            raise e

class UserRegular(UserType):
    def prepare_user_groups(self):
        u = User.objects.get(pk=2)
        return (u, u.ugroups.create(name="User's UG"))

class UserSuperuser(UserType):
    def prepare_user_groups(self):
        u = User.objects.get(pk=1)
        return (u, u.ugroups.create(name="User's UG"))

class UserAdmin(UserType):
    def prepare_user_groups(self):
        u = User.objects.get(pk=2)
        return (u, u.ugroups.create(name="User's UG", admin=True))

class SessionHasUG(SessionUGPossession):
    def prepare_session(self, ug):
        sesh = Session.objects.get(pk=1)
        sesh.usergroups.add(ug)
        sesh.usergroups.create(name="Random UG")  
        return sesh

class SessionHasNotUG(SessionUGPossession):
    def prepare_session(self, ug):
        sesh = Session.objects.get(pk=1)
        sesh.usergroups.create(name="Random UG")  
        return sesh

class AllTaskGroupsHaveUG(TaskGroupUGPossession):
    def prepare_task_groups(self, ug, s):
        for tg in s.task_groups.all():
            tg.usergroups.add(ug)

class OneTaskGroupHasNotUG(TaskGroupUGPossession):
    def prepare_task_groups(self, ug, s):
        for (i, tg) in enumerate(s.task_groups.all()):
            if i == 0:
                tg.usergroups.create(name=("UG for TG %d" % tg.pk))
            else:
                tg.usergroups.add(ug)

class PermittedSessionBuilder(SessionBuilderExistenceAndPermittedness):
    def maybe_prepare_sessionbuilder(self, ug, sesh):
        sb = SessionBuilder.objects.get(pk=1)
        sb.usergroups.add(ug)
        sb.usergroups.create(name="Random UG")  
        st = SessionTemplate.objects.get(pk=1)
        for tg in st.task_groups.all():
            tg.usergroups.add(ug)
        st.usergroups.add(ug)
        stf = SessionTemplateFrequency.objects.create( session_builder  = sb
                                                     , session_template = st
                                                     , frequency        = 1
                                                     )
        sesh.session_template_frequency = stf
        sesh.save()
        return sb

class NonPermittedSessionBuilder(SessionBuilderExistenceAndPermittedness):
    def maybe_prepare_sessionbuilder(self, ug, sesh):
        sb = SessionBuilder.objects.get(pk=1)
        sb.usergroups.create(name="Random UG")  
        st = SessionTemplate.objects.get(pk=1)
        stf = SessionTemplateFrequency.objects.create( session_builder  = sb
                                                     , session_template = st
                                                     , frequency        = 1
                                                     )
        sesh.session_template_frequency = stf
        return sb

class NoSessionBuilder(SessionBuilderExistenceAndPermittedness):
    def maybe_prepare_sessionbuilder(self, ug, sesh):
        pass




class UserRegular_SessionHasUG_AllTaskGroupsHaveUG_NoSessionBuilder(       TestCase, Test_SessionManager, UserRegular  , SessionHasUG,     AllTaskGroupsHaveUG, NoSessionBuilder):
    def should_permit(self):
        return True

class UserRegular_SessionHasUG_OneTaskGroupHasNotUG_NoSessionBuilder(      TestCase, Test_SessionManager, UserRegular  , SessionHasUG,     OneTaskGroupHasNotUG, NoSessionBuilder):
    def should_permit(self):
        return False

class UserRegular_SessionHasNotUG_AllTaskGroupsHaveUG_NoSessionBuilder(    TestCase, Test_SessionManager, UserRegular  , SessionHasNotUG,  AllTaskGroupsHaveUG, NoSessionBuilder):
    def should_permit(self):
        return False

class UserRegular_SessionHasNotUG_OneTaskGroupHasNotUG_NoSessionBuilder(   TestCase, Test_SessionManager, UserRegular  , SessionHasNotUG,  OneTaskGroupHasNotUG, NoSessionBuilder):
    def should_permit(self):
        return False

class UserAdmin_SessionHasUG_AllTaskGroupsHaveUG_NoSessionBuilder(         TestCase, Test_SessionManager, UserAdmin    , SessionHasUG,     AllTaskGroupsHaveUG, NoSessionBuilder):
    def should_permit(self):
        return True

class UserAdmin_SessionHasUG_OneTaskGroupHasNotUG_NoSessionBuilder(        TestCase, Test_SessionManager, UserAdmin    , SessionHasUG,     OneTaskGroupHasNotUG, NoSessionBuilder):
    def should_permit(self):
        return True

class UserAdmin_SessionHasNotUG_AllTaskGroupsHaveUG_NoSessionBuilder(      TestCase, Test_SessionManager, UserAdmin    , SessionHasNotUG,  AllTaskGroupsHaveUG, NoSessionBuilder):
    def should_permit(self):
        return True

class UserAdmin_SessionHasNotUG_OneTaskGroupHasNotUG_NoSessionBuilder(     TestCase, Test_SessionManager, UserAdmin    , SessionHasNotUG,  OneTaskGroupHasNotUG, NoSessionBuilder):
    def should_permit(self):
        return True

class UserSuperuser_SessionHasUG_AllTaskGroupsHaveUG_NoSessionBuilder(     TestCase, Test_SessionManager, UserSuperuser, SessionHasUG,     AllTaskGroupsHaveUG, NoSessionBuilder):
    def should_permit(self):
        return True

class UserSuperuser_SessionHasUG_OneTaskGroupHasNotUG_NoSessionBuilder(    TestCase, Test_SessionManager, UserSuperuser, SessionHasUG,     OneTaskGroupHasNotUG, NoSessionBuilder):
    def should_permit(self):
        return True

class UserSuperuser_SessionHasNotUG_AllTaskGroupsHaveUG_NoSessionBuilder(  TestCase, Test_SessionManager, UserSuperuser, SessionHasNotUG,  AllTaskGroupsHaveUG, NoSessionBuilder):
    def should_permit(self):
        return True

class UserSuperuser_SessionHasNotUG_OneTaskGroupHasNotUG_NoSessionBuilder( TestCase, Test_SessionManager, UserSuperuser, SessionHasNotUG,  OneTaskGroupHasNotUG, NoSessionBuilder):
    def should_permit(self):
        return True



class UserRegular_SessionHasUG_OneTaskGroupHasNotUG_PermittedSessionBuilder(      TestCase, Test_SessionManager, UserRegular  , SessionHasUG,     OneTaskGroupHasNotUG, PermittedSessionBuilder):
    def should_permit(self):
        return True

class UserRegular_SessionHasNotUG_AllTaskGroupsHaveUG_PermittedSessionBuilder(    TestCase, Test_SessionManager, UserRegular  , SessionHasNotUG,  AllTaskGroupsHaveUG, PermittedSessionBuilder):
    def should_permit(self):
        return True

class UserRegular_SessionHasNotUG_OneTaskGroupHasNotUG_PermittedSessionBuilder(   TestCase, Test_SessionManager, UserRegular  , SessionHasNotUG,  OneTaskGroupHasNotUG, PermittedSessionBuilder):
    def should_permit(self):
        return True

class UserAdmin_SessionHasUG_AllTaskGroupsHaveUG_PermittedSessionBuilder(         TestCase, Test_SessionManager, UserAdmin    , SessionHasUG,     AllTaskGroupsHaveUG, PermittedSessionBuilder):
    def should_permit(self):
        return True

class UserAdmin_SessionHasUG_OneTaskGroupHasNotUG_PermittedSessionBuilder(        TestCase, Test_SessionManager, UserAdmin    , SessionHasUG,     OneTaskGroupHasNotUG, PermittedSessionBuilder):
    def should_permit(self):
        return True

class UserAdmin_SessionHasNotUG_AllTaskGroupsHaveUG_PermittedSessionBuilder(      TestCase, Test_SessionManager, UserAdmin    , SessionHasNotUG,  AllTaskGroupsHaveUG, PermittedSessionBuilder):
    def should_permit(self):
        return True

class UserAdmin_SessionHasNotUG_OneTaskGroupHasNotUG_PermittedSessionBuilder(     TestCase, Test_SessionManager, UserAdmin    , SessionHasNotUG,  OneTaskGroupHasNotUG, PermittedSessionBuilder):
    def should_permit(self):
        return True

class UserSuperuser_SessionHasUG_AllTaskGroupsHaveUG_PermittedSessionBuilder(     TestCase, Test_SessionManager, UserSuperuser, SessionHasUG,     AllTaskGroupsHaveUG, PermittedSessionBuilder):
    def should_permit(self):
        return True

class UserSuperuser_SessionHasUG_OneTaskGroupHasNotUG_PermittedSessionBuilder(    TestCase, Test_SessionManager, UserSuperuser, SessionHasUG,     OneTaskGroupHasNotUG, PermittedSessionBuilder):
    def should_permit(self):
        return True

class UserSuperuser_SessionHasNotUG_AllTaskGroupsHaveUG_PermittedSessionBuilder(  TestCase, Test_SessionManager, UserSuperuser, SessionHasNotUG,  AllTaskGroupsHaveUG, PermittedSessionBuilder):
    def should_permit(self):
        return True

class UserSuperuser_SessionHasNotUG_OneTaskGroupHasNotUG_PermittedSessionBuilder( TestCase, Test_SessionManager, UserSuperuser, SessionHasNotUG,  OneTaskGroupHasNotUG, PermittedSessionBuilder):
    def should_permit(self):
        return True


class UserRegular_SessionHasUG_AllTaskGroupsHaveUG_NonPermittedSessionBuilder(       TestCase, Test_SessionManager, UserRegular  , SessionHasUG,     AllTaskGroupsHaveUG, NonPermittedSessionBuilder):
    def should_permit(self):
        return True

class UserRegular_SessionHasUG_OneTaskGroupHasNotUG_NonPermittedSessionBuilder(      TestCase, Test_SessionManager, UserRegular  , SessionHasUG,     OneTaskGroupHasNotUG, NonPermittedSessionBuilder):
    def should_permit(self):
        return False

class UserRegular_SessionHasNotUG_AllTaskGroupsHaveUG_NonPermittedSessionBuilder(    TestCase, Test_SessionManager, UserRegular  , SessionHasNotUG,  AllTaskGroupsHaveUG, NonPermittedSessionBuilder):
    def should_permit(self):
        return False

class UserRegular_SessionHasNotUG_OneTaskGroupHasNotUG_NonPermittedSessionBuilder(   TestCase, Test_SessionManager, UserRegular  , SessionHasNotUG,  OneTaskGroupHasNotUG, NonPermittedSessionBuilder):
    def should_permit(self):
        return False

class UserAdmin_SessionHasUG_AllTaskGroupsHaveUG_NonPermittedSessionBuilder(         TestCase, Test_SessionManager, UserAdmin    , SessionHasUG,     AllTaskGroupsHaveUG, NonPermittedSessionBuilder):
    def should_permit(self):
        return True

class UserAdmin_SessionHasUG_OneTaskGroupHasNotUG_NonPermittedSessionBuilder(        TestCase, Test_SessionManager, UserAdmin    , SessionHasUG,     OneTaskGroupHasNotUG, NonPermittedSessionBuilder):
    def should_permit(self):
        return True

class UserAdmin_SessionHasNotUG_AllTaskGroupsHaveUG_NonPermittedSessionBuilder(      TestCase, Test_SessionManager, UserAdmin    , SessionHasNotUG,  AllTaskGroupsHaveUG, NonPermittedSessionBuilder):
    def should_permit(self):
        return True

class UserAdmin_SessionHasNotUG_OneTaskGroupHasNotUG_NonPermittedSessionBuilder(     TestCase, Test_SessionManager, UserAdmin    , SessionHasNotUG,  OneTaskGroupHasNotUG, NonPermittedSessionBuilder):
    def should_permit(self):
        return True

class UserSuperuser_SessionHasUG_AllTaskGroupsHaveUG_NonPermittedSessionBuilder(     TestCase, Test_SessionManager, UserSuperuser, SessionHasUG,     AllTaskGroupsHaveUG, NonPermittedSessionBuilder):
    def should_permit(self):
        return True

class UserSuperuser_SessionHasUG_OneTaskGroupHasNotUG_NonPermittedSessionBuilder(    TestCase, Test_SessionManager, UserSuperuser, SessionHasUG,     OneTaskGroupHasNotUG, NonPermittedSessionBuilder):
    def should_permit(self):
        return True

class UserSuperuser_SessionHasNotUG_AllTaskGroupsHaveUG_NonPermittedSessionBuilder(  TestCase, Test_SessionManager, UserSuperuser, SessionHasNotUG,  AllTaskGroupsHaveUG, NonPermittedSessionBuilder):
    def should_permit(self):
        return True

class UserSuperuser_SessionHasNotUG_OneTaskGroupHasNotUG_NonPermittedSessionBuilder( TestCase, Test_SessionManager, UserSuperuser, SessionHasNotUG,  OneTaskGroupHasNotUG, NonPermittedSessionBuilder):
    def should_permit(self):
        return True
