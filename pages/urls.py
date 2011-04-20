# -*- coding: utf-8 -*-

from django.conf.urls.defaults import *
from pages import views


urlpatterns = patterns('',
    url(r'^$', views.all_rolemodels, name='all_rolemodels'),
)


