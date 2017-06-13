from django.test import TestCase
from mci.models import TaskGroup, UserGroup
from django.contrib.auth.models import User
from pprint import pformat

class UserType(object):
    def prepare_user_groups(self):
        raise NotImplementedError
class TaskGroupUGPossession(object):
    def prepare_task_group(self, ug):
        raise NotImplementedError

class Test_TaskGroupManager(UserType, TaskGroupUGPossession):
    fixtures = ['test', 'users']
    def test_permitted(self):
        (u, ug) = self.prepare_user_groups()
        tg = self.prepare_task_group(ug)
        try:
            self.assertEqual( TaskGroup.objects.permitted(u).filter(pk=tg.pk).exists()
                            , self.should_permit()
                            )
        except AssertionError as e:
            print "Caught AssertionError!"
            print "User UserGroup:       \n%s" % pformat(ug)
            print "TaskGroup UserGroups: \n%s" % pformat(tg.usergroups.all())
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
    def prepare_task_group(self, ug):
        obj = TaskGroup.objects.get(pk=1)
        obj.usergroups.add(ug)
        obj.usergroups.create(name="Random UG")  
        return obj

class TaskGroupHasNotUG(TaskGroupUGPossession):
    def prepare_task_group(self, ug):
        obj = TaskGroup.objects.get(pk=1)
        obj.usergroups.create(name="Random UG")  
        return obj


class TC_TaskGroupManager_UserRegular_TaskGroupHasUG(      TestCase, Test_TaskGroupManager, UserRegular,   TaskGroupHasUG):
    def should_permit(self):
        return True

class TC_TaskGroupManager_UserRegular_TaskGroupHasNotUG(   TestCase, Test_TaskGroupManager, UserRegular,   TaskGroupHasNotUG):
    def should_permit(self):
        return False

class TC_TaskGroupManager_UserAdmin_TaskGroupHasUG(        TestCase, Test_TaskGroupManager, UserAdmin,     TaskGroupHasUG):
    def should_permit(self):
        return True

class TC_TaskGroupManager_UserAdmin_TaskGroupHasNotUG(     TestCase, Test_TaskGroupManager, UserAdmin,     TaskGroupHasNotUG):
    def should_permit(self):
        return True

class TC_TaskGroupManager_UserSuperuser_TaskGroupHasUG(    TestCase, Test_TaskGroupManager, UserSuperuser, TaskGroupHasUG):
    def should_permit(self):
        return True

class TC_TaskGroupManager_UserSuperuser_TaskGroupHasNotUG( TestCase, Test_TaskGroupManager, UserSuperuser, TaskGroupHasNotUG):
    def should_permit(self):
        return True
