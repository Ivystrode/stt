from django import forms

class UserSearchForm(forms.Form):
    user = forms.CharField()
    numtweets = forms.IntegerField()
    
class ActivateTweetStreamerForm(forms.Form):
    keywords = forms.CharField()
    duration = forms.IntegerField()
    
class TweetSubjectSentimentForm(forms.Form):
    subject = forms.CharField()
    
# class GetNewsForm(forms.Form):
#     subject = forms.CharField()