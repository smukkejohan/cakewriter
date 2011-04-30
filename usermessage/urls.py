from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('',
    (r'^delete/$', 'usermessage.views.usermessage_delete'),
)