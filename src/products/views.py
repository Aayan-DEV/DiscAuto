# Imports: 
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import OneTimeProductCategory, OneTimeProduct, UnlimitedProduct, ProductSale
from .forms import OneTimeProductCategoryForm, OneTimeProductForm, UnlimitedProductForm
from django.http import JsonResponse
from django.urls import reverse
from django.contrib import messages 
from helpers.supabase import upload_to_supabase
import stripe
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail, EmailMultiAlternatives
import os
import json
from pycoinpayments import CoinPayments
import uuid
from dotenv import load_dotenv, dotenv_values
from auths.models import UserProfile
import requests
from .models import UserIncome
from decimal import Decimal
from django.template.loader import render_to_string
from autosell.models import AutoSell, LandingPage 

# First we check if the application is running in a specific environment, such as on Railway.
# We do that because i have had issues where the application uses the old .env from its cache rather
# than updating it and using the new environment variables, so its always good to just override the 
# variables with the new ones. 
# We don't do that if the application is running in a production environment because i would place the
# variables inside of railway and not push my .env file as its sensitive.
if not os.getenv('RAILWAY_ENVIRONMENT'):
    # First we override
    load_dotenv(override=True)  
    # Then we update the current process's environment variables with values from the .env file.
    os.environ.update(dotenv_values())  

# Here we get the Stripe secret key from environment variables.
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')

# Here we get the Stripe publishable key from environment variables.
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')

# Here we get the email host user (sender email address) from environment variables.
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')

# Here we get the CoinPayments public key from environment variables.
COINPAYMENTS_PUBLIC_KEY = os.getenv('COINPAYMENTS_PUBLIC_KEY')

# Here we get the CoinPayments private key from environment variables.
COINPAYMENTS_PRIVATE_KEY = os.getenv('COINPAYMENTS_PRIVATE_KEY')

# We set the Stripe API key to authenticate API requests. This is needed to do 
# transactions and manage payment intents using Stripe's Python library.
stripe.api_key = STRIPE_SECRET_KEY

# Assigning the CoinPayments client with public and private keys from the environment variables. 
coinpayments_client = CoinPayments(
    public_key=COINPAYMENTS_PUBLIC_KEY,
    private_key=COINPAYMENTS_PRIVATE_KEY
)


def send_pushover_notification(user_key, message):
    # First we get the Pushover API token from the environment variables.
    pushover_token = os.getenv('PUSHOVER_API_TOKEN') 
    
    # We have to check if the either the user_key needed to send the notification is missing, 
    # or the pushover_token needed to send the notification as the website is missing. 
    if not pushover_token or not user_key:
        print("Pushover App Token or User Key is missing in the environment file.")
        return  

    # Here we define the Pushover API endpoint URL for sending messages.
    url = "https://api.pushover.net/1/messages.json"
    
    # Then we create a data dictionary with the parameters required by the Pushover API:
    # - "token": The app's API token to authenticate the request.
    # - "user": The user's unique key to identify the person recieving the notification.
    # - "message": The notification message to be sent.
    # - "title": A title for the notification.
    # - "sound": A sound that would play when the notification is received (e.g., "Cha-Ching").
    data = {
        "token": pushover_token, 
        "user": user_key, 
        "message": message,
        "title": "Cha-Ching!",
        "sound": "Cha-Ching"
    }

    try:
        # It sends a POST request to the Pushover API endpoint with the data dictionary.
        response = requests.post(url, data=data)
        
        # Then it parses the JSON response given back by the API.
        response_data = response.json()
        
        # It checks if the response status code is 200 (successful).
        if response.status_code == 200:
            # Prints confirmation message
            print("Pushover notification sent successfully.")
        else:
            # Print an error message if failure. 
            print(f"Failed to send Pushover notification: {response.status_code}, Response: {response_data}")
    
    # Here it catches any exceptions that might come.
    except Exception as e:
        # Print the message.
        print(f"Error while sending Pushover notification: {str(e)}")

# We disable CSRF validation for this view to allow external sources (like API clients) to send POST requests.
@csrf_exempt
def create_crypto_transaction(request, product_id, product_type):
    # Here we make sure that the request method is POST before starting.
    if request.method == 'POST':
        # Then we parse the JSON data from the request body to get the transaction details.
        data = json.loads(request.body)

        # if the product type is 'one_time', then get the product from OneTimeProduct model;
        # otherwise, get from the UnlimitedProduct model.
        if product_type == 'one_time':
            product = get_object_or_404(OneTimeProduct, id=product_id)
        else:
            product = get_object_or_404(UnlimitedProduct, id=product_id)

        # Extract the user's name, email, and chosen cryptocurrency from the JSON data.
        name = data.get('name')
        email = data.get('email')
        crypto_choice = data.get('crypto_choice')

        # Check if both name and email are provided.
        if not name or not email:
            return JsonResponse({'error': 'Name and email are required'}, status=400)

        # Set the price_in_crypto to the corresponding value from the database according to the choice. 
        if crypto_choice == 'BTC':
            price_in_crypto = product.btc_price
        elif crypto_choice == 'LTC':
            price_in_crypto = product.ltc_price
        elif crypto_choice == 'ETH':
            price_in_crypto = product.eth_price
        elif crypto_choice == 'USDT.BEP20':
            price_in_crypto = product.usdt_price
        elif crypto_choice == 'USDT.ERC20':
            price_in_crypto = product.usdt_price
        elif crypto_choice == 'USDT.PRC20':
            price_in_crypto = product.usdt_price
        elif crypto_choice == 'USDT.SOL':
            price_in_crypto = product.usdt_price
        elif crypto_choice == 'USDT.TRC20':
            price_in_crypto = product.usdt_price
        elif crypto_choice == 'SOL':
            price_in_crypto = product.sol_price
        elif crypto_choice == 'LTCT': 
            price_in_crypto = product.test_price
        else:

            # If the selected cryptocurrency is not supported, then give an error.
            return JsonResponse({'error': 'Invalid cryptocurrency selected'}, status=400)

        # Check if the price in the selected cryptocurrency is available.
        if not price_in_crypto:
            return JsonResponse({'error': f"No price set for {crypto_choice}"}, status=400)

        try:
            # Here we use the CoinPayments API client to create a transaction with the previously gotten crypto price,
            # currency, buyer's details, and product details.
            response = coinpayments_client.create_transaction({
                'amount': price_in_crypto,       
                'currency1': crypto_choice,       
                'currency2': crypto_choice,      
                'buyer_email': email,             
                'item_name': product.title,      
                'custom': json.dumps({           
                    'product_id': product_id,
                    'name': name,
                    'email': email,
                    'product_type': product_type
                })
            })

            # Print the API response for debugging.
            print(f"CoinPayments response: {response}")

            # Check if transaction was successful.
            if response.get('error') == 'ok':
                # If successful, provide the checkout URL to the user to complete the payment.
                return JsonResponse({'checkout_url': response['checkout_url']})
            else:
                # If the API returned an error, give an error message to the user.
                return JsonResponse({'error': f"CoinPayments error: {response['error']}"}, status=400)

        # Handle any exceptions during the transaction process, such as network or API issues.
        except Exception as e:
            print(f"Exception occurred: {str(e)}") 
            return JsonResponse({'error': f"Failed to create transaction: {str(e)}"}, status=400)

    # If the request method is not POST, return an error.
    return JsonResponse({'error': 'Invalid request method'}, status=400)

