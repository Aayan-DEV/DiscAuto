from django import forms
from .models import PayoutRequest
from decimal import Decimal

class PayoutRequestForm(forms.ModelForm):
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

    currency = forms.ChoiceField(choices=CURRENCY_CHOICES, label="Currency")

    class Meta:
        model = PayoutRequest
        fields = ['amount', 'currency', 'payment_method', 'contact_method', 'contact_info']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(PayoutRequestForm, self).__init__(*args, **kwargs)

        if user:
            user_profile = getattr(user, 'userprofile', None)
            if user_profile:
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
                self.fields['payment_method'].choices = [method for method in available_methods if method]

        self.fields['amount'].widget.attrs.update({'min': '0'})


    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        currency = self.cleaned_data.get('currency')
        
        if not currency:
            return amount
        
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

        min_value = Decimal(minimums.get(currency, 5))

        if amount < min_value:
            raise forms.ValidationError(f"The minimum payout for {currency} is {min_value}.")

        return amount
