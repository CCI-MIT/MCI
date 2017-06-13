from django.core.management.base import BaseCommand, CommandError
from pprint import * 
import os, re, redis
from settings import MCI_ETHERPAD_REDIS_CONF

class Command(BaseCommand):
    def handle(self, *args, **options):
        rc = redis.Redis( host = MCI_ETHERPAD_REDIS_CONF['host']
                        , port = MCI_ETHERPAD_REDIS_CONF['port']
                        , db   = MCI_ETHERPAD_REDIS_CONF['database']
                        ) 
        keysRevs = rc.keys("*:revs:*")
        self.stdout.write("got %d Revision keys" % len(keysRevs))

        keysChat = rc.keys("*:chat:*")
        self.stdout.write("got %d Chat keys" % len(keysChat))

        prog = re.compile("^pad:([^:]+):(revs|chat):([^:]+)$")

        for k in keysRevs + keysChat:
            m = prog.match(k)
            if m:
                keySet = "pad:%s:%s" % (m.group(1), m.group(2))
                rc.sadd(keySet, k)
                #print "members of %s:\n%s" % (keySet, pformat(rc.smembers(keySet)))

        keysGlobalAuthor = rc.keys("globalAuthor:*")
        self.stdout.write("got %d globalAuthor keys" % len(keysGlobalAuthor))
        for k in keysGlobalAuthor:
            keySet = "ueberDB:keys:globalAuthor"
            rc.sadd(keySet, k)

        keysMapper2Author = rc.keys("mapper2author:*")
        self.stdout.write("got %d mapper2author keys" % len(keysMapper2Author))
        for k in keysMapper2Author:
            keySet = "ueberDB:keys:mapper2author"
            rc.sadd(keySet, k)
