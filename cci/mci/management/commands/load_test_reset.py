from django.core.management.base import BaseCommand, CommandError
from mci.models import Session, Subject, SubjectIdentity
import csv, os
from datetime import datetime, timedelta


class Command(BaseCommand):

    def handle(self, *args, **options):

        Session.objects.filter(name__contains="Load Test").delete()
        Subject.objects.filter(external_id__contains="load_test").delete()
        SubjectIdentity.objects.filter(mturk_id__contains="load_test").delete()
