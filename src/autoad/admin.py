from django.contrib import admin 
from .models import Channels

# ChannelsAdmin is a class used to customize how the channels models apear in the Django admin interface. 
# It gets data from admin.ModelAdmin, which will provide it with a set of featues that will allow for customization. 
class ChannelsAdmin(admin.ModelAdmin):
    # List_display tells the fields to be displayed in the list view of the Channels model in the admin interface. 
    list_display = ('channel_name', 'channel_id', 'user', 'start_time')
    # The search_fields makes a search bar in the admin to search by specified fields, and it tells what is possible to search (channel name, channel id, etc...)
    search_fields = ('channel_name', 'channel_id', 'user__username')
    # The list_filter makes a dropdown menu in the admin where you can filter by specified fields, and it tells what is possible to filter (user, etc...)
    list_filter = ('user',)
# Here we register the channels model with the custom ChannelsAdmin class to control how it looks in the Django admin page.
admin.site.register(Channels, ChannelsAdmin)