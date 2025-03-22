# Imports:
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from decimal import Decimal
from autosell.models import LandingPage

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
    category_image = models.ImageField(upload_to='category_images/', null=True, blank=True)
    category_image_url = models.URLField(max_length=500, null=True, blank=True)
    landing_pages = models.ManyToManyField('autosell.AutoSell', blank=True, related_name='one_time_categories')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if hasattr(self, 'products'):
            for product in self.products.all():
                product.landing_pages.set(self.landing_pages.all())

    def __str__(self):
        return f'{self.name} - {self.user.username}'
    
    class Meta:
        verbose_name_plural = "One time product categories"

class OneTimeProduct(models.Model):
    category = models.ForeignKey(OneTimeProductCategory, related_name='products', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ltc_price = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    btc_price = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    eth_price = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    usdt_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sol_price = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    test_price = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=10, choices=[
        ('USD', 'USD'),
        ('EUR', 'EUR'),
        ('GBP', 'GBP')
    ])
    product_content = models.TextField(blank=True, null=True) 
    product_image = models.ImageField(upload_to='one_time_products/', null=True, blank=True)
    product_image_url = models.URLField(max_length=500, null=True, blank=True)
    stripe_product_id = models.CharField(max_length=100, null=True, blank=True)
    stripe_price_id = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)  
    landing_pages = models.ManyToManyField(
        'autosell.AutoSell',  
        blank=True,
        related_name='onetime_products'  
    )

    def __str__(self):
        return f'{self.title} - {self.category.name} - {self.category.user.username}'

