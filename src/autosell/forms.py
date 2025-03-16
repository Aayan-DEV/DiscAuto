from django import forms
from .models import AutoSell, SocialLink, LandingPage  # Add LandingPage here

class SocialLinkForm(forms.ModelForm):
    class Meta:
        model = SocialLink
        fields = ['platform', 'url', 'title']
        widgets = {
            'platform': forms.Select(attrs={'class': 'social-platform-select'}),
            'url': forms.URLInput(attrs={'class': 'social-url-input'}),
            'title': forms.TextInput(attrs={'class': 'social-title-input'})
        }

class AutoSellForm(forms.ModelForm):
    class Meta:
        model = AutoSell
        fields = ['banner', 'profile_picture', 'name', 'title', 'email', 'custom_link']

class LandingPageForm(forms.ModelForm):
    class Meta:
        model = LandingPage
        fields = ['name', 'slug', 'unlimited_products', 'one_time_products']
        widgets = {
            'unlimited_products': forms.CheckboxSelectMultiple(),
            'one_time_products': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            # Filter products by user
            self.fields['unlimited_products'].queryset = UnlimitedProduct.objects.filter(user=user)
            self.fields['one_time_products'].queryset = OneTimeProduct.objects.filter(category__user=user)

"""
Citations:
("Working with forms") -> Lines 4 - 7
"""