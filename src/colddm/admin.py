from django.contrib import admin
from .models import ColdDM, UserColdDMStats

# Admin class to manage ColdDM model in the Django admin
# It gets data from admin.ModelAdmin, which will provide it with a set of featues that will allow for customization. 
class ColdDMAdmin(admin.ModelAdmin):
    # 'list_display' is for the columns which are shown in the admin list view for ColdDM objects.
    list_display = ('username', 'user_id', 'note', 'saved_by')
    # 'search_fields' adds a search bar to the admin interface.
    # Admins can search by 'username' or 'user_id' to find specific ColdDMs.
    # This is useful for the admin of the website. 
    search_fields = ('username', 'user_id')
    # 'list_filter' adds a filter option in the admin interface.
    # This allows admins to filter ColdDMs by 'saved_by'.
    list_filter = ('saved_by',)
    
# Register ColdDM model with ColdDMAdmin configuration
admin.site.register(ColdDM, ColdDMAdmin)

# Admin class for managing UserColdDMStats in the Django admin
class UserColdDMStatsAdmin(admin.ModelAdmin):
    # 'list_display' is for the columns which are shown in the admin list view for UserColdDMStats.
    list_display = ('user', 'total_cold_dms_posted')
    # 'search_fields' adds a search bar where admins can search UserColdDMStats by the related user's username.
    search_fields = ('user__username',)

# Register UserColdDMStats model with UserColdDMStatsAdmin configuration
# We cannot register all 4 things at once, because django only allowed 2-3 per. 
admin.site.register(UserColdDMStats, UserColdDMStatsAdmin)



'''
Citations: 
("Document How to Extend UserAdmin") -> 6 - 29
'''

