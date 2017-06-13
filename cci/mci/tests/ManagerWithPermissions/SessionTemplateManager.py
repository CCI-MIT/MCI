from django.test import TestCase
from mci.models import Session, SessionTemplate, UserGroup
from django.contrib.auth.models import User
from pprint import pformat

class UserType(object):
    def prepare_user_groups(self):
        raise NotImplementedError
class SessionTemplateUGPossession(object):
    def prepare_sessiontemplate(self, ug):
        raise NotImplementedError
class TaskGroupUGPossession(object):
    def prepare_task_groups(self, ug, s):
        raise NotImplementedError

class Test_SessionTemplateManager(UserType, SessionTemplateUGPossession, TaskGroupUGPossession):
    fixtures = ['test', 'users']
    def test_permitted(self):
        (u, ug) = self.prepare_user_groups()
        st = self.prepare_sessiontemplate(ug)
        self.prepare_task_groups(ug, st)
        try:
            self.assertEqual( SessionTemplate.objects.permitted(u).filter(pk=st.pk).exists()
                            , self.should_permit()
                            )
        except AssertionError as e:
            print "Caught AssertionError!"
            print "User UserGroup:                           \n%s" % pformat(ug)
            print "SessionTemplate's Usergroups:             \n%s" % pformat(st.usergroups.all())
            print "SessionTemplate's TaskGroup's UserGroups: \n%s" % pformat([(tg, tg.usergroups.all()) for tg in st.task_groups.all()])
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

class SessionTemplateHasUG(SessionTemplateUGPossession):
    def prepare_sessiontemplate(self, ug):
        st = SessionTemplate.objects.get(pk=1)
        st.usergroups.add(ug)
        st.usergroups.create(name="Random UG")  
        return st

class SessionTemplateHasNotUG(SessionTemplateUGPossession):
    def prepare_sessiontemplate(self, ug):
        st = SessionTemplate.objects.get(pk=1)
        st.usergroups.create(name="Random UG")  
        return st

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


class UserRegular_SessionTemplateHasUG_AllTaskGroupsHaveUG(       TestCase, Test_SessionTemplateManager, UserRegular  , SessionTemplateHasUG,     AllTaskGroupsHaveUG):
    def should_permit(self):
        return True

class UserRegular_SessionTemplateHasUG_OneTaskGroupHasNotUG(      TestCase, Test_SessionTemplateManager, UserRegular  , SessionTemplateHasUG,     OneTaskGroupHasNotUG):
    def should_permit(self):
        return False

class UserRegular_SessionTemplateHasNotUG_AllTaskGroupsHaveUG(    TestCase, Test_SessionTemplateManager, UserRegular  , SessionTemplateHasNotUG,  AllTaskGroupsHaveUG):
    def should_permit(self):
        return False

class UserRegular_SessionTemplateHasNotUG_OneTaskGroupHasNotUG(   TestCase, Test_SessionTemplateManager, UserRegular  , SessionTemplateHasNotUG,  OneTaskGroupHasNotUG):
    def should_permit(self):
        return False

class UserAdmin_SessionTemplateHasUG_AllTaskGroupsHaveUG(         TestCase, Test_SessionTemplateManager, UserAdmin    , SessionTemplateHasUG,     AllTaskGroupsHaveUG):
    def should_permit(self):
        return True

class UserAdmin_SessionTemplateHasUG_OneTaskGroupHasNotUG(        TestCase, Test_SessionTemplateManager, UserAdmin    , SessionTemplateHasUG,     OneTaskGroupHasNotUG):
    def should_permit(self):
        return True

class UserAdmin_SessionTemplateHasNotUG_AllTaskGroupsHaveUG(      TestCase, Test_SessionTemplateManager, UserAdmin    , SessionTemplateHasNotUG,  AllTaskGroupsHaveUG):
    def should_permit(self):
        return True

class UserAdmin_SessionTemplateHasNotUG_OneTaskGroupHasNotUG(     TestCase, Test_SessionTemplateManager, UserAdmin    , SessionTemplateHasNotUG,  OneTaskGroupHasNotUG):
    def should_permit(self):
        return True

class UserSuperuser_SessionTemplateHasUG_AllTaskGroupsHaveUG(     TestCase, Test_SessionTemplateManager, UserSuperuser, SessionTemplateHasUG,     AllTaskGroupsHaveUG):
    def should_permit(self):
        return True

class UserSuperuser_SessionTemplateHasUG_OneTaskGroupHasNotUG(    TestCase, Test_SessionTemplateManager, UserSuperuser, SessionTemplateHasUG,     OneTaskGroupHasNotUG):
    def should_permit(self):
        return True

class UserSuperuser_SessionTemplateHasNotUG_AllTaskGroupsHaveUG(  TestCase, Test_SessionTemplateManager, UserSuperuser, SessionTemplateHasNotUG,  AllTaskGroupsHaveUG):
    def should_permit(self):
        return True

class UserSuperuser_SessionTemplateHasNotUG_OneTaskGroupHasNotUG( TestCase, Test_SessionTemplateManager, UserSuperuser, SessionTemplateHasNotUG,  OneTaskGroupHasNotUG):
    def should_permit(self):
        return True
