# Imports: 
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import OneTimeProductCategory, OneTimeProduct, UnlimitedProduct, ProductSale
from .forms import OneTimeProductCategoryForm, OneTimeProductForm, UnlimitedProductForm
from django.http import JsonResponse
from django.urls import reverse
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
from autosell.models import AutoSell  

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

# Requires user login to access the add_category page.
@login_required
def add_category(request):
    # First we check if the request method is POST as usual, we don't want random requests from outside the server. 
    if request.method == 'POST':
        # Then we initialize a form with data and files that are provided by the user when the request is sent.
        form = OneTimeProductCategoryForm(request.POST, request.FILES)
        # Then we validate the form data, meaning we check if the data provided in the form is correct and meets all the 
        # requirements specified in the form's fields. 
        if form.is_valid():
            # Then we create a new category object from the form data without saving it to the database yet.
            category = form.save(commit=False)
            # Then we assign the current logged-in user as the owner of the new category.
            category.user = request.user
            # Then we check if an image file is included in the request.
            if 'category_image' in request.FILES:
                # Then we upload the image to Supabase and get the URL to save in the category object, this way can save all
                # image files into supabase and show using urls 
                category_image_url = upload_to_supabase(request.FILES['category_image'], folder='categories')
                # Then we set the category's image URL to the uploaded file URL to access later. 
                category.category_image_url = category_image_url 
            
            # Then we finally save the category object to the database.
            category.save()
            # It also redirects the user to the products page after.
            return redirect('products')
    else:
        # Send error if request method is not POST.
        return JsonResponse({'error': 'Invalid request method!'}, status=400)

    # Finally we render the "add_category.html" template with the form to show the user.
    return render(request, 'features/products/add_category.html', {'form': form})

# Require user login to access add_product_to_category page.
@login_required
def add_product_to_category(request, category_id):
    # First we get the category with the given ID that relates to the logged-in user.
    category = get_object_or_404(OneTimeProductCategory, id=category_id, user=request.user)
    
    # Then we check if the request method is POST.
    if request.method == 'POST':
        # Then we initialize a form with data and files that are provided by the user when the request is sent.
        form = OneTimeProductForm(request.POST, request.FILES)
        # Then we validate the form data, meaning we check if the data provided in the form is correct and meets all the 
        # requirements specified in the form's fields. 
        if form.is_valid():
            # Then we create a new product object from the form data without saving it to the database yet.
            one_time_product = form.save(commit=False)
            # Then we assign the product to the specific category.
            one_time_product.category = category
            # Then we check if a product image file is included in the request.
            if 'product_image' in request.FILES:
                # Then we upload the image to Supabase and get the public URL to save in the product object.
                product_image_url = upload_to_supabase(request.FILES['product_image'], folder='one_time_products')
                # Then we set the product's image URL to the uploaded file URL.
                one_time_product.product_image_url = product_image_url 
            # Finally we save the one-time product to the database.
            one_time_product.save()

            try:
                # We also have to create a new stripe product.
                # Create a new product in Stripe for this one-time product.
                stripe_product = stripe.Product.create(
                    name=one_time_product.title, 
                    description=one_time_product.description, 
                    metadata={
                        'django_product_id': one_time_product.id 
                    }
                )
                # Create a price object in Stripe for the product.
                stripe_price = stripe.Price.create(
                    product=stripe_product.id,
                    unit_amount=int(one_time_product.price * 100), 
                    currency=one_time_product.currency.lower(),  
                    recurring=None, 
                )
                # Save the Stripe product ID and price ID in Django.
                one_time_product.stripe_product_id = stripe_product.id
                one_time_product.stripe_price_id = stripe_price.id
                # Update the product in the database with the Stripe IDs.
                one_time_product.save()

            except stripe.error.StripeError as e:
                # If any error message print the error and return a 400 error response.
                print(f"Stripe error: {e}")
                return JsonResponse({'error': f"Stripe error: {e}"}, status=400)

            # Redirect to the category details page after adding the product.
            return redirect('category_detail', category_id=category.id)
    else:
        # Send error if request method is not POST.
        return JsonResponse({'error': 'Invalid request method!'}, status=400)
    
    # Finally render the "add_product_to_category.html" template with the form and category context to show the user.
    return render(request, 'features/products/add_product_to_category.html', {'form': form, 'category': category})


