from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

def get_default_category():
    try:
        return OneTimeProductCategory.objects.first().id
    except (AttributeError, ObjectDoesNotExist):
        first_user = User.objects.first()
        if first_user:
            default_category = OneTimeProductCategory.objects.create(name='Default Category', user=first_user)
            return default_category.id
        else:
            return None 

class OneTimeProductCategory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    show_on_custom_lander = models.BooleanField(default=True)  
    category_image = models.ImageField(upload_to='category_images/', null=True, blank=True) 

    def __str__(self):
        return f'{self.name} - {self.user.username}'

class OneTimeProduct(models.Model):
    category = models.ForeignKey(OneTimeProductCategory, related_name='products', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    ltc_price = models.DecimalField(max_digits=30, decimal_places=20, blank=True, null=True)
    btc_price = models.DecimalField(max_digits=30, decimal_places=20, blank=True, null=True)
    eth_price = models.DecimalField(max_digits=30, decimal_places=20, blank=True, null=True)
    usdt_price = models.DecimalField(max_digits=30, decimal_places=20, blank=True, null=True)
    test_price = models.DecimalField(max_digits=30, decimal_places=20, blank=True, null=True)
    sol_price = models.DecimalField(max_digits=30, decimal_places=20, blank=True, null=True)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    discount_percentage = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    currency = models.CharField(max_length=4, choices=[('USD', 'USD'), ('GBP', 'GBP'), ('EUR', 'EUR')])
    description = models.TextField(blank=True, default='') 
    product_content = models.TextField(blank=True, null=True)
    stripe_product_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_price_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def normalize_price(self, value):
        """Normalize Decimal fields to remove trailing zeros."""
        if value is not None:
            return value.normalize()  # Removes trailing zeros
        return value

    def save(self, *args, **kwargs):
        # Normalize the prices to remove extra zeros
        self.ltc_price = self.normalize_price(self.ltc_price)
        self.btc_price = self.normalize_price(self.btc_price)
        self.eth_price = self.normalize_price(self.eth_price)
        self.usdt_price = self.normalize_price(self.usdt_price)
        self.test_price = self.normalize_price(self.test_price)

        super().save(*args, **kwargs)  # Call the real save() method

    def __str__(self):
        return f'{self.title} - {self.category.name} - {self.category.user.username}'

from decimal import Decimal

class UnlimitedProduct(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    ltc_price = models.DecimalField(max_digits=30, decimal_places=20, blank=True, null=True)
    btc_price = models.DecimalField(max_digits=30, decimal_places=20, blank=True, null=True)
    eth_price = models.DecimalField(max_digits=30, decimal_places=20, blank=True, null=True)
    usdt_price = models.DecimalField(max_digits=30, decimal_places=20, blank=True, null=True)
    sol_price = models.DecimalField(max_digits=30, decimal_places=20, blank=True, null=True)
    test_price = models.DecimalField(max_digits=30, decimal_places=20, blank=True, null=True)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    discount_percentage = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    currency = models.CharField(max_length=4, choices=[('USD', 'USD'), ('GBP', 'GBP'), ('EUR', 'EUR')])
    sku = models.CharField(max_length=100)
    quantity = models.IntegerField(default=-1, help_text="Enter -1 for unlimited quantity.")
    link = models.URLField()
    description = models.TextField(blank=True, default='')
    product_image = models.ImageField(upload_to='products/', null=True, blank=True)
    stripe_product_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_price_id = models.CharField(max_length=255, blank=True, null=True)
    show_on_custom_lander = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def normalize_price(self, value):
        """Normalize Decimal fields to remove trailing zeros."""
        if value is not None:
            return value.normalize()  # Removes trailing zeros
        return value

    def save(self, *args, **kwargs):
        # Normalize the prices to remove extra zeros
        self.ltc_price = self.normalize_price(self.ltc_price)
        self.btc_price = self.normalize_price(self.btc_price)
        self.eth_price = self.normalize_price(self.eth_price)
        self.usdt_price = self.normalize_price(self.usdt_price)
        self.test_price = self.normalize_price(self.test_price)

        super().save(*args, **kwargs)  # Call the real save() method
        
    def __str__(self):
        return f'{self.title} - {self.user.username}'

class ProductSale(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(
        OneTimeProduct, null=True, blank=True, on_delete=models.CASCADE, 
        related_name='sales'
    )
    unlimited_product = models.ForeignKey(
        UnlimitedProduct, null=True, blank=True, on_delete=models.CASCADE, 
        related_name='sales'
    )
    stripe_session_id = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=4)
    customer_name = models.CharField(max_length=255)  
    customer_email = models.EmailField()  
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.product:
            return f'{self.user.username} bought {self.product.title} for {self.amount} {self.currency} (One-time)'
        return f'{self.user.username} bought {self.unlimited_product.title} for {self.amount} {self.currency} (Unlimited)'
    
class UserIncome(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='income')
    usd_total = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    gbp_total = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    eur_total = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    btc_total = models.DecimalField(max_digits=30, decimal_places=8, default=Decimal('0.00000000'))
    ltc_total = models.DecimalField(max_digits=30, decimal_places=8, default=Decimal('0.00000000'))
    sol_total = models.DecimalField(max_digits=30, decimal_places=8, default=Decimal('0.00000000'))
    eth_total = models.DecimalField(max_digits=30, decimal_places=8, default=Decimal('0.00000000'))
    usdt_bep20_total = models.DecimalField(max_digits=30, decimal_places=8, default=Decimal('0.00000000'))
    usdt_erc20_total = models.DecimalField(max_digits=30, decimal_places=8, default=Decimal('0.00000000'))
    usdt_prc20_total = models.DecimalField(max_digits=30, decimal_places=8, default=Decimal('0.00000000'))
    usdt_trc20_total = models.DecimalField(max_digits=30, decimal_places=8, default=Decimal('0.00000000'))
    usdt_sol_total = models.DecimalField(max_digits=30, decimal_places=8, default=Decimal('0.00000000'))
    ltct_total = models.DecimalField(max_digits=30, decimal_places=8, default=Decimal('0.00000000'))
    

    def update_income(self, amount, currency):
        if currency == 'USD':
            self.usd_total += amount
        elif currency == 'GBP':
            self.gbp_total += amount
        elif currency == 'EUR':
            self.eur_total += amount
        elif currency == 'BTC':
            self.btc_total += amount
        elif currency == 'LTC':
            self.ltc_total += amount
        elif currency == 'SOL':
            self.sol_total += amount
        elif currency == 'ETH':
            self.eth_total += amount
        elif currency == 'USDT_BEP20':
            self.usdt_bep20_total += amount
        elif currency == 'USDT_ERC20':
            self.usdt_erc20_total += amount
        elif currency == 'USDT_PRC20':
            self.usdt_prc20_total += amount
        elif currency == 'USDT_SOL':
            self.usdt_sol_total += amount
        elif currency == 'USDT_TRC20':
            self.usdt_trc20_total += amount
        elif currency == 'LTCT':
            self.ltct_total += amount
        self.save()

    def __str__(self):
        return f'{self.user.username} - USD: {self.usd_total}, GBP: {self.gbp_total}, EUR: {self.eur_total}, BTC: {self.btc_total}'
