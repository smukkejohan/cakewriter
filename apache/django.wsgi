import os
import sys

sys.path.append('/home/johan/srv/cakethebook')
sys.path.append('/home/johan/srv/cakethebook/cakewriter')

os.environ['DJANGO_SETTINGS_MODULE'] = 'cakewriter.settings'

import django.core.handlers.wsgi

application = django.core.handlers.wsgi.WSGIHandler()
