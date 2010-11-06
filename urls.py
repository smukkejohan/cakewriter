from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    
    url(r'^$', 'views.index', name='index'),
    
    (r'^book/', include('cakewriter.book.urls')),
    
    #(r'^u/', include('accounts.urls')),
    
    (r'^c/', include('django.contrib.comments.urls')),
    
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/', include(admin.site.urls)),
)
