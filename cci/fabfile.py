from fabric.api import run, env, prompt
from fabric.context_managers import cd, prefix
from fabric.operations import local, sudo, require
from contextlib import contextmanager as _contextmanager

hostnameProd = 'something.com'

@_contextmanager
def _virtualenv():
  """Run a command within the virtualenv environment on the target machine"""
  require( 'project_root'
         , 'activate'
         , provided_by=("staging","production")
         )
  with cd(env.project_root + "cci"):
    with prefix(env.activate):
      yield

# TODO -- this function may not be necessary, need to look at git flow again.
def tag_release(version):
  """Tag `master` as a release with the version number provided"""
  print "Tagging version %s" % version
  local("git tag -a %s -m 'v%s'" % (version, version))

def staging():
  """Setup environment variables for the staging environment"""
  env.hosts = ['',]
  env.project_root = '/app/cci/'
  env.activate = 'source /opt/local/python-environments/cci-ssl2/bin/activate'

def production():
  """Setup environment variables for the production environment"""
  env.hosts = [hostnameProd,]
  env.project_root = '/app/cci/'
  env.activate = 'source /opt/local/python-environments/cci-ssl2/bin/activate'

def deploy(branchname):
  """Deploy to the target environment, updating all required packages"""

  if hostnameProd in env.hosts:
      msg = "Are you sure you want to deploy to %s?" % hostnameProd
      should_continue = prompt(msg, default="n") == "y"
      if not should_continue:
          print "Exiting..."
          exit(1)

  require( 'project_root'
         , provided_by=("staging","production")
         )

  with cd(env.project_root):
      run('git status')
      run('git diff')

      with _virtualenv():
          run('./manage.py migrate mci --list')

          run('git fetch --all')
          run('git fetch --tags')
          run('git checkout "%s"' % (branchname))
          run('git merge --ff-only "%s%s"' % ( "" if "tags/" in branchname else "origin/"
                                             , branchname
                                             ))

          set_version(branchname)
    
          run("python bootstrap.py")

          run('./manage.py migrate mci --list')
          should_migrate = prompt("Run migration?", default="y") == "y"
          if should_migrate:
              run("./manage.py migrate mci")

          should_update_permissions = prompt("Update permissions?", default="y") == "y"
          if should_update_permissions:
              run("./manage.py update_permissions")

          run("./manage.py collectstatic -v0 --noinput")
          sudo("/usr/sbin/apachectl restart")
          sudo("/etc/init.d/realtimegames stop")
          sudo("/etc/init.d/realtimegames start")

def set_version(branchname):
  """Set the 'project version' in the target environment"""
  require( 'project_root'
         , provided_by=("staging","production")
         )
  with cd(env.project_root):
      run('echo "%s" > version.txt' % (branchname))
