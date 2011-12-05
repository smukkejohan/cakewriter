from django.conf.urls.defaults import *
from accounts import views

urlpatterns = patterns('',
    url(r'^users/$', views.users, name='users-overview'),
    url(r'^users/(?P<username>[\w.@+-]+)/$', views.user, name='user-overview'),
    url(r'^account/edit/$', views.edit_profile, name='edit_profile'),
    (r'^account/$', views.account),
)