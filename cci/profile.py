import cProfile, pstats, StringIO
from mci.models import *
from mci.util.export import export_zip
import sys

def logForSessionGroup(sesh_id):
    sesh = Session.objects.get(pk=sesh_id)
    l = sesh.build_session_log(1)

def zipExport(sesh_id):
    sesh = Session.objects.get(pk=sesh_id)
    e = export_zip(sesh)

def doIt(function, sesh_id):
    pr = cProfile.Profile()
    pr.enable()
     
    function(sesh_id)

    pr.disable()
    s = StringIO.StringIO()
    sortby = 'cumulative'
    ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    ps.print_stats(30)
    print s.getvalue()