# Exempt this view from CSRF validation since it needs to accept POST requests from outside sources (API).
@csrf_exempt
def coinpayments_ipn(request):
    # We need to check if the request method is POST to start.
    if request.method == 'POST':
        # Get the data from the POST request, which has the IPN data.
        data = request.POST

        # Print the received IPN data to the console for debugging.
        print("IPN Data Received:", data)

        # Get the merchant ID from environment variables.
        merchant_id = os.getenv('COINPAYMENTS_MERCHANT_ID')
        # We need to verify if the merchant ID in the data matches the merchant ID that is in the environment variables.
        if data.get('merchant') != merchant_id:
            print("Invalid merchant ID received")
            return JsonResponse({'error': 'Invalid merchant ID'}, status=400)

        # Check if transaction status tells a complete payment, used 100 as told in the docs. 
        if data.get('status') == '100':
            # Get the 'custom' field, which has the additional transaction details.
            custom_field = data.get('custom')
            # If 'custom' field is missing, print error and return a 400 error.
            if not custom_field:
                print("Missing 'custom' field in IPN data")
                return JsonResponse({'error': 'Missing custom field'}, status=400)

            try:
                # Here we parse the 'custom' field JSON data to get the transaction details.
                custom_data = json.loads(custom_field)
            except (json.JSONDecodeError, TypeError):
                # If parsing fails, print an error and return a 400 error.
                print("Error parsing custom data")
                return JsonResponse({'error': 'Invalid custom data'}, status=400)

            # Get the product id, type, name, email and the txn id fields from the parsed custom data.
            product_id = custom_data.get('product_id')
            product_type = custom_data.get('product_type')
            name = custom_data.get('name')
            email = custom_data.get('email')
            txn_id = data.get('txn_id')
            # We need to convert the amount field to a Decimal for accurate currency calculations.
            amount = Decimal(data.get('amount1'))
            # Also need to convert the currency field to uppercase for consistency.
            currency = data.get('currency1').upper()

            # Here we check if a sale with this transaction ID already exists to avoid duplicate processing which was a problem as
            # the IPN's were being sent multiple times.
            if ProductSale.objects.filter(stripe_session_id=txn_id).exists():
                print(f"Duplicate IPN received for transaction {txn_id}.") 
                return JsonResponse({'status': 'Transaction already processed'}, status=200)

            # If product type is 'one_time', process as a one-time purchase.
            if product_type == 'one_time':
                # Get the product from the OneTimeProduct model.
                product = get_object_or_404(OneTimeProduct, id=product_id)
                # Create a record of the sale in the ProductSale model so the user can see the sales.
                ProductSale.objects.create(
                    user=product.category.user,
                    product=product,
                    stripe_session_id=txn_id,
                    amount=amount,
                    currency=currency,
                    customer_name=name,
                    customer_email=email
                )

                # Update the seller's income with the sale amount.
                update_user_income(product.category.user, Decimal(data.get('amount1')), data.get('currency1').upper())

                # We also check if the seller has a Pushover notification key and send a notification as an optional notification way with the email.
                profile = UserProfile.objects.filter(user=product.category.user).first()
                if profile and profile.pushover_user_key:
                    send_pushover_notification(profile.pushover_user_key, f"🎉 {name} Ordered 1 item from your store!")

                # Here we prepare an email for the customer giving their order.
                from_name = AutoSell.objects.filter(user=product.category.user).first().name or "Mystorelink"
                from_email = f"{from_name} <{EMAIL_HOST_USER}>"
                customer_subject = f"Your purchase of {product.title}"
                customer_html_template = render_to_string("emails/crypto_one_time_purchase_confirmation.html", {
                    "customer_name": name,
                    "product_title": product.title,
                    "product_content": product.product_content,
                    "amount": amount,
                    "currency": currency,
                    "unique_hash": str(uuid.uuid4())
                })
                customer_email_message = EmailMultiAlternatives(
                    subject=customer_subject,
                    body=f"Hi {name},\n\nThank you for your purchase!",
                    from_email=from_email,
                    to=[email]
                )
                customer_email_message.attach_alternative(customer_html_template, "text/html")
                customer_email_message.send()
                print(f"Email sent for transaction {txn_id} (One-time product).")

                # Send a notification email to the product owner telling that they got a sale.
                owner_email = product.category.user.email
                owner_subject = f"DiscAuto Order confirmation for: {product.title} from {name}"
                owner_html_content = render_to_string("emails/crypto_sale_notification.html", {
                    "username": product.category.user.username,
                    "customer_name": name,
                    "product_title": product.title,
                    "customer_email": email,
                    "amount": amount,
                    "currency": currency,
                    "unique_hash": str(uuid.uuid4())
                })
                owner_email_message = EmailMultiAlternatives(
                    subject=owner_subject,
                    body=f"Congratulations on your sale, {product.category.user.username}!",
                    from_email=f"Mystorelink <{EMAIL_HOST_USER}>",
                    to=[product.category.user.email]
                )
                owner_email_message.attach_alternative(owner_html_content, "text/html")
                owner_email_message.send()
                print(f"Owner notification email sent to {owner_email} for transaction {txn_id}.")

            # If the product type is 'unlimited', do all the things same as above. 
            elif product_type == 'unlimited':
                # Get the UnlimitedProduct record based on the ID.
                product = get_object_or_404(UnlimitedProduct, id=product_id)
                ProductSale.objects.create(
                    user=product.user,
                    unlimited_product=product,
                    stripe_session_id=txn_id,
                    amount=amount,
                    currency=currency,
                    customer_name=name,
                    customer_email=email
                )

                # Update seller's total income.
                update_user_income(product.user, Decimal(data.get('amount1')), data.get('currency1').upper())

                # Send a Pushover notification (if user_key is there).
                profile = UserProfile.objects.filter(user=product.user).first()
                if profile and profile.pushover_user_key:
                    send_pushover_notification(profile.pushover_user_key, f"🎉 {name} Ordered 1 item from your store!")

                # Compile an email for the customer.
                from_name = AutoSell.objects.filter(user=product.user).first().name or "Mystorelink"
                from_email = f"{from_name} <{EMAIL_HOST_USER}>"
                customer_subject = f"Your purchase of {product.title}"
                customer_html_template = render_to_string("emails/crypto_purchase_confirmation.html", {
                    "customer_name": name,
                    "product_title": product.title,
                    "download_link": product.link,
                    "amount": amount,
                    "currency": currency,
                    "unique_hash": str(uuid.uuid4())
                })
                customer_email_message = EmailMultiAlternatives(
                    subject=customer_subject,
                    body=f"Hi {name},\n\nThank you for your purchase!",
                    from_email=from_email,
                    to=[email]
                )
                customer_email_message.attach_alternative(customer_html_template, "text/html")
                customer_email_message.send()
                print(f"Email sent for transaction {txn_id} (Unlimited product).")

                # Send an email to the product owner.
                owner_email = product.user.email
                owner_subject = f"DiscAuto Order confirmation for: {product.title} from {name}"
                owner_html_content = render_to_string("emails/crypto_sale_notification.html", {
                    "username": product.user.username,
                    "customer_name": name,
                    "product_title": product.title,
                    "customer_email": email,
                    "amount": amount,
                    "currency": currency,
                    "unique_hash": str(uuid.uuid4())
                })
                owner_email_message = EmailMultiAlternatives(
                    subject=owner_subject,
                    body=f"Congratulations on your sale, {product.user.username}!",
                    from_email=f"Mystorelink <{EMAIL_HOST_USER}>",
                    to=[product.user.email]
                )
                owner_email_message.attach_alternative(owner_html_content, "text/html")
                owner_email_message.send()
                print(f"Owner notification email sent to {owner_email} for transaction {txn_id}.")

            # Handle unknown product types by logging an error and giving back a 400 error response.
            else:
                print(f"Unknown product type: {product_type}")
                return JsonResponse({'error': 'Unknown product type'}, status=400)

            # Return a success status once processing is complete.
            return JsonResponse({'status': 'success'}, status=200)

        # Here it handles withdrawal completion status, which is 2. 
        elif data.get('status') == '2':
            print(f"Withdrawal complete for txn_id: {data.get('txn_id')}")
            return JsonResponse({'status': 'Complete'}, status=200)

        # Here it handle payment cancellation,which is '-1'
        elif data.get('status') == '-1':
            try:
                # First we parse custom data to get transaction details.
                custom_data = json.loads(data.get('custom'))
            except json.JSONDecodeError:
                print("Error parsing custom data")
                return JsonResponse({'error': 'Invalid custom data'}, status=400)

            product_id = custom_data.get('product_id')
            product_type = custom_data.get('product_type')
            currency = data.get('currency2')
            name = custom_data.get('name')
            email = custom_data.get('email')
            amount = data.get('amount1')
            txn_id = data.get('txn_id')

            # Then we send the cancellation email to the customer. This will make sure they know why they
            # haven't received their order. 
            send_mail(
                subject=f"Payment Cancellation Notification for {name}",
                message=(
                    f"Hi {name},\n\n"
                    f"Your payment for the {product_type} product has been canceled.\n\n"
                    f"Details:\n"
                    f"Amount you were supposed to pay: {amount} {currency}\n"
                    f"Your Unique ID: {txn_id}\n\n"
                    f"If you need any support, please contact us on our website.\n\n"
                    "Best regards,"
                ),
                from_email=from_email,
                recipient_list=[email],
            )
            print(f"Payment canceled email sent to {email} for transaction {txn_id}.")
            return JsonResponse({'status': 'canceled'}, status=200)

        # Here we handle pending payments.
        elif data.get('status') == '0':
            try:
                custom_data = json.loads(data.get('custom'))
            except json.JSONDecodeError:
                print("Error parsing custom data")
                return JsonResponse({'error': 'Invalid custom data'}, status=400)

            name = custom_data.get('name')
            email = custom_data.get('email')
            txn_id = data.get('txn_id')
            print(f"Waiting For Payment: {name}, Email: {email}, txn_id: {txn_id}")
            return JsonResponse({'status': 'Waiting'}, status=200)

        # Here we handle complete status for received payments.
        elif data.get('status') == '2':
            try:
                custom_data = json.loads(data.get('custom'))
            except json.JSONDecodeError:
                print("Error parsing custom data")
                return JsonResponse({'error': 'Invalid custom data'}, status=400)

            name = custom_data.get('name')
            email = custom_data.get('email')
            txn_id = data.get('txn_id')
            print(f"Payment completed for: {name}, Email: {email}, txn_id: {txn_id}")
            return JsonResponse({'status': 'Complete'}, status=200)

        # Here we handle funds coming to the owner of site. 
        elif data.get('status') == '1':
            try:
                custom_data = json.loads(data.get('custom'))
            except json.JSONDecodeError:
                print("Error parsing custom data")
                return JsonResponse({'error': 'Invalid custom data'}, status=400)

            name = custom_data.get('name')
            email = custom_data.get('email')
            txn_id = data.get('txn_id')
            print(f"Payment completed for: {name}, Email: {email}, txn_id: {txn_id} | Funds are being sent to you! (Owner)")
            return JsonResponse({'status': 'Sending you the funds!'}, status=200)

        # We log any unrecognized status which is missed and notify the user of an incomplete payment.
        else:
            status_text = data.get('status_text', 'Unknown status')
            print(f"Payment not complete. Status: {data.get('status')}, Message: {status_text}")
            return JsonResponse({'error': 'Payment not complete'}, status=400)

    # If request not a post, an error is returned. 
    print("Received non-POST request")
    return JsonResponse({'error': 'Invalid request method'}, status=400)


