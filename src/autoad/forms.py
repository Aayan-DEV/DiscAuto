from django import forms
from auths.models import DiscordToken

class DataForm(forms.Form):
    channel_id = forms.IntegerField(required=True, label='Channel ID')
    token = forms.MultipleChoiceField(label='Select Token(s)', choices=[], widget=forms.CheckboxSelectMultiple)

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(DataForm, self).__init__(*args, **kwargs)
        if user:
            tokens = DiscordToken.objects.filter(user=user)
            token_choices = [(token.token, token.username or token.token) for token in tokens]
            token_choices.append(('all', 'Select All'))
            self.fields['token'].choices = token_choices

class StopBotForm(forms.Form):
    tokens = forms.MultipleChoiceField(label='Select Token(s) to Stop', choices=[], widget=forms.CheckboxSelectMultiple)

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(StopBotForm, self).__init__(*args, **kwargs)
        if user:
            tokens = DiscordToken.objects.filter(user=user)
            token_choices = [(token.token, token.username or token.token) for token in tokens]
            self.fields['tokens'].choices = token_choices
