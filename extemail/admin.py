from django import forms
from django.contrib import admin

from tinymce.widgets import TinyMCE
from emencia.django.newsletter.models import Newsletter
from emencia.django.newsletter.admin import NewsletterAdmin


class NewsletterTinyMCEForm(forms.ModelForm):
    content = forms.CharField(widget=TinyMCE(attrs={'cols': 100, 'rows': 50}), initial='<body><div style="width:100%; height:100%; margin:0px; background-color:#d3d8dd;"><div style="background-color:#d3d8dd;"><div style="padding:50px 0px 50px 0px;"><div style="margin:0px auto 0px auto; background-color:#FFF; width:600px; padding-bottom:30px;font-family: Helvetica, Verdana, Arial, sans-serif;-moz-box-shadow:  0px 0px 50px 0px #3d3d3d; -webkit-box-shadow: 0px 0px 50px 0px #3d3d3d; box-shadow: 0px 0px 50px 0px #3d3d3d;"><div style="height:50px;background-color:#01a3d4; padding:40px 0px 40px 30px; font-size:20px; font-weight: bold; font-size: 50px; color:#FFF; text-shadow: #000 0px -1px 0px;">Updates from WWL</div><div style="margin:50px 50px 0px 50px; color:#565454;"><p>Hi {{contact.content_object.username}}</p><p></p><p>----Write here----</p><p></p><p>Winning Without Losing</p><p>www.winning-without-losing.com</p></div></div></div></div></div></body>')

    class Meta:
        model = Newsletter

class NewsletterTinyMCEAdmin(NewsletterAdmin):
    form = NewsletterTinyMCEForm

admin.site.unregister(Newsletter)
admin.site.register(Newsletter, NewsletterTinyMCEAdmin)