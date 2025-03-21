from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal

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

    CURRENCY_CHOICES = [
        ('EUR', 'EUR'),  # Make EUR the first/default choice
        ('USD', 'USD'),
        ('GBP', 'GBP'),
        ('BTC', 'BTC'),
        ('LTC', 'LTC'),
        ('SOL', 'SOL'),
        ('ETH', 'ETH'),
        ('USDT.BEP20', 'USDT (BEP20)'),
        ('USDT.ERC20', 'USDT (ERC20)'),
        ('USDT.PRC20', 'USDT (PRC20)'),
        ('USDT.TRC20', 'USDT (TRC20)'),
        ('USDT.SOL', 'USDT (SOL)'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, choices=CURRENCY_CHOICES, default='EUR')  # Set default to EUR
    payout_method = models.CharField(max_length=255, choices=PAYMENT_METHODS)
    payout_address = models.CharField(max_length=255)
    eur_equivalent = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    conversion_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=20, default='pending', choices=[
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.amount} {self.currency}"


"""
Citations:
("Models") -> Lines 4 - 27
"""