# Makes sure people who are logged in can only use the page. 
@login_required
def edit_one_time_product(request, pk):
    # First get the specific one-time product by using the primary key (pk) from the database.
    one_time_product = get_object_or_404(OneTimeProduct, pk=pk)

    # Check if the request method is POST.
    if request.method == 'POST':
        # Here we have to initialize the form with the user submitted data and files, and connect it to the 
        # existing product instance, making it so that we can validate and save updates to this specific product.
        form = OneTimeProductForm(request.POST, request.FILES, instance=one_time_product)
        
        if form.is_valid():
            # Save the form data without committing to the database.
            updated_product = form.save(commit=False)
            
            # Check if a new product image is uploaded by the user when editing. 
            if 'product_image' in request.FILES:
                # Upload the new image to Supabase in the 'one_time_products' folder.
                # The Public URL from Supabase is then saved to the product, so that it can be used to 
                # display the images later.
                product_image_url = upload_to_supabase(request.FILES['product_image'], folder='one_time_products')
                updated_product.product_image_url = product_image_url 
            
            # Save the updated product with all changes to the database.
            updated_product.save()

            # We also want to update the product on stripe using the stipe ID.
            if one_time_product.stripe_product_id:
                try:
                    # We can update the product name and description on Stripe.
                    stripe.Product.modify(
                        one_time_product.stripe_product_id,
                        name=updated_product.title,
                        description=updated_product.description,
                    )

                    # First we get the current Stripe price.
                    current_stripe_price = stripe.Price.retrieve(one_time_product.stripe_price_id)
                    
                    # If the price or currency has changed, we need to create a new price in Stripe.
                    if (updated_product.price * 100 != current_stripe_price.unit_amount) or (updated_product.currency.lower() != current_stripe_price.currency):
                        # Deactivate the old price so only the new price is active.
                        # We cannot delete a price, rather we have to deactivate it.
                        stripe.Price.modify(
                            one_time_product.stripe_price_id,
                            active=False
                        )
                        # Create a new price on Stripe with the updated amount and currency.
                        new_price = stripe.Price.create(
                            product=one_time_product.stripe_product_id,
                            unit_amount=int(updated_product.price * 100),  
                            currency=updated_product.currency.lower(),
                            recurring=None,  
                        )
                        # Update the product with the new Stripe price ID.
                        updated_product.stripe_price_id = new_price.id

                # Catch any errors from Stripe and print them. 
                except stripe.error.StripeError as e:
                    print(f"Stripe error: {e}")
                    return JsonResponse({'error': f"Stripe error: {e}"}, status=400)

            # Redirect the user to the category detail page after saving.
            return redirect('category_detail', category_id=one_time_product.category.id)
    else:
        # Send error if request method is not POST.
        return JsonResponse({'error': 'Invalid request method!'}, status=400)

    # Finally render the template with the form to show the user.
    return render(request, 'features/products/edit_one_time_product.html', {'form': form})

