from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import OneTimeProductCategory, OneTimeProduct, UnlimitedProduct
from .forms import OneTimeProductCategoryForm, OneTimeProductForm, UnlimitedProductForm

@login_required
def products(request):
    categories = OneTimeProductCategory.objects.filter(user=request.user)
    unlimited_products = UnlimitedProduct.objects.filter(user=request.user)
    
    return render(request, "features/products/products.html", {
        'categories': categories,
        'unlimited_products': unlimited_products
    })

@login_required
def add_category(request):
    if request.method == 'POST':
        form = OneTimeProductCategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.user = request.user
            category.save()
            return redirect('one_time_product_categories')
    else:
        form = OneTimeProductCategoryForm()
    return render(request, 'features/products/add_category.html', {'form': form})

@login_required
def one_time_product_categories(request):
    categories = OneTimeProductCategory.objects.filter(user=request.user)
    return render(request, "features/products/one_time_product_categories.html", {'categories': categories})

@login_required
def add_product_to_category(request, category_id):
    category = get_object_or_404(OneTimeProductCategory, id=category_id, user=request.user)
    
    if request.method == 'POST':
        form = OneTimeProductForm(request.POST)
        
        if form.is_valid():
            one_time_product = form.save(commit=False)
            one_time_product.category = category
            one_time_product.save()
            return redirect('category_detail', category_id=category.id)
    else:
        form = OneTimeProductForm()
    
    return render(request, 'features/products/add_product_to_category.html', {'form': form, 'category': category})

@login_required
def edit_one_time_product(request, pk):
    one_time_product = get_object_or_404(OneTimeProduct, pk=pk)

    if request.method == 'POST':
        form = OneTimeProductForm(request.POST, instance=one_time_product)

        if form.is_valid():
            form.save()
            return redirect('category_detail', category_id=one_time_product.category.id)
    else:
        form = OneTimeProductForm(instance=one_time_product)

    return render(request, 'features/products/edit_one_time_product.html', {
        'form': form,
    })

@login_required
def delete_one_time_product(request, pk):
    product = get_object_or_404(OneTimeProduct, pk=pk)
    category_id = product.category.id
    product.delete()
    return redirect('category_detail', category_id=category_id)

@login_required
def delete_category(request, pk):
    category = get_object_or_404(OneTimeProductCategory, pk=pk, user=request.user)
    category.delete()
    return redirect('products')

@login_required
def add_product_options(request):
    return render(request, "features/products/add_product_options.html")

@login_required
def add_unlimited_product(request):
    if request.method == 'POST':
        form = UnlimitedProductForm(request.POST)
        if form.is_valid():
            unlimited_product = form.save(commit=False)
            unlimited_product.user = request.user
            unlimited_product.save()
            return redirect('products')
    else:
        form = UnlimitedProductForm()
    
    return render(request, 'features/products/add_unlimited_product.html', {'form': form})

@login_required
def edit_unlimited_product(request, pk):
    product = get_object_or_404(UnlimitedProduct, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = UnlimitedProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            return redirect('products')
    else:
        form = UnlimitedProductForm(instance=product)
    
    return render(request, 'features/products/edit_unlimited_product.html', {'form': form})

@login_required
def delete_unlimited_product(request, pk):
    product = get_object_or_404(UnlimitedProduct, pk=pk, user=request.user)
    product.delete()
    return redirect('products')

@login_required
def category_detail(request, category_id):
    category = get_object_or_404(OneTimeProductCategory, id=category_id, user=request.user)
    products = category.products.all() 
    return render(request, 'features/products/category_detail.html', {
        'category': category,
        'products': products,
    })
