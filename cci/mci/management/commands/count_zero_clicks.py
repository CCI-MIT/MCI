from django.core.management.base import BaseCommand, CommandError
from mci.models import SI_SB_Status, Session, Subject, EventLog
from mci.reporting.views import _build_session_log
from pprint import * 
import os

class Command(BaseCommand):

    def handle(self, *args, **options):

        stats_with_subs = SI_SB_Status.objects.filter(subject__isnull=False)
        sessions = list(set([stat.subject.session for stat in stats_with_subs
                                                  if "Load Test" not in stat.subject.session.name]))

        self.stdout.write("\nTotal # of Sessions being considered: %d" % len(sessions))

#        for s in sessions:
#            _build_session_log(s, 1)

        subjects = set([sub for sesh in sessions
                            for sub in sesh.subject_set.all()])
        sub_clicks = dict([
            (sub.pk,
            sub.eventlog_set.filter(
                event="Click",
#                completed_task__solo_subject__isnull=True
            ).count()) for sub in subjects
        ])
        self.stdout.write("\nTotal # of Subjects in these sessions: %d" % len(subjects))
        zero_clickers = [s for s in subjects if sub_clicks[s.pk] == 0]

        self.stdout.write("\n# of Subjects who had 0 clicks: %d" % len(zero_clickers))

        nps_logfile_name = args[0]
        logfile = open(nps_logfile_name, "r")
        lines = logfile.readlines()
        relevant_lines = [l for l in lines if "to Subject" in l]
        def connected(subject):
            snippet = "to Subject %d" % subject.pk
            return any((snippet in l for l in relevant_lines))
        non_connectors = [s for s in subjects if not connected(s)]
        connectors = [s for s in subjects if connected(s)]

        self.stdout.write("\n# of Subjects who never connected: %d" % len(non_connectors))
        self.stdout.write("\nNon-connectors:")
        self.stdout.write("\n%s" % pformat([sub.pk for sub in non_connectors]))
        self.stdout.write("\nConnectors:")
        self.stdout.write("\n%s" % pformat([sub.pk for sub in connectors]))

#        zero_but_connected = [s for s in connectors
#                                if  s in zero_clickers]
#        self.stdout.write("\nSubjects who had 0 clicks but did connect to the game server: %d" % len(zero_but_connected))
#
#        zeroes_loaded_workspace = [s for s in zero_clickers
#                                     if  s.eventlog_set.filter(event="Load Workspace").count() > 0]
#        self.stdout.write("\n# of 0-clickers who did load the workspace: %d" % len(zeroes_loaded_workspace))
#
#        subs_loaded_workspace = [s for s in subjects
#                                   if  s.eventlog_set.filter(event="Load Workspace").count() > 0]
#        self.stdout.write("\n# of all subjects who did load the workspace: %d" % len(subs_loaded_workspace))

        subs_loaded_wr = [s for s in subjects
                            if  s.eventlog_set.filter(event="Entering waiting room").count() > 0]
        self.stdout.write("\n# of all subjects who did enter their Session's WR: %d" % len(subs_loaded_wr))


#        zbc_stats = dict([
#            (s.external_id, {
#                'session': s.session,
#                'subs_in_session': s.session.subject_set.all().count(),
#            }) for s in zero_but_connected
#        ])

#        self.stdout.write("\nZBC stats:")
#        self.stdout.write("\n%s" % pformat(zbc_stats))

        def sesh_dicts(sessions):
            return dict([
                (session.name, dict([
                    (sub.external_id, sub_clicks[sub.pk])
                        for sub in session.subject_set.all()
                ])) for session in sessions
            ])

        def run(cfcs, csfvs):
            invalid_sessions = [
                sesh for sesh in sessions
                     if len([
                         sub for sub in sesh.subject_set.all()
                             if  sub_clicks[sub.pk] >= cfcs
                         ]) < csfvs
            ]
            valid_sessions = [
                sesh for sesh in sessions
                     if len([
                         sub for sub in sesh.subject_set.all()
                             if  sub_clicks[sub.pk] >= cfcs
                         ]) >= csfvs
            ]
            invalid_sesh_dicts = sesh_dicts(invalid_sessions)
            valid_sesh_dicts = sesh_dicts(valid_sessions)
            return (invalid_sesh_dicts, valid_sesh_dicts)
         
#        for clicking in range(1,5):
#            isd, vsd = run(1, clicking)
#            pct = float(len(vsd)) / float(len(sessions)) * 100.0
##            print "\npct: %f" % pct
#            self.stdout.write("\n{0:.000f}% of sessions had at least {1} subject{2} clicking".format(pct, clicking, "s" if clicking > 1 else ""))
#            if clicking == 4:
#                self.stdout.write("\nInvalid sessions: \n%s" % pformat(isd))
#                self.stdout.write("\nValid sessions: \n%s" % pformat(vsd))
        self.stdout.write("\n")
