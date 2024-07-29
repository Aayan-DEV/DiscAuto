from django.shortcuts import render, redirect
from django.urls import reverse
from subscriptions.models import SubscriptionPrice, UserSubscription
from django.contrib.auth.decorators import login_required
import helpers.billing

@login_required
def user_subscription_view(request):
    user_sub_obj, created = UserSubscription.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        if user_sub_obj.stripe_id:
            sub_data = helpers.billing.get_subscription(user_sub_obj.stripe_id, raw=False)
            for k,v in sub_data.items():
                setattr(user_sub_obj, k, v)
                user_sub_obj.save()
        return redirect(user_sub_obj.get_absolute_url())
    return render(request, 'subscriptions/user_detail_view.html', {"subscription": user_sub_obj})

# Create your views here.
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