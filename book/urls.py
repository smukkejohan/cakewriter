# -*- coding: utf-8 -*-

from django.conf.urls.defaults import *

from book import views

urlpatterns = patterns('',
    url(r'^chapter/(?P<chapter_id>\d+)/$', views.chapter, name='chapter'),
)