from django import forms
from .models import PayoutRequest
from decimal import Decimal

class PayoutRequestForm(forms.ModelForm):
    class Meta:
        model = PayoutRequest
        fields = ['amount', 'currency', 'payout_method', 'payout_address']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'payout_address': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Add help text about conversion fee
        self.fields['currency'].help_text = "Note: A 2% conversion fee applies for payouts in USD and GBP. No fee for EUR payouts."
        
        # Add JavaScript to show/hide conversion fee warning
        self.fields['currency'].widget.attrs.update({
            'onchange': 'showConversionFeeWarning(this.value)'
        })
        
        # Customize the payout method field based on currency
        self.fields['payout_method'].widget.attrs.update({
            'class': 'form-control',
            'id': 'payout_method'
        })
        
        self.fields['payout_address'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your payout address'
        })