from mci.models import SubjectCountry
import os

path = os.path.dirname(os.path.realpath(__file__)) + "/../media/flags/"

class UsageError(Exception):
    pass

def use_flag_size(size):

    if not isinstance(size, basestring):
        raise TypeError("'size' must be a string")

    if not size in ['16', '24', '32', '48', '64', '128', '256']:
        raise UsageError("'size' must be one '16', '24', '32', '48', '64', '128', or '256'")

    if not os.path.exists(path):
      print "Did not find directory ../media/flags"
      exit(1)
    else:
      print "Found directory ../media/flags"
    
    for filename in os.listdir(path):

        def sc(sizetag):
            name = filename\
                    .split(sizetag)[0]\
                    .replace("-", " ")\
                    .replace(" Flag", "")
            print "Using %s for %s" % (filename, name)
            try:
                scs = SubjectCountry.objects.filter(name=name)
                for sc in scs:
                    sc.flag = "flags/" + filename
                    sc.save()
            except SubjectCountry.DoesNotExist:
                SubjectCountry.objects.create(
                    name=name,
                    flag="flags/" + filename)
    
        if ("-" + size) in filename:
            sc("-" + size)
        elif size in filename:
            sc(size)
