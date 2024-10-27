from django import forms
from .models import OneTimeProductCategory, OneTimeProduct, UnlimitedProduct

class OneTimeProductCategoryForm(forms.ModelForm):
    class Meta:
        model = OneTimeProductCategory
        fields = ['name', 'category_image', 'show_on_custom_lander']
        widgets = {
            'category_image': forms.ClearableFileInput(attrs={
                'class': 'block w-full text-gray-900 px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-blue-500 focus:border-blue-500',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Override the widget to remove the "Clear" checkbox
        self.fields['category_image'].widget.can_clear = False

class OneTimeProductForm(forms.ModelForm):
    class Meta:
        model = OneTimeProduct
        fields = ['title', 'price', 'sale_price', 'ltc_price', 'btc_price', 'eth_price', 'usdt_price', 'sol_price', 'test_price', 'discount_percentage', 'currency', 'description', 'product_content']  
        widgets = {
            'product_image': forms.ClearableFileInput(), 
        }

class UnlimitedProductForm(forms.ModelForm):
    class Meta:
        model = UnlimitedProduct
        fields = ['title', 'price', 'sale_price', 'ltc_price', 'btc_price', 'eth_price', 'usdt_price', 'sol_price', 'test_price', 'discount_percentage', 'currency', 'sku', 'quantity', 'link', 'description', 'product_image', 'show_on_custom_lander']
        widgets = {
            'product_image': forms.ClearableFileInput(), 
        }
