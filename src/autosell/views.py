# ImportS:
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import AutoSell, AutoSellView, SocialLink, LandingPage  # Add LandingPage here
from .forms import AutoSellForm, LandingPageForm  # Add LandingPageForm here
from products.models import OneTimeProductCategory, UnlimitedProduct, OneTimeProduct
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from products.models import ProductSale
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_POST
from django.utils import timezone
from helpers.supabase import upload_to_supabase

# User needs to be logged in to access and use the page. 
@login_required
def auto_sell_view(request):
    # First we get the AutoSell instance for the logged-in user.
    auto_sell = AutoSell.objects.filter(user=request.user).first()
    social_links = SocialLink.objects.filter(auto_sell=auto_sell) if auto_sell else []

    # Check if request is POST or not. 
    if request.method == 'POST':
        # Here we connect the form to the submitted data and files.
        form = AutoSellForm(request.POST, request.FILES, instance=auto_sell)

        # Validate the form.
        if form.is_valid():
            # First we save the form without committing to the database.
            auto_sell = form.save(commit=False)

            # If a banner was uploaded, it saves it to Supabase, gets the Public URL, then assigns it to auto_sell.
            if 'banner' in request.FILES:
                banner_url = upload_to_supabase(request.FILES['banner'], folder='banners')
                auto_sell.banner = banner_url

            # If a Profile pic was uploaded, it saves it to Supabase, gets the Public URL, then assigns it to auto_sell.
            if 'profile_picture' in request.FILES:
                profile_url = upload_to_supabase(request.FILES['profile_picture'], folder='profiles')
                auto_sell.profile_picture = profile_url

            auto_sell.user = request.user
            # Add this line to handle the checkbox
            auto_sell.show_social_names = 'show_social_names' in request.POST
            
            auto_sell.save()

            # Handle social links
            social_data = request.POST.getlist('social_platform[]')
            social_urls = request.POST.getlist('social_url[]')
            social_titles = request.POST.getlist('social_title[]')

            # Delete existing social links
            SocialLink.objects.filter(auto_sell=auto_sell).delete()

            # Create new social links
            for platform, url, title in zip(social_data, social_urls, social_titles):
                if url:  # Only create if URL is provided
                    SocialLink.objects.create(
                        auto_sell=auto_sell,
                        platform=platform,
                        url=url,
                        title=title if platform == 'custom' else ''
                    )

            messages.success(request, 'Your Landing page has been successfully updated!')
            return redirect('auto_sell_list')  # Change from 'auto_sell' to 'auto_sell_list'
        else:
            # If the form is invalid, show error. 
            messages.error(request, 'Please correct the errors below.')
    else:
        # If the request method is not POST, create a form with the existing auto_sell instance, if available.
        form = AutoSellForm(instance=auto_sell)

    # Here we initialize the custom link URL as None.
    custom_link_url = None
    if auto_sell:
        custom_link_url = request.build_absolute_uri('/') + auto_sell.custom_link

    # Render the auto-sell template with the form, auto_sell data, and custom link URL so they can be used in the landing page.
    return render(request, 'features/auto-sell/auto-sell.html', {
        'form': form,
        'auto_sell': auto_sell,
        'custom_link_url': custom_link_url,
        'social_links': social_links,
        'social_types': SocialLink.SOCIAL_TYPES
    })  # Add missing closing brace here

def custom_landing_page(request, custom_link):
    """
    This renders the custom landing page with only the products specifically chosen for this page.
    """
    # First get the AutoSell instance using the custom link provided
    try:
        user_data = AutoSell.objects.get(custom_link=custom_link)
    except AutoSell.DoesNotExist:
        raise Http404("The requested landing page does not exist.")

    # Check if there's a LandingPage associated with this custom_link
    landing_page = LandingPage.objects.filter(slug=custom_link).first()
    
    if landing_page:
        # If a landing page exists, get only the selected products
        unlimited_products = landing_page.unlimited_products.all()
        one_time_products = landing_page.one_time_products.all()
        
        # Get categories that contain the selected one-time products
        category_ids = one_time_products.values_list('category', flat=True).distinct()
        categories = OneTimeProductCategory.objects.filter(id__in=category_ids)
        
        # For each category, filter products to only include those selected for this landing page
        for category in categories:
            # Replace the products queryset with only the products that are in one_time_products
            category.filtered_products = one_time_products.filter(category=category)
    else:
        # If no specific landing page configuration exists, check if products are directly linked to AutoSell
        unlimited_products = user_data.unlimited_products.all()
        
        # For one-time products, we need to get all categories and their products
        categories = OneTimeProductCategory.objects.filter(user=user_data.user).prefetch_related('products')
        one_time_products = None
        
        # No filtering needed since we're showing all products

    # Record the view
    AutoSellView.objects.create(
        auto_sell=user_data,
        ip_address=request.META.get('REMOTE_ADDR')
    )

    return render(request, 'features/landing_page.html', {
        'user_data': user_data,
        'categories': categories,
        'unlimited_products': unlimited_products,
        'one_time_products': one_time_products,
        'landing_page': landing_page,
    })

