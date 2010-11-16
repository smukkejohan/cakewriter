from dango import forms

class RatingForm(forms.Form):
    score = forms.IntegerField(max_value=5, min_value=0)
    
    