# Requires user login to access the products page.
@login_required
def products(request):
    # First we query OneTimeProductCategory for categories that are associated with the logged-in user.
    categories = OneTimeProductCategory.objects.filter(user=request.user)
    # Then we query UnlimitedProduct for products that are associated with the logged-in user.
    unlimited_products = UnlimitedProduct.objects.filter(user=request.user)

    # Finally we render the "products.html" template and pass the user's categories and unlimited products.
    # That will make it so that these variables can be accessed in the template and be used to display products.
    return render(request, "features/products/products.html", {
        'categories': categories,  
        'unlimited_products': unlimited_products, 
    })

@login_required
def add_category(request):
    if request.method == 'POST':
        form = OneTimeProductCategoryForm(request.POST, request.FILES)
        if form.is_valid():
            category = form.save(commit=False)
            category.user = request.user
            
            if 'category_image' in request.FILES:
                image_url = upload_to_supabase(request.FILES['category_image'], folder='category_images')
                category.category_image_url = image_url
            
            category.save()
            
            # Get AutoSell instances instead of LandingPage
            auto_sell_ids = request.POST.getlist('landing_pages')
            if auto_sell_ids:
                category.landing_pages.set(auto_sell_ids)
            
            messages.success(request, 'Category created successfully!')
            return redirect('products')
    else:
        form = OneTimeProductCategoryForm()
    
    # Get AutoSell instances for the current user
    landing_pages = AutoSell.objects.filter(user=request.user)
    
    return render(request, 'features/products/add_category.html', {
        'form': form,
        'landing_pages': landing_pages
    })

