from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.db.models.signals import post_save
from django.urls import reverse
from django.db.models import Q
from django.utils import timezone
import datetime

User = get_user_model()

ALLOW_CUSTOM_GROUPS = True
SUBSCRIPTION_PERMISSIONS = [
    ("pro", "Pro Perm"),  # subscriptions.pro
    ("starter", "Starter Perm"),  # subscriptions.starter
]

class Subscription(models.Model):
    """
    Subscription Plan = Stripe Product
    """
    name = models.CharField(max_length=120)
    subtitle = models.TextField(blank=True, null=True)
    active = models.BooleanField(default=True)
    groups = models.ManyToManyField(Group)
    permissions = models.ManyToManyField(
        Permission,
        limit_choices_to={
            "content_type__app_label": "subscriptions",
            "codename__in": [x[0] for x in SUBSCRIPTION_PERMISSIONS],
        },
    )
    stripe_id = models.CharField(max_length=120, null=True, blank=True)

    order = models.IntegerField(default=-1, help_text="Ordering on Django pricing page")
    featured = models.BooleanField(default=True, help_text="Featured on the pricing page.")
    updated = models.DateTimeField(auto_now=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name}"

    class Meta:
        ordering = ["order", "featured", "-updated"]
        permissions = SUBSCRIPTION_PERMISSIONS

    def save(self, *args, **kwargs):
        if not self.stripe_id:
            from helpers.billing import create_product
            stripe_id = create_product(
                name=self.name,
                metadata={
                    "subscription_plan_id": self.id,
                },
                raw=False,
            )
            self.stripe_id = stripe_id
        super().save(*args, **kwargs)


class SubscriptionPrice(models.Model):
    """
    Subscription Price = Stripe Price
    """

    class IntervalChoices(models.TextChoices):
        MONTHLY = "month", "Monthly"
        WEEKLY = "week", "Weekly"
        YEARLY = "year", "Annual"

    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, null=True)
    stripe_id = models.CharField(max_length=120, null=True, blank=True)
    interval = models.CharField(
        max_length=120, default=IntervalChoices.MONTHLY, choices=IntervalChoices.choices
    )

    price = models.DecimalField(max_digits=10, decimal_places=2, default=99.99)
    order = models.IntegerField(default=-1, help_text="Ordering on Django pricing page")
    featured = models.BooleanField(default=True, help_text="Featured on the subscription page.")
    updated = models.DateTimeField(auto_now=True)
    timestamp = models.DateTimeField(auto_now_add=True)
        
    class Meta:
        ordering = ["subscription__order", "order", "featured", "-updated"]

    def get_checkout_url(self):
        return reverse("sub-price-checkout", kwargs={"price_id": self.id})

    @property
    def display_sub_name(self):
        if not self.subscription:
            return "Plan"
        return self.subscription.name
    
    @property
    def display_sub_subtitle(self):
        if not self.subscription:
            return "Plan"
        return self.subscription.subtitle

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_price = self.price
        self._original_interval = self.interval

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
        is_new = not self.pk
        if is_new and not self.stripe_id and self.product_stripe_id is not None:
            from helpers.billing import create_price
            stripe_id = create_price(
                currency=self.stripe_currency,
                unit_amount=self.stripe_price,
                interval=self.interval,
                product=self.product_stripe_id,
                metadata={"subscription_plan_price_id": self.id},
                raw=False,
            )
            self.stripe_id = stripe_id
        else:
            if self.stripe_id and (self.price != self._original_price or self.interval != self._original_interval):
                from helpers.billing import delete_price, create_price
                delete_price(self.stripe_id)
                new_stripe_id = create_price(
                    currency=self.stripe_currency,
                    unit_amount=self.stripe_price,
                    interval=self.interval,
                    product=self.product_stripe_id,
                    metadata={"subscription_plan_price_id": self.id},
                    raw=False,
                )
                self.stripe_id = new_stripe_id

        super().save(*args, **kwargs)
        self._original_price = self.price
        self._original_interval = self.interval
        if self.featured and self.subscription:
            qs = SubscriptionPrice.objects.filter(
                subscription=self.subscription, interval=self.interval
            ).exclude(id=self.id)
            qs.update(featured=False)


class SubscriptionStatus(models.TextChoices):
    ACTIVE = "active", 'Active'
    TRAILING = "trailing", 'Trailing'
    INCOMPLETE = "incomplete", 'Incomplete'
    INCOMPLETE_EXPIRED = "incomplete_expired", 'Incomplete Expired'
    PAST_DUE = "past_due", 'Past Due'
    CANCELLED = "cancelled", 'Cancelled'
    UNPAID = "unpaid", 'Unpaid'
    PAUSED = "paused", 'Paused'

