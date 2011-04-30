from django.conf.urls.defaults import *
from accounts import views

urlpatterns = patterns('',
    url(r'^username/(?P<username>[\w.@+-]+)/$', views.user, name='user-overview'),
    url(r'^edit/$', views.edit_profile, name='edit_profile'),
)