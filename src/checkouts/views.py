from django.shortcuts import render, redirect
from django.urls import reverse
from subscriptions.models import SubscriptionPrice, Subscription, UserSubscription
import helpers.billing
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpResponseBadRequest
from django.contrib.auth.decorators import login_required  # Add this import at the top

BASE_URL = settings.BASE_URL
User = get_user_model()

def product_price_redirect_view(request, price_id=None, *args, **kwargs):
    """
    Save the chosen SubscriptionPrice ID to session and redirect to the checkout start view.
    """
    request.session['checkout_subscription_price_id'] = price_id
    return redirect('stripe-checkout-start')

@login_required  # Add this decorator
def checkout_redirect_view(request):
    """
    Retrieve the SubscriptionPrice object from session,
    create a Stripe Checkout Session for that price,
    and redirect the user to the Stripe hosted checkout page.
    """
    checkout_subscription_price_id = request.session.get('checkout_subscription_price_id')
    if checkout_subscription_price_id is None:
        return redirect('pricing')  # fallback if no price is chosen

    try:
        obj = SubscriptionPrice.objects.get(id=checkout_subscription_price_id)
    except SubscriptionPrice.DoesNotExist:
        return redirect('pricing')  # fallback if invalid price

    customer_stripe_id = request.user.customer.stripe_id
    # Construct success & cancel URLs.
    success_url_path = reverse("stripe-checkout-end")
    pricing_url_path = reverse("pricing")
    success_url = f"{BASE_URL}{success_url_path}"
    cancel_url = f"{BASE_URL}{pricing_url_path}"
    price_stripe_id = obj.stripe_id
    if not price_stripe_id:
        return redirect('pricing')  # fallback if not found in Stripe

    checkout_session_url = helpers.billing.start_checkout_session(
        customer_id=customer_stripe_id,
        success_url=success_url,
        cancel_url=cancel_url,
        price_stripe_id=price_stripe_id,
        raw=False,  # Return just the URL.
        customer_update={  # Add this parameter
            'address': 'auto',
            'shipping': 'auto'
        }
    )
    return redirect(checkout_session_url)

def checkout_finalize_view(request):
    """
    After successful payment, finalize the checkout by:
      1. Retrieving subscription details using the Stripe session_id.
      2. Updating (or creating) the UserSubscription record.
      3. Redirecting the user to where they were before checkout (if available).
    """
    session_id = request.GET.get('session_id')
    if not session_id:
        return render(request, "checkout/checkout_success.html", {
            'error': "Missing session_id parameter."
        })

    checkout_data = helpers.billing.get_checkout_customer_plan(session_id)
    if not checkout_data:
        return render(request, "checkout/checkout_success.html", {
            'error': "Unable to find checkout data."
        })

    plan_id = checkout_data.pop('plan_id')         # Price's stripe product ID.
    customer_id = checkout_data.pop('customer_id')   # Stripe customer ID.
    sub_stripe_id = checkout_data.pop('sub_stripe_id')  # The new subscription ID from Stripe.
    subscription_data = {**checkout_data}

    try:
        sub_obj = Subscription.objects.get(subscriptionprice__stripe_id=plan_id)
    except Subscription.DoesNotExist:
        sub_obj = None

    try:
        user_obj = User.objects.get(customer__stripe_id=customer_id)
    except User.DoesNotExist:
        user_obj = None

    if None in [sub_obj, user_obj]:
        return HttpResponseBadRequest("Invalid subscription or user.")

    updated_sub_options = {
        "subscription": sub_obj,
        "stripe_id": sub_stripe_id,
        "user_cancelled": False,
        **subscription_data,
    }

    try:
        user_sub_obj, created = UserSubscription.objects.get_or_create(user=user_obj)
        old_stripe_id = user_sub_obj.stripe_id
        if old_stripe_id and old_stripe_id != sub_stripe_id:
            try:
                helpers.billing.cancel_subscription(
                    old_stripe_id,
                    reason="Auto ended, new membership.",
                    feedback="other"
                )
            except Exception:
                pass

        for k, v in updated_sub_options.items():
            setattr(user_sub_obj, k, v)
        user_sub_obj.save()

        # Redirect to the page where the user was before checkout if stored.
        redirect_url = request.session.get('redirect_after_checkout', user_sub_obj.get_absolute_url())
        if 'redirect_after_checkout' in request.session:
            del request.session['redirect_after_checkout']
        return redirect(redirect_url)

    except Exception:
        return render(request, "checkout/checkout_success.html", {
            'error': "Error creating or updating user subscription."
        })

def checkout_cancel_view(request):
    """
    Render a dedicated checkout cancellation page.
    This view is for when a user cancels their Stripe checkout session.
    """
    return render(request, "checkout/cancel.html")
