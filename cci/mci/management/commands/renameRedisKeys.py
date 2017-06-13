from django.core.management.base import BaseCommand, CommandError
from mci.models import SI_SB_Status, Session, Subject, EventLog
from mci.reporting.views import _build_session_log
from pprint import * 
import redis, re, json
from settings import MCI_REDIS_SERVER, MCI_REDIS_PORT
from pprint import pprint

class Command(BaseCommand):

    def handle(self, *args, **options):

        rc = redis.Redis(host=MCI_REDIS_SERVER, port=MCI_REDIS_PORT)
        
        # NOTE: be careful to run more specific original-key pairs first,
        # otherwise there might be a risk that the more specific patterns will
        # get matched under the more general patterns.  (Not that we have any
        # actual examples of this, yet.)

        patterns = [ ( 'concentration_completedtask_%s_vars'
                     , 'ct_%s_vars'
                     , 'hash'
                     )
                   , ( 'conc_task_%s_points_global'
                     , 'ct_%s_points_global'
                     , 'key'
                     )
                   , ( 'concentration_users_%s'
                     , 'ct_%s_users'
                     , 'hash'
                     )
                   , ( 'conc_task_%s_current_round'
                     , 'ct_%s_current_round'
                     , 'key'
                     )
                   , ( 'concentration_clicks_%s'
                     , 'ct_%s_card_clicks'
                     , 'queue'
                     )
                   , ( 'concentration_assister_sid_%s'
                     , 'ct_%s_assister_sid'
                     , 'key'
                     )
                   , ( 'concentration_cards_%s_%s'
                     , 'ct_%s_cards_round_%s'
                     , 'hash'
                     )
                   ]

        # NOTE: We're matching on the location of the end of each key to
        #       filter out/ignore those ending with "*_clash_bak_....".

        for (oldPattern, newPattern, keyType) in patterns:
            nVars = oldPattern.count("%s")
            ks = rc.keys(oldPattern % tuple(["*" for i in range(nVars)]))
            for keyOnOldPattern in ks:
                matches = re.findall(
                    (oldPattern % tuple(["(\d+)" for i in range(nVars)])) + "($)",
                    keyOnOldPattern)
                try:
                    extracted = matches[0]

                    print "\n\n"
                    print "old key: " + keyOnOldPattern
                    print "extracted values: %r" % (extracted[:-1],)
                    if keyType == 'key':
                        print "old value:"
                        print rc.get(keyOnOldPattern)
                    elif keyType == 'hash':
                        hks = rc.hkeys(keyOnOldPattern)
                        print "old hash keys:"
                        pprint(hks)
                        print "old hash key values:"
                        for hk in hks:
                            try:
                                print rc.hget(keyOnOldPattern, hk)
                            except ValueError as e:
                                pprint(e)
                                raise
                    elif keyType == 'queue':
                        print "old queue length:"
                        print(rc.llen(keyOnOldPattern))

                    keyOnNewPattern = newPattern % extracted[:-1]
                    rc.rename(keyOnOldPattern, keyOnNewPattern)

                    print "new key: " + keyOnNewPattern
                    if keyType == 'key':
                        print "new value:"
                        pprint(rc.get(keyOnNewPattern))
                    elif keyType == 'hash':
                        hks = rc.hkeys(keyOnNewPattern)
                        print "new hash keys:"
                        pprint(hks)
                        print "new hash key values:"
                        for hk in hks:
                            pprint(rc.hget(keyOnNewPattern, hk))
                    elif keyType == 'queue':
                        print "new queue length:"
                        print(rc.llen(keyOnNewPattern))

                except IndexError:
                    print "\n\nskipping " + keyOnOldPattern
                except:
                    print "unaccountable error with key: " + keyOnOldPattern
                    print "extracted values: %r" % extracted[:-1]
                    raise
