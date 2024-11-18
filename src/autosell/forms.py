from django import forms
from .models import AutoSell

class AutoSellForm(forms.ModelForm):
    class Meta:
        model = AutoSell
        fields = ['banner', 'profile_picture', 'name', 'title', 'email', 'instagram_link', 'tiktok_link', 'custom_link']

"""
Citations:
("Working with forms") -> Lines 4 - 7
"""