# Only allow logged in users. 
@login_required
def edit_unlimited_product(request, pk):
    # Get the unlimited product by using the primary key (pk).
    product = get_object_or_404(UnlimitedProduct, pk=pk)

    # Check if the request method is POST.
    if request.method == 'POST':
        # Here we have to initialize the form with the user submitted data and files, and connect it to the 
        # existing product instance, making it so that we can validate and save updates to this specific product.
        form = UnlimitedProductForm(request.POST, request.FILES, instance=product)
        
        # Validate form
        if form.is_valid():
            # Save form without committing.
            updated_product = form.save(commit=False)

            # Check if a new product image was uploaded.
            if 'product_image' in request.FILES:
                # Upload the image to Supabase and save the Public URL to the product.
                product_image_url = upload_to_supabase(request.FILES['product_image'], folder='unlimited_products')
                updated_product.product_image_url = product_image_url 

            # Save the updated product with the new information.
            updated_product.save()

            # If the product has stripe product ID, update info on Stripe.
            if product.stripe_product_id:
                try:
                    # Modify product’s name and description on Stripe.
                    # If they weren't changed, thats fine, it will keep it the same. 
                    stripe.Product.modify(
                        product.stripe_product_id,
                        name=updated_product.title,
                        description=updated_product.description,
                    )
                    
                    # Get the current Stripe price.
                    current_stripe_price = stripe.Price.retrieve(product.stripe_price_id)

                    # Check if the price or currency has changed
                    if (updated_product.price * 100 != current_stripe_price.unit_amount) or (updated_product.currency.lower() != current_stripe_price.currency):
                        # Deactivate the old price
                        stripe.Price.modify(
                            product.stripe_price_id,
                            active=False
                        )
                        # Create a new price on Stripe (with amount and currency).
                        new_price = stripe.Price.create(
                            product=product.stripe_product_id,
                            unit_amount=int(updated_product.price * 100), 
                            currency=updated_product.currency.lower(),
                        )

                        # Update the product with the new Stripe price ID.
                        updated_product.stripe_price_id = new_price.id

                # Catch and print any Stripe errors.
                except stripe.error.StripeError as e:
                    print(f"Stripe error: {e}")
                    return JsonResponse({'error': f"Stripe error: {e}"}, status=400)

            # Save any final changes to the database and redirect the user to the products page.
            updated_product.save()
            return redirect('products')
    else:
        # Send error if request method is not POST.
        return JsonResponse({'error': 'Invalid request method!'}, status=400)

    # Finally render the template with the form to show the user.
    return render(request, 'features/products/edit_unlimited_product.html', {'form': form})


















# Only allow logged in users. 
@login_required
def edit_category(request, pk):
    # First get the specific category by primary key (pk) from the database, or return a 404 error.
    category = get_object_or_404(OneTimeProductCategory, pk=pk)

    # Check if the request method is POST, meaning the form has been submitted.
    if request.method == 'POST':
        # Bind the form to the submitted data and files, and link it to the current category instance.
        form = OneTimeProductCategoryForm(request.POST, request.FILES, instance=category)
        
        # Validate the form data to ensure it meets all required conditions.
        if form.is_valid():
            # Save the form data without committing to the database yet, allowing further edits.
            updated_category = form.save(commit=False)

            # Check if a new category image is included in the request.
            if 'category_image' in request.FILES:
                # Upload the image to Supabase, saving the returned URL to the category object.
                category_image_url = upload_to_supabase(request.FILES['category_image'], folder='category_images')
                updated_category.category_image_url = category_image_url

            # Save the updated category to the database.
            updated_category.save()
            # Redirect the user to the category detail page after saving.
            return redirect('category_detail', category_id=category.id)
    else:
        # Send error if request method is not POST.
        return JsonResponse({'error': 'Invalid request method!'}, status=400)

    # Finally render the template with the form to show the user.
    return render(request, 'features/products/edit_category.html', {'form': form})


