from usermessage.models import UserMessage, StandardUserMessage
from django.contrib import admin
from django.utils.text import truncate_words

class UserMessageAdmin(admin.ModelAdmin):
    list_display = ('pk','contact', 'user', 'category', 'creation_date')
class StandardUserMessageAdmin(admin.ModelAdmin):
    def Content(self, obj):
        return truncate_words(obj.content,10)
    list_display = ('pk', 'Content')
admin.site.register(UserMessage, UserMessageAdmin)
admin.site.register(StandardUserMessage, StandardUserMessageAdmin)