from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from subscriptions.models import SubscriptionPrice, UserSubscription, Subscription, SubscriptionStatus
from django.contrib.auth.decorators import login_required
import helpers.billing
from django.contrib import messages
from subscriptions import utils as subs_utils
from django.conf import settings
import stripe

@login_required
def user_subscription_view(request):
    user_sub_obj, created = UserSubscription.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        finished = subs_utils.refresh_active_users_subscriptions(user_ids=[request.user.id], active_only=False)
        if finished:
            messages.success(request, 'Your plan details have been updated successfully.')
        else:
            if not user_sub_obj.stripe_id:
                messages.error(request, 'You do not have an active subscription with us. Please contact support if you believe this is an error.')
            else:
                messages.error(request, 'An error occurred while updating your plan details. Please try again later or contact support for assistance.')
        return redirect(user_sub_obj.get_absolute_url())
    
    if user_sub_obj.cancel_at_period_end:
        status_display = f"Your subscription is CANCELLED. You will lose access to premium features on {user_sub_obj.current_period_end}."
    elif user_sub_obj.current_period_end:
        status_display = f"Your subscription is ACTIVE. You will be charged again on {user_sub_obj.current_period_end}."
    else:
        status_display = "You do not have an active subscription. Please consider subscribing to one of our plans."
    
    return render(request, 'subscriptions/user_detail_view.html', {
        "subscription": user_sub_obj,
        "status_display": status_display,
        "current_period_end": user_sub_obj.current_period_end,
    })

@login_required
def user_subscription_cancel_view(request):
    user_sub_obj, created = UserSubscription.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        if user_sub_obj.stripe_id and user_sub_obj.is_active_status:
            try:
                sub_data = helpers.billing.cancel_subscription(
                    user_sub_obj.stripe_id, 
                    reason="User wanted to end", 
                    feedback="other", 
                    cancel_at_period_end=True,  
                    raw=False
                )
                for k, v in sub_data.items():
                    setattr(user_sub_obj, k, v)
                user_sub_obj.save()
                messages.success(request, 'Your subscription has been cancelled.')
            except Exception as e:
                messages.error(request, f"An error occurred while cancelling your subscription: {e}")
        return redirect(user_sub_obj.get_absolute_url())
    return render(request, 'subscriptions/user_cancel_view.html', {"subscription": user_sub_obj})

def pricing_view(request):
    """
    Renders a pricing page with:
      - A FREE plan card.
      - All active paid subscription plans.
      - For each plan, if the user’s current subscription matches both the plan and its interval:
          * If cancelled, show a "Resubscribe to ..." button.
          * Otherwise, show a disabled "Current Plan" button.
      - All other intervals show the upgrade/downgrade or buy options.
    """
    subs_qs = Subscription.objects.filter(active=True).order_by('order')
    plans_data = []
    for sub in subs_qs:
        weekly_price = None
        monthly_price = None
        yearly_price = None
        for price_obj in sub.subscriptionprice_set.all():
            if price_obj.interval == SubscriptionPrice.IntervalChoices.WEEKLY:
                weekly_price = price_obj
            elif price_obj.interval == SubscriptionPrice.IntervalChoices.MONTHLY:
                monthly_price = price_obj
            elif price_obj.interval == SubscriptionPrice.IntervalChoices.YEARLY:
                yearly_price = price_obj
        plans_data.append({
            'subscription': sub,
            'weekly_price': weekly_price,
            'monthly_price': monthly_price,
            'yearly_price': yearly_price,
        })

    paid_plans_exist = any(
        pd['weekly_price'] or pd['monthly_price'] or pd['yearly_price']
        for pd in plans_data
    )

    current_subscription = None
    if request.user.is_authenticated:
        try:
            user_sub_obj = UserSubscription.objects.get(user=request.user)
            current_subscription = user_sub_obj
            # If there's a Stripe subscription, fetch the interval from Stripe
            if user_sub_obj.stripe_id:
                stripe.api_key = settings.STRIPE_SECRET_KEY
                stripe_sub = stripe.Subscription.retrieve(user_sub_obj.stripe_id)
                # Get the price ID from the Stripe subscription
                price_id = stripe_sub['plan']['id'] if stripe_sub['plan'] else None
                if price_id:
                    try:
                        price_obj = SubscriptionPrice.objects.get(stripe_id=price_id)
                        current_subscription.interval = price_obj.interval  # e.g., 'week', 'month', 'year'
                        current_subscription.plan_id = price_obj.subscription.id
                    except SubscriptionPrice.DoesNotExist:
                        current_subscription.interval = None
                        current_subscription.plan_id = user_sub_obj.subscription.id if user_sub_obj.subscription else None
                else:
                    current_subscription.interval = None
                    current_subscription.plan_id = user_sub_obj.subscription.id if user_sub_obj.subscription else None
            else:
                # No Stripe subscription; use the linked Subscription object if it exists
                current_subscription.interval = None
                current_subscription.plan_id = user_sub_obj.subscription.id if user_sub_obj.subscription else None
        except UserSubscription.DoesNotExist:
            current_subscription = None

    context = {
        'plans_data': plans_data,
        'paid_plans_exist': paid_plans_exist,
        'current_subscription': current_subscription,
    }
    return render(request, 'subscriptions/pricing.html', context)

@login_required
def user_subscription_resubscribe_view(request, price_id):
    user_sub_obj, created = UserSubscription.objects.get_or_create(user=request.user)
    price_obj = get_object_or_404(SubscriptionPrice, id=price_id)
    
    if not user_sub_obj.subscription or user_sub_obj.subscription.id != price_obj.subscription.id:
        messages.error(request, "You do not have a cancelled subscription for this plan.")
        return redirect("user_subscription")
    
    try:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        stripe.Subscription.modify(
            user_sub_obj.stripe_id,
            cancel_at_period_end=False,
            proration_behavior="none",
        )
        user_sub_obj.cancel_at_period_end = False
        user_sub_obj.user_cancelled = False
        user_sub_obj.status = SubscriptionStatus.ACTIVE
        user_sub_obj.save()
        messages.success(request, "Your subscription has been resumed for free!")
    except Exception as e:
        messages.error(request, f"An error occurred while resuming your subscription: {str(e)}")
    
    return redirect("user_subscription")

def pricing_page(request):
    plans = Subscription.objects.filter(active=True).order_by('order')
    context = {
        'plans': plans,
    }
    return render(request, 'subscriptions/pricing.html', context)