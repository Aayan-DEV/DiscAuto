from subscriptions.models import UserSubscription

def subscription_plan(request):
    subscription_plan_name = None
    subscription_interval = None

    if request.user.is_authenticated:
        user_subscription = UserSubscription.objects.filter(user=request.user).first()
        if user_subscription and user_subscription.subscription:
            subscription_plan_name = user_subscription.subscription.name.lower()
            subscription_price = user_subscription.subscription.subscriptionprice_set.first()
            if subscription_price:
                subscription_interval = subscription_price.interval

    return {
        'subscription_plan_name': subscription_plan_name,
        'subscription_interval': subscription_interval,
    }
