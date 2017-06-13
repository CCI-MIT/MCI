from django.core.management.base import BaseCommand
from settings import MCI_ETHERPAD_USING_REDIS
from mci.models import CompletedTask, EtherpadLiteRecord
from pprint import * 
from redis import Redis


class Command(BaseCommand):

    def handle(self, *args, **options):

        if MCI_ETHERPAD_USING_REDIS:
            print "Redis backend in use.  Exiting."
            exit(1)

        if len(args) != 1:
            print "Invalid # of args"
            exit(1)

        print EtherpadLiteRecord.objects.count()

        elrs = EtherpadLiteRecord.objects.all()[:10000000]
        elr_ct = elrs.count()
        print ("elr count: %i" % elr_ct)

        redis_db = args[0]
        rc = Redis(db=redis_db)
        ps = enumerate(elrs)

        print ("ready to start copying...")

        for i, elr in ps:
            should_print = i % 10000 == 0
            if should_print:
                print ("About to insert ELR #%i into Redis" % i)
            rc.set(elr.key, elr.value_raw)
            if should_print:
                print ("Processed ELR #%i" % i)

        print ("done!  now you need to verify that it all got copied correctly -- were there any Redis errors while copying? -- and, if so, drop the MySQL table...")
                
