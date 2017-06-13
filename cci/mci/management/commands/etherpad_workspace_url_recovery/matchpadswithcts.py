from django.core.management.base import BaseCommand, CommandError
from mci.models import CompletedTask, Pad
from django.db.models import Q

class Command(BaseCommand):
    args = ""
    help = ''

    def handle(self, *args, **options):

        pads = Pad.objects.all()

        for i, pad in enumerate(pads):

            if i % 1000 == 0:
                print "Matching CTs for Pad %d." % i

            # **Remove**, NOT delete
            pad.incident_cts.clear()

            # Look for a CT that's already got us as its One and Only.
            true_loves = CompletedTask.objects.filter(
                etherpad_workspace_url__contains=pad.pad_id)

            if len(true_loves) > 1:
                for ct in true_loves:
                    print "CompletedTask %s has %s as its etherpad_workspace_url!" % (ct, ct.etherpad_workspace_url)
                raise Exception
            
            for ct in true_loves:
                pad.incident_cts.add(ct)

            # If we don't have our True Love yet, continue looking for candidates.
            if pad.incident_cts.count() == 0:

                incident_cts_with_known_end_times = CompletedTask.objects.filter(
                    # Case definition
                    Q(etherpad_workspace_url__isnull=True) |
                    Q(etherpad_workspace_url=""),
                    start_time__isnull=False,
                    next_ct__isnull=False,
                    next_ct__start_time__isnull=False,
                    # Data filter
                    start_time__lte=pad.first_event,
                    next_ct__start_time__gte=pad.last_event)
    
                for ct in incident_cts_with_known_end_times:
                    pad.incident_cts.add(ct)
    
                incident_cts_without_known_end_times = CompletedTask.objects.filter(
                    # Case definition
                    Q(etherpad_workspace_url__isnull=True) |
                    Q(etherpad_workspace_url=""),
                    start_time__isnull=False,
                    next_ct__isnull=True,
                    # Data filter
                    start_time__lte=pad.first_event,
                    max_actual_end_time__gte=pad.last_event)
    
                for ct in incident_cts_without_known_end_times:
                    pad.incident_cts.add(ct)

        # TODO: print a note about what's been done
