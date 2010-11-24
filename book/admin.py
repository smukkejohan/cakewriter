# -*- coding: utf-8 -*-

from django.contrib import admin
from book.models import Chapter

class ChapterAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('title', 'summary', 'body')
        }),
        ('Meta', {
            'fields': ('author', 'pub_date', 'mod_date', 'index')
         }),
    )
    list_display = ('title', 'pub_date', 'mod_date', 'index')
    list_filter = ['pub_date', 'mod_date']

admin.site.register(Chapter, ChapterAdmin)