def live_search(request, custom_link):
    """
    This is a AJAX-based live search functionality to search for products and categories dynamically.
    """
    try:
        user_data = AutoSell.objects.get(custom_link=custom_link)
    except AutoSell.DoesNotExist:
        raise Http404("The requested landing page does not exist.")
    
    query = request.GET.get('query', '')

    if query:
        categories = OneTimeProductCategory.objects.filter(
            name__icontains=query,
            user=user_data.user
        )
        unlimited_products = UnlimitedProduct.objects.filter(
            Q(title__icontains=query) | Q(description__icontains=query),
            user=user_data.user
        )
    else:
        categories = []
        unlimited_products = []

    return render(request, 'features/live_search_results.html', {
        'categories': categories,
        'unlimited_products': unlimited_products,
    })

@login_required
def delete_lander(request, auto_sell_id):
    """
    Here, we allow the logged-in user to delete their AutoSell landing page.
    """
    # First get the AutoSell instance for the given ID and ensure it belongs to the current user.
    # Using get_object_or_404 is good, as it gives an automatic error handling incase the object is not found. 
    auto_sell = get_object_or_404(AutoSell, id=auto_sell_id, user=request.user)
    
    if request.method == 'POST':
        # If the request is POST, proceed with deleting the AutoSell instance.
        auto_sell.delete()
        # Show a success message after deletion.
        messages.success(request, 'Your Auto-Sell page has been deleted.')
        # Redirect to the main auto_sell page.
        return redirect('auto_sell_list')  # Change from 'auto_sell' to 'auto_sell_list'

def get_seller_page(request, product_id):
    """
    Redirect the user to the seller's custom page based on the product type.
    """
    product = None
    user = None

    # Try to find the product in UnlimitedProduct first
    try:
        product = UnlimitedProduct.objects.get(id=product_id)
        user = product.user  # For UnlimitedProduct, user is directly on the product
    except UnlimitedProduct.DoesNotExist:
        # If not found, try finding the product in OneTimeProduct
        try:
            product = OneTimeProduct.objects.get(id=product_id)
            user = product.category.user  # For OneTimeProduct, user is on the category
        except OneTimeProduct.DoesNotExist:
            # If still not found, try finding it in the OneTimeProductCategory
            try:
                product = OneTimeProductCategory.objects.get(id=product_id)
                user = product.user  # For OneTimeProductCategory, user is directly on the category
            except OneTimeProductCategory.DoesNotExist:
                # If no product is found, raise a 404
                raise Http404("Product not found")

    # Find the most recently created AutoSell instance for the user's AutoSell page
    auto_sell = AutoSell.objects.filter(user=user).order_by('-id').first()
    if not auto_sell:
        raise Http404("Seller page not found")

    # Build the custom URL for the seller's page
    custom_url = request.build_absolute_uri(f"/{auto_sell.custom_link}")

    # Redirect to the seller's custom page
    return redirect(custom_url)

@require_POST
def increment_view_count(request, custom_link):
    if not custom_link:
        return JsonResponse({'error': 'Missing custom link'}, status=400)

    try:
        landing_page = AutoSell.objects.get(custom_link=custom_link)
    except AutoSell.DoesNotExist:
        return JsonResponse({'error': 'Landing page not found'}, status=404)

    # Create view with timestamp only
    AutoSellView.objects.create(
        auto_sell=landing_page,
        ip_address=request.META.get('REMOTE_ADDR')
    )

    return JsonResponse({'success': True})


# Add these new views at the top of the file

@login_required
def auto_sell_list(request):
    """
    Display all auto-sell pages for the logged-in user
    """
    auto_sells = AutoSell.objects.filter(user=request.user)
    return render(request, 'features/auto-sell/auto-sell-list.html', {
        'auto_sells': auto_sells
    })

