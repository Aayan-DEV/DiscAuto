from django.contrib import admin
from django.urls import path, include
from .views import home_view, contact
from subscriptions import views as subscriptions_views
from checkouts import views as checkout_views
from landing import views as landing_views
from autoad import views as autoad_views
from colddm import views as colddm_views
from products import views as products_views
from auths import views as auths_views
from autosell import views as autosell_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('accounts/', include('allauth.urls')),
    path('profiles/', include('profiles.urls')),
    path("hello-world/", home_view),
    path("", landing_views.landing_dashboard_page_view, name="dashboard"),  
    path("", home_view, name="home"),
    path("contact/", contact, name="contact"),
    path('admin/', admin.site.urls),
    path('checkout/one-time/success/', products_views.one_time_checkout_success, name='one_time_checkout_success'),
    path('create_one_time_checkout_session/<int:product_id>/', products_views.create_one_time_checkout_session, name='create_one_time_checkout_session'),
    path('auto-sell/', autosell_views.auto_sell_view, name='auto_sell'),
    path('pricing/', subscriptions_views.subscription_price_view, name="pricing"),
    path('accounts/billing/cancel', subscriptions_views.user_subscription_cancel_view, name="user_subscription_cancel"),
    path('accounts/billing/', subscriptions_views.user_subscription_view, name="user_subscription"),
    path("checkout/success/", checkout_views.checkout_finalize_view, name='stripe-checkout-end'),
    path("checkout/start/", checkout_views.checkout_redirect_view, name='stripe-checkout-start'),
    path('checkout-success/', products_views.checkout_success, name='checkout_success'),
    path('products/', products_views.products, name='products'),
    path('refresh-sales/', products_views.refresh_sales, name='refresh_sales'),
    path('products/add/', products_views.add_product_options, name='add_product_options'),
    path('products/add/category/', products_views.add_category, name='add_category'),
    path('products/add/unlimited/', products_views.add_unlimited_product, name='add_unlimited_product'),
    path('checkout/success/', products_views.checkout_success, name='stripe-checkout-end'),
    path('checkout/cancel/', products_views.checkout_cancel, name='checkout_cancel'),
    path("auths/", auths_views.auths, name="auths"), 
    path('cold-dm/', colddm_views.cold_dm_view, name='cold_dm'),
    path('auto-ad/', autoad_views.auto_ad, name='auto_ad'),
    path('auto-ad/save-channel/', autoad_views.auto_ad, name='save_channel'),
    path('auto-ad/delete-channel/', autoad_views.delete_channel, name='delete_channel'),
    path('send-timer-expiry-email/', autoad_views.send_timer_expiry_email, name='send_timer_expiry_email'),
    path('confirm-ad-posted/', autoad_views.confirm_ad_posted, name='confirm_ad_posted'),
    path('confirm-ad-posted/', autoad_views.confirm_ad_posted, name='confirm-ad-posted'),
    path('delete-channel/', autoad_views.delete_channel, name='delete-channel'),
    path('auto-ad/confirm-ad-posted/', autoad_views.confirm_ad_posted, name='confirm-ad-posted'), 
    path('coinpayments-ipn/', products_views.coinpayments_ipn, name='coinpayments_ipn'),
    path('create_crypto_transaction/<int:product_id>/<str:product_type>/', products_views.create_crypto_transaction, name='create_crypto_transaction'),
    path('seller/<int:product_id>/', autosell_views.get_seller_page, name='get_seller_page'),
    path('auto-sell/delete/<int:auto_sell_id>/', autosell_views.delete_lander, name='delete_lander'),
    path('live-search/<str:custom_link>/', autosell_views.live_search, name='live_search'),
    path("checkout/sub-price/<int:price_id>/", checkout_views.product_price_redirect_view, name='sub-price-checkout'),
    path('pricing/<str:interval>/', subscriptions_views.subscription_price_view, name="pricing_interval"),
    path('cold-dm/delete/<str:user_id>/', colddm_views.delete_cold_dm, name='delete_cold_dm'),
    path('cold-dm/update/<str:user_id>/', colddm_views.update_cold_dm, name='update_cold_dm'),  
    path('create-checkout-session/<int:product_id>/', products_views.create_checkout_session, name='create_checkout_session'),
    path('products/edit/unlimited/<int:pk>/', products_views.edit_unlimited_product, name='edit_unlimited_product'),
    path('products/edit/category/<int:pk>/', products_views.edit_category, name='edit_category'),
    path('products/delete/unlimited/<int:pk>/', products_views.delete_unlimited_product, name='delete_unlimited_product'),
    path('unlimited-product/<int:product_id>/', products_views.unlimited_product_detail, name='unlimited_product_detail'),
    path('one-time-product/<int:product_id>/', products_views.one_time_product_detail, name='one_time_product_detail'),
    path('category/<int:category_id>/', products_views.category_detail, name='category_detail'),
    path('products/delete/one-time/<int:pk>/', products_views.delete_one_time_product, name='delete_one_time_product'),
    path('products/category/<int:category_id>/add/', products_views.add_product_to_category, name='add_product_to_category'),
    path('products/delete/category/<int:pk>/', products_views.delete_category, name='delete_category'),
    path('products/edit/one-time/<int:pk>/', products_views.edit_one_time_product, name='edit_one_time_product'),
    path('products/delete/one-time/<int:pk>/', products_views.delete_one_time_product, name='delete_one_time_product'),
    path('<str:custom_link>/', autosell_views.custom_landing_page, name='custom_landing_page'),
    path('<str:custom_link>/increment-view-count/', autosell_views.increment_view_count, name='increment_view_count'),
    path('confirm-timer/<str:channel_id>/', autoad_views.confirm_ad_posted, name='confirm_timer'),
    
     # TEMPORARY PATHS: 

    # path('products/categories/', products_views.one_time_product_categories, name='one_time_product_categories'),
    # path('products/category/<int:category_id>/', products_views.category_detail, name='category_detail'),
    # path('product/<str:product_type>/<int:product_id>/', products_views.product_detail, name='product_detail'),
    # path('product/<int:product_id>/', products_views.one_time_product_detail, name='one_time_product_detail'),
    # path('auto-ad/save-channel/', autoad_views.save_channel, name='save-channel'),
    # path('get_timers/', autoad_views.get_timers, name='get_timers'),
    # path('get_timer/<str:channel_id>/', autoad_views.get_timer, name='get_timer'),  # For individual timer
    

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
