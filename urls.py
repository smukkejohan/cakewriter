from django.conf.urls.defaults import *
from django.conf import settings

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    
    url(r'^$', 'views.index', name='index'),
    
    (r'^book/', include('cakewriter.book.urls')),
    
    #(r'^u/', include('accounts.urls')),
    
    (r'^accounts/', include('registration.urls')),
    
    (r'^c/', include('django.contrib.comments.urls')),
    
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/', include(admin.site.urls)),
)


if settings.DEVELOPMENT_MODE:
    urlpatterns += patterns('django.views',
        url(r'%s(?P<path>.*)$' % settings.MEDIA_URL[1:], 'static.serve', {
            'document_root': settings.MEDIA_ROOT, 'show_indexes': True }),
    )