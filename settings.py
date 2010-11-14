# coding=<utf-8>

import os.path, sys, platform

PROJECT_ROOT = os.path.dirname(__file__)
MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'static')

DEVELOPMENT_MODE = (platform.node() != "tango")

ADMIN_MEDIA_PREFIX = '/media/'

if DEVELOPMENT_MODE:
    DEBUG = True
    MEDIA_URL = '/m/'
    EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
    EMAIL_FILE_PATH = '../tmp-emails/app-messages'
else:
    DEBUG = False
    MEDIA_URL = 'http://m.cakethebook.com/'
    ADMIN_MEDIA_PREFIX = MEDIA_URL + 'admin/'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'cakewriter.dev.db',        
        'USER': '',
        'PASSWORD': '',
        'HOST': '',  
        'PORT': '',
        }
}

TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Johan Bichel Lindegaard', 'sysadmin@johan.cc'),
)
MANAGERS = ADMINS

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Copenhagen'

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

# Make this unique, and don't share it with anybody.
SECRET_KEY = ')dtk*18jea%+khj_6s)j_x8^nd6jat=^h4xta&sh8hkxxue8sv'

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

ROOT_URLCONF = 'cakewriter.urls'

TEMPLATE_DIRS = (
    os.path.join(PROJECT_ROOT, 'templates'),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.comments',
    'registration',
    'djangoratings',
    'book',
    'accounts',
    'voting',
)

ACCOUNT_ACTIVATION_DAYS = 30
LOGIN_REDIRECT_URL = '/'

AUTH_PROFILE_MODULE = 'accounts.UserProfile'

RATINGS_VOTES_PER_IP = 3

try:
    from settings_local import *
except ImportError:
    import sys
    sys.stderr.write('Unable to read settings_local.py\n')
    sys.exit(1)
