from django.contrib import admin
from django.urls import path, include
from .views import home_view,about_view, pw_proted_view, user_only_view, staff_only_view, contact
from subscriptions import views as subscriptions_views
from checkouts import views as checkout_views
from landing import views as landing_views
from autoad import views as autoad_views
from colddm import views as colddm_views
from autodm import views as autodm_views
from products import views as products_views
from ticketbot import views as ticketbot_views
from tickets import views as tickets_views
from auths import views as auths_views

urlpatterns = [
    path("auths/",auths_views.auths, name="auths"),
    path("tickets/",tickets_views.tickets, name="tickets"),
    path("ticket-bot/",ticketbot_views.ticket_bot, name="ticket_bot"),
    path("products/",products_views.products, name="products"),
    path("auto-dm/",autodm_views.auto_dm, name="auto_dm"),
    path("contact/", contact, name="contact"),
    path("auto-ad/",autoad_views.auto_ad, name="auto_ad"),
    path("cold-dm/", colddm_views.cold_dm, name="cold_dm"),
    path("", landing_views.landing_dashboard_page_view, name="dashboard"),
    path('accounts/billing/cancel', subscriptions_views.user_subscription_cancel_view, name="user_subscription_cancel"),
    path('accounts/billing/', subscriptions_views.user_subscription_view, name="user_subscription"),
    path('accounts/', include('allauth.urls')),
    path('profiles/', include('profiles.urls')),
    # path("register/", auth_views.register_view),
    path("hello-world/", home_view),
    # path("login/", auth_views.login_view),
    path("about/", about_view),
    path("", home_view, name="home"),
    path('admin/', admin.site.urls),
    path('protected/', pw_proted_view),
    path('protected/user-only/', user_only_view),
    path('protected/staff-only/', staff_only_view),
    path('pricing/', subscriptions_views.subscription_price_view, name="pricing"),
    path('pricing/<str:interval>/', subscriptions_views.subscription_price_view, name="pricing_interval"),
    path("checkout/sub-price/<int:price_id>/", checkout_views.product_price_redirect_view, name='sub-price-checkout'),
    path("checkout/start/", checkout_views.checkout_redirect_view, name='stripe-checkout-start'),
    path("checkout/success/", checkout_views.checkout_finalize_view, name='stripe-checkout-end'),
]
