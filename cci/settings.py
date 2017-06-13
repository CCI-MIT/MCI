# Django settings for cci project.

import os, sys, json, socket
from minify_json import json_minify

settings_path = os.path.dirname(os.path.abspath(__file__))

VERSION = open(settings_path + "/../version.txt").read()

_CWD = os.path.dirname(__file__)       # Current Working Directory
sys.path.append(_CWD + '/contrib')  # To include 3rd-party apps

hostnameProd = ''
hostnameTest = ''

hostname = socket.gethostname()
if hostname == hostnameTest:
  env = ""
elif hostname == hostnameProd:
  env = ""
else:
	env = "Dev"

ALLOWED_HOSTS = ['*']

DEBUG = env == "Dev"
TEMPLATE_DEBUG = DEBUG

ADMINS_EXTRA = [('John Smith', 'jsmith@yahoo.com')] if env == "Prod" else []
ADMINS = [('Sally Jones', 'sjones@yahoo.com')] + ADMINS_EXTRA

MANAGERS = ADMINS

DATABASES = {
	'default': {
		'ENGINE': 'django.db.backends.mysql',
		'NAME': 'cci',
		'USER': 'cci',
		'PASSWORD': 'cci',
		'HOST': '',                      # Set to empty string for localhost.
		'PORT': '',                      # Set to empty string for default.
		'OPTIONS': {
			"init_command": "SET storage_engine=INNODB",
		}
	}
}

DATABASE_ROUTERS = ['mci.routers.ModelDatabaseRouter']

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = None

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

install_root = '/home/username/app/cci/'

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = install_root + '../media'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = install_root + 'static'

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
	# Put strings here, like "/home/html/static" or "C:/www/django/static".
	# Always use forward slashes, even on Windows.
	# Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
	'django.contrib.staticfiles.finders.FileSystemFinder',
	'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = ''

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
	'django.template.loaders.filesystem.Loader',
	'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
	'django.middleware.common.CommonMiddleware',
	'django.contrib.sessions.middleware.SessionMiddleware',
	'django.middleware.csrf.CsrfViewMiddleware',
	'django.contrib.auth.middleware.AuthenticationMiddleware',
	'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = (
	# Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
	# Always use forward slashes, even on Windows.
	# Don't forget to use absolute paths, not relative paths.
	install_root + "templates",
)

INSTALLED_APPS = (
	'django.contrib.auth',
	'django.contrib.contenttypes',
	'django.contrib.sessions',
	'django.contrib.sites',
	'django.contrib.messages',
	'django.contrib.staticfiles',
	'grappelli.dashboard',
	'grappelli',
	'filebrowser',
	'django.contrib.admin',
	'django.contrib.admindocs',
	'mci',
	'django_extensions',
)

SOUTH_TESTS_MIGRATE = False

LOG_DIR = settings_path + "/../logs"

LOGGING = {
	'version': 1,
	'disable_existing_loggers': False,
	'formatters' : {
		"audit" : {
			'format': '%(asctime)s %(levelname)8s %(module)s [%(lineno)d]  %(message)s',
		},
	},
	'handlers': {
		'console':{
			'level': 'DEBUG',
			'class': 'logging.StreamHandler',
			'formatter': 'audit'
		},
		'mail_admins': {
			'level': 'ERROR',
			'class': 'django.utils.log.AdminEmailHandler',
			'include_html': True,
		},
		# Log to a text file that can be rotated by logrotate
		'spoof_log': {
			'level': 'DEBUG',
			'class': 'logging.handlers.WatchedFileHandler',
			'filename': LOG_DIR + "/cci_spoof.log",
			'formatter' : 'audit',
		},
		# Log to a text file that can be rotated by logrotate
		'audit_log': {
			'level': 'INFO',
			'class': 'logging.handlers.WatchedFileHandler',
			'filename': LOG_DIR + "/cci_audit.log",
			'formatter' : 'audit',
		},
		# Log to a text file that can be rotated by logrotate
		'debug_log': {
			'level': 'DEBUG',
			'class': 'logging.handlers.WatchedFileHandler',
			'filename': LOG_DIR + "/cci_debug.log",
			'formatter' : 'audit',
		},
		# Log to a text file that can be rotated by logrotate
		'concentration_cards_debug_log': {
			'level': 'DEBUG',
			'class': 'logging.handlers.WatchedFileHandler',
			'filename': LOG_DIR + "/cci_concentration_cards_debug.log",
			'formatter' : 'audit',
		},
	},
	'loggers': {
		'django.request': { 'handlers': [ 'mail_admins'
										, 'audit_log'
										, 'debug_log'
										]
						  , 'level': 'ERROR'
						  , 'propagate': True
						  },
		'django.security.DisallowedHost': {
			'handlers': ['spoof_log'],
			'level': 'ERROR',
			'propagate': False,
		},
		'cci': {
			'handlers': [ 'audit_log'
						, 'debug_log'
						, 'console'
						],
			'level': 'DEBUG',
			'propagate': True,
		},
		'concentration_cards': {
			'handlers': [ 'concentration_cards_debug_log'
						, 'console'
						],
			'level': 'DEBUG',
			'propagate': False,
		},
	}
}

