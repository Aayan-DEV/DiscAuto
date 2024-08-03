from django.shortcuts import render
from django.http import Http404
from subscriptions.models import UserSubscription
from django.contrib.auth.decorators import login_required

# Create your views here.
@login_required
def auto_dm(request):
    user_subscription = UserSubscription.objects.filter(user=request.user).first()
    if not user_subscription or user_subscription.subscription.name.lower() != "pro plan":
        raise Http404("This page does not exist.")
    return render(request, "features/auto-dm/auto-dm.html", {})