@login_required
def create_auto_sell(request):
    """
    Create a new auto-sell page
    """
    if request.method == 'POST':
        form = AutoSellForm(request.POST, request.FILES)
        if form.is_valid():
            auto_sell = form.save(commit=False)
            
            if 'banner' in request.FILES:
                banner_url = upload_to_supabase(request.FILES['banner'], folder='banners')
                auto_sell.banner = banner_url

            if 'profile_picture' in request.FILES:
                profile_url = upload_to_supabase(request.FILES['profile_picture'], folder='profiles')
                auto_sell.profile_picture = profile_url

            auto_sell.user = request.user
            # Add this line to handle the checkbox
            auto_sell.show_social_names = 'show_social_names' in request.POST
            
            auto_sell.save()
            
            # Handle social links
            social_data = request.POST.getlist('social_platform[]')
            social_urls = request.POST.getlist('social_url[]')
            social_titles = request.POST.getlist('social_title[]')

            # Create new social links
            for platform, url, title in zip(social_data, social_urls, social_titles):
                if url:  # Only create if URL is provided
                    SocialLink.objects.create(
                        auto_sell=auto_sell,
                        platform=platform,
                        url=url,
                        title=title if platform == 'custom' else ''
                    )
                    
            messages.success(request, 'Your Landing page has been successfully created!')
            return redirect('auto_sell_list')
        else:
            # Improved error handling with specific error messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.capitalize()}: {error}")
            if not form.errors:
                messages.error(request, 'Please correct the errors below.')
    else:
        form = AutoSellForm()

    # Add these context variables
    return render(request, 'features/auto-sell/auto-sell.html', {
        'form': form,
        'auto_sell': None,
        'social_links': [],  # Empty list since this is a new auto-sell page
        'social_types': SocialLink.SOCIAL_TYPES  # Add the social types from the model
    })

@login_required
def edit_auto_sell(request, auto_sell_id):
    """
    Edit an existing auto-sell page
    """
    auto_sell = get_object_or_404(AutoSell, id=auto_sell_id, user=request.user)
    social_links = SocialLink.objects.filter(auto_sell=auto_sell)
    
    if request.method == 'POST':
        form = AutoSellForm(request.POST, request.FILES, instance=auto_sell)
        if form.is_valid():
            auto_sell = form.save(commit=False)
            
            if 'banner' in request.FILES:
                banner_url = upload_to_supabase(request.FILES['banner'], folder='banners')
                auto_sell.banner = banner_url

            if 'profile_picture' in request.FILES:
                profile_url = upload_to_supabase(request.FILES['profile_picture'], folder='profiles')
                auto_sell.profile_picture = profile_url

            # Add this line to handle the checkbox
            auto_sell.show_social_names = 'show_social_names' in request.POST
            
            auto_sell.save()

            # Handle social links
            social_data = request.POST.getlist('social_platform[]')
            social_urls = request.POST.getlist('social_url[]')
            social_titles = request.POST.getlist('social_title[]')

            # Delete existing social links
            SocialLink.objects.filter(auto_sell=auto_sell).delete()

            # Create new social links
            for platform, url, title in zip(social_data, social_urls, social_titles):
                if url:  # Only create if URL is provided
                    SocialLink.objects.create(
                        auto_sell=auto_sell,
                        platform=platform,
                        url=url,
                        title=title if platform == 'custom' else ''
                    )

            messages.success(request, 'Your Landing page has been successfully updated!')
            return redirect('auto_sell_list')  # Change from 'auto_sell' to 'auto_sell_list'
        else:
            # Improved error handling with specific error messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.capitalize()}: {error}")
            if not form.errors:
                messages.error(request, 'Please correct the errors below.')
    else:
        form = AutoSellForm(instance=auto_sell)

    custom_link_url = request.build_absolute_uri('/') + auto_sell.custom_link
    return render(request, 'features/auto-sell/auto-sell.html', {
        'form': form,
        'auto_sell': auto_sell,
        'custom_link_url': custom_link_url,
        'social_links': social_links,
        'social_types': SocialLink.SOCIAL_TYPES
   })


# In your landing_page view, make sure to filter products by the landing page
# Fix the landing_page_view function
def landing_page_view(request, slug):
    """
    View for displaying a landing page with specific products
    """
    landing_page = get_object_or_404(LandingPage, slug=slug)
    
    # Get products specifically associated with this landing page
    unlimited_products = landing_page.unlimited_products.all()
    one_time_products = landing_page.one_time_products.all()
    
    # Get the user's AutoSell data
    user_data = AutoSell.objects.filter(user=landing_page.user).first()
    if not user_data:
        raise Http404("Seller information not found")
    
    # Get categories that contain the selected one-time products
    category_ids = one_time_products.values_list('category', flat=True).distinct()
    categories = OneTimeProductCategory.objects.filter(id__in=category_ids)
    
    return render(request, 'features/landing_page.html', {
        'landing_page': landing_page,
        'unlimited_products': unlimited_products,
        'one_time_products': one_time_products,
        'categories': categories,
        'user_data': user_data
    })