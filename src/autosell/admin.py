from django.contrib import admin
from .models import AutoSell, AutoSellView, SocialLink

class SocialLinkInline(admin.TabularInline):
    model = SocialLink
    extra = 1

@admin.register(AutoSell)
class AutoSellAdmin(admin.ModelAdmin):
    list_display = ['name', 'title', 'email', 'custom_link', 'show_social_names']  # Add show_social_names
    search_fields = ['name', 'title', 'email', 'custom_link']
    inlines = [SocialLinkInline]

@admin.register(AutoSellView)
class AutoSellViewAdmin(admin.ModelAdmin):
    list_display = ['auto_sell', 'timestamp', 'ip_address']
    list_filter = ['timestamp']
    search_fields = ['auto_sell__name']

@admin.register(SocialLink)
class SocialLinkAdmin(admin.ModelAdmin):
    list_display = ['auto_sell', 'platform', 'url']
    list_filter = ['platform']
    search_fields = ['auto_sell__name', 'platform', 'url']

    