@login_required
def edit_category(request, pk):  # Change parameter from category_id to pk
    category = get_object_or_404(OneTimeProductCategory, id=pk, user=request.user)  # Change category_id to pk
    if request.method == 'POST':
        form = OneTimeProductCategoryForm(request.POST, request.FILES, instance=category)
        if form.is_valid():
            category = form.save(commit=False)
            
            if 'category_image' in request.FILES:
                image_url = upload_to_supabase(request.FILES['category_image'], folder='category_images')
                category.category_image_url = image_url
            
            category.save()
            
            # Get AutoSell instances instead of LandingPage
            auto_sell_ids = request.POST.getlist('landing_pages')
            if auto_sell_ids:
                category.landing_pages.set(auto_sell_ids)
            else:
                category.landing_pages.clear()
            
            messages.success(request, 'Category updated successfully!')
            return redirect('products')
    else:
        form = OneTimeProductCategoryForm(instance=category)
    
    # Get AutoSell instances for the current user
    landing_pages = AutoSell.objects.filter(user=request.user)
    selected_landing_pages = [page.id for page in category.landing_pages.all()]
    
    return render(request, 'features/products/edit_category.html', {
        'form': form,
        'category': category,
        'landing_pages': landing_pages,
        'selected_landing_pages': selected_landing_pages
    })

@login_required
def add_product_to_category(request, category_id):
    category = get_object_or_404(OneTimeProductCategory, id=category_id, user=request.user)
    
    if request.method == 'POST':
        form = OneTimeProductForm(request.POST, request.FILES)
        if form.is_valid():
            one_time_product = form.save(commit=False)
            one_time_product.category = category
            
            if 'product_image' in request.FILES:
                product_image_url = upload_to_supabase(request.FILES['product_image'], folder='one_time_products')
                one_time_product.product_image_url = product_image_url 

            one_time_product.save()

            # Handle landing pages - Fix: Get the landing page IDs from POST data
            landing_page_ids = request.POST.getlist('landing_pages')
            if landing_page_ids:
                # Get AutoSell objects that belong to the user
                landing_pages = AutoSell.objects.filter(id__in=landing_page_ids, user=request.user)
                one_time_product.landing_pages.set(landing_pages)

            try:
                stripe_product = stripe.Product.create(
                    name=one_time_product.title,
                    description=one_time_product.description or "No description provided",
                    metadata={
                        'django_product_id': one_time_product.id
                    }
                )

                stripe_price = stripe.Price.create(
                    product=stripe_product.id,
                    unit_amount=int(one_time_product.price * 100),
                    currency=one_time_product.currency.lower(),
                    recurring=None,
                    tax_behavior='exclusive',
                )

                one_time_product.stripe_product_id = stripe_product.id
                one_time_product.stripe_price_id = stripe_price.id
                one_time_product.save()

            except stripe.error.StripeError as e:
                print(f"Stripe error: {e}")
                return JsonResponse({'error': f"Stripe error: {e}"}, status=400)

            return redirect('category_detail', category_id=category.id)
    else:
        form = OneTimeProductForm()

    # Get available landing pages for the user
    landing_pages = AutoSell.objects.filter(user=request.user)
    return render(request, 'features/products/add_product_to_category.html', {
        'form': form,
        'category': category,
        'landing_pages': landing_pages,
    })


