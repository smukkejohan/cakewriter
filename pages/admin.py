from pages.models import Frontpage, Editpage, Rolemodels, Rolemodelpage
from django.contrib import admin
from django.utils.text import truncate_words

class RolemodelsAdmin(admin.ModelAdmin):
    def Content(self, obj):
        return truncate_words(obj.content,10)
    fieldsets = (
        (None, {
            'fields': ('name', 'content', 'picture')
        }),
    )
    list_display = ('name', 'Content', 'picture')
    
admin.site.register(Frontpage)
admin.site.register(Editpage)
admin.site.register(Rolemodels, RolemodelsAdmin)
admin.site.register(Rolemodelpage)