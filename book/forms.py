from django import forms
from tinymce.widgets import TinyMCE

class ConfirmRatingForm(forms.Form):
    score = forms.IntegerField(max_value=5, min_value=0, widget=forms.HiddenInput)
    
class UserChapterForm(forms.Form):
    title = forms.CharField(max_length=90, help_text='<br />the title should be no more than 5 words')
    summary = forms.CharField(widget=TinyMCE(attrs={'cols': 100, 'rows': 10}), initial='Write a brief summary to present your chapter')
    content = forms.CharField(widget=TinyMCE(attrs={'cols': 100, 'rows': 50}), initial='Give us a hand... in no more than 600 words!')
    photo = forms.ImageField(required=False, help_text='<br />Upload a photo to go with your chapter')
    picture_description = forms.CharField(required=False)