@login_required
def edit_one_time_product(request, pk):
    one_time_product = get_object_or_404(OneTimeProduct, pk=pk)
    
    if request.method == 'POST':
        form = OneTimeProductForm(request.POST, request.FILES, instance=one_time_product)
        if form.is_valid():
            updated_product = form.save(commit=False)
            
            if 'product_image' in request.FILES:
                product_image_url = upload_to_supabase(request.FILES['product_image'], folder='one_time_products')
                updated_product.product_image_url = product_image_url 

           # Handle landing pages selection
            landing_page_ids = request.POST.getlist('landing_pages')
            if landing_page_ids:
                # Get AutoSell objects that belong to the user
                landing_pages = AutoSell.objects.filter(id__in=landing_page_ids, user=request.user)
                updated_product.landing_pages.set(landing_pages)
            else:
                # Clear all landing pages if none selected
                updated_product.landing_pages.clear()

            if one_time_product.stripe_product_id:
                try:
                    stripe.Product.modify(
                        one_time_product.stripe_product_id,
                        name=updated_product.title,
                        description=updated_product.description,
                    )
                    
                    current_stripe_price = stripe.Price.retrieve(one_time_product.stripe_price_id)
                    if (updated_product.price * 100 != current_stripe_price.unit_amount) or (updated_product.currency.lower() != current_stripe_price.currency):
                        stripe.Price.modify(
                            one_time_product.stripe_price_id,
                            active=False
                        )
                        new_price = stripe.Price.create(
                            product=one_time_product.stripe_product_id,
                            unit_amount=int(updated_product.price * 100),
                            currency=updated_product.currency.lower(),
                            recurring=None,
                            tax_behavior='exclusive',
                        )
                        updated_product.stripe_price_id = new_price.id
                        updated_product.save()

                except stripe.error.StripeError as e:
                    print(f"Stripe error: {e}")
                    return JsonResponse({'error': f"Stripe error: {e}"}, status=400)

            return redirect('category_detail', category_id=one_time_product.category.id)
    else:
        form = OneTimeProductForm(instance=one_time_product)

    # Get all landing pages for this user to display in the form
    landing_pages = AutoSell.objects.filter(user=request.user)

    return render(request, 'features/products/edit_one_time_product.html', {
        'form': form,
        'product': one_time_product,
        'landing_pages': landing_pages,
    })

