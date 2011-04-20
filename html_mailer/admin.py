from django.contrib import admin
from html_mailer.models import Message, DontSendEntry, MessageLog, Organizer

class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'to_address', 'subject', 'when_added', 'priority')

class DontSendEntryAdmin(admin.ModelAdmin):
    list_display = ('to_address', 'when_added')

class MessageLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'to_address', 'subject', 'when_attempted', 'result')

class OrganizerAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'when_added')
    
admin.site.register(Message, MessageAdmin)
admin.site.register(DontSendEntry, DontSendEntryAdmin)
admin.site.register(MessageLog, MessageLogAdmin)
admin.site.register(Organizer, OrganizerAdmin)