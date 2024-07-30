from django.shortcuts import render, redirect
from django.urls import reverse
from subscriptions.models import SubscriptionPrice, UserSubscription
from django.contrib.auth.decorators import login_required
import helpers.billing
from django.contrib import messages
from subscriptions import utils as subs_utils

@login_required
def user_subscription_view(request):
    user_sub_obj, created = UserSubscription.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        finished = subs_utils.refresh_active_users_subscriptions(user_ids=[request.user.id])
        if finished:
            messages.success(request, 'Your plan details have been updated.')
        else:
            messages.error(request, 'An error occurred while updating your plan details. Please try again later.')
        return redirect(user_sub_obj.get_absolute_url())
    
    if user_sub_obj.cancel_at_period_end:
        status_display = f"Your subscription is CANCELLED, you will lose access to all premium features on {user_sub_obj.current_period_end}."
    else:
        status_display = f"Your subscription is ACTIVE, you will get charged again on {user_sub_obj.current_period_end}."
    
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
            sub_data = helpers.billing.cancel_subscription(
                user_sub_obj.stripe_id, 
                reason="User wanted to end", 
                feedback="other", 
                cancel_at_period_end=True,  # Set this to True
                raw=False
            )
            for k, v in sub_data.items():
                setattr(user_sub_obj, k, v)
            user_sub_obj.save()
        return redirect(user_sub_obj.get_absolute_url())
    return render(request, 'subscriptions/user_cancel_view.html', {"subscription": user_sub_obj})

def subscription_price_view(request, interval="week"):
    qs = SubscriptionPrice.objects.filter(featured=True)
    inv_wk = SubscriptionPrice.IntervalChoices.WEEKLY
    inv_mo = SubscriptionPrice.IntervalChoices.MONTHLY
    object_list = qs.filter(interval=inv_wk)
    url_path_name = "pricing_interval"
    wk_url = reverse(url_path_name, kwargs={"interval": inv_wk})
    mo_url = reverse(url_path_name, kwargs={"interval": inv_mo})
    active = inv_wk
    if interval == inv_mo:
        active = inv_mo
        object_list = qs.filter(interval=inv_mo)
    return render(request, 'subscriptions/pricing.html', {
        "object_list": object_list,
        "wk_url": wk_url,
        "mo_url": mo_url,
        "active": active,
    })