@login_required
def edit_unlimited_product(request, pk):
    product = get_object_or_404(UnlimitedProduct, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = UnlimitedProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            updated_product = form.save(commit=False)
            
            if 'product_image' in request.FILES:
                product_image_url = upload_to_supabase(request.FILES['product_image'], folder='unlimited_products')
                updated_product.product_image_url = product_image_url 

            # Save the product first
            updated_product.save()

            # Handle landing pages
            landing_page_ids = request.POST.getlist('landing_pages')
            if landing_page_ids:
                updated_product.landing_pages.set(landing_page_ids)
            else:
                updated_product.landing_pages.clear()

            if product.stripe_product_id:
                try:
                    stripe.Product.modify(
                        product.stripe_product_id,
                        name=updated_product.title,
                        description=updated_product.description or "No description provided",
                    )
                    
                    current_stripe_price = stripe.Price.retrieve(product.stripe_price_id)
                    if (updated_product.price * 100 != current_stripe_price.unit_amount) or (updated_product.currency.lower() != current_stripe_price.currency):
                        stripe.Price.modify(
                            product.stripe_price_id,
                            active=False
                        )
                        new_price = stripe.Price.create(
                            product=product.stripe_product_id,
                            unit_amount=int(updated_product.price * 100),
                            currency=updated_product.currency.lower(),
                            tax_behavior='exclusive',
                        )
                        updated_product.stripe_price_id = new_price.id
                        updated_product.save()

                except stripe.error.StripeError as e:
                    print(f"Stripe error: {e}")
                    return JsonResponse({'error': f"Stripe error: {e}"}, status=400)

            return redirect('products')
    else:
        form = UnlimitedProductForm(instance=product, user=request.user)

    landing_pages = AutoSell.objects.filter(user=request.user)
    return render(request, 'features/products/edit_unlimited_product.html', {
        'form': form,
        'product': product,
        'landing_pages': landing_pages,
    })

@login_required
def delete_one_time_product(request, pk):
    # Here we first get the one-time product by primary key for the current user’s category.
    product = get_object_or_404(OneTimeProduct, pk=pk, category__user=request.user)
    # Then we store the ID of the category that the product belongs to, as we will use it later
    category_id = product.category.id

    # Here we check if the product has an associated Stripe product ID because we need to archive it from there.
    if product.stripe_product_id:
        try:
            # We deactivate the product on Stripe.
            stripe.Product.modify(
                product.stripe_product_id,
                active=False
            )
        # We also handle any errors from Stripe gracefully.
        except stripe.error.StripeError as e:
            print(f"Error archiving one-time product on Stripe: {e}")

    # Here we delete the product from the database after archiving it from stripe.
    product.delete()

    # Finally we redirect the user to the category detail page after successfully deleting the product.
    return redirect('category_detail', category_id=category_id)

@login_required
def delete_category(request, pk):
    # First we get the category by primary key that belongs to the current user.
    category = get_object_or_404(OneTimeProductCategory, pk=pk, user=request.user)

    # Then we get all the one-time products associated with this category to handle them before deleting the category.
    one_time_products = OneTimeProduct.objects.filter(category=category)

    # Here we loop through each product in the category to archive all the products from stripe.
    for product in one_time_products:
        # If the product has a Stripe product ID, deactivate it on Stripe before deletion.
        if product.stripe_product_id:
            try:
                stripe.Product.modify(
                    product.stripe_product_id,
                    active=False  #
                )
            except stripe.error.StripeError as e:
                print(f"Error archiving product {product.title} on Stripe: {e}")
        
        # And we also delete the product from database.
        product.delete()

    # After deleting all the products inside the category, we delete the category too.
    category.delete()

    # Finally we redirect the user to the main products page.
    return redirect('products')

@login_required
def add_product_options(request):
    # Here we only render the page with options for adding different types of products.
    return render(request, "features/products/add_product_options.html")


@login_required
def add_unlimited_product(request):
    if request.method == 'POST':
        form = UnlimitedProductForm(request.POST, request.FILES)
        if form.is_valid():
            
            unlimited_product = form.save(commit=False)

            if 'product_image' in request.FILES:
                product_image_url = upload_to_supabase(request.FILES['product_image'], folder='unlimited_products')
                unlimited_product.product_image_url = product_image_url 

            unlimited_product.user = request.user
            unlimited_product.save()

            # Save landing pages
            landing_page_ids = request.POST.getlist('landing_pages')
            if landing_page_ids:
                unlimited_product.landing_pages.set(landing_page_ids)

            try:
                stripe_product = stripe.Product.create(
                    name=unlimited_product.title,
                    description=unlimited_product.description or "No description provided",
                    metadata={
                        'django_product_id': unlimited_product.id
                    }
                )

                stripe_price = stripe.Price.create(
                    product=stripe_product.id,
                    unit_amount=int(unlimited_product.price * 100),
                    currency=unlimited_product.currency.lower(),
                    recurring=None,
                    tax_behavior='exclusive',
                )

                unlimited_product.stripe_product_id = stripe_product.id
                unlimited_product.stripe_price_id = stripe_price.id
                unlimited_product.save()

            except stripe.error.StripeError as e:
                print(f"Stripe error: {e}")
                return JsonResponse({'error': f"Stripe error: {e}"}, status=400)

            return redirect('products')
    else:
        form = UnlimitedProductForm(user=request.user)

    landing_pages = AutoSell.objects.filter(user=request.user)
    return render(request, 'features/products/add_unlimited_product.html', {
        'form': form,
        'landing_pages': landing_pages,
    })

@login_required
def delete_unlimited_product(request, pk):
    product = get_object_or_404(UnlimitedProduct, pk=pk, user=request.user)

    # First we check if the product has a Stripe product ID 
    if product.stripe_product_id:
        try:
            # We try to deactivate the product on Stripe
            stripe.Product.modify(
                product.stripe_product_id,
                active=False
            )
        except stripe.error.StripeError as e:
            # If any errors, we log them
            print(f"Error archiving unlimited product on Stripe: {e}")

    # Then we delete the product from the database
    product.delete()

    # We also redirect the user to the products page
    return redirect('products')

@login_required
def category_detail(request, category_id):
    category = get_object_or_404(OneTimeProductCategory, id=category_id, user=request.user)

    # First we get all products connected with this category for display in the template.
    products = category.products.all()
    
    # Then we render the category detail template, passing in the category and its products to show on frontend
    return render(request, 'features/products/category_detail.html', {
        'category': category,
        'products': products,
    })

def product_detail(request, product_id):
    product = get_object_or_404(UnlimitedProduct, id=product_id)

    # Here we render the product detail template, we pass in the product and Stripe publishable key to use in the Fronted.
    return render(request, 'features/products/product_detail.html', {
        'product': product,
        'STRIPE_PUBLISHABLE_KEY': STRIPE_PUBLISHABLE_KEY 
    })
    
@csrf_exempt
def create_checkout_session(request, product_id):
    if request.method == 'POST':
        try:
            # Parse the JSON data from request and log it
            print(f"[DEBUG] Raw request body: {request.body}")
            data = json.loads(request.body)
            print(f"[DEBUG] Parsed JSON data: {data}")
            
            # Get the product and log its details
            product = get_object_or_404(UnlimitedProduct, id=product_id)
            print(f"[DEBUG] Product found: {product.id}, stripe_price_id: {product.stripe_price_id}")
            
            # Get and log customer details
            customer_name = data.get('name')
            customer_email = data.get('email')
            print(f"[DEBUG] Customer details - Name: {customer_name}, Email: {customer_email}")

            # Validate required fields
            if not customer_name or not customer_email:
                error_msg = "Name and email are required"
                print(f"[ERROR] {error_msg}")
                return JsonResponse({'error': error_msg}, status=400)

            # Validate stripe_price_id
            if not product.stripe_price_id:
                error_msg = "Product does not have a valid Stripe Price ID"
                print(f"[ERROR] {error_msg}")
                return JsonResponse({'error': error_msg}, status=400)

            # Create line items using the product's stripe price ID
            line_items = [{
                'price': product.stripe_price_id,
                'quantity': 1,
            }]

            # Create checkout session without automatic tax
            print("[DEBUG] Creating Stripe checkout session...")
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=line_items,
                mode='payment',
                success_url=request.build_absolute_uri(reverse('checkout_success')) + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=request.build_absolute_uri(reverse('checkout_cancel')),
                customer_email=customer_email,
                metadata={
                    'product_id': product.id,
                    'customer_name': customer_name,
                    'customer_email': customer_email
                }
            )
            print(f"[DEBUG] Checkout session created: {checkout_session.id}")
            
            return JsonResponse({'id': checkout_session.id})
            
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON data: {str(e)}"
            print(f"[ERROR] {error_msg}")
            return JsonResponse({'error': error_msg}, status=400)
        except stripe.error.StripeError as e:
            error_msg = f"Stripe error: {str(e)}"
            print(f"[ERROR] {error_msg}")
            return JsonResponse({'error': error_msg}, status=400)
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"[ERROR] {error_msg}")
            print(f"[ERROR] Full traceback: {traceback.format_exc()}")
            return JsonResponse({'error': 'An unexpected error occurred'}, status=400)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

