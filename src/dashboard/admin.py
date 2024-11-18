from django.contrib import admin
from .models import PayoutRequest

@admin.register(PayoutRequest)
class PayoutRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'currency', 'payment_method', 'contact_method', 'contact_info', 'created_at')
    search_fields = ('user__username', 'email', 'currency', 'payment_method')
    list_filter = ('currency', 'payment_method', 'created_at')
    ordering = ('-created_at',)

'''
Citations: 
("The Django Admin") -> 4 - 9
'''