# Ensure only logged-in users can delete a one-time product, protecting data access.
@login_required
def delete_one_time_product(request, pk):
    # Retrieve the one-time product by primary key (pk) for the current user’s category.
    # If the product doesn’t exist or doesn’t belong to the user, return a 404 error.
    product = get_object_or_404(OneTimeProduct, pk=pk, category__user=request.user)
    # Store the ID of the category that the product belongs to, to use in redirection after deletion.
    category_id = product.category.id

    # Check if the product has an associated Stripe product ID for archiving.
    if product.stripe_product_id:
        try:
            # Deactivate the product on Stripe to prevent further use but keep it in Stripe’s records.
            stripe.Product.modify(
                product.stripe_product_id,
                active=False
            )
        # Handle any errors from Stripe gracefully.
        except stripe.error.StripeError as e:
            print(f"Error archiving one-time product on Stripe: {e}")

    # Delete the product from the database after handling Stripe archiving.
    product.delete()

    # Redirect the user to the category detail page after successful deletion.
    return redirect('category_detail', category_id=category_id)

# Ensure only logged-in users can delete a category to protect user data.
@login_required
def delete_category(request, pk):
    # Retrieve the category by primary key (pk) that belongs to the current user.
    # Return a 404 error if it doesn’t exist or doesn’t belong to the user.
    category = get_object_or_404(OneTimeProductCategory, pk=pk, user=request.user)

    # Retrieve all one-time products associated with this category to handle them before deleting the category.
    one_time_products = OneTimeProduct.objects.filter(category=category)

    # Loop through each product in the category to handle any Stripe-related data.
    for product in one_time_products:
        # If the product has a Stripe product ID, deactivate it on Stripe before deletion.
        if product.stripe_product_id:
            try:
                stripe.Product.modify(
                    product.stripe_product_id,
                    active=False  # Deactivates the product on Stripe.
                )
            except stripe.error.StripeError as e:
                # Print an error message if the deactivation fails.
                print(f"Error archiving product {product.title} on Stripe: {e}")
        
        # Delete the product from the database after handling Stripe.
        product.delete()

    # Delete the category itself from the database after all products have been removed.
    category.delete()

    # Redirect the user to the main products page after deleting the category.
    return redirect('products')

# Ensure only logged-in users can access the product options page for adding new products.
@login_required
def add_product_options(request):
    # Render the page with options for adding different types of products.
    return render(request, "features/products/add_product_options.html")

# Ensure only logged-in users can add an unlimited product to protect data.
@login_required
def add_unlimited_product(request):
    # Check if the request method is POST, indicating form submission for adding a new product.
    if request.method == 'POST':
        # Initialize the form with the submitted data and files.
        form = UnlimitedProductForm(request.POST, request.FILES)
        
        # Validate the form data to ensure it meets all requirements.
        if form.is_valid():
            # Save the form data without committing, so we can set additional fields.
            unlimited_product = form.save(commit=False)
            # Assign the current logged-in user as the owner of the new product.
            unlimited_product.user = request.user

            # Check if an image file is uploaded with the product form.
            if 'product_image' in request.FILES:
                # Upload the image to Supabase and get the URL, saving it to the product.
                product_image_url = upload_to_supabase(request.FILES['product_image'], folder='unlimited_products')
                unlimited_product.product_image_url = product_image_url 

            # Save the product to the database with all information.
            unlimited_product.save()

            # Create a new product on Stripe to link this Django product to Stripe.
            stripe_product = stripe.Product.create(
                name=unlimited_product.title,
                description=unlimited_product.description,
                metadata={
                    'django_product_id': unlimited_product.id  # Attach the Django product ID for reference.
                }
            )
            # Create a price on Stripe associated with this product using the provided price and currency.
            stripe_price = stripe.Price.create(
                product=stripe_product.id,
                unit_amount=int(unlimited_product.price * 100),  # Convert price to cents for Stripe.
                currency=unlimited_product.currency.lower(),
                recurring=None,  # No recurring price since this is a one-time product.
            )

            # Save the Stripe product and price IDs to the unlimited product for future reference.
            unlimited_product.stripe_product_id = stripe_product.id
            unlimited_product.stripe_price_id = stripe_price.id
            unlimited_product.save()  # Commit all changes to the database.

            # Redirect the user to the products page after successfully adding the product.
            return redirect('products')
    else:
        # If the request method is not POST, initialize an empty form for the user to fill in.
        form = UnlimitedProductForm()

    # Render the add unlimited product page with the form for user input.
    return render(request, 'features/products/add_unlimited_product.html', {'form': form})


