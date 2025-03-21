from django.contrib import admin
from .models import PayoutRequest

class PayoutRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'currency', 'payout_method', 'status', 'created_at']
    list_filter = ['currency', 'payout_method', 'status']
    search_fields = ['user__username', 'payout_address']
    readonly_fields = ['created_at']
    
    fieldsets = [
        ('User Information', {'fields': ['user']}),
        ('Payout Details', {'fields': ['amount', 'currency', 'eur_equivalent', 'conversion_fee']}),
        ('Payment Method', {'fields': ['payout_method', 'payout_address']}),
        ('Status', {'fields': ['status']}),
        ('Timestamps', {'fields': ['created_at']}),
    ]

admin.site.register(PayoutRequest, PayoutRequestAdmin)
