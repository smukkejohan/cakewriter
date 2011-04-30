from django import forms
from accounts.models import Profile
from django.contrib.auth.models import User

class ProfileForm(forms.Form):
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)
    photo = forms.ImageField(required=False)
    firm = forms.CharField(max_length=100,required=False)
    facebook = forms.URLField(required=False)
    twitter = forms.URLField(required=False)
    www = forms.URLField(required=False)
    blog = forms.URLField(required=False)

class ProfileUserForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ProfileUserForm, self).__init__(*args, **kwargs)
        try:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
        except User.DoesNotExist:
            pass
    
    first_name  = forms.CharField(max_length=30, required=True)
    last_name  = forms.CharField(max_length=30, required=True)
    
    class Meta:
      model = Profile
      exclude = ('user','score','level')
      fields = ('first_name','last_name','photo','firm','facebook','twitter','www','blog')
    
    def save(self, *args, **kwargs):
      """
      Update the primary email address on the related User object as well. 
      """
      u = self.instance.user
      u.first_name = self.cleaned_data['first_name']
      u.last_name = self.cleaned_data['last_name']
      u.save()
      profile = super(ProfileUserForm, self).save(*args,**kwargs)
      return profile