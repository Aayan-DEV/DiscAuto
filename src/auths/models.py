from django.db import models
from django.contrib.auth.models import User

# First we define a model named "UserProfile" that receives data from Django's Model Class. 
class UserProfile(models.Model):
    # Normal Fields.
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    pushover_user_key = models.CharField(max_length=255, blank=True, null=True)
    paypal_email = models.EmailField(blank=True, null=True)
    revolut_tag = models.CharField(blank=True, null=True)
    btc_wallet = models.CharField(max_length=255, blank=True, null=True)
    ltc_wallet = models.CharField(max_length=255, blank=True, null=True)
    sol_wallet = models.CharField(max_length=255, blank=True, null=True)
    eth_wallet = models.CharField(max_length=255, blank=True, null=True)
    usdt_bep20_wallet = models.CharField(max_length=255, blank=True, null=True)
    usdt_erc20_wallet = models.CharField(max_length=255, blank=True, null=True)
    usdt_prc20_wallet = models.CharField(max_length=255, blank=True, null=True)
    usdt_sol_wallet = models.CharField(max_length=255, blank=True, null=True)
    usdt_trc20_wallet = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.user.username

"""
Citations:
("Models") -> Lines 5 - 22
"""