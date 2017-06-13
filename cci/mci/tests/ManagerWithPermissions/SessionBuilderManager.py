from django.test import TestCase
from mci.models import SessionBuilder, SessionTemplate, SessionTemplateFrequency, UserGroup
from django.contrib.auth.models import User
from pprint import pformat

class UserType(object):
    def prepare_user_groups(self):
        raise NotImplementedError
class SessionBuilderUGPossession(object):
    def prepare_sessionbuilder(self, ug):
        raise NotImplementedError
class SessionTemplatePermission(object):
    def prepare_session_templates(self, ug, s):
        raise NotImplementedError

class Test_SessionBuilderManager(UserType, SessionBuilderUGPossession, SessionTemplatePermission):
    fixtures = ['test', 'users']
    def test_permitted(self):
        (u, ug) = self.prepare_user_groups()
        sb = self.prepare_sessionbuilder(ug)
        self.prepare_session_templates(ug, sb)
        try:
            self.assertEqual( SessionBuilder.objects.permitted(u).filter(pk=sb.pk).exists()
                            , self.should_permit()
                            )
        except AssertionError as e:
            print "Caught AssertionError!"
            print "User UserGroup:                                \n%s" % pformat(ug)
            print "SessionBuilder's Usergroups:                   \n%s" % pformat(sb.usergroups.all())
            print "SessionBuilder's SessionTemplate's UserGroups: \n%s" % pformat([(st, st.usergroups.all()) for st in sb.session_templates.all()])
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

class SessionBuilderHasUG(SessionBuilderUGPossession):
    def prepare_sessionbuilder(self, ug):
        sb = SessionBuilder.objects.get(pk=1)
        sb.usergroups.add(ug)
        sb.usergroups.create(name="Random UG")  
        return sb

class SessionBuilderHasNotUG(SessionBuilderUGPossession):
    def prepare_sessionbuilder(self, ug):
        sb = SessionBuilder.objects.get(pk=1)
        sb.usergroups.create(name="Random UG")  
        return sb

class AllSessionTemplatesHaveUG(SessionTemplatePermission):
    def prepare_session_templates(self, ug, sb):
        for i in range(3):
            st = SessionTemplate.objects.create(name = "Test ST %d" % i)
            SessionTemplateFrequency.objects.create( session_builder  = sb
                                                   , session_template = st
                                                   , frequency        = 1
                                                   )
            st.usergroups.add(ug)

class OneSessionTemplateHasNotUG(SessionTemplatePermission):
    def prepare_session_templates(self, ug, sb):
        for i in range(3):
            st = SessionTemplate.objects.create(name = "Test ST %d" % i)
            SessionTemplateFrequency.objects.create( session_builder  = sb
                                                   , session_template = st
                                                   , frequency        = 1
                                                   )
            if i == 0:
                st.usergroups.create(name=("UG for ST %d" % st.pk))
            else:
                st.usergroups.add(ug)


class UserRegular_SessionBuilderHasUG_AllSessionTemplatesHaveUG(       TestCase, Test_SessionBuilderManager, UserRegular,   SessionBuilderHasUG,     AllSessionTemplatesHaveUG):
    def should_permit(self):
        return True

class UserRegular_SessionBuilderHasUG_OneSessionTemplateHasNotUG(      TestCase, Test_SessionBuilderManager, UserRegular,   SessionBuilderHasUG,     OneSessionTemplateHasNotUG):
    def should_permit(self):
        return False

class UserRegular_SessionBuilderHasNotUG_AllSessionTemplatesHaveUG(    TestCase, Test_SessionBuilderManager, UserRegular,   SessionBuilderHasNotUG,  AllSessionTemplatesHaveUG):
    def should_permit(self):
        return False

class UserRegular_SessionBuilderHasNotUG_OneSessionTemplateHasNotUG(   TestCase, Test_SessionBuilderManager, UserRegular,   SessionBuilderHasNotUG,  OneSessionTemplateHasNotUG):
    def should_permit(self):
        return False

class UserAdmin_SessionBuilderHasUG_AllSessionTemplatesHaveUG(         TestCase, Test_SessionBuilderManager, UserAdmin,     SessionBuilderHasUG,     AllSessionTemplatesHaveUG):
    def should_permit(self):
        return True

class UserAdmin_SessionBuilderHasUG_OneSessionTemplateHasNotUG(        TestCase, Test_SessionBuilderManager, UserAdmin,     SessionBuilderHasUG,     OneSessionTemplateHasNotUG):
    def should_permit(self):
        return True

class UserAdmin_SessionBuilderHasNotUG_AllSessionTemplatesHaveUG(      TestCase, Test_SessionBuilderManager, UserAdmin,     SessionBuilderHasNotUG,  AllSessionTemplatesHaveUG):
    def should_permit(self):
        return True

class UserAdmin_SessionBuilderHasNotUG_OneSessionTemplateHasNotUG(     TestCase, Test_SessionBuilderManager, UserAdmin,     SessionBuilderHasNotUG,  OneSessionTemplateHasNotUG):
    def should_permit(self):
        return True

class UserSuperuser_SessionBuilderHasUG_AllSessionTemplatesHaveUG(     TestCase, Test_SessionBuilderManager, UserSuperuser, SessionBuilderHasUG,     AllSessionTemplatesHaveUG):
    def should_permit(self):
        return True

class UserSuperuser_SessionBuilderHasUG_OneSessionTemplateHasNotUG(    TestCase, Test_SessionBuilderManager, UserSuperuser, SessionBuilderHasUG,     OneSessionTemplateHasNotUG):
    def should_permit(self):
        return True

class UserSuperuser_SessionBuilderHasNotUG_AllSessionTemplatesHaveUG(  TestCase, Test_SessionBuilderManager, UserSuperuser, SessionBuilderHasNotUG,  AllSessionTemplatesHaveUG):
    def should_permit(self):
        return True

class UserSuperuser_SessionBuilderHasNotUG_OneSessionTemplateHasNotUG( TestCase, Test_SessionBuilderManager, UserSuperuser, SessionBuilderHasNotUG,  OneSessionTemplateHasNotUG):
    def should_permit(self):
        return True
