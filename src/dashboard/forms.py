from django import forms
from .models import PayoutRequest
from decimal import Decimal

# Here we define the PayoutRequestForm class.
class PayoutRequestForm(forms.ModelForm):
    # First we define the available currency choices for the form:
    CURRENCY_CHOICES = [
        ('USD', 'USD - United States Dollar'), 
        ('GBP', 'GBP - British Pound'),
        ('EUR', 'EUR - Euro'), 
        ('BTC', 'BTC - Bitcoin'), 
        ('LTC', 'LTC - Litecoin'),  
        ('SOL', 'SOL - Solana'),  
        ('ETH', 'ETH - Ether (ETH)'), 
        ('USDT.BEP20', 'USDT - Tether (USDT) BEP20'),
        ('USDT.ERC20', 'USDT - Tether (USDT) ERC20'),  
        ('USDT.PRC20', 'USDT - Tether (USDT) PRC20'), 
        ('USDT.SOL20', 'USDT - Tether (USDT) SOL20'), 
        ('USDT.TRC20', 'USDT - Tether (USDT) TRC20'), 
    ]

    # Then we create a dropdown field for currency selection.
    currency = forms.ChoiceField(choices=CURRENCY_CHOICES, label="Currency")

    # The Meta class is used to define which model and fields the form is based on (The PayoutRequest Form)
    class Meta:
        # Here we link the form to the PayoutRequest model
        model = PayoutRequest  
        # We also include fields for payout amount, currency, payment method, and contact details
        fields = ['amount', 'currency', 'payment_method', 'contact_method', 'contact_info']  
       

    # Here we initialize the form, which then makes it possible for customizations based on the user's profile
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(PayoutRequestForm, self).__init__(*args, **kwargs)

        # If a user is provided, we then customize the payment method options
        if user:
            # Here we go to the user's profile to get their payment methods
            user_profile = getattr(user, 'userprofile', None)
            if user_profile:
                # Then we create a list of available payment methods which the user sets, based on the user's saved wallet details
                available_methods = [
                    ('paypal_email', 'PayPal') if user_profile.paypal_email else None,
                    ('revolut_tag', 'Revolut') if user_profile.revolut_tag else None,
                    ('btc_wallet', 'Bitcoin') if user_profile.btc_wallet else None,
                    ('ltc_wallet', 'Litecoin') if user_profile.ltc_wallet else None,
                    ('sol_wallet', 'Solana') if user_profile.sol_wallet else None,
                    ('eth_wallet', 'Ethereum') if user_profile.eth_wallet else None,
                    ('usdt_bep20_wallet', 'USDT BEP20') if user_profile.usdt_bep20_wallet else None,
                    ('usdt_erc20_wallet', 'USDT ERC20') if user_profile.usdt_erc20_wallet else None,
                    ('usdt_prc20_wallet', 'USDT PRC20') if user_profile.usdt_prc20_wallet else None,
                    ('usdt_sol_wallet', 'USDT SOL') if user_profile.usdt_sol_wallet else None,
                    ('usdt_trc20_wallet', 'USDT TRC20') if user_profile.usdt_trc20_wallet else None,
                ]
                # Then we filter out None values and assign the remaining methods to the payment_method field, so only the payment method
                # the user has set is shown in the dropdown menu.
                self.fields['payment_method'].choices = [method for method in available_methods if method]

        # We also set a minimum value of 0 for the amount input field to make sure the user cannot put negative values
        self.fields['amount'].widget.attrs.update({'min': '0'})

    # This is a method to validate the payout amount field, so that the final amount is all correct and all error checking 
    # has been done.
    def clean_amount(self):
        # Here we get the amount and currency fields from the cleaned data
        amount = self.cleaned_data.get('amount')
        currency = self.cleaned_data.get('currency')
        
        # If no currency is selected, we can return the amount as it is
        if not currency:
            return amount
        
        # Here we define the minimum payout amounts for each currency.
        minimums = {
            'USD': 5,  
            'GBP': 4, 
            'EUR': 4.5,  
            'BTC': 0.0001, 
            'LTC': 0.01, 
            'SOL': 0.05, 
            'ETH': 0.002,  
            'USDT.BEP20': 5, 
            'USDT.ERC20': 10, 
            'USDT.PRC20': 5,  
            'USDT.SOL20': 5,  
            'USDT.TRC20': 1,  
        }

        # Here we get the minimum value for the selected currency, if the minimum is not set, the defauly is set to 5
        min_value = Decimal(minimums.get(currency, 5))

        # Here we make sure that if the entered amount is less than the minimum then we raise an error
        if amount < min_value:
            raise forms.ValidationError(f"The minimum payout for {currency} is {min_value}.")

        # Finally we return the final amount. 
        return amount

"""
Citations:
("Working with forms") -> Lines 6 - 100
"""