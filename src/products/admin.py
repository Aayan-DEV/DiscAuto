from django.contrib import admin
from .models import OneTimeProductCategory, OneTimeProduct, UnlimitedProduct, ProductItem


class ProductItemInline(admin.TabularInline):
    model = ProductItem
    extra = 0
    readonly_fields = ['created_at']


@admin.register(OneTimeProduct)
class OneTimeProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'price', 'currency', 'created_at')
    list_filter = ('category__user', 'currency', 'created_at')
    search_fields = ('title', 'category__name', 'category__user__username')
    ordering = ('created_at',)
    inlines = [ProductItemInline]


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
    list_display = ('title', 'user', 'price', 'currency', 'sku', 'quantity', 'created_at')
    list_filter = ('user', 'currency', 'created_at')
    search_fields = ('title', 'user__username', 'sku')
    ordering = ('created_at',)

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
            ],
        }
        return [products_dict]

products_admin_site = ProductsAdminSite(name='products_admin')
products_admin_site.register(OneTimeProductCategory, OneTimeProductCategoryAdmin)
products_admin_site.register(UnlimitedProduct, UnlimitedProductAdmin)
