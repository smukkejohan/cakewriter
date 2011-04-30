from usermessage.models import UserMessage
from django.contrib import admin

class UserMessageAdmin(admin.ModelAdmin):
    list_display = ('pk','contact', 'user', 'category', 'creation_date')

admin.site.register(UserMessage, UserMessageAdmin)