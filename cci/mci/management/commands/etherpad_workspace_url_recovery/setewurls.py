from django.core.management.base import BaseCommand, CommandError
from mci.models import CompletedTask, Pad
from mci.workspace.workspace import etherpad_workspace_url

class Command(BaseCommand):
    args = ""
    help = ''

    def handle(self, *args, **options):

        pads = Pad.objects.all()

        n_assigned = 0

        for i, pad in enumerate(pads):

            if i % 1000 == 0:
                print "Matching CTs for Pad %d." % i

            cts = pad.incident_cts.all()
            if len(cts) == 1:
                cts[0].etherpad_workspace_url = etherpad_workspace_url(pad.pad_id)
                cts[0].save()
                n_assigned += 1

        print "Set the etherpad_workspace_url on %d CompletedTasks." % n_assigned