def update_user_income(user, amount, currency):
    try:
        # Debug: Print initial values
        print(f"[DEBUG] Updating income for user: {user.username}")
        print(f"[DEBUG] Amount: {amount}, Currency: {currency}")

        # Get or create UserIncome record
        user_income, created = UserIncome.objects.get_or_create(user=user)
        print(f"[DEBUG] UserIncome record {'created' if created else 'retrieved'}")

        # Debug: Print current balances before update
        currency_attribute = f"{currency.lower().replace('.', '_')}_total"
        current_balance = getattr(user_income, currency_attribute, None)
        print(f"[DEBUG] Current balance for {currency_attribute}: {current_balance}")

        # Update income and get the result
        update_result = user_income.update_income(Decimal(str(amount)), currency)
        
        # Debug: Print new balance after update
        new_balance = getattr(user_income, currency_attribute, None)
        print(f"[DEBUG] New balance for {currency_attribute}: {new_balance}")
        print(f"[DEBUG] Update result: {update_result}")

        return True
    except Exception as e:
        print(f"[ERROR] Failed to update user income: {str(e)}")
        print(f"[ERROR] Traceback: ", traceback.format_exc())
        return False

def checkout_cancel(request):
    # Render the checkout cancel template
    return render(request, 'checkout/cancel.html')

def checkout_success(request):
    try:
        # Get the session ID from the request
        session_id = request.GET.get('session_id')
        if not session_id:
            return render(request, 'checkout/checkout_success.html', {'error': 'No session ID provided'})

        # Retrieve the checkout session from Stripe
        session = stripe.checkout.Session.retrieve(session_id)
        # Get metadata from the session
        product_id = session.metadata.get('product_id')
        customer_name = session.metadata.get('customer_name')
        customer_email = session.metadata.get('customer_email')
        
        # Get the product
        product = UnlimitedProduct.objects.filter(id=product_id).first()
        
        if not product:
            return render(request, 'checkout/checkout_success.html', {'error': 'Product not found'})

        # Prepare context for the template
        context = {
            'customer_name': customer_name,
            'product': product,
            'amount': session.amount_total / 100,  # Convert from cents to actual currency
            'currency': session.currency.upper(),
            'download_link': product.link if hasattr(product, 'link') else None,
            'session_id': session_id
        }
        
        # Record the sale in database
        ProductSale.objects.create(
            user=product.user,
            unlimited_product=product,
            stripe_session_id=session_id,
            amount=session.amount_total / 100,
            currency=session.currency.upper(),
            customer_name=customer_name,
            customer_email=customer_email
        )

        # Update the user's income
        update_user_income(product.user, session.amount_total / 100, session.currency.upper())

        # Get AutoSell info for email sending
        autosell_info = AutoSell.objects.filter(user=product.user).first()
        from_name = autosell_info.name if autosell_info else "Mystorelink"
        from_email = f"{from_name} <{EMAIL_HOST_USER}>"

        # Generate unique identifier for tracking
        unique_hash = str(uuid.uuid4())

        # Send confirmation email to customer
        customer_subject = f"Your purchase of {product.title}"
        customer_html_template = render_to_string("emails/purchase_confirmation.html", {
            "customer_name": customer_name,
            "product_title": product.title,
            "download_link": product.link,
            "amount": session.amount_total / 100,
            "currency": session.currency.upper(),
            "unique_hash": unique_hash
        })
        
        customer_email = EmailMultiAlternatives(
            subject=customer_subject,
            body=f"Hi {customer_name},\n\nThank you for your purchase!",
            from_email=from_email,
            to=[customer_email]
        )
        customer_email.attach_alternative(customer_html_template, "text/html")
        customer_email.send()

        # Send notification email to product owner
        owner_subject = f"New order: {product.price} {product.currency} from {customer_name}"
        owner_html_content = render_to_string("emails/sale_notification.html", {
            "username": product.user.username,
            "customer_name": customer_name,
            "product_title": product.title,
            "customer_email": session.metadata.get('customer_email'),  # Use the email string directly
            "amount": session.amount_total / 100,
            "currency": session.currency.upper(),
            "unique_hash": unique_hash
        })
        
        owner_email = EmailMultiAlternatives(
            subject=owner_subject,
            body=f"Congratulations on your sale {product.user.username}!",
            from_email=f"Mystorelink <{EMAIL_HOST_USER}>",
            to=[product.user.email]
        )
        owner_email.attach_alternative(owner_html_content, "text/html")
        owner_email.send()

        # Send Pushover notification if enabled
        profile, created = UserProfile.objects.get_or_create(user=product.user)
        if profile.pushover_user_key:
            message = f"🎉 {customer_name} ordered 1 item from your store!"
            send_pushover_notification(profile.pushover_user_key, message)

        # Render success template with context
        return render(request, 'checkout/checkout_success.html', context)

    except stripe.error.StripeError as e:
        return render(request, 'checkout/checkout_success.html', {'error': str(e)})
    except Exception as e:
        return render(request, 'checkout/checkout_success.html', {'error': 'An unexpected error occurred'})

