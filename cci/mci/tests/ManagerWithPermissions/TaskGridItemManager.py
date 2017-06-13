from django.test import TestCase
from mci.models import TaskGridItem, UserGroup
from django.contrib.auth.models import User
from pprint import pformat

class UserType(object):
    def prepare_user_groups(self):
        raise NotImplementedError
class TaskGroupUGPossession(object):
    def prepare_task_grid_item(self, ug):
        raise NotImplementedError

class Test_TaskGridItemManager(UserType, TaskGroupUGPossession):
    fixtures = ['test', 'users']
    def test_permitted(self):
        (u, ug) = self.prepare_user_groups()
        tgi = self.prepare_task_grid_item(ug)
        try:
            self.assertEqual( TaskGridItem.objects.permitted(u).filter(pk=tgi.pk).exists()
                            , self.should_permit()
                            )
        except AssertionError as e:
            print "Caught AssertionError!"
            print "User UserGroup:            \n%s" % pformat(ug)
            print "Task TaskGroup UserGroups: \n%s" % pformat(tgi.task.task_group.usergroups.all())
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
    def prepare_task_grid_item(self, ug):
        obj = TaskGridItem.objects.get(pk=1)
        obj.task.task_group.usergroups.add(ug)
        obj.task.task_group.usergroups.create(name="Random UG")  
        return obj

class TaskGroupHasNotUG(TaskGroupUGPossession):
    def prepare_task_grid_item(self, ug):
        obj = TaskGridItem.objects.get(pk=1)
        obj.task.task_group.usergroups.create(name="Random UG")  
        return obj


class UserRegular_TaskGroupHasUG(      TestCase, Test_TaskGridItemManager, UserRegular,   TaskGroupHasUG):
    def should_permit(self):
        return True

class UserRegular_TaskGroupHasNotUG(   TestCase, Test_TaskGridItemManager, UserRegular,   TaskGroupHasNotUG):
    def should_permit(self):
        return False

class UserAdmin_TaskGroupHasUG(        TestCase, Test_TaskGridItemManager, UserAdmin,     TaskGroupHasUG):
    def should_permit(self):
        return True

class UserAdmin_TaskGroupHasNotUG(     TestCase, Test_TaskGridItemManager, UserAdmin,     TaskGroupHasNotUG):
    def should_permit(self):
        return True

class UserSuperuser_TaskGroupHasUG(    TestCase, Test_TaskGridItemManager, UserSuperuser, TaskGroupHasUG):
    def should_permit(self):
        return True

class UserSuperuser_TaskGroupHasNotUG( TestCase, Test_TaskGridItemManager, UserSuperuser, TaskGroupHasNotUG):
    def should_permit(self):
        return True
