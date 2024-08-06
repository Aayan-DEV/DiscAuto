from django import forms
from auths.models import DiscordToken

class DataForm(forms.Form):
    channel_id = forms.IntegerField(required=True, label='Channel ID')
    universal_message = forms.CharField(required=False, label='Universal Message', widget=forms.Textarea(attrs={'rows': 4, 'cols': 40}))
    token = forms.MultipleChoiceField(label='Select User(s)', choices=[], widget=forms.CheckboxSelectMultiple)

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(DataForm, self).__init__(*args, **kwargs)
        if user:
            tokens = DiscordToken.objects.filter(user=user)
            token_choices = [(token.token, token.username or token.token) for token in tokens]
            token_choices.append(('all', 'Select All'))
            self.fields['token'].choices = token_choices

class UniversalMessageForm(forms.Form):
    universal_message = forms.CharField(required=False, label='Universal Message', widget=forms.Textarea(attrs={'rows': 4, 'cols': 40}))