class UnlimitedProduct(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  
    ltc_price = models.DecimalField(max_digits=30, decimal_places=20, blank=True, null=True)
    btc_price = models.DecimalField(max_digits=30, decimal_places=20, blank=True, null=True)
    eth_price = models.DecimalField(max_digits=30, decimal_places=20, blank=True, null=True)
    usdt_price = models.DecimalField(max_digits=30, decimal_places=20, blank=True, null=True)
    sol_price = models.DecimalField(max_digits=30, decimal_places=20, blank=True, null=True)
    test_price = models.DecimalField(max_digits=30, decimal_places=20, blank=True, null=True)
    discount_percentage = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    currency = models.CharField(max_length=4, choices=[('USD', 'USD'), ('GBP', 'GBP'), ('EUR', 'EUR')])
    sku = models.CharField(max_length=100)
    quantity = models.IntegerField(default=-1, help_text="Enter -1 for unlimited quantity.")
    link = models.URLField()
    description = models.TextField(blank=True, default='', null=True)
    product_image = models.ImageField(upload_to='products/', null=True, blank=True)
    product_image_url = models.URLField(max_length=500, blank=True, null=True)
    stripe_product_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_price_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    landing_pages = models.ManyToManyField('autosell.AutoSell', blank=True, related_name='unlimited_products')
    
    def __str__(self):
        return self.title

class ProductSale(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(OneTimeProduct, on_delete=models.SET_NULL, null=True, blank=True)
    unlimited_product = models.ForeignKey(UnlimitedProduct, on_delete=models.SET_NULL, null=True, blank=True)
    product_name = models.CharField(max_length=255, null=True, blank=True)  # Add this field
    stripe_session_id = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10)
    customer_name = models.CharField(max_length=255)
    customer_email = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Fee details
    stripe_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    platform_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    payout_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    converted_amount_eur = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    fee_details_fetched = models.BooleanField(default=False)
    
    def __str__(self):
        product_info = self.product_name or "Unknown Product"
        return f"{product_info} - {self.customer_name} - {self.amount} {self.currency}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        if self.payout_amount is not None and not self.payout_processed:
            self.update_user_income()
    
    def update_user_income(self):
        """Update the user's income based on this sale"""
        print(f"Starting update_user_income for sale {self.id} - Amount: {self.payout_amount} {self.currency}")
        
        try:
            user_income, created = UserIncome.objects.get_or_create(user=self.user)
            print(f"User income record {'created' if created else 'retrieved'} for user {self.user.username}")
            print(f"Current EUR balance: {user_income.EUR_TOTAL}")
            
            if self.currency == 'EUR':
                amount_to_add = self.payout_amount
                print(f"Using direct EUR amount: {amount_to_add}")
            else:
                if self.converted_amount_eur is not None:
                    amount_to_add = self.converted_amount_eur
                    print(f"Using converted EUR amount: {amount_to_add}")
                else:
                    amount_to_add = self.payout_amount
                    print(f"No conversion available, using original amount: {amount_to_add}")
            
            if isinstance(amount_to_add, float):
                decimal_amount = Decimal(str(amount_to_add))
                print(f"Converting float {amount_to_add} to Decimal {decimal_amount}")
            else:
                decimal_amount = amount_to_add
                
            print(f"Before update: EUR_TOTAL = {user_income.EUR_TOTAL}")
            user_income.EUR_TOTAL += decimal_amount
            print(f"After update: EUR_TOTAL = {user_income.EUR_TOTAL}")
            user_income.save()
            user_income.refresh_from_db()
            print(f"After update, EUR balance: {user_income.EUR_TOTAL}")
            self.payout_processed = True
            print(f"Marking sale {self.id} as processed")
            self.save(update_fields=['payout_processed'])
            print(f"Sale {self.id} processing completed")
            return True
        except Exception as e:
            print(f"Error in update_user_income: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return False
    
    def __str__(self):
        product_name = self.product.title if self.product else (self.unlimited_product.title if self.unlimited_product else "Unknown Product")
        return f"{product_name} - {self.customer_name} - {self.amount} {self.currency}"

class UserIncome(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    EUR_TOTAL = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    BTC_TOTAL = models.DecimalField(max_digits=10, decimal_places=8, default=Decimal('0.00000000'))
    ETH_TOTAL = models.DecimalField(max_digits=10, decimal_places=8, default=Decimal('0.00000000'))
    LTC_TOTAL = models.DecimalField(max_digits=10, decimal_places=8, default=Decimal('0.00000000'))
    SOL_TOTAL = models.DecimalField(max_digits=10, decimal_places=8, default=Decimal('0.00000000'))
    USDT_TRC20_TOTAL = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    USDT_ERC20_TOTAL = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    USDT_BEP20_TOTAL = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    USDT_SOL_TOTAL = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    USDT_PRC20_TOTAL = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    LTCT_TOTAL = models.DecimalField(max_digits=10, decimal_places=8, default=Decimal('0.00000000'))
    
    def update_income(self, amount, currency):
        """Update income based on currency type"""
        print(f"update_income called with amount={amount}, currency={currency}")
        self.EUR_TOTAL += amount
        self.save()
        print(f"Added {amount} {currency} directly to EUR_TOTAL. New balance: {self.EUR_TOTAL}")
    
    def get_formatted_values(self):
        """Return a dictionary of formatted values for display in templates"""
        return {
            'EUR_TOTAL': str(self.EUR_TOTAL),
            'BTC_TOTAL': str(self.BTC_TOTAL),
            'ETH_TOTAL': str(self.ETH_TOTAL),
            'LTC_TOTAL': str(self.LTC_TOTAL),
            'SOL_TOTAL': str(self.SOL_TOTAL),
            'USDT_TRC20_TOTAL': str(self.USDT_TRC20_TOTAL),
            'USDT_ERC20_TOTAL': str(self.USDT_ERC20_TOTAL),
            'USDT_BEP20_TOTAL': str(self.USDT_BEP20_TOTAL),
            'USDT_SOL_TOTAL': str(self.USDT_SOL_TOTAL),
            'USDT_PRC20_TOTAL': str(self.USDT_PRC20_TOTAL),
            'LTCT_TOTAL': str(self.LTCT_TOTAL),
        }
    
    def __str__(self):
        return f"{self.user.username}'s Income"
