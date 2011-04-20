# -*- coding: utf-8 -*-

from django.contrib import admin
from book.models import Chapter

class ChapterAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('title', 'summary', 'body', 'user_created', 'visible', 'picture')
        }),
        ('Meta', {
            'fields': ('author', 'pub_date', 'mod_date', 'index')
         }),
        ('Html version (do not change it)', {
            'classes': ('collapse',),
            'fields': ('summary_html', 'body_html')
        }),
    )
    list_display = ('title', 'pub_date', 'mod_date', 'index','visible','user_created')
    list_filter = ['pub_date', 'mod_date']

admin.site.register(Chapter, ChapterAdmin)