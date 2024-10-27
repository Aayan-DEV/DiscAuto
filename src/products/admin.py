from django.contrib import admin
from .models import OneTimeProductCategory, OneTimeProduct, UnlimitedProduct, ProductSale, UserIncome

@admin.register(OneTimeProduct)
class OneTimeProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'price', 'sale_price', 'discount_percentage', 'currency', 'created_at')
    list_filter = ('category__user', 'currency', 'created_at')
    search_fields = ('title', 'category__name', 'category__user__username')
    ordering = ('created_at',)

class OneTimeProductInline(admin.TabularInline):
    model = OneTimeProduct
    extra = 0
    readonly_fields = ['created_at']

@admin.register(OneTimeProductCategory)
class OneTimeProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'user')
    list_filter = ('user',)
    search_fields = ('name', 'user__username')
    ordering = ('name',)
    inlines = [OneTimeProductInline]

@admin.register(UnlimitedProduct)
class UnlimitedProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'price', 'discount_percentage', 'sale_price', 'currency', 'sku', 'quantity', 'created_at')
    list_filter = ('user', 'currency', 'created_at')
    search_fields = ('title', 'user__username', 'sku')
    ordering = ('created_at',)

@admin.register(ProductSale)
class ProductSaleAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'amount', 'currency', 'created_at')
    list_filter = ('user', 'product__title', 'currency', 'created_at')
    search_fields = ('user__username', 'product__title')
    ordering = ('-created_at',)

# Admin for UserIncome
@admin.register(UserIncome)
class UserIncomeAdmin(admin.ModelAdmin):
    list_display = ('user', 'usd_total', 'gbp_total', 'eur_total', 'btc_total', 'ltc_total', 'sol_total', 'eth_total',
                    'usdt_bep20_total', 'usdt_erc20_total', 'usdt_prc20_total', 'usdt_sol_total', 'usdt_trc20_total')
    search_fields = ('user__username',)
    ordering = ('user',)

class ProductsAdminSite(admin.AdminSite):
    site_header = "Products Administration"
    site_title = "Products Admin Portal"
    index_title = "Products Management"

    def get_app_list(self, request):
        app_dict = self._build_app_dict(request)
        products_dict = {
            'name': 'Products',
            'app_label': 'products',
            'models': [
                {
                    'name': 'Categories',
                    'object_name': 'OneTimeProductCategory',
                    'admin_url': '/admin/app_name/onetimeproductcategory/',
                    'perms': {'add': True, 'change': True, 'delete': True, 'view': True},
                },
                {
                    'name': 'Unlimited Use Products',
                    'object_name': 'UnlimitedProduct',
                    'admin_url': '/admin/app_name/unlimitedproduct/',
                    'perms': {'add': True, 'change': True, 'delete': True, 'view': True},
                },
                {
                    'name': 'Product Sales',
                    'object_name': 'ProductSale',
                    'admin_url': '/admin/app_name/productsale/',
                    'perms': {'add': True, 'change': True, 'delete': True, 'view': True},
                },
                {
                    'name': 'User Income',
                    'object_name': 'UserIncome',
                    'admin_url': '/admin/app_name/userincome/',
                    'perms': {'add': True, 'change': True, 'delete': True, 'view': True},
                },
            ],
        }
        return [products_dict]

products_admin_site = ProductsAdminSite(name='products_admin')
products_admin_site.register(OneTimeProductCategory, OneTimeProductCategoryAdmin)
products_admin_site.register(UnlimitedProduct, UnlimitedProductAdmin)
products_admin_site.register(ProductSale, ProductSaleAdmin)
products_admin_site.register(UserIncome, UserIncomeAdmin)
