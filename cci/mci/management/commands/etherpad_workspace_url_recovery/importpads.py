from django.core.management.base import BaseCommand, CommandError
from mci.models import Pad
from django.db.models import F
import sys, os, MySQLdb, MySQLdb.cursors, json
from datetime import datetime, timedelta
import re
import numpy as np

class Command(BaseCommand):
    args = "<max slice length> <timestamp to start from>"
    help = ''

    # This command is no longer used
    def handle(self, *args, **options):

        reset = 'reset' in args

        if reset:
            print "Deleting the %d existing Pad objects." % Pad.objects.count()
            Pad.objects.all().delete()
            print "Remaining Pad objects: %d." % Pad.objects.count()

        limit = int(args[0])
        min_timestamp = int(args[1])
        min_time = datetime.fromtimestamp(min_timestamp)

        frmt = '%Y-%m-%d %I:%M:%S%p %Z'

        print "We're only considering pad events that took place after %s." % \
            min_time.strftime(frmt)

        print "About to connect to etherpad-lite db."
        try:
          db = MySQLdb.connect(
            user='root',
            passwd='.',
            db='.',
            cursorclass = MySQLdb.cursors.DictCursor)
        except MySQLdb.Error, e:
          print "\nError %d: %s" % (e.args[0], e.args[1])
          raise MySQLdb.Error
        
        print "Connected to db."  
        
        c = db.cursor()
        c.execute((
            "select * from `store` "
            "where `key` LIKE '%revs%' "
               "or `key` LIKE '%chat%' LIMIT {0}"
            ";").format(limit))
        all_results = [{
            'key': r['key'],
            'value': json.loads(r['value']),
        } for r in c.fetchall()]
        print "Total # of pad events (chat, revs): %d" % len(all_results)
        c.close()
        db.close()
        print "Closed the db connection."

        def has_timestamp(r):
            v = r['value']
            return 'time' in v or ('meta' in v and 'timestamp' in v['meta'])

        def not_workspace_setup(r):
            v = r['value']
            has_author = 'meta' in v and 'author' in v['meta'] and len(v['meta']['author']) > 0
            return has_author or not 'meta' in v

        def timestamp(r):
            v = r['value']
            if 'time' in v:
                return int(v['time']) / 1000
            else:
                return int(v['meta']['timestamp']) / 1000

        results_with_timestamp = [r for r in all_results if has_timestamp(r)]
        print "# of pad events (out of total) with a timestamp: %d" % \
            len(results_with_timestamp)

        results_after_timestamp = [r for r in results_with_timestamp
                                     if timestamp(r) > min_timestamp]
        results_not_setup = [r for r in results_after_timestamp
                               if not_workspace_setup(r)]
        print "Ignoring %d Workspace Setup events." % (
            len(results_after_timestamp) - len(results_not_setup)) 
        results = results_not_setup[:limit]
        n_results = len(results)
        print ("# of pad events that will be considered in the identification "
               "of unique Pads: %d") % n_results 

        def event_type(r):
            if 'revs' in r['key']:
                return 'n_revs'
            elif 'chat' in r['key']:
                return 'n_chats'

        # Get timestamp of each pad's first and last event
        pads = {}
        for i, r in enumerate(results):
            m = re.compile('pad:(.*?):chat').search(r['key'])
            if m:
                pad_id = m.group(1)
            else:
                m = re.compile('pad:(.*?):revs').search(r['key'])
                if m:
                    pad_id = m.group(1)
            if pad_id:
                ts = timestamp(r)
                if not pad_id in pads:
                    pads[pad_id] = {
                        'first': 2147483647,
                        'last': 0,
                        'n_chats': 0,
                        'n_revs': 0,
                        'events': [],
                    }
                pads[pad_id][event_type(r)] += 1
                pads[pad_id]['events'].append({
                    'timestamp': ts,
                    'text': r,
                })

        def reject_outliers(events):
            timestamps = np.array([e['timestamp'] for e in events])
            m = 2
            u = np.mean(timestamps)
            s = np.std(timestamps)
            filtered_timestamps = [e for e in events
                                     if (u - 2 * s < e['timestamp'] < u + 2 * s)]
            return filtered_timestamps

        n_outlier_events = 0

        for pad_id, pad_data in pads.items():
            pad_data['events'].sort(key=lambda e: e['timestamp'])

        # Now that we have all the events associated with each pad...
        for pad_id, pad_data in pads.items():

            print "\nPad ID: %s" % pad_id
#            print "\tStarting with %d events." % len(pad_data['events']) 

#            max_loops_remaining = 2
#            while max_loops_remaining > 0 and len(pad_data['events']) > 1:
#                max_loops_remaining -= 1

                #timestamps = [e['timestamp'] for e in pad_data['events']]
                #for ts in timestamps:
                #    print "\t%s" % ts

#                print "\tFiltering out outlier events..."
#                _events = reject_outliers(pad_data['events'])
#                n_new_outliers = len(pad_data['events']) - len(_events)
#                print "\tFiltered out %d outlier events." % n_new_outliers
#                pad_data['events'] = _events
#                n_outlier_events += n_new_outliers
                
#                if len(pad_data['event_timestamps']) > 1: 

            timestamps = [e['timestamp'] for e in pad_data['events']]

            # Find the (new) first and last events.
            pad_data['first'] = min(timestamps)
            pad_data['last'] = max(timestamps)

            # NOTE: what follows is so I can eyeball it.
            # Find the distribution of events -- we're looking for outliers,
            # events that could have taken place before or (more likely) after
            # the Completed Task had ended.
            n_intervals = 10
            spread = pad_data['last'] - pad_data['first']
            print "\tSpread between first, last events: %d seconds" % spread
            intervals = [(pad_data['first'] + int(spread * i         / 10.0),
                          pad_data['first'] + int(spread * (i + 1.0) / 10.0))
                              for i in range(n_intervals)]
            n_events = len(pad_data['events'])
            ns = [len([ts for ts in timestamps
                           if ts >= lo and ts <= hi])
                     for lo, hi in intervals]
            print ns
            for e in pad_data['events']:
                print "\t\t%s" % e['timestamp']
                print "\t\t%s" % e['text']

            # (end while loop)

            if len(pad_data['events']) > 1:
                if reset:
                    # Create a Pad.
                    Pad.objects.create(            
                        first_event=datetime.fromtimestamp(pad_data['first']),
                        last_event=datetime.fromtimestamp(pad_data['last']),
                        n_chats=pad_data['n_chats'],
                        n_revs=pad_data['n_revs'],
                        pad_id=pad_id,
                        event_distribution=json.dumps(dict(enumerate(ns))))
                else:
                    p = Pad.objects.get(pad_id=pad_id)
                    p.event_distribution = json.dumps(dict(enumerate(ns)))
                    p.save()

        print "\nIn total, filtered out %d outlier events." % n_outlier_events 

        if reset:
            print "Identified and imported %d unique Pads." % Pad.objects.count() 
        else:
            print "event_distribution is NOT NULL for %d Pads." % \
                Pad.objects.filter(event_distribution__isnull=False).count()
