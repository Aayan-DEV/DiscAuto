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

# Login required as usual. 
@login_required
def auto_sell_view(request):
    """
    The filter() gets all the records from the database that match the filter condition,
    so in this case, its user = request.user, meaning get the autosell instantce for the 
    logged in user. And the .first() method will return the first record from the database 
    that matches the conditions.
    """
    auto_sell = AutoSell.objects.filter(user=request.user).first()

    if request.method == 'POST':
        # Passes the POST data gotten into the form, and binds it to the auto_sell instance. 
        form = AutoSellForm(request.POST, request.FILES, instance=auto_sell)
        if form.is_valid():
            # If form is valid, we save it with commit == False as this returns 
            # an instance of the model, but it's not saved to the database yet.
            # This is used because then we want to add the current user to that
            # instance before saving it.
            auto_sell = form.save(commit=False)

            # Make sure that the custom link is unique: 
            if AutoSell.objects.filter(custom_link=auto_sell.custom_link).exclude(id=auto_sell.id).exists():
                messages.error(request, 'The custom link is already in use. Please choose another one.')
            else:
                # If the custom link is unique, we save the form instance to the database.
                # First we assign the current user as the owner of this AutoSell instance, then save the changes.
                auto_sell.user = request.user
                auto_sell.save()
                messages.success(request, 'Your Landing page has been successfully created!')
                # To combat with the problem of re-submitting when hitting refresh, using
                # redirect is helpful, it just stays on the same page after saving changes, 
                # but it also makes it so that you dont re-submit when you refresh. 
                return redirect('auto_sell')  
        # Error handling: 
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        # If the request method is not POST, we initialize the form with the auto_sell instance.
        # Used when editing the exiting data! 
        form = AutoSellForm(instance=auto_sell)

    # Generate the full URL for the custom link (if auto_sell exists)
    custom_link_url = None
    if auto_sell:
        custom_link_url = request.build_absolute_uri('/') + auto_sell.custom_link

    success_message = None
    channels = AutoSell.objects.filter(user=request.user)
    
    # As explain before, this is how to render on the templatate, and all the 
    # necessary data is passed to the template, which can be later used in the template. 
    return render(request, 'features/auto-sell/auto-sell.html', {
        'form': form,
        'auto_sell': auto_sell, 
        'custom_link_url': custom_link_url, 
        'channels': channels  # Pass filtered channels to the template
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