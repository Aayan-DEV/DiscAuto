from django import forms
from .models import AutoSell

# Here we define a form for the AutoSell model using Django's ModelForm.
class AutoSellForm(forms.ModelForm):
    class Meta:
        model = AutoSell
        # These are all the fields that have to be included in the AutoSell model.
        fields = [
            'banner',           # Field for uploading a banner image.
            'profile_picture',   # Field for uploading a profile picture.
            'name',              # The name of the user.
            'title',             # A title for the AutoSell page.
            'email',             # Email for the AutoSell page.
            'instagram_link',    # URL field for the AutoSell page.
            'tiktok_link',       # URL field for the AutoSell page.
            'custom_link'        # Field for specifying a custom link for the landing page.
        ]
