from django.contrib import admin
from .models import AutoSell, AutoSellView

@admin.register(AutoSell)
class AutoSellAdmin(admin.ModelAdmin):
    # These are the fields which will be displayed in the list view of the AutoSell objects in the admin panel.
    list_display = (
        'name',              # Name of the user.
        'title',             # Title of the AutoSell page.
        'email',             # User's email for the autosell page.
        'instagram_link',    # Instagram profile link for the autosell page.
        'tiktok_link',       # TikTok profile link for the autosell page.
        'custom_link',       # Custom slug for the AutoSell landing page.
        'total_views'        # A calculated field for displaying the total number of views.
    )

    # Custom method to calculate the total number of views for the AutoSell instance.
    def total_views(self, obj):
        # Count the AutoSellView instance associated with the current AutoSell object.
        return AutoSellView.objects.filter(autosell=obj).count()
    
    # Set a more human-readable label for the 'total_views' column in the admin panel.
    total_views.short_description = 'Total Views'



    