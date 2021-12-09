from django import forms

class SentimentDisplayForm(forms.Form):
    subject = forms.CharField()
    
class GetNewNews(forms.Form):
    subject = forms.CharField()