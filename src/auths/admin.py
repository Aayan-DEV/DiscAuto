from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from django.contrib.auth.models import User
from .models import DiscordToken

class DiscordTokenInline(admin.TabularInline):
    model = DiscordToken
    extra = 1

class CustomUserAdmin(DefaultUserAdmin):
    inlines = [DiscordTokenInline]

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
