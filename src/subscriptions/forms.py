from django import forms
from subscriptions.models import SubscriptionFeature

class SubscriptionFeatureForm(forms.ModelForm):
    class Meta:
        model = SubscriptionFeature
        fields = ["subscription", "title", "icon"]
