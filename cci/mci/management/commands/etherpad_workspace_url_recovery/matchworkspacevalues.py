from django.core.management.base import BaseCommand, CommandError
from mci.models import CompletedTask
import json
from pprint import pprint

class Command(BaseCommand):
    args = ''
    help = ''

    def handle(self, *args, **options):

        rows = json.load(open('../workspace_values_export.txt'))['data']
        pprint(rows)

        exit(0)        

        for row in rows:
            ct = CompletedTask.objects.get(pk=row['id'])
            ct.etherpad_workspace_url = row['workspace']
            ct.save() 
