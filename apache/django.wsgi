import os
import sys
import site

site.addsitedir('/home/tmpethick/.virtualenvs/cakewriter/lib/python2.7/site-packages')

sys.path.append('/home/tmpethick/srv')
sys.path.append('/home/tmpethick/srv/cakewriter')

os.environ['DJANGO_SETTINGS_MODULE'] = 'cakewriter.settings'

import django.core.handlers.wsgi

application = django.core.handlers.wsgi.WSGIHandler()
