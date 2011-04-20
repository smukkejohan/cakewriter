from pages.models import Frontpage, Editpage, Rolemodels, Rolemodelpage
from django.contrib import admin
    
class RolemodelsAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('name', 'content', 'picture')
        }),
    )
    list_display = ('name', 'content', 'picture')
    
admin.site.register(Frontpage)
admin.site.register(Editpage)
admin.site.register(Rolemodels, RolemodelsAdmin)
admin.site.register(Rolemodelpage)