# autoad/admin.py
from django.contrib import admin
from .models import AutoAdUser, AutoAdConfig, AutoAdDetail

@admin.register(AutoAdUser)
class AutoAdUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'username')
    search_fields = ('username',)

@admin.register(AutoAdConfig)
class AutoAdConfigAdmin(admin.ModelAdmin):
    list_display = ('user', 'universal_message')
    search_fields = ('user__username', 'universal_message')

@admin.register(AutoAdDetail)
class AutoAdDetailAdmin(admin.ModelAdmin):
    list_display = ('config', 'channel_id', 'usernames', 'slowmode_duration', 'channel_name', 'server_name', 'bot_running')
    search_fields = ('config__user__username', 'channel_name', 'server_name')
    list_filter = ('bot_running',)
