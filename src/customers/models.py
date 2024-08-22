from django.conf import settings
from django.db import models
import helpers.billing

from allauth.account.signals import (
    user_signed_up as allauth_user_signed_up,
    email_confirmed as allauth_email_confirmed
)
from allauth.socialaccount.models import SocialAccount

User = settings.AUTH_USER_MODEL

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    stripe_id = models.CharField(max_length=120, null=True, blank=True)
    init_email = models.EmailField(null=True, blank=True)
    init_email_comfirmed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}"
    
    def save(self, *args, **kwargs):
        if not self.stripe_id and self.init_email_comfirmed and self.init_email:
            email = self.user.email
            if email != "" or email is not None:
                stripe_id = helpers.billing.create_customer(
                    name=self.user.username,  
                    email=email,
                    metadata={
                        "user_id": self.user.id, 
                        "username": self.user.username 
                    }, 
                    raw=False
                )
                self.stripe_id = stripe_id
        super().save(*args, **kwargs)

def allauth_user_signed_up_handler(request, user, *args, **kwargs):
    email = user.email
    social_account_exists = SocialAccount.objects.filter(user=user).exists()
    init_email_confirmed = social_account_exists
    customer = Customer.objects.create(user=user, init_email=email, init_email_comfirmed=init_email_confirmed)
    if init_email_confirmed:
        customer.save()

allauth_user_signed_up.connect(allauth_user_signed_up_handler)

def allauth_email_confirmed_handler(request, email_address, *args, **kwargs):
    qs = Customer.objects.filter(init_email=email_address.email, init_email_comfirmed=False)
    for obj in qs:
        obj.init_email_comfirmed = True
        obj.save()

allauth_email_confirmed.connect(allauth_email_confirmed_handler)
