# -*- coding: utf-8 -*-

from django.contrib import admin
from book.models import Chapter, UserChapter

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

class UserChapterAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('title', 'summary', 'body', 'picture')
        }),
        ('Meta', {
            'fields': ('author', 'pub_date', 'index')
         }),
        ('Html version (do not change it)', {
            'classes': ('collapse',),
            'fields': ('summary_html', 'body_html')
        }),
    )
    list_display = ('title', 'pub_date', 'index')
    list_filter = ['pub_date']
    
    def make_chapter_public(self, request, queryset):
        from django.db.models import Max
        antal=0
        for userchapter in queryset:
            highest_index = Chapter.objects.aggregate(Max('index'))
            index = highest_index['index__max']+1
            chapter = Chapter(title=userchapter.title,
                               summary=userchapter.summary,
                               summary_html=userchapter.summary_html,
                               body=userchapter.body,
                               body_html=userchapter.body_html,
                               mod_date=userchapter.pub_date,
                               pub_date=userchapter.pub_date,
                               index=index,
                               author=userchapter.author,
                               user_created=True,
                               visible=True,
                               picture=userchapter.picture)
            chapter.save()
            userchapter.delete()
            antal+=1
        self.message_user(request, '%s successfully made public.' % antal)
    
    make_chapter_public.short_description = 'Make chapter public'
    actions = ['make_chapter_public']
admin.site.register(UserChapter, UserChapterAdmin)
admin.site.register(Chapter, ChapterAdmin)