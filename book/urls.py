# -*- coding: utf-8 -*-

from django.conf.urls.defaults import *
from voting.views import vote_on_object
from django.contrib.comments.models import Comment
from book import views
from djangoratings.views import AddRatingFromModel

comment_dict = {
    'model': Comment,
    'template_object_name': 'comment',
    'allow_xmlhttprequest': True,
}

urlpatterns = patterns('',
    url(r'^chapter/(?P<chapter_id>\d+)/$', views.chapter, name='chapter'),
    (r'^comment/(?P<object_id>\d+)/(?P<direction>up|down|clear)vote/?$', vote_on_object, comment_dict),

    url(r'^chapter/(?P<object_id>\d+)/rate/(?P<score>\d+)/', AddRatingFromModel(), {
        'app_label': 'chapters',
        'model': 'chapter',
        'field_name': 'rating',
    }),
)


