from django.core.management.base import BaseCommand, CommandError
from mci.models import CompletedTask
from pprint import * 
import os, json
from redis import Redis
from datetime import *
from dateutil import rrule
from itertools import takewhile, dropwhile 

class Command(BaseCommand):

    def handle(self, *args, **options):

        ctid          = args[0]
        revsPerMinute = int(args[1])

        def analyze(accum, datetime):
            self.stdout.write("\nAnalyzing typing activity in the minute preceding %s..." % str(datetime))
        
            pred = lambda pair: pair[0] < datetime
            revsInPeriod = list(takewhile(pred, accum['remaining']))
            authorsInPeriod = set([r[1]['meta']['author'] for r in revsInPeriod])
            def isActive(author):
                def isByAuthor(revPair):
                  return revPair[1]['meta']['author'] == author
                revsByAuthorInPeriod = len(filter(isByAuthor, revsInPeriod))
                # print ("isActive >> revsByAuthorInPeriod: %i" % revsByAuthorInPeriod)
                return revsByAuthorInPeriod > revsPerMinute
            activeAuthorsInPeriod = filter(isActive, authorsInPeriod)
            result = { 'datetime': datetime
                     , 'activeAuthorsInPrecedingMinute': len(activeAuthorsInPeriod)
                     }
            revsRemaining  = list(dropwhile(pred, accum['remaining']))
        
            #print ("Analyze >> revsInPeriod: \n%s" % pformat([r[0] for r in revsInPeriod]))
        
            return { 'results':   accum['results'] + [result]
                   , 'remaining': revsRemaining
                   }        

        ct = CompletedTask.objects.get(pk=ctid)
        padRevKey = "pad:%s:revs*" % ct.pad_id()

        #print("\npadRevKey: " + padRevKey)

        r = Redis(db=1)

        revKeys = r.keys(padRevKey)
        #print ("revKeys >> \n%s" % pformat(revKeys))

        revsUnsorted = [json.loads(r.get(rev)) for rev in revKeys]
        revPairsUnsorted = [( datetime.fromtimestamp(int(rev['meta']['timestamp'])/1000)
                            , rev 
                            ) for rev in revsUnsorted
                           ]

        revPairs = sorted(revPairsUnsorted, key=lambda p: p[0])

        #print ("revPairs >> \n%s" % pformat(revPairs))

        datetimes = list(rrule.rrule( rrule.MINUTELY
                                    , dtstart=ct.expected_start_time
                                    , until=ct.expected_finish_time + timedelta(minutes=1)
                                    ))[1:]

        #print ("datetimes >> \n%s" % pformat(datetimes))
        
        accum = reduce(analyze, datetimes, { 'results': [], 'remaining': revPairs })
        self.stdout.write("\nresults: %s" % pformat(accum['results']))