MCI_ETHERPAD_BASE_URL,MCI_ETHERPAD_API_URL="",""

# The ports can be whatever you want. Etherpad runs on port 9001 by default

if env == "Dev":
    MCI_DOMAIN = ""
    MCI_BASE_URL = "http://" + MCI_DOMAIN + ":80/"
    MCI_ETHERPAD_BASE_URL = "http://" + MCI_DOMAIN + ":9001/"
    MCI_ETHERPAD_API_URL = MCI_ETHERPAD_BASE_URL + "api"
    MCI_CONCENTRATION_BASE_URL = "http://" + MCI_DOMAIN + ":10000/"

elif env == "Test":
	MCI_DOMAIN = ""
	MCI_BASE_URL= "http://" + MCI_DOMAIN + "/"
	MCI_ETHERPAD_BASE_URL = "http://" + MCI_DOMAIN + ":9001/"
	MCI_ETHERPAD_API_URL="http://" + MCI_DOMAIN + "api"
	MCI_CONCENTRATION_BASE_URL = "http://" + MCI_DOMAIN + ":10000/"

elif env == "Prod":
	MCI_DOMAIN = ""
	MCI_BASE_URL = "http://" + MCI_DOMAIN + "/"
	MCI_ETHERPAD_BASE_URL = "http://" + MCI_DOMAIN + ":9001/"
	MCI_ETHERPAD_API_URL = "http://" + MCI_DOMAIN + "api"
	MCI_CONCENTRATION_BASE_URL = "http://" + MCI_DOMAIN + ":10000/"

# You can read this from the file, or just paste the value from the file in
MCI_ETHERPAD_API_KEY= ""

el_settings = json.loads(json_minify(open(settings_path + "/../etherpad-lite/settings.json").read()))
MCI_ETHERPAD_USING_REDIS=el_settings['dbType'] == 'redis'
MCI_ETHERPAD_REDIS_CONF=el_settings['dbSettings'] if MCI_ETHERPAD_USING_REDIS else None

MCI_REDIS_SERVER="localhost"
MCI_REDIS_PORT=6379

MCI_OPENTOK_API_KEY = '21112792'
MCI_OPENTOK_API_SECRET = '4c2ddbf446e183e4e3470b05a99cb9da2f3dac62'

GRAPPELLI_ADMIN_TITLE="Center for Collective Intelligence - Measuring Collective Intelligence"

# This is a variable that determines a path. If you put the application in a subdirectory
# named 'test' you will need this to say test.dashboard.CustomIndexDashboard
GRAPPELLI_INDEX_DASHBOARD = 'dashboard.CustomIndexDashboard'

FILE_UPLOAD_PERMISSIONS=0444

TEMPLATE_CONTEXT_PROCESSORS = (
	"django.contrib.auth.context_processors.auth",
	"django.core.context_processors.request",
	"django.core.context_processors.i18n",
	'django.contrib.messages.context_processors.messages',
)

# CONSTANTS
game_board_height = 296
game_board_width = 576
squares_set_width = 96
squares_set_height = 72
board_area_border_thickness = 1
