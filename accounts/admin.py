# -*- coding: utf-8 -*-

from django.contrib import admin
from accounts.models import Profile

class ProfileAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('user', 'score', 'level')
        }),
    )
    list_display = ('user', 'score', 'level')

admin.site.register(Profile, ProfileAdmin)