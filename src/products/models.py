# Imports:
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from decimal import Decimal

# This is a function that gets the default category ID if needed for OneTimeProductCategory.
def get_default_category():
    try:
        # First it attempts to get the ID of the first existing category.
        return OneTimeProductCategory.objects.first().id
    except (AttributeError, ObjectDoesNotExist):
        # If somehow there is no category, meaning it does not exit, find the first user to create a default category for them.
        first_user = User.objects.first()
        if first_user:
            # Create a new default category for the first user and return its ID.
            default_category = OneTimeProductCategory.objects.create(name='Default Category', user=first_user)
            return default_category.id
        else:
            # Return None if no user exists to create the category for.
            return None

# Here we define a model to represent categories for one-time products.
class OneTimeProductCategory(models.Model):
    # The first field is the user, which links each category to a user.
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # The next field is setting the category name with a max length of 255 characters.
    name = models.CharField(max_length=255)
    # Remove the show_on_custom_lander field
    # Image for the category, stored in the 'category_images/' folder.
    category_image = models.ImageField(upload_to='category_images/', null=True, blank=True)
    # URL of the category image stored which is gotten from supabase. 
    category_image_url = models.URLField(max_length=500, null=True, blank=True)
    # Add this new field
    landing_pages = models.ManyToManyField('autosell.AutoSell', blank=True, related_name='one_time_categories')

    def __str__(self):
        return f'{self.name} - {self.user.username}'
    
    class Meta:
        verbose_name_plural = "One time product categories"

# Here we define a model for individual one-time products.
class OneTimeProduct(models.Model):
    # All fields are just standard fields needed. 
    # Because one time products are stored inside of a category, the category is a foreign key here. 

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
    product_content = models.TextField(blank=True, null=True)  # Make this field nullable
    product_image = models.ImageField(upload_to='one_time_products/', null=True, blank=True)
    product_image_url = models.URLField(max_length=500, null=True, blank=True)
    stripe_product_id = models.CharField(max_length=100, null=True, blank=True)
    stripe_price_id = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)  # Add the missing created_at field
    landing_pages = models.ManyToManyField(
        'autosell.LandingPage',  # Change this to reference the correct model
        blank=True,
        related_name='product_onetime'  # Changed this related_name
    )

    def __str__(self):
        return f'{self.title} - {self.category.name} - {self.category.user.username}'

# Here we define a model for unlimited products.
class UnlimitedProduct(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Add this field
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
    # Removed the landing_page field
    
    def __str__(self):
        return self.title

# Here we define a model to record product sales.
class ProductSale(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # Every order would have 1 field empty as a person is unable to buy more than 1 product. 
    # Or 2 products with different categories at the same time.

    # We connect it to the one-time product if it’s a one-time sale.
    product = models.ForeignKey(
        OneTimeProduct, null=True, blank=True, on_delete=models.CASCADE, 
        related_name='sales'
    )

    # We connect it to the unlimited product if it’s an unlimited sale.
    unlimited_product = models.ForeignKey(
        UnlimitedProduct, null=True, blank=True, on_delete=models.CASCADE, 
        related_name='sales'
    )
    
    # Normal fields. 
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

# Here we define the model which keeps track of a user’s total income.
class UserIncome(models.Model):
    # We have to link each income record to one user.
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='income')
    # Normal fields. 
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
    
    # Here is a function to add to the user's income based on the currency.
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
        # Save the updated income totals in the database.
        self.save()

    def __str__(self):
        return f'{self.user.username} - USD: {self.usd_total}, GBP: {self.gbp_total}, EUR: {self.eur_total}, BTC: {self.btc_total}'

"""
Citations:
("Models") -> Lines 8 - 213
"""
