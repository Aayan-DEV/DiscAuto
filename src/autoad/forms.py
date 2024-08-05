# forms.py
from django import forms

class DataForm(forms.Form):
    channel_id = forms.IntegerField(required=True, label='Channel ID')

class StopBotForm(forms.Form):
    confirm = forms.BooleanField(required=True, label='Confirm Stop')