# Restrict this view to logged-in users for security, only allowing product deletion by the owner.
@login_required
def delete_unlimited_product(request, pk):
    # Retrieve the unlimited product by primary key (pk) that belongs to the logged-in user.
    # If it doesn’t exist or doesn’t belong to the user, return a 404 error.
    product = get_object_or_404(UnlimitedProduct, pk=pk, user=request.user)

    # Check if the product has a Stripe product ID before attempting to deactivate it.
    if product.stripe_product_id:
        try:
            # Deactivate the product on Stripe to keep records without allowing new purchases.
            stripe.Product.modify(
                product.stripe_product_id,
                active=False
            )
        except stripe.error.StripeError as e:
            # Log any errors encountered when attempting to deactivate the product on Stripe.
            print(f"Error archiving unlimited product on Stripe: {e}")

    # Delete the product from the database after handling Stripe.
    product.delete()

    # Redirect the user to the products page after successfully deleting the product.
    return redirect('products')

# Limit access to logged-in users to view details of a specific category.
@login_required
def category_detail(request, category_id):
    # Retrieve the category by its ID, ensuring it belongs to the logged-in user.
    # Return a 404 error if the category doesn’t exist or doesn’t belong to the user.
    category = get_object_or_404(OneTimeProductCategory, id=category_id, user=request.user)

    # Retrieve all products associated with this category for display in the template.
    products = category.products.all()
    
    # Render the category detail template, passing in the category and its products for display.
    return render(request, 'features/products/category_detail.html', {
        'category': category,
        'products': products,
    })

# View the details of a specific unlimited product, accessible to all users.
def product_detail(request, product_id):
    # Retrieve the unlimited product by its ID.
    # Return a 404 error if the product doesn’t exist.
    product = get_object_or_404(UnlimitedProduct, id=product_id)

    # Render the product detail template, passing in the product and Stripe publishable key for frontend use.
    return render(request, 'features/products/product_detail.html', {
        'product': product,
        'STRIPE_PUBLISHABLE_KEY': STRIPE_PUBLISHABLE_KEY 
    })

# Exempt CSRF protection for creating a checkout session, since it’s meant to receive POST requests from external sources.
@csrf_exempt
def create_checkout_session(request, product_id):
    # Check if the request method is POST, indicating a request to create a checkout session.
    if request.method == 'POST':
        # Parse the JSON data from the request body, expecting customer details.
        data = json.loads(request.body)
        
        # Retrieve the unlimited product by ID, returning a 404 if it doesn’t exist.
        product = get_object_or_404(UnlimitedProduct, id=product_id)
        customer_name = data.get('name')
        customer_email = data.get('email')

        # Store the previous page URL in session to redirect back after checkout.
        previous_url = request.META.get('HTTP_REFERER')
        request.session['previous_url'] = previous_url

        try:
            # Create a Stripe checkout session for the selected product.
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card', 'paypal'],
                line_items=[{
                    'price': product.stripe_price_id,  # Use the product's Stripe price ID.
                    'quantity': 1,
                }],
                mode='payment',  # Set the mode to one-time payment.
                success_url=request.build_absolute_uri(reverse('checkout_success')) + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=request.build_absolute_uri(reverse('checkout_cancel')),
                customer_email=customer_email,  # Pre-fill customer's email for Stripe.
                metadata={
                    'product_id': product.id,
                    'customer_name': customer_name,  
                    'customer_email': customer_email
                }
            )
            # Return the checkout session ID as a JSON response for frontend use.
            return JsonResponse({'id': checkout_session.id})
        except Exception as e:
            # Return an error message in JSON format if creating the session fails.
            return JsonResponse({'error': str(e)}, status=400)

