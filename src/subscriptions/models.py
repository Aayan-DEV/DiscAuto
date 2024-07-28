from django.db import models
from django.contrib.auth.models import Group, Permission
from django.conf import settings
from django.db.models.signals import post_save
import helpers.billing

User = settings.AUTH_USER_MODEL

ALLOW_CUSTOM_GROUPS = True
SUBSCRIPTION_PERMISSIONS = [
    ("Paid", "Paid Perm"), # subscriptions.paid
    ("Free", "Free Perm"), # subscriptions.free
]

# Create your models here.
class Subscription(models.Model):
    """
    Subscription Plan = Stripe Product
    """

    name = models.CharField(max_length=120)
    active = models.BooleanField(default=True)
    groups = models.ManyToManyField(Group)
    permissions = models.ManyToManyField(Permission, limit_choices_to={"content_type__app_label":"subscriptions", "codename__in": [x[0]for x in SUBSCRIPTION_PERMISSIONS]})
    stripe_id = models.CharField(max_length=120, null=True, blank=True)
    def __str__(self):
        return f"{self.name}"

    class Meta:
        permissions = SUBSCRIPTION_PERMISSIONS

    def save(self, *args, **kwargs):
        if not self.stripe_id:
            stripe_id = helpers.billing.create_product(
                    name=self.name, 
                    metadata={
                        "subscription_plan_id": self.id, 
                        },raw=False)
            self.stripe_id = stripe_id
        super().save(*args, **kwargs)

class SubscriptionPrice(models.Model):
    """
    Subscription Price = Stripe Price
    """
    class IntervalChoices(models.TextChoices):
        MONTHLY = "month", "Monthly"
        WEEKLY = "week", "Weekly"
    
    subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True)
    stripe_id = models.CharField(max_length=120, null=True, blank=True)
    interval = models.CharField(max_length=120, default=IntervalChoices.MONTHLY,
                                choices=IntervalChoices.choices)

    price = models.DecimalField(max_digits=10, decimal_places=2, default=99.99)

    @property
    def stripe_currency(self):
        return "usd"
    
    @property
    def stripe_price(self):
        """
        Remove decimal places
        """
        return int(self.price * 100)

    @property
    def product_stripe_id(self):
        if not self.subscription:
            return None
        return self.subscription.stripe_id
    
    def save(self, *args, **kwargs):
        if (self.stripe_id and self.stripe_id is not None):
            stripe_id = helpers.billing.create_price(
            currency=self.stripe_currency,
            unit_amount=1000,
            interval=self.interval,
            product=self.product_stripe_id,
            metadata={
                "subscription_plan_price_id": self.id,
            },
            raw=False
            )
            self.stripe_id = stripe_id
        super().save(*args, **kwargs)
    

class UserSubscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True, blank=True)
    active = models.BooleanField(default=True)

def user_sub_post_save(sender, instance, *args, **kwargs):
    user_sub_instance = instance
    user = user_sub_instance.user
    subscription_obj = user_sub_instance.subscription
    groups_ids = []
    if subscription_obj is not None:
        groups = subscription_obj.groups.all()
        group_ids = groups.values_list('id', flat=True)
    if not ALLOW_CUSTOM_GROUPS:
        user.groups.set(group_ids)
    else:
        subs_qs = Subscription.objects.filter(active=True)
        if subscription_obj is not None:
            subs_qs = subs_qs.exclude(id=subscription_obj.id)
        subs_groups = subs_qs.values_list('groups__id', flat=True)
        subs_groups_Set = set(subs_groups)
        # groups_ids = groups.values_list('id', flat=True)
        current_groups = user.groups.all().values_list('id', flat=True)
        groups_ids_set = set(groups_ids)
        current_groups_set = set(current_groups) - subs_groups_Set
        final_group_ids = list(groups_ids_set | current_groups_set)
        user.groups.set(final_group_ids)

post_save.connect(user_sub_post_save, sender=UserSubscription)