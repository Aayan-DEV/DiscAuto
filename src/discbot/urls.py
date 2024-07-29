from django.contrib import admin
from django.urls import path, include 
from auth import views as auth_views
from .views import home_view,about_view, pw_proted_view, user_only_view, staff_only_view
from subscriptions import views as subscriptions_views
from checkouts import views as checkout_views

urlpatterns = [
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
