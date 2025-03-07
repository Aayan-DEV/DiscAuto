from subscriptions.models import UserSubscription, Subscription, SubscriptionStatus
from customers.models import Customer
import helpers.billing
from django.db.models import Q

def refresh_active_users_subscriptions(
        user_ids=None, 
        active_only=True, 
        days_left=0, 
        days_ago=0,  
        day_start=0,
        day_end=0,
        verbose=False):
    qs = UserSubscription.objects.all()
    if active_only:
        qs = qs.by_active_trialing()
    if user_ids is not None:
        qs = qs.by_user_ids(user_ids=user_ids)
    if days_ago > 0:
        qs = qs.by_days_ago(days_ago=days_ago)
    if days_left > 0:
        qs = qs.by_days_left(days_left=days_left)
    if day_start > 0 and day_end > 0:
        qs = qs.by_range(days_start=day_start, days_end=day_end)
    complete_count = 0
    qs_count = qs.count()
    for obj in qs:
        if verbose:
            print("Updating user", obj.user, "subscription", obj.current_period_end)
        if obj.stripe_id:
            sub_data = helpers.billing.get_subscription(obj.stripe_id, raw=False)
            for k, v in sub_data.items():
                setattr(obj, k, v)
            obj.save()
            complete_count += 1
    return complete_count == qs_count

def clear_dangling_subs():
    qs = Customer.objects.filter(stripe_id__isnull=False)
    for customer_obj in qs:
        user = customer_obj.user
        customer_stripe_id = customer_obj.stripe_id
        print(f"Sync {user} - {customer_stripe_id} subs and remove old ones")
        try:
            subs = helpers.billing.get_customer_active_subscriptions(customer_stripe_id)
        except Exception as e:
            print(f"Error retrieving subscriptions for {customer_stripe_id}: {e}")
            continue

        for sub in subs:
            try:
                existing_user_subs_qs = UserSubscription.objects.filter(stripe_id__iexact=f"{sub.id}".strip())
                if existing_user_subs_qs.exists():
                    continue
                helpers.billing.cancel_subscription(sub.id, reason="Active Subscriptions which are NOT being used and are Dangling.", cancel_at_period_end=False, raw=True)
                print(sub.id, existing_user_subs_qs.exists())
            except Exception as e:
                print(f"Error cancelling subscription {sub.id}: {e}")


def syc_subs_group_permissions():
    qs = Subscription.objects.filter(active=True)
    for obj in qs:
        sub_perms = obj.permissions.all()
        for group in obj.groups.all():
            group.permissions.set(sub_perms)
        
