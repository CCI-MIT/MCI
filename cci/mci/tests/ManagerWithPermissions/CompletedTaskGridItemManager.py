from django.test import TestCase
from mci.models import CompletedTaskGridItem, Session, UserGroup
from django.contrib.auth.models import User
from pprint import pformat

class UserType(object):
    def prepare_user_groups(self):
        raise NotImplementedError
class SessionUGPossession(object):
    def prepare_completedtaskgriditem(self, ug):
        raise NotImplementedError
class TaskGroupUGPossession(object):
    def prepare_task_groups(self, ug, ctgi):
        raise NotImplementedError

class Test_SessionManager(UserType, SessionUGPossession, TaskGroupUGPossession):
    fixtures = ['test', 'users']
    def test_permitted(self):
        (u, ug) = self.prepare_user_groups()
        ctgi = self.prepare_completedtaskgriditem(ug)
        self.prepare_task_groups(ug, ctgi)
        try:
            self.assertEqual( CompletedTaskGridItem.objects.permitted(u).filter(pk=ctgi.pk).exists()
                            , self.should_permit()
                            )
        except AssertionError as e:
            print "Caught AssertionError!"
            print "User's UserGroup:                                 \n%s" % pformat(ug)
            print "CompletedTask's Session's Usergroups:             \n%s" % pformat(s.usergroups.all())
            print "CompletedTask's Session's TaskGroups' UserGroups: \n%s" % pformat([(tg, tg.usergroups.all()) for tg in ctgi.completed_task.session.task_groups.all()])
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
    def prepare_completedtaskgriditem(self, ug):
        s = Session.objects.get(pk=27)
        s.usergroups.add(ug)
        s.usergroups.create(name="Random UG")  
        return s.completedtask_set.all()[0].completedtaskgriditem_set.all()[0]

class SessionHasNotUG(SessionUGPossession):
    def prepare_completedtaskgriditem(self, ug):
        s = Session.objects.get(pk=27)
        s.usergroups.create(name="Random UG")  
        return s.completedtask_set.all()[0].completedtaskgriditem_set.all()[0]

class AllTaskGroupsHaveUG(TaskGroupUGPossession):
    def prepare_task_groups(self, ug, ctgi):
        for tg in ctgi.completed_task.session.task_groups.all():
            tg.usergroups.add(ug)

class OneTaskGroupHasNotUG(TaskGroupUGPossession):
    def prepare_task_groups(self, ug, ctgi):
        for (i, tg) in enumerate(ctgi.completed_task.session.task_groups.all()):
            if i == 0:
                tg.usergroups.create(name=("UG for TG %d" % tg.pk))
            else:
                tg.usergroups.add(ug)


class UserRegular_SessionHasUG_AllTaskGroupsHaveUG(       TestCase, Test_SessionManager, UserRegular,   SessionHasUG,     AllTaskGroupsHaveUG):
    def should_permit(self):
        return True

class UserRegular_SessionHasUG_OneTaskGroupHasNotUG(      TestCase, Test_SessionManager, UserRegular,   SessionHasUG,     OneTaskGroupHasNotUG):
    def should_permit(self):
        return False

class UserRegular_SessionHasNotUG_AllTaskGroupsHaveUG(    TestCase, Test_SessionManager, UserRegular,   SessionHasNotUG,  AllTaskGroupsHaveUG):
    def should_permit(self):
        return False

class UserRegular_SessionHasNotUG_OneTaskGroupHasNotUG(   TestCase, Test_SessionManager, UserRegular,   SessionHasNotUG,  OneTaskGroupHasNotUG):
    def should_permit(self):
        return False

class UserAdmin_SessionHasUG_AllTaskGroupsHaveUG(         TestCase, Test_SessionManager, UserAdmin,     SessionHasUG,     AllTaskGroupsHaveUG):
    def should_permit(self):
        return True

class UserAdmin_SessionHasUG_OneTaskGroupHasNotUG(        TestCase, Test_SessionManager, UserAdmin,     SessionHasUG,     OneTaskGroupHasNotUG):
    def should_permit(self):
        return True

class UserAdmin_SessionHasNotUG_AllTaskGroupsHaveUG(      TestCase, Test_SessionManager, UserAdmin,     SessionHasNotUG,  AllTaskGroupsHaveUG):
    def should_permit(self):
        return True

class UserAdmin_SessionHasNotUG_OneTaskGroupHasNotUG(     TestCase, Test_SessionManager, UserAdmin,     SessionHasNotUG,  OneTaskGroupHasNotUG):
    def should_permit(self):
        return True

class UserSuperuser_SessionHasUG_AllTaskGroupsHaveUG(     TestCase, Test_SessionManager, UserSuperuser, SessionHasUG,     AllTaskGroupsHaveUG):
    def should_permit(self):
        return True

class UserSuperuser_SessionHasUG_OneTaskGroupHasNotUG(    TestCase, Test_SessionManager, UserSuperuser, SessionHasUG,     OneTaskGroupHasNotUG):
    def should_permit(self):
        return True

class UserSuperuser_SessionHasNotUG_AllTaskGroupsHaveUG(  TestCase, Test_SessionManager, UserSuperuser, SessionHasNotUG,  AllTaskGroupsHaveUG):
    def should_permit(self):
        return True

class UserSuperuser_SessionHasNotUG_OneTaskGroupHasNotUG( TestCase, Test_SessionManager, UserSuperuser, SessionHasNotUG,  OneTaskGroupHasNotUG):
    def should_permit(self):
        return True

