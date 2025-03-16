from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class SocialLink(models.Model):
    SOCIAL_TYPES = [
        ('youtube', 'YouTube'),
        ('tiktok', 'TikTok'),
        ('instagram', 'Instagram'),
        ('twitter', 'Twitter'),
        ('pinterest', 'Pinterest'),
        ('discord', 'Discord Server'),
        ('snapchat', 'Snapchat'),
        ('custom', 'Custom Link')
    ]

    auto_sell = models.ForeignKey('AutoSell', on_delete=models.CASCADE, related_name='social_links')
    platform = models.CharField(max_length=20, choices=SOCIAL_TYPES)
    url = models.URLField(max_length=500)
    title = models.CharField(max_length=100, blank=True, null=True)  # For custom link title

    def __str__(self):
        return f"{self.get_platform_display()} - {self.auto_sell.name}"

class AutoSell(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    banner = models.ImageField(upload_to='banners/', max_length=500)  
    profile_picture = models.ImageField(upload_to='profiles/', max_length=500) 
    name = models.CharField(max_length=200)
    title = models.CharField(max_length=200)
    email = models.EmailField(blank=True, null=True)
    custom_link = models.CharField(max_length=200, unique=True)
    show_social_names = models.BooleanField(default=False)  # Changed default to False

    def __str__(self):
        return self.name

class AutoSellView(models.Model):
    auto_sell = models.ForeignKey(
        AutoSell, 
        on_delete=models.CASCADE, 
        related_name='views',
        null=True,  # Add this to allow null values
        blank=True  # Add this to allow blank values in forms
    )
    timestamp = models.DateTimeField(default=timezone.now)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    def __str__(self):
        return f"View of {self.auto_sell.name if self.auto_sell else 'Unknown'} at {self.timestamp}"

    class Meta:
        ordering = ['-timestamp']


class LandingPage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    unlimited_products = models.ManyToManyField(
        'products.UnlimitedProduct', 
        blank=True, 
        related_name='landing_page_unlimited'
    )
    one_time_products = models.ManyToManyField(
        'products.OneTimeProduct', 
        blank=True,
        related_name='landing_page_onetime'  # Keep only this, remove the through parameter
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']