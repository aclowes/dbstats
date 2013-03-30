from django import forms

class ExplainForm(forms.Form):
    statement = forms.CharField(widget=forms.Textarea(attrs={'rows': 10}))
