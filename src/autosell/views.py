# ImportS:
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import AutoSell, AutoSellView
from .forms import AutoSellForm
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
                print(f"Banner URL: {banner_url}")  

            # If a Profile pic was uploaded, it saves it to Supabase, gets the Public URL, then assigns it to auto_sell.
            if 'profile_picture' in request.FILES:
                profile_url = upload_to_supabase(request.FILES['profile_picture'], folder='profiles')
                auto_sell.profile_picture = profile_url
                print(f"Profile Picture URL: {profile_url}")  

            # Set the current user as the owner of the AutoSell instance.
            # The person who uploaded the files is the owner of the landing page. 
            auto_sell.user = request.user
            # Save the auto_sell data to the database with all changes.
            auto_sell.save()
            messages.success(request, 'Your Landing page has been successfully created!')
            return redirect('auto_sell')
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
        'custom_link_url': custom_link_url
    })

def custom_landing_page(request, custom_link):
    """
    This renders the custom landing page with products and categories.
    """
    # First get the AutoSell instance using the custom link provided, to gell all the data. 
    try:
        user_data = AutoSell.objects.get(custom_link=custom_link)
    except AutoSell.DoesNotExist:
        raise Http404("The requested landing page does not exist.")

    # Get all categories and products with 'show_on_custom_lander=True'
    # Because categories contain all the one time products, using prefetch_related, we can get all the products related, in a single query.
    categories = OneTimeProductCategory.objects.filter(user=user_data.user, show_on_custom_lander=True).prefetch_related('products')
    unlimited_products = UnlimitedProduct.objects.filter(user=user_data.user, show_on_custom_lander=True)

    return render(request, 'features/landing_page.html', {
        'user_data': user_data,
        'categories': categories,
        'unlimited_products': unlimited_products,
    })


def live_search(request, custom_link):
    """
    This is a AJAX-based live search functionality to search for products and categories dynamically.
    AJAX search means that you see the products and categories as you type, which makes it easier 
    to search for products.
    """
    # Try to get the AutoSell instance by custom link.
    try:
        user_data = AutoSell.objects.get(custom_link=custom_link)
    except AutoSell.DoesNotExist:
        # If not found, return a 404 error.
        raise Http404("The requested landing page does not exist.")
    
    # Get the search query string from the request's GET parameters.
    # Meaning getting the character the person is typing. 
    query = request.GET.get('query', '')

    # If there's a search query, filter categories and products based on it.
    if query:
        # Filter categories whose names contain the search query, limited to the owner of the AutoSell.
        # It's limited to the owner of the AutoSell, so that only the products of the owner of the AutoSell
        # only show up. 
        categories = OneTimeProductCategory.objects.filter(
            # The "__icontains" is a query lookup that is used to perform case-insensitive string matching. 
            name__icontains=query,
            user=user_data.user,
            show_on_custom_lander=True
        )
        # Filter products based on title or description, and ensure they belong to the AutoSell user.
        # The Q() method is used to make complex queries. It makes it so that i can combine conditions
        # using logical operators (and (&)/or (|)). I have used OR here because the title and description
        # are not the same. But it is always helpful if a word is in the description rather than in the title. 
        # I cannot compare without the use of Q(), because it is just not allowed, and Q() is nessesary. 
        unlimited_products = UnlimitedProduct.objects.filter(
            Q(title__icontains=query) | Q(description__icontains=query),
            user=user_data.user,
            show_on_custom_lander=True
        )
    else:
        # If no query is provided, return empty results.
        categories = []
        unlimited_products = []

    # Render the search results template with the filtered data.
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
        return redirect('auto_sell')

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

    # Find the AutoSell instance for the user's AutoSell page
    auto_sell = get_object_or_404(AutoSell, user=user)

    # Build the custom URL for the seller's page
    custom_url = request.build_absolute_uri(f"/{auto_sell.custom_link}")

    # Redirect to the seller's custom page
    return redirect(custom_url)

@require_POST
def increment_view_count(request, custom_link):
    """
    Here we Increment the view count for the given custom landing page.
    """
    # If no custom link is provided, return an error response.
    if not custom_link:
        return JsonResponse({'error': 'Missing custom link'}, status=400)

    # Try to fetch the AutoSell instance by the custom link. To know who got a view?
    try:
        landing_page = AutoSell.objects.get(custom_link=custom_link)
    except AutoSell.DoesNotExist:
        # If the landing page doesn't exist, return a 404 error. Probably not possible
        # but error handling is always important. 
        return JsonResponse({'error': 'Landing page not found'}, status=404)

    # Record a new view by creating an AutoSellView instance with today's date.
    AutoSellView.objects.create(autosell=landing_page, view_date=timezone.now().date())

    # Return a success response with the updated total view count.
    return JsonResponse({'success': True})