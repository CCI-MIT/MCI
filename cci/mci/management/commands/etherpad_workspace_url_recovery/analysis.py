from django.core.management.base import BaseCommand, CommandError
from mci.models import CompletedTask, Pad
from django.db.models import F
import sys, os, MySQLdb, MySQLdb.cursors, json
from datetime import datetime, timedelta
import re

class Command(BaseCommand):
    args = ""
    help = ''

    def handle(self, *args, **options):

        pads = Pad.objects.all()

        nums_of_incident_cts = {}
        for pad in pads:

            #if pad.event_distribution:
            #    print sorted(json.loads(pad.event_distribution).items())

            n_cts = len(pad.incident_cts.all())
            # Initialize, if necessary, the key for our data about the Pads
            # that overlap with n_cts CompletedTasks.
            if not n_cts in nums_of_incident_cts:
                nums_of_incident_cts[n_cts] = {
                    'n_pads': 0,
                    'max_events_per_pad': {
                        0: 0,
                        1: 0,
                        3: 0,
                        5: 0,
                        10: 0,
                        20: 0,
                        30: 0,
                        1000000: 0,
                    },
                    'timespans': [],
                    'start_times': [],
                }
            # Count the current pad as one more that overlaps with n_cts
            # CompletedTasks.
            nums_of_incident_cts[n_cts]['n_pads'] += 1
            nums_of_incident_cts[n_cts]['timespans'].append(
                (pad.last_event - pad.first_event).seconds)
            nums_of_incident_cts[n_cts]['start_times'].append(pad.first_event)
            # For each threshold in our n_cts-specific list of thresholds, if
            # the number of pad events in this pad is less than the threshold,
            # record that fact.  We're doing this so that we can (below)
            # report on differences in the average numbers of Pad events
            # between, say, the set of Pads that overlap with 0 CompletedTasks,
            # the set of Pads that overlap with 1 CompletedTask, the set that
            # overlap with 5+ CompletedTasks, etc.
            for i in nums_of_incident_cts[n_cts]['max_events_per_pad']:
                if pad.n_chats + pad.n_revs <= i:
                    nums_of_incident_cts[n_cts]['max_events_per_pad'][i] += 1

        # Report on the different segments
        for n, data_about_pads_with_n_incident_cts in nums_of_incident_cts.items():
            n_pads = data_about_pads_with_n_incident_cts['n_pads']
            max_events_per_pad = data_about_pads_with_n_incident_cts['max_events_per_pad']
            timespans = data_about_pads_with_n_incident_cts['timespans']
            avg_timespan = sum(timespans) / len(timespans)
            print "\nSubset of unique Pads with %d overlapping CompletedTasks:" % n
            print "\tNumber of pads:         %d" % n_pads
            print "\tPercentage of all pads: {0:.0f}%".format(
                float(100 * n_pads / len(pads)))

            start_times = data_about_pads_with_n_incident_cts['start_times']
            d = datetime.strptime("2012-06-01", "%Y-%m-%d")
            n_pads_before = len([t for t in start_times if t < d])
            n_pads_after = n_pads - n_pads_before
            print "\t%d of these Pads are from before 2012-06-01." % n_pads_before
            print "\t%d of these Pads are from after." % n_pads_after

            #print "\tAmong these pads, the number whose event count was..."
            #for i in sorted([n for n in max_events_per_pad if n != 1000000]):
            #    ct = max_events_per_pad[i]
            #    print "\t\t...{0} or less: {1} (that's {2:.0f}% of Pads in this subset)".format(i, ct, float(100 * ct / n_pads))
            print "\tAverage timespan of a Pad in this subset: %d seconds" % avg_timespan 
