from django.db import models
from django.contrib.auth.models import User

class PayoutRequest(models.Model):
    PAYMENT_METHODS = [
        ('paypal_email', 'PayPal'),
        ('btc_wallet', 'Bitcoin'),
        ('ltc_wallet', 'Litecoin'),
        ('sol_wallet', 'Solana'),
        ('eth_wallet', 'Ethereum'),
        ('usdt_bep20_wallet', 'USDT BEP20'),
        ('usdt_erc20_wallet', 'USDT ERC20'),
        ('usdt_prc20_wallet', 'USDT PRC20'),
        ('usdt_sol_wallet', 'USDT SOL'),
        ('usdt_trc20_wallet', 'USDT TRC20'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10)
    payment_method = models.CharField(max_length=255, choices=PAYMENT_METHODS)
    contact_method = models.CharField(max_length=50)
    contact_info = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.amount} {self.currency}"
