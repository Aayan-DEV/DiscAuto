from django.contrib import admin
from django.urls import path, include
from .views import home_view, contact
from subscriptions import views as subscriptions_views
from checkouts import views as checkout_views
from landing import views as landing_views
from products import views as products_views
from auths import views as auths_views
from autosell import views as autosell_views
from django.conf import settings
from django.conf.urls.static import static
from dashboard import views as dashboard_views

urlpatterns = [
    path('accounts/', include('allauth.urls')),
    path('profiles/', include('profiles.urls')),
    path('auto-sell/', autosell_views.auto_sell_list, name='auto_sell_list'),  # Main listing page
    path('auto-sell/create/', autosell_views.create_auto_sell, name='create_auto_sell'),  # Create new page
    path('auto-sell/edit/<int:auto_sell_id>/', autosell_views.edit_auto_sell, name='edit_auto_sell'),  # Edit existing page
    path('auto-sell/delete/<int:auto_sell_id>/', autosell_views.delete_lander, name='delete_lander'),  # Delete page
    path("hello-world/", home_view),
    path("", landing_views.landing_dashboard_page_view, name="dashboard"),  
    path('dashboard/get-chart-data/', dashboard_views.get_chart_data, name='get_chart_data'),
    path('dashboard/get-summary-data/', dashboard_views.get_summary_data, name='get_summary_data'),  # New endpoint
    path('dashboard/refresh-income/', dashboard_views.refresh_income, name='refresh_income'),
    # Add this new URL pattern for get_sale_details
    path('products/get-sale-details/<int:sale_id>/', products_views.get_sale_details, name='get_sale_details'),
    path("", home_view, name="home"),
    path("contact/", contact, name="contact"),
    path('admin/', admin.site.urls),
    path('checkout/one-time/success/', products_views.one_time_checkout_success, name='one_time_checkout_success'),
    # The URL pattern should already exist, but make sure it's correct
    path('create_one_time_checkout_session/<int:product_id>/', products_views.create_one_time_checkout_session, name='create_one_time_checkout_session'),
    path('pricing/', subscriptions_views.pricing_view, name='pricing'),
    path('accounts/billing/cancel', subscriptions_views.user_subscription_cancel_view, name="user_subscription_cancel"),
    path('accounts/billing/', subscriptions_views.user_subscription_view, name="user_subscription"),
    path('pricing/', subscriptions_views.pricing_page, name='pricing'),
    path('resubscribe/<int:price_id>/', subscriptions_views.user_subscription_resubscribe_view, name='user_subscription_resubscribe'),    
    path("checkout/success/", checkout_views.checkout_finalize_view, name='stripe-checkout-end'),
    path("checkout/start/", checkout_views.checkout_redirect_view, name='stripe-checkout-start'),
    # Use the checkout cancel view from checkouts/views.py:
    path("checkout/cancel/", checkout_views.checkout_cancel_view, name='stripe-checkout-cancel'),
    path('checkout-success/', products_views.checkout_success, name='checkout_success'),
    path('products/', products_views.products, name='products'),
    path('products/add/', products_views.add_product_options, name='add_product_options'),
    path('products/add/category/', products_views.add_category, name='add_category'),
    path('products/add/unlimited/', products_views.add_unlimited_product, name='add_unlimited_product'),
    path("auths/", auths_views.auths, name="auths"), 
    path('coinpayments-ipn/', products_views.coinpayments_ipn, name='coinpayments_ipn'),
    path('create_crypto_transaction/<int:product_id>/<str:product_type>/', products_views.create_crypto_transaction, name='create_crypto_transaction'),
    path('seller/<int:product_id>/', autosell_views.get_seller_page, name='get_seller_page'),
    path('auto-sell/delete/<int:auto_sell_id>/', autosell_views.delete_lander, name='delete_lander'),
    path('live-search/<str:custom_link>/', autosell_views.live_search, name='live_search'),
    path("checkout/sub-price/<int:price_id>/", checkout_views.product_price_redirect_view, name='sub-price-checkout'),
    path('create-checkout-session/<int:product_id>/', products_views.create_checkout_session, name='create_checkout_session'),
    path('checkout/cancel/', products_views.checkout_cancel, name='checkout_cancel'),
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
    
    # TEMPORARY PATHS: 
    # path('products/category/<int:category_id>/', products_views.category_detail, name='category_detail'),
    # path('product/<str:product_type>/<int:product_id>/', products_views.product_detail, name='product_detail'),
    # path('product/<int:product_id>/', products_views.one_time_product_detail, name='one_time_product_detail'),
    # path('refresh-sales/', products_views.refresh_sales, name='refresh_sales'),
    # Replace the existing auto-sell URL with these new ones
    # Update these URL patterns
]

if settings.DEBUG:
    # Add this to your urlpatterns
    urlpatterns += [
        path('landing/<str:slug>/', autosell_views.landing_page_view, name='landing_page_view'),
    ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
