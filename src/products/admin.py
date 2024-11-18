from django.contrib import admin
from .models import OneTimeProductCategory, OneTimeProduct, UnlimitedProduct, ProductSale, UserIncome

# Here we register the OneTimeProduct model with custom admin settings.
@admin.register(OneTimeProduct)
class OneTimeProductAdmin(admin.ModelAdmin):
    # Here it will display these fields in the list view, so that the admin can quickly see product details.
    list_display = ('title', 'category', 'price', 'sale_price', 'discount_percentage', 'currency', 'created_at')
    # Here we allow filtering by user, currency, and creation date to make it easier to find products.
    list_filter = ('category__user', 'currency', 'created_at')
    # Here we add a search box to look up products by title, category name, or owner's username.
    search_fields = ('title', 'category__name', 'category__user__username')
    # Here we specify the order of products, right now it will order products by creation date for easy viewing.
    ordering = ('created_at',)

# Here we define an inline admin to so that an admin can edit OneTimeProducts directly in the OneTimeProductCategory admin.
class OneTimeProductInline(admin.TabularInline):
    # We specify the model that this inline represents.
    model = OneTimeProduct
    # The extra blank fields for adding new items is set to 0 as its not needed.
    extra = 0
    # Here we tell it to display the creation date as a read-only field as the admin should not accidentally change it.
    readonly_fields = ['created_at']

# Here we register the OneTimeProductCategory model with custom admin settings.
@admin.register(OneTimeProductCategory)
class OneTimeProductCategoryAdmin(admin.ModelAdmin):
    # It will show these fields in the list view to help find products. 
    list_display = ('name', 'user')
    # Filtering is enabled so that its easier to search. 
    list_filter = ('user',)
    # Here we allow searching for categories by name or by the owner's username.
    search_fields = ('name', 'user__username')
    # Here we specify the order of products, right now it will order products alphabetically by name.
    ordering = ('name',)
    # Now we also include the TabularInline created earlier.
    inlines = [OneTimeProductInline]

# Here we register the UnlimitedProduct model with custom admin settings.
@admin.register(UnlimitedProduct)
class UnlimitedProductAdmin(admin.ModelAdmin):
    # We can display important details of each unlimited product in the list view.
    list_display = ('title', 'user', 'price', 'discount_percentage', 'sale_price', 'currency', 'sku', 'quantity', 'created_at')
    # Filtering is enabled and uses user, currency, and creation date for organization.
    list_filter = ('user', 'currency', 'created_at')
    # A search box is added to help find products by title, owner's username, or SKU.
    search_fields = ('title', 'user__username', 'sku')
    # Here we specify the order of products, right now it will order products by creation date for easy viewing.
    ordering = ('created_at',)

# Here we register the ProductSale model with custom admin settings.
@admin.register(ProductSale)
class ProductSaleAdmin(admin.ModelAdmin):
    # We can display these details in the list views.
    list_display = ('user', 'product', 'amount', 'currency', 'created_at')
    # Filtering is enabled and uses these:
    list_filter = ('user', 'product__title', 'currency', 'created_at')
    # Search is enabled and uses these:
    search_fields = ('user__username', 'product__title')
    # Here we specify the order of products, right now it will order it by newest order on top. 
    # without the negative new sales would be below, but instead they go above each other, making the most recent sale
    # always on top. 
    ordering = ('-created_at',)

# Here we register the UserIncome model with custom admin settings for managing user earnings.
@admin.register(UserIncome)
class UserIncomeAdmin(admin.ModelAdmin):
    # We can display user earnings in list view. The major ones first and the less important ones later. 
    list_display = ('user', 'usd_total', 'gbp_total', 'eur_total', 'btc_total', 'ltc_total', 'sol_total', 'eth_total',
                    'usdt_bep20_total', 'usdt_erc20_total', 'usdt_prc20_total', 'usdt_sol_total', 'usdt_trc20_total')
    # Here we allow searching by username.
    search_fields = ('user__username',)
    # The order would be using the username. 
    ordering = ('user',)

# Custom admin site for product management with personalized titles.
class ProductsAdminSite(admin.AdminSite):
    # Set custom header for the products administration page.
    site_header = "Products Administration"
    # Set the title for the admin portal in the browser.
    site_title = "Products Admin Portal"
    # Set the title on the main index page of the admin.
    index_title = "Products Management"

products_admin_site = ProductsAdminSite(name='products_admin')

# Register all.
products_admin_site.register(OneTimeProductCategory, OneTimeProductCategoryAdmin)
products_admin_site.register(UnlimitedProduct, UnlimitedProductAdmin)
products_admin_site.register(ProductSale, ProductSaleAdmin)
products_admin_site.register(UserIncome, UserIncomeAdmin)


'''
Citations: 
("The Django Admin") -> 6 - 92
'''

