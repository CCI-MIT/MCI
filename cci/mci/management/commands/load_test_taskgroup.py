from django.core.management.base import BaseCommand, CommandError
from mci.models import Task, TaskGroup, Session, Subject, SubjectCountry
import csv, os
from datetime import datetime, timedelta


class Command(BaseCommand):
    args = """<tasks_csv_filename>"""
    help = 'Creates Task Group for SessionBuilder load testing.'

    def handle(self, *args, **options):

        thisdir = os.path.dirname(os.path.realpath(__file__))

        try:
            tasks_csv = open(thisdir + "/load_test_csvs/" + args[0], "rU")
            task_rows = list(csv.DictReader(tasks_csv))
        except Exception:
            self.stdout.write("Failed to open Tasks CSV! \n")
            exit(1)

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