# Update the user's income with the amount and currency, creating an income record if it doesn’t exist.
def update_user_income(user, amount, currency):
    # Retrieve or create a UserIncome record for the user, then update their income.
    user_income, created = UserIncome.objects.get_or_create(user=user)
    user_income.update_income(Decimal(str(amount)), currency)

# Handle successful checkout sessions, including updating records and sending confirmation emails.
def checkout_success(request):
    # Retrieve the session ID from the query parameters.
    session_id = request.GET.get('session_id')
    # Fetch the checkout session details from Stripe.
    session = stripe.checkout.Session.retrieve(session_id)

    # Retrieve metadata from the session for product and customer details.
    product_id = session.metadata.get('product_id')
    customer_name = session.metadata.get('customer_name')
    customer_email = session.metadata.get('customer_email')

    # Find the purchased unlimited product by its ID.
    unlimited_product = UnlimitedProduct.objects.filter(id=product_id).first()

    # Proceed if the product exists, otherwise return an error.
    if unlimited_product:
        user = unlimited_product.user

        # Retrieve the user's AutoSell info for branding the email sender.
        autosell_info = AutoSell.objects.filter(user=user).first()
        from_name = autosell_info.name if autosell_info else "Mystorelink"
        from_email = f"{from_name} <{EMAIL_HOST_USER}>"

        # Record the sale in the ProductSale model, including all transaction details.
        ProductSale.objects.create(
            user=unlimited_product.user,
            unlimited_product=unlimited_product,
            stripe_session_id=session_id,
            amount=session.amount_total / 100,
            currency=session.currency.upper(),
            customer_name=customer_name,
            customer_email=customer_email
        )

        # Generate a unique identifier for tracking purposes.
        unique_hash = str(uuid.uuid4())

        # Prepare and send a confirmation email to the customer with the purchase details.
        customer_subject = f"Your purchase of {unlimited_product.title}"
        customer_html_template = render_to_string("emails/purchase_confirmation.html", {
            "customer_name": customer_name,
            "product_title": unlimited_product.title,
            "download_link": unlimited_product.link,
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

        # Prepare and send a notification email to the product owner about the sale.
        owner_subject = f"DiscAuto Order confirmation for: {unlimited_product.price} {unlimited_product.currency} from {customer_name}"
        owner_html_content = render_to_string("emails/sale_notification.html", {
            "username": unlimited_product.user.username,
            "customer_name": customer_name,
            "product_title": unlimited_product.title,
            "customer_email": customer_email,
            "amount": session.amount_total / 100,
            "currency": session.currency.upper(),
            "unique_hash": unique_hash
        })
        owner_email = EmailMultiAlternatives(
            subject=owner_subject,
            body=f"Congratulations on your sale {unlimited_product.user.username}!",
            from_email=f"Mystorelink <{EMAIL_HOST_USER}>",
            to=[unlimited_product.user.email]
        )
        owner_email.attach_alternative(owner_html_content, "text/html")
        owner_email.send()

        # Update the owner's income record and send a Pushover notification if they have a key.
        profile, created = UserProfile.objects.get_or_create(user=unlimited_product.user)
        owner_pushover_key = profile.pushover_user_key
        if owner_pushover_key:
            message = f"🎉 {customer_name} Ordered 1 item from your store!"
            send_pushover_notification(owner_pushover_key, message)
            # Add the income to the user's income record with the transaction currency.
            update_user_income(unlimited_product.user, session.amount_total / 100, session.currency.upper())
        else:
            # Log a message if the owner doesn’t have a Pushover key for notifications.
            print(f"No Pushover key found for {unlimited_product.user.username}, skipping push notification.")
    
    else:
        # Return a JSON error if the product isn’t found.
        return JsonResponse({'error': 'Product not found'}, status=400)

    # Retrieve the previous URL from the session for redirection, then remove it.
    previous_url = request.session.get('previous_url', '/')
    request.session.pop('previous_url', None)
    # Redirect the user back to the previous page or homepage after checkout.
    return redirect(previous_url)


# Render the cancel checkout page if a customer cancels the checkout process.
def checkout_cancel(request):
    return render(request, 'checkout/cancel.html')

# Display the details of a specific one-time product.
def one_time_product_detail(request, product_id):
    # Retrieve the one-time product by its ID; return a 404 error if not found.
    product = get_object_or_404(OneTimeProduct, id=product_id)

    # Get the first product in the product's category for additional context, if needed.
    first_product_in_category = product.category.products.first()

    # Store the previous page URL in session to return to it later, if available.
    if 'HTTP_REFERER' in request.META:
        request.session['previous_url'] = request.META.get('HTTP_REFERER')

    # Prepare context data to pass to the template, including the product, its category, and Stripe key.
    context = {
        'product': product,
        'first_product': first_product_in_category,
        'previous_url': request.session.get('previous_url'),
        'STRIPE_PUBLISHABLE_KEY': os.getenv('STRIPE_PUBLISHABLE_KEY')
    }

    # Render the one-time product detail template with the context data.
    return render(request, 'features/products/one_time_product_detail.html', context)

# Display the details of a specific unlimited product.
def unlimited_product_detail(request, product_id):
    # Retrieve the unlimited product by its ID; return a 404 error if not found.
    product = get_object_or_404(UnlimitedProduct, id=product_id)

    # Render the unlimited product detail template, passing in the product and Stripe publishable key.
    return render(request, 'features/products/unlimited_product_detail.html', {
        'product': product,
        'STRIPE_PUBLISHABLE_KEY': STRIPE_PUBLISHABLE_KEY  
    })

# Exempt CSRF protection for creating a one-time checkout session.
@csrf_exempt
def create_one_time_checkout_session(request, product_id):
    # Ensure the request method is POST before processing.
    if request.method == 'POST':
        # Parse JSON data from the request body to retrieve customer details.
        data = json.loads(request.body)

        # Retrieve the one-time product by ID; return a 404 if not found.
        current_product = get_object_or_404(OneTimeProduct, id=product_id)

        customer_name = data.get('name')
        customer_email = data.get('email')

        try:
            # Create a checkout session on Stripe for the specified one-time product.
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card', 'paypal'],
                line_items=[{
                    'price': current_product.stripe_price_id,  # Use Stripe price ID for the product.
                    'quantity': 1,
                }],
                mode='payment',  # Set session to one-time payment mode.
                success_url=request.build_absolute_uri(reverse('one_time_checkout_success')) + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=request.build_absolute_uri(reverse('checkout_cancel')),
                customer_email=customer_email,
                metadata={
                    'product_id': current_product.id, 
                    'customer_name': customer_name,
                    'customer_email': customer_email,
                }
            )

            # Return the checkout session ID as a JSON response.
            return JsonResponse({'id': checkout_session.id})

        except stripe.error.StripeError as e:
            # If a Stripe error occurs, return the error as a JSON response.
            return JsonResponse({'error': str(e)}, status=400)

# Handle successful checkout for a one-time product purchase.
def one_time_checkout_success(request):
    # Retrieve the session ID from the query parameters.
    session_id = request.GET.get('session_id')
    # Retrieve the Stripe checkout session to access metadata and payment details.
    session = stripe.checkout.Session.retrieve(session_id)

    # Extract product and customer details from the session metadata.
    product_id = session.metadata.get('product_id')
    customer_name = session.metadata.get('customer_name')
    customer_email = session.metadata.get('customer_email')

    # Retrieve the one-time product by ID; return a 404 if it doesn’t exist.
    product = get_object_or_404(OneTimeProduct, id=product_id)

    # Create a new record of the sale in the ProductSale model.
    ProductSale.objects.create(
        user=product.category.user,  # Assign the sale to the product's owner.
        product=product, 
        stripe_session_id=session_id,
        amount=session.amount_total / 100,  # Convert cents to dollars.
        currency=session.currency.upper(),
        customer_name=customer_name, 
        customer_email=customer_email 
    )

    # Retrieve the product owner's AutoSell information for email branding.
    user = product.category.user
    autosell_info = AutoSell.objects.filter(user=user).first()
    from_name = autosell_info.name if autosell_info else "Mystorelink"
    from_email = f"{from_name} <{EMAIL_HOST_USER}>"

    # Generate a unique identifier for tracking and include it in the email.
    unique_hash = str(uuid.uuid4())

    # Prepare and send a confirmation email to the customer.
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

    # Prepare and send a notification email to the product owner about the sale.
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

    # Check if the product owner has a Pushover key and send a notification if available.
    profile, created = UserProfile.objects.get_or_create(user=product.category.user)
    owner_pushover_key = profile.pushover_user_key
    if owner_pushover_key:
        message = f"🎉 {customer_name} ordered 1 item from your store!"
        send_pushover_notification(owner_pushover_key, message)

    # Update the product owner's income with the sale amount and currency.
    update_user_income(product.category.user, session.amount_total / 100, session.currency.upper())

    # Deactivate the product on Stripe to prevent further purchases, since it's a one-time sale.
    try:
        stripe.Product.modify(product.stripe_product_id, active=False)
    except stripe.error.StripeError as e:
        # Log any errors encountered during deactivation on Stripe.
        print(f"Error archiving product on Stripe: {e}")

    # Delete the product from the database after handling the sale.
    product.delete()

    # Redirect the user back to the previous URL or the homepage if not available.
    previous_url = request.session.get('previous_url', '/')
    return redirect(previous_url)



# @login_required
# def add_one_time_product_to_category(request, category_id):
#     category = get_object_or_404(OneTimeProductCategory, id=category_id, user=request.user)

#     if request.method == 'POST':
#         form = OneTimeProductForm(request.POST, request.FILES)
#         if form.is_valid():
#             one_time_product = form.save(commit=False)
#             one_time_product.category = category
#             one_time_product.save()  

#             try:
#                 stripe_product = stripe.Product.create(
#                     name=one_time_product.title,
#                     description=one_time_product.description,
#                     metadata={
#                         'django_product_id': one_time_product.id
#                     }
#                 )

#                 stripe_price = stripe.Price.create(
#                     product=stripe_product.id,
#                     unit_amount=int(one_time_product.price * 100),  
#                     currency=one_time_product.currency.lower(),
#                     recurring=None  
#                 )

#                 one_time_product.stripe_product_id = stripe_product.id
#                 one_time_product.stripe_price_id = stripe_price.id
#                 one_time_product.save() 

#             except stripe.error.StripeError as e:
#                 print(f"Stripe error: {e}")
#                 return JsonResponse({'error': f"Stripe error: {e}"}, status=400)

#             return redirect('category_detail', category_id=category.id)
#     else:
#         form = OneTimeProductForm()

#     return render(request, 'features/products/add_product_to_category.html', {'form': form, 'category': category})
 

 

# @login_required
# def refresh_sales(request):
#     products = UnlimitedProduct.objects.filter(user=request.user)

#     for product in products:
#         stripe_sessions = stripe.checkout.Session.list(payment_status='paid')
#         for session in stripe_sessions:
#             if session.metadata['product_id'] == str(product.id) and not ProductSale.objects.filter(stripe_session_id=session.id).exists():
#                 ProductSale.objects.create(
#                     user=request.user,
#                     product=product,
#                     stripe_session_id=session.id,
#                     amount=session.amount_total / 100,  
#                     currency=session.currency.upper(),
#                 )

#     return JsonResponse({'message': 'Sales data refreshed successfully'})
