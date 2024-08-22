from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

def get_default_category():
    try:
        return OneTimeProductCategory.objects.first().id
    except (AttributeError, ObjectDoesNotExist):
        default_category = OneTimeProductCategory.objects.create(name='Default Category', user=User.objects.first())
        return default_category.id


class OneTimeProductCategory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

    def __str__(self):
        return f'{self.name} - {self.user.username}'

class OneTimeProduct(models.Model):
    category = models.ForeignKey(OneTimeProductCategory, related_name='products', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, choices=[('USD', 'USD'), ('GBP', 'GBP'), ('CAD', 'CAD')])
    description = models.TextField(blank=True, null=True)
    product_content = models.TextField(blank=True, null=True) 
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.title} - {self.category.name} - {self.category.user.username}'

class ProductItem(models.Model):
    product = models.ForeignKey(OneTimeProduct, related_name='items', on_delete=models.CASCADE)
    product_content = models.TextField(help_text="Individual product, e.g., an account, key, etc.")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.product.title} - Product {self.pk}'


class UnlimitedProduct(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, choices=[('USD', 'USD'), ('GBP', 'GBP'), ('CAD', 'CAD')])
    sku = models.CharField(max_length=100)
    quantity = models.IntegerField(default=-1, help_text="Enter -1 for unlimited quantity.")
    link = models.URLField()
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.title} - {self.user.username}'
