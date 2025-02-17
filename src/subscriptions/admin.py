from django.contrib import admin
from .models import Subscription, UserSubscription, SubscriptionPrice

class SubscriptionPriceInline(admin.StackedInline):
    model = SubscriptionPrice
    readonly_fields = ['stripe_id']
    can_delete = False
    extra = 0

class SubscriptionAdmin(admin.ModelAdmin):
    inlines = [SubscriptionPriceInline]
    list_display = ['name', 'active']
    readonly_fields = ['stripe_id']

@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan_name')

# Register the Subscription model
admin.site.register(Subscription, SubscriptionAdmin)
