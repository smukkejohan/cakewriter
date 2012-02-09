from django.conf.urls.defaults import *
from django.conf import settings
from book.models import LatestChapterFeed
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()
from django.views.generic.simple import direct_to_template

urlpatterns = patterns('',
    
    url(r'^$', 'views.index', name='index'),
    
    (r'^book/', include('cakewriter.book.urls')),
    
    (r'^', include('accounts.urls')),
    
    (r'^accounts/', include('registration.urls')),
    
    (r'^rolemodels/$', include('pages.urls')),
    
    (r'^c/', include('django.contrib.comments.urls')),
    
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/', include(admin.site.urls)),
    (r'^edit/', direct_to_template, {'template': 'simplewiki_error.html'}),
    (r'^captcha/', include('captcha.urls')),
    (r'^tinymce/', include('tinymce.urls')),
    (r'^newsletters/', include('emencia.django.newsletter.urls')),
    (r'^subscribe/$', 'views.subscribe_resent_chapters'),
    (r'^usermessage/', include('usermessage.urls')),
    (r'^update_point_session/$', 'views.update_point_session'),
    (r'^rss/latest/$', LatestChapterFeed()),
    (r'^tagging_autocomplete/', include('tagging_autocomplete.urls')),
    #(r'^quiz/', include('quiz.urls'))
)



if settings.DEVELOPMENT_MODE:
    urlpatterns += patterns('django.views',
        url(r'%s(?P<path>.*)$' % settings.STATIC_URL[1:], 'static.serve', {
            'document_root': settings.STATIC_ROOT, 'show_indexes': True }),
    )