class UserSubscriptionQuerySet(models.QuerySet):
    def by_range(self, days_start=7, days_end=120):
            now = timezone.now()
            days_start_from_now = now + datetime.timedelta(days=days_start)
            days_end_from_now = now + datetime.timedelta(days=days_end)
            range_start = days_start_from_now.replace(hour=0, minute=0, second=0, microsecond=0)
            range_end = days_end_from_now.replace(hour=23, minute=59, second=59, microsecond=59)
            return self.filter(
                current_period_end__gte = range_start,
                current_period_end__lte = range_end
            )

    def by_days_left(self, days_left=7):
            now = timezone.now()
            in_n_days = now + datetime.timedelta(days=days_left)
            day_start = in_n_days.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = in_n_days.replace(hour=23, minute=59, second=59, microsecond=59)
            return self.filter(
                current_period_end__gte = day_start,
                current_period_end__lte = day_end
            )
    
    def by_days_ago(self, days_ago=3):
            now = timezone.now()
            in_n_days = now - datetime.timedelta(days=days_ago)
            day_start = in_n_days.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = in_n_days.replace(hour=23, minute=59, second=59, microsecond=59)
            return self.filter(
                current_period_end__gte = day_start,
                current_period_end__lte = day_end
            )

    def by_active_trialing(self):
        active_qs_lookup = (
            Q(status = SubscriptionStatus.ACTIVE) |
            Q(status = SubscriptionStatus.TRAILING)
        )
        return self.filter(active_qs_lookup)
    def by_user_ids(self, user_ids=None):
        qs = self
        if isinstance(user_ids, list):
            qs = self.filter(user_id__in=user_ids)
        elif isinstance(user_ids, int):
            qs = self.filter(user_id__in=[user_ids])
        elif isinstance(user_ids, str):
            qs = self.filter(user_id__in=[user_ids])
        return qs

class UserSubscriptionManager(models.Manager):
    def get_queryset(self):
        return UserSubscriptionQuerySet(self.model, using=self._db)
    
class UserSubscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True, blank=True)
    stripe_id = models.CharField(max_length=120, null=True, blank=True)
    active = models.BooleanField(default=True)
    user_cancelled = models.BooleanField(default=False)
    original_period_start = models.DateTimeField(auto_now=False, auto_now_add=False, null=True, blank=True)
    current_period_start = models.DateTimeField(auto_now=False, auto_now_add=False, null=True, blank=True)
    current_period_end = models.DateTimeField(auto_now=False, auto_now_add=False, null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)
    status = models.CharField(max_length=20,choices=SubscriptionStatus.choices, null=True, blank=True)

    objects = UserSubscriptionManager()

    def get_absolute_url(self):
        return reverse("user_subscription")
    
    def get_cancel_url(self):
        return reverse("user_subscription_cancel")
    
    @property
    def is_active_status(self):
        return self.status in [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRAILING]
    
    @property
    def plan_name(self):
        if not self.subscription:
            return "No Plan"
        return self.subscription.name

    def serialize(self):
        return {
            "plan_name": self.plan_name,
            "status": self.status,
            "current_period_start": self.current_period_start,
            "current_period_end": self.current_period_end,
        }

    @property
    def billing_cycle_anchor(self):
        """
        https://docs.stripe.com/payments/checkout/billing-cycle
        Optional delay to start new subscription in Stripe Checkout
        """
        if not self.current_period_end:
            return None
        return int(self.current_period_end.timestamp())

    def save(self, *args, **kwargs):
        if (self.original_period_start is None and self.current_period_start is not None):
            self.original_period_start = self.current_period_start
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user.username} - {self.plan_name}"

def user_sub_post_save(sender, instance, *args, **kwargs):
    user_sub_instance = instance
    user = user_sub_instance.user
    subscription_obj = user_sub_instance.subscription
    if subscription_obj is not None:
        groups = subscription_obj.groups.all()
        group_ids = groups.values_list("id", flat=True)
        if not ALLOW_CUSTOM_GROUPS:
            user.groups.set(group_ids)
        else:
            subs_qs = Subscription.objects.filter(active=True)
            if subscription_obj is not None:
                subs_qs = subs_qs.exclude(id=subscription_obj.id)
            subs_groups = subs_qs.values_list("groups__id", flat=True)
            subs_groups_set = set(subs_groups)
            current_groups = user.groups.all().values_list("id", flat=True)
            current_groups_set = set(current_groups) - subs_groups_set
            final_group_ids = list(set(group_ids) | current_groups_set)
            user.groups.set(final_group_ids)

post_save.connect(user_sub_post_save, sender=UserSubscription)

class SubscriptionFeature(models.Model):
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name="feature_set"
    )
    title = models.CharField(max_length=255, help_text="Short title or name of the feature.")
    icon = models.ImageField(
        upload_to="subscription_features/",
        max_length=500,  # Increased to store longer URLs
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.subscription.name} - {self.title}"

    def save(self, *args, **kwargs):
        # If an icon is provided and it doesn't already start with 'http',
        # upload it to Supabase and replace its value with the returned URL.
        if self.icon and not str(self.icon).startswith("http"):
            from helpers.supabase import upload_to_supabase
            public_url = upload_to_supabase(self.icon, folder="subscription_features")
            # Store the public URL instead of a local file path.
            self.icon = public_url
        super().save(*args, **kwargs)

    @property
    def icon_url(self):
        """
        Returns the icon URL:
          - If the stored value starts with 'http', assume it’s an external URL.
          - Otherwise, use the built-in .url attribute.
        """
        if self.icon:
            icon_str = str(self.icon)
            if icon_str.startswith("http"):
                return icon_str
            return self.icon.url
        return None