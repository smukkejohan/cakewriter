# -*- coding: utf-8 -*-

from django.contrib import admin
from accounts.models import Profile, ScoreLog

class ScoreLogInline(admin.TabularInline):
    model = ScoreLog


class ProfileAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('user', 'score', 'level')
        }),
    )
    list_display = ('user', 'score', 'level')
    inlines = [
        ScoreLogInline,
    ]
    
admin.site.register(Profile, ProfileAdmin)