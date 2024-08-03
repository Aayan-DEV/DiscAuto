from django import forms

class DataForm(forms.Form):
    token = forms.CharField(max_length=255, required=True, label='Token')
    channel_id = forms.IntegerField(required=True, label='Channel ID')

class StopBotForm(forms.Form):
    confirm = forms.BooleanField(required=True, label='Confirm Stop')
