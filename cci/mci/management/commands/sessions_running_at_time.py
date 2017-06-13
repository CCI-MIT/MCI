from django.core.management.base import BaseCommand, CommandError
from mci.models import *
from django.db.models import F
from pprint import * 
from datetime import datetime
import os

class Command(BaseCommand):

    def handle(self, *args, **options):

        datetime_str = args[0]
        try:
            dt = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            self.stdout.write("\n Argument '%s' does not follow format '%Y-%m-%d %H:%M:%S'." % datetime_str)
            exit(1)

        cts = CompletedTask.objects.filter( expected_start_time__lte=dt
                                          , expected_finish_time__gte=dt
                                          )
        self.stdout.write("\nCompletedTasks that were in progress -- either instructions, or primer, or workspace -- at this time: \n%s"
            % pformat([(ct.__unicode__(), ct.pk, (ct.session.__unicode__(), ct.session.pk)) for ct in cts]))

        # The 'config stage' is the 25 seconds prior to the session's recorder
        # 'start_datetime' attribute, because the first step of configuration is
        # to set 'start_datetime' to 25 seconds hence, whatever it was before.
        sessions_in_config_stage = Session.objects.filter( 
            start_datetime__lte=(dt + timedelta(seconds=25))
          , start_datetime__gte=dt
          )

        self.stdout.write("\nSessions that were configuring, or had just configured, at this time: \n%s" 
            % pformat([(s.__unicode__(), s.pk) for s in sessions_in_config_stage]))

        _sessions_in_intro_stage = Session.objects.filter( 
            start_datetime__lte=dt
          )
        sessions_in_intro_stage = filter(lambda s: s.intro_end_time() >= dt, _sessions_in_intro_stage)

        self.stdout.write("\nSessions that were showing the Intro screen at this time: \n%s" 
            % pformat([(s.__unicode__(), s.pk) for s in sessions_in_intro_stage]))
