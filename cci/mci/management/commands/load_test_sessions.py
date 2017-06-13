from django.core.management.base import BaseCommand, CommandError
from mci.models import Task, TaskGroup, Session, Subject, SubjectCountry
import csv, os
from datetime import datetime, timedelta


class Command(BaseCommand):
    args = """<tasks_csv_filename subjects_csv_filename seconds_to_start num_sessions subjects_per_session>"""
    help = 'Creates Tasks, Sessions and Subjects for load testing.'

    def handle(self, *args, **options):

        thisdir = os.path.dirname(os.path.realpath(__file__))

        try:
            tasks_csv = open(thisdir + "/load_test_csvs/" + args[0], "rU")
            task_rows = list(csv.DictReader(tasks_csv))
        except Exception:
            self.stdout.write("Failed to open Tasks CSV! \n")
            exit(1)
        
        try:
            subjects_csv = open(thisdir + "/load_test_csvs/" + args[1], "rU")
            subject_rows = list(csv.DictReader(subjects_csv))
        except Exception:
            self.stdout.write("Failed to open Subjects CSV! \n")
            exit(1)
        
        try:
            start_datetime = datetime.now() + timedelta(seconds=int(args[2]))
        except Exception:
            self.stdout.write("""Failed to get 'seconds before sessions' scheduled start time' from 3rd command-line argument! \n""")
            exit(1)

        try:
            num_sessions = int(args[3])
        except Exception:
            self.stdout.write("""Failed to get "# parallel sessions" from 4th command-line argument! \n""")
            exit(1)

        try:
            subjects_per_session = int(args[4])
        except Exception:
            self.stdout.write("""Failed to get "# subjects per session" from 5th command-line argument! \n""")
            exit(1)

        waiting_room_time = 5400   # 90 minutes
        intro_time = 10
        done_time = 25

        timestamp = datetime.now()

        task_group = TaskGroup.objects.create(
            name="Load Testing %s" % timestamp)
        for task_row in task_rows:
            task = Task.objects.create(
                name="Load Testing %s %s" % (timestamp, task_row['name']),
                time_before_play=task_row['time_before_play'],
                time_between_rounds=task_row['time_between_rounds'],
                time_unmatched_pairs_remain_faceup=task_row['time_unmatched_pairs_remain_faceup'],
                pairs_in_generated_round=task_row['pairs_in_generated_round'], 
                instructions_time=task_row['instructions_time'], 
                primer_time=task_row['primer_time'], 
                interaction_time=task_row['interaction_time'], 
                mousemove_interval=task_row['mousemove_interval'],
                # Automatic
                task_group=task_group,
                task_type='C',
                instructions='Instructions: This task is for load testing.  Why are you here, dummy?',
                primer='Primer: This task is for load testing!  How many times I gotta tell you?',
            )

        for session_num in range(num_sessions):
            session = Session.objects.create(
                load_test=True,
                name="Load Testing %s %s" % (timestamp, session_num),
                min_group_size=subjects_per_session,
                max_group_size=subjects_per_session,
                waiting_room_time=waiting_room_time,
                introduction_time=intro_time,
                done_time=done_time,
                introduction_text="""Welcome to this load testing Session!""",
                done_text="""This has been a load testing Session!""",
                start_datetime=start_datetime,
                status='P',
                done_redirect_url="http://www.yahoo.com",
                disguise_subjects=True,
            )
            self.stdout.write('Successfully created %s \n' % session)
            session.task_groups.add(task_group)
            for subject_row in subject_rows:
                subject = Subject.objects.create(
                    external_id="%i_%s" % (session_num, subject_row['external_id_suffix']),
                    display_name=subject_row['display_name'],
                    country=SubjectCountry.objects.get(name=subject_row['country_name']),
                    consent_and_individual_tests_completed=True,
                    in_waiting_room=False,
                    session=session,
                )
                self.stdout.write('Successfully created %s \n' % subject)
