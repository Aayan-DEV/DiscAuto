from django import forms
from .models import OneTimeProductCategory, OneTimeProduct, UnlimitedProduct

class OneTimeProductCategoryForm(forms.ModelForm):
    class Meta:
        model = OneTimeProductCategory
        fields = ['name']

class OneTimeProductForm(forms.ModelForm):
    class Meta:
        model = OneTimeProduct
        fields = ['title', 'price', 'currency', 'description', 'product_content']

class UnlimitedProductForm(forms.ModelForm):
    class Meta:
        model = UnlimitedProduct
        fields = ['title', 'price', 'currency', 'sku', 'quantity', 'link', 'description']
