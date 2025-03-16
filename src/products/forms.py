from django import forms
from .models import OneTimeProductCategory, OneTimeProduct, UnlimitedProduct
from autosell.models import LandingPage  # Add this import
from helpers.supabase import upload_to_supabase

# Add this new form class
class OneTimeProductCategoryForm(forms.ModelForm):
    class Meta:
        model = OneTimeProductCategory
        fields = ['name', 'category_image']
        # Exclude landing_pages as we'll handle it in the view
        widgets = {
            'category_image': forms.ClearableFileInput(attrs={
                'class': 'block w-full text-gray-900 px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-blue-500 focus:border-blue-500',
            }),
        }

    def save(self, commit=True):
        category = super().save(commit=False)
        
        if self.cleaned_data.get('category_image'):
            category_image = self.cleaned_data['category_image']
            # Note: The actual upload to Supabase happens in the view
            
        if commit:
            category.save()
        return category

class OneTimeProductForm(forms.ModelForm):
    class Meta:
        model = OneTimeProduct
        fields = [
            'title', 'description', 'price', 'sale_price', 
            'ltc_price', 'btc_price', 'eth_price', 'usdt_price', 
            'sol_price', 'test_price', 'discount_percentage', 
            'currency', 'product_content'  # Remove 'landing_pages' from here
        ]

    def save(self, commit=True):
        product = super().save(commit=False)
        
        if self.cleaned_data.get('product_image'):
            product_image = self.cleaned_data['product_image']
            product.product_image_url = upload_to_supabase(product_image, folder='one_time_products')
            product.product_image = None 

        if commit:
            product.save()
            self.save_m2m()  # Save many-to-many relationships
        return product

# Your UnlimitedProductForm should handle landing_pages correctly
class UnlimitedProductForm(forms.ModelForm):
    class Meta:
        model = UnlimitedProduct
        fields = [
            'title', 'price', 'sale_price', 'ltc_price', 'btc_price', 
            'eth_price', 'usdt_price', 'sol_price', 'test_price', 
            'discount_percentage', 'currency', 'sku', 'quantity', 
            'link', 'description', 'product_image'
            # Removed 'landing_page' from here
        ]

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            # We'll keep this for future reference if needed
            pass

    def save(self, commit=True):
        product = super().save(commit=False)
        
        # Here we upload to Supabase and store URL only
        if self.cleaned_data.get('product_image'):
            product_image = self.cleaned_data['product_image']
            product.product_image_url = upload_to_supabase(product_image, folder='unlimited_products')
            # Here we clear the local image field
            product.product_image = None 

        if commit:
            product.save()
            
            # Handle landing pages manually
            if 'landing_pages' in self.data:
                landing_page_ids = self.data.getlist('landing_pages')
                product.landing_pages.clear()
                for page_id in landing_page_ids:
                    if page_id:  # Skip empty values
                        product.landing_pages.add(page_id)
            
        return product
 
"""
Citations:
("Working with forms") -> Lines 6 - 80
"""

