import os
import sys

sys.path.append('/home/wwl/srv')
sys.path.append('/home/wwl/srv/cakewriter')

os.environ['DJANGO_SETTINGS_MODULE'] = 'cakewriter.settings'

import django.core.handlers.wsgi

application = django.core.handlers.wsgi.WSGIHandler()