# Here we show the details of a specific one-time product.
def one_time_product_detail(request, product_id):
    # We get the one-time product by its ID
    product = get_object_or_404(OneTimeProduct, id=product_id)

    # Here we get the first product in the product's category
    first_product_in_category = product.category.products.first()

    # Then we also store the previous page URL if available 
    if 'HTTP_REFERER' in request.META:
        request.session['previous_url'] = request.META.get('HTTP_REFERER')

    # Here we prepare context data to pass to the template, including the product, its category, and Stripe key.
    context = {
        'product': product,
        'first_product': first_product_in_category,
        'previous_url': request.session.get('previous_url'),
        'STRIPE_PUBLISHABLE_KEY': os.getenv('STRIPE_PUBLISHABLE_KEY')
    }

    # Finally we render the one-time product detail template with the context data collected
    return render(request, 'features/products/one_time_product_detail.html', context)

# Here we show the details of a specific unlimited product.
def unlimited_product_detail(request, product_id):
    # First we get the unlimited product by its ID
    product = get_object_or_404(UnlimitedProduct, id=product_id)

    # Then we render the unlimited product detail template
    return render(request, 'features/products/unlimited_product_detail.html', {
        'product': product,
        'STRIPE_PUBLISHABLE_KEY': STRIPE_PUBLISHABLE_KEY  
    })

@csrf_exempt
def create_one_time_checkout_session(request, product_id):
    if request.method == 'POST':
        data = json.loads(request.body)

        # First we get the one-time product by ID
        current_product = get_object_or_404(OneTimeProduct, id=product_id)
        customer_name = data.get('name')
        customer_email = data.get('email')

        try:
            # Here we create a checkout session on Stripe for the one-time product.
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],  # Simplified payment methods
                line_items=[{
                    'price': product.stripe_price_id,
                    'quantity': 1,
                }],
                automatic_tax={"enabled": True},  # Enable automatic tax calculation
                customer_update={  # Add address collection for tax calculation
                    'address': 'auto',
                    'shipping': 'auto'
                },
                mode='payment',
                success_url=request.build_absolute_uri(reverse('checkout_success')) + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=request.build_absolute_uri(reverse('checkout_cancel')),
                customer_email=customer_email,
                metadata={
                    'product_id': product.id,
                    'customer_name': customer_name,
                    'customer_email': customer_email
                }
            )

            return JsonResponse({'id': checkout_session.id})
        except stripe.error.StripeError as e:
            return JsonResponse({'error': str(e)}, status=400)

# Here we handle successful checkout for a one-time product purchase.
def one_time_checkout_success(request):
    session_id = request.GET.get('session_id')
    # Here it gets the Stripe checkout session to see metadata and payment details
    session = stripe.checkout.Session.retrieve(session_id)

    # Then we take out the product and customer details from the session metadata
    product_id = session.metadata.get('product_id')
    customer_name = session.metadata.get('customer_name')
    customer_email = session.metadata.get('customer_email')

    # Then we get the one-time product by ID
    product = get_object_or_404(OneTimeProduct, id=product_id)

    # Here we create a new record of the sale in the ProductSale model.
    ProductSale.objects.create(
        user=product.category.user,  
        product=product, 
        stripe_session_id=session_id,
        amount=session.amount_total / 100,  
        currency=session.currency.upper(),
        customer_name=customer_name, 
        customer_email=customer_email 
    )

    # Here we get the product owner's AutoSell information to send them a email.
    user = product.category.user
    autosell_info = AutoSell.objects.filter(user=user).first()
    from_name = autosell_info.name if autosell_info else "Mystorelink"
    from_email = f"{from_name} <{EMAIL_HOST_USER}>"

    unique_hash = str(uuid.uuid4())

    customer_subject = f"Your purchase of {product.title}"
    customer_html_template = render_to_string("emails/one_time_product_purchase_confirmation.html", {
        "customer_name": customer_name,
        "product_title": product.title,
        "product_content": product.product_content, 
        "amount": session.amount_total / 100,
        "currency": session.currency.upper(),
        "unique_hash": unique_hash
    })
    customer_email_message = EmailMultiAlternatives(
        subject=customer_subject,
        body=f"Hi {customer_name},\n\nThank you for your purchase!",
        from_email=from_email,
        to=[customer_email]
    )
    customer_email_message.attach_alternative(customer_html_template, "text/html")
    customer_email_message.send()

    owner_subject = f"New Order for {product.title} from {customer_name}"
    owner_html_content = render_to_string("emails/one_time_product_sale_notification.html", {
        "username": product.category.user.username,
        "product_title": product.title,
        "customer_name": customer_name,
        "customer_email": customer_email,
        "amount": session.amount_total / 100,
        "currency": session.currency.upper(),
        "unique_hash": unique_hash
    })
    owner_email_message = EmailMultiAlternatives(
        subject=owner_subject,
        body=f"Congratulations on your sale {product.category.user.username}!",
        from_email=f"Mystorelink <{EMAIL_HOST_USER}>",
        to=[product.category.user.email]
    )
    owner_email_message.attach_alternative(owner_html_content, "text/html")
    owner_email_message.send()

    profile, created = UserProfile.objects.get_or_create(user=product.category.user)
    owner_pushover_key = profile.pushover_user_key
    if owner_pushover_key:
        message = f"🎉 {customer_name} ordered 1 item from your store!"
        send_pushover_notification(owner_pushover_key, message)

    update_user_income(product.category.user, session.amount_total / 100, session.currency.upper())

    try:
        stripe.Product.modify(product.stripe_product_id, active=False)
    except stripe.error.StripeError as e:
        print(f"Error archiving product on Stripe: {e}")

    product.delete()

    previous_url = request.session.get('previous_url', '/')
    return redirect(previous_url)
