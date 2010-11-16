from dango import forms

class ConfirmRatingForm(forms.Form):
    score = forms.IntegerField(max_value=5, min_value=0, widget=forms.HiddenInput)
    
    