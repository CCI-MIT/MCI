import subprocess
import os
import sys

if "VIRTUAL_ENV" not in os.environ:
    from pip.baseparser import parser
    sys.stderr.write("$VIRTUAL_ENV not found.\n\n")
    parser.print_usage()
    sys.exit(-1)
virtualenv = os.environ["VIRTUAL_ENV"]
file_path = os.path.dirname(__file__)
subprocess.call([
                   "sudo",
                   "pip",
                   "install",
                   "-r",
                   os.path.join(file_path, "requirements/apps.txt"),
                   '-f',
                   os.path.join('file:///app/cci/requirements/'),
                ])
