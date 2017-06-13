from django.core.management.base import BaseCommand, CommandError
from pprint import * 
from django.contrib.auth.models import User
from mci.models import UserProfile
from django.db.models import Q

def users_without_profiles():
    profiles = UserProfile.objects.all()
    users_of_profiles = [p.user.pk for p in list(profiles)]
    return User.objects.filter(~Q(pk__in=users_of_profiles))

class Command(BaseCommand):
    def handle(self, *args, **options):
        uwp = users_without_profiles()
        self.stdout.write("Users without UserProfiles before run: %d" % uwp.count())

        for user in uwp:
            UserProfile.objects.create(user=user)

        self.stdout.write("Users without UserProfiles after run: %d" % users_without_profiles().count())
