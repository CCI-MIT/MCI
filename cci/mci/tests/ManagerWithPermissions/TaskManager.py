from django.test import TestCase
from mci.models import Task, UserGroup
from django.contrib.auth.models import User
from pprint import pformat

class UserType(object):
    def prepare_user_groups(self):
        raise NotImplementedError
class TaskGroupUGPossession(object):
    def prepare_task(self, ug):
        raise NotImplementedError

class Test_TaskManager(UserType, TaskGroupUGPossession):
    fixtures = ['test', 'users']
    def test_permitted(self):
        (u, ug) = self.prepare_user_groups()
        t = self.prepare_task(ug)
        try:
            self.assertEqual( Task.objects.permitted(u).filter(pk=t.pk).exists()
                            , self.should_permit()
                            )
        except AssertionError as e:
            print "Caught AssertionError!"
            print "User UserGroup:       \n%s" % pformat(ug)
            print "TaskGroup UserGroups: \n%s" % pformat(t.task_group.usergroups.all())
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

class TaskGroupHasUG(TaskGroupUGPossession):
    def prepare_task(self, ug):
        obj = Task.objects.get(pk=1)
        obj.task_group.usergroups.add(ug)
        obj.task_group.usergroups.create(name="Random UG")  
        return obj

class TaskGroupHasNotUG(TaskGroupUGPossession):
    def prepare_task(self, ug):
        obj = Task.objects.get(pk=1)
        obj.task_group.usergroups.create(name="Random UG")  
        return obj


class TC_TaskManager_UserRegular_TaskGroupHasUG(      TestCase, Test_TaskManager, UserRegular,   TaskGroupHasUG):
    def should_permit(self):
        return True

class TC_TaskManager_UserRegular_TaskGroupHasNotUG(   TestCase, Test_TaskManager, UserRegular,   TaskGroupHasNotUG):
    def should_permit(self):
        return False

class TC_TaskManager_UserAdmin_TaskGroupHasUG(        TestCase, Test_TaskManager, UserAdmin,     TaskGroupHasUG):
    def should_permit(self):
        return True

class TC_TaskManager_UserAdmin_TaskGroupHasNotUG(     TestCase, Test_TaskManager, UserAdmin,     TaskGroupHasNotUG):
    def should_permit(self):
        return True

class TC_TaskManager_UserSuperuser_TaskGroupHasUG(    TestCase, Test_TaskManager, UserSuperuser, TaskGroupHasUG):
    def should_permit(self):
        return True

class TC_TaskManager_UserSuperuser_TaskGroupHasNotUG( TestCase, Test_TaskManager, UserSuperuser, TaskGroupHasNotUG):
    def should_permit(self):
        return True
