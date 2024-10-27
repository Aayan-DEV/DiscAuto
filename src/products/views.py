from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import OneTimeProductCategory, OneTimeProduct, UnlimitedProduct, ProductSale
from .forms import OneTimeProductCategoryForm, OneTimeProductForm, UnlimitedProductForm
from django.http import JsonResponse
from django.urls import reverse
from helpers.supabase import upload_to_supabase
import stripe
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
import os
import json
from pycoinpayments import CoinPayments
from dotenv import load_dotenv 
from auths.models import UserProfile
import requests
from .models import UserIncome
from decimal import Decimal

# Load .env file
if not os.getenv('RAILWAY_ENVIRONMENT'):
    load_dotenv(override=True)

# Get Stripe keys directly from the .env file
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')

# CoinPayments API credentials
COINPAYMENTS_PUBLIC_KEY = os.getenv('COINPAYMENTS_PUBLIC_KEY')
COINPAYMENTS_PRIVATE_KEY = os.getenv('COINPAYMENTS_PRIVATE_KEY')


# Set the Stripe API key to the secret key from .env
stripe.api_key = STRIPE_SECRET_KEY

# Initialize CoinPaymentsAPI using keys from environment
coinpayments_client = CoinPayments(
    public_key=COINPAYMENTS_PUBLIC_KEY,
    private_key=COINPAYMENTS_PRIVATE_KEY
)

        
# Function to send Pushover notification
def send_pushover_notification(user_key, message):
    pushover_token = os.getenv('PUSHOVER_API_TOKEN')  # Load App Token from .env
    if not pushover_token or not user_key:
        print("Pushover App Token or User Key is missing in the environment file.")
        return

    url = "https://api.pushover.net/1/messages.json"
    data = {
        "token": pushover_token,  # App Token
        "user": user_key,  # User Key
        "message": message,
        "title": "Cha-Ching!",
        "sound": "Cha-Ching"
    }

    try:
        response = requests.post(url, data=data)
        response_data = response.json()
        
        if response.status_code == 200:
            print("Pushover notification sent successfully.")
        else:
            print(f"Failed to send Pushover notification: {response.status_code}, Response: {response_data}")
    except Exception as e:
        print(f"Error while sending Pushover notification: {str(e)}")
        
@csrf_exempt
def create_crypto_transaction(request, product_id, product_type):
    if request.method == 'POST':
        data = json.loads(request.body)

        # Determine if the product is OneTime or Unlimited
        if product_type == 'one_time':
            product = get_object_or_404(OneTimeProduct, id=product_id)
        else:
            product = get_object_or_404(UnlimitedProduct, id=product_id)

        # Get user information
        name = data.get('name')
        email = data.get('email')
        crypto_choice = data.get('crypto_choice')

        if not name or not email:
            return JsonResponse({'error': 'Name and email are required'}, status=400)

        # Select the correct price based on the chosen cryptocurrency
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
        elif crypto_choice == 'LTCT':  # Handle the test coin (LTCT)
            price_in_crypto = product.test_price
        else:
            return JsonResponse({'error': 'Invalid cryptocurrency selected'}, status=400)

        # Ensure a price exists for the selected cryptocurrency
        if not price_in_crypto:
            return JsonResponse({'error': f"No price set for {crypto_choice}"}, status=400)

        # Create CoinPayments transaction for the chosen cryptocurrency
        try:
            response = coinpayments_client.create_transaction({
                'amount': price_in_crypto,          # The amount in the chosen crypto
                'currency1': crypto_choice,  
                'currency2': crypto_choice,          # Payment will be made in this currency
                'buyer_email': email,               # Customer's email
                'item_name': product.title,         # Product title for the transaction
                'custom': json.dumps({
                    'product_id': product_id,
                    'name': name,
                    'email': email,
                    'product_type': product_type
                })
            })

            # Log the response from CoinPayments for debugging purposes
            print(f"CoinPayments response: {response}")

            if response.get('error') == 'ok':
                return JsonResponse({'checkout_url': response['checkout_url']})
            else:
                return JsonResponse({'error': f"CoinPayments error: {response['error']}"}, status=400)

        except Exception as e:
            print(f"Exception occurred: {str(e)}")  # Log the exception
            return JsonResponse({'error': f"Failed to create transaction: {str(e)}"}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@csrf_exempt
def coinpayments_ipn(request):
    if request.method == 'POST':
        data = request.POST

        # Log received IPN for debugging
        print("IPN Data Received:", data)

        # Verify IPN by checking the merchant ID
        merchant_id = os.getenv('COINPAYMENTS_MERCHANT_ID')
        if data.get('merchant') != merchant_id:
            print("Invalid merchant ID received")
            return JsonResponse({'error': 'Invalid merchant ID'}, status=400)

        # Check if payment is complete
        if data.get('status') == '100':  # Status 100 means payment complete
            custom_field = data.get('custom')
            if not custom_field:
                print("Missing 'custom' field in IPN data")
                return JsonResponse({'error': 'Missing custom field'}, status=400)

            try:
                custom_data = json.loads(custom_field)  # Our custom product info
            except (json.JSONDecodeError, TypeError):
                print("Error parsing custom data")
                return JsonResponse({'error': 'Invalid custom data'}, status=400)

            # Extract the fields from the custom data
            product_id = custom_data.get('product_id')
            product_type = custom_data.get('product_type')
            name = custom_data.get('name')
            email = custom_data.get('email')
            txn_id = data.get('txn_id')  # CoinPayments transaction ID

            # Check if this transaction ID has already been processed
            if ProductSale.objects.filter(stripe_session_id=txn_id).exists():
                print(f"Duplicate IPN received for transaction {txn_id}.")
                return JsonResponse({'status': 'Transaction already processed'}, status=200)

            # Process the sale based on the product type
            if product_type == 'one_time':
                product = get_object_or_404(OneTimeProduct, id=product_id)
                ProductSale.objects.create(
                    user=product.category.user,
                    product=product,
                    stripe_session_id=txn_id,
                    amount=data.get('amount1'),
                    currency=data.get('currency1'),
                    customer_name=name,
                    customer_email=email
                )

                # Update user's income
                update_user_income(product.category.user, Decimal(data.get('amount1')), data.get('currency1').upper())

                # Send Pushover notification
                profile = UserProfile.objects.filter(user=product.category.user).first()
                if profile and profile.pushover_user_key:
                    message = f"🎉 {name} Ordered 1 item from your store!"
                    send_pushover_notification(profile.pushover_user_key, message)

                # Send email to the customer
                send_mail(
                    subject=f"Your purchase of {product.title}",
                    message=f"Hi {name},\n\nThank you for your purchase of {product.title}.\n {product.product_content} \nBest regards,",
                    from_email=os.getenv('EMAIL_HOST_USER'),
                    recipient_list=[email],
                )
                print(f"Email sent for transaction {txn_id} (One-time product).")

                # Send email to the product owner
                owner_email = product.category.user.email
                send_mail(
                    subject=f"DiscAuto Order confirmation for: {product.title} from {name}",
                    message=f"Congratulations on your sale, {product.category.user.username}!\n"
                            f"Order Details:\n"
                            f"Product: {product.title}\n"
                            f"Purchased by: {name}\n"
                            f"Customer Email: {email}\n\n"
                            "Thank you for Selling With DiscAuto!",
                    from_email=os.getenv('EMAIL_HOST_USER'),
                    recipient_list=[owner_email],
                )
                print(f"Owner notification email sent to {owner_email} for transaction {txn_id}.")

            elif product_type == 'unlimited':
                product = get_object_or_404(UnlimitedProduct, id=product_id)
                ProductSale.objects.create(
                    user=product.user,
                    unlimited_product=product,
                    stripe_session_id=txn_id,
                    amount=data.get('amount1'),
                    currency=data.get('currency1'),
                    customer_name=name,
                    customer_email=email
                )

                # Update user's income
                update_user_income(product.user, Decimal(data.get('amount1')), data.get('currency1').upper())

                # Send Pushover notification
                profile = UserProfile.objects.filter(user=product.user).first()
                if profile and profile.pushover_user_key:
                    message = f"🎉 {name} Ordered 1 item from your store!"
                    send_pushover_notification(profile.pushover_user_key, message)

                # Send email with product download link to the customer
                send_mail(
                    subject=f"Your purchase of {product.title}",
                    message=f"Hi {name},\n\nThank you for your purchase! You can download your product using the following link: {product.link}\n\nBest regards,",
                    from_email=os.getenv('EMAIL_HOST_USER'),
                    recipient_list=[email],
                )
                print(f"Email sent for transaction {txn_id} (Unlimited product).")

                # Send email to the product owner
                owner_email = product.user.email
                send_mail(
                    subject=f"DiscAuto Order confirmation for: {product.title} from {name}",
                    message=f"Congratulations on your sale, {product.user.username}!\n"
                            f"Order Details:\n"
                            f"Product: {product.title}\n"
                            f"Purchased by: {name}\n"
                            f"Customer Email: {email}\n\n"
                            "Thank you for Selling With DiscAuto!",
                    from_email=os.getenv('EMAIL_HOST_USER'),
                    recipient_list=[owner_email],
                )
                print(f"Owner notification email sent to {owner_email} for transaction {txn_id}.")

            else:
                print(f"Unknown product type: {product_type}")
                return JsonResponse({'error': 'Unknown product type'}, status=400)

            return JsonResponse({'status': 'success'}, status=200)

        elif data.get('status') == '2':  # Status 2 means withdrawal complete (for example)
            print(f"Withdrawal complete for txn_id: {data.get('txn_id')}")
            # Handle the withdrawal IPN, etc.
            return JsonResponse({'status': 'Complete'}, status=200)
        
        # Handle non-complete payments
        elif data.get('status') == '-1':  # Status -1 means payment was canceled
            try:
                custom_data = json.loads(data.get('custom'))  # Our custom product info
            except json.JSONDecodeError:
                print("Error parsing custom data")
                return JsonResponse({'error': 'Invalid custom data'}, status=400)

            product_id = custom_data.get('product_id')
            product_type = custom_data.get('product_type')
            currency = data.get('currency2')
            name = custom_data.get('name')
            email = custom_data.get('email')
            amount = data.get('amount1')  # Amount that was supposed to be sent
            txn_id = data.get('txn_id')  # CoinPayments transaction ID

            # Send cancellation email
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
                from_email=os.getenv('EMAIL_HOST_USER'),
                recipient_list=[email],
            )
            print(f"Payment canceled email sent to {email} for transaction {txn_id}.")

            return JsonResponse({'status': 'canceled'}, status=200)

        elif data.get('status') == '0':  # Status 0 means payment pending
            try:
                custom_data = json.loads(data.get('custom'))  # Our custom product info
            except json.JSONDecodeError:
                print("Error parsing custom data")
                return JsonResponse({'error': 'Invalid custom data'}, status=400)

            name = custom_data.get('name')
            email = custom_data.get('email')
            txn_id = data.get('txn_id')  # CoinPayments transaction ID

            print(f"Waiting For Payment: {name}, Email: {email}, txn_id: {txn_id}")
            return JsonResponse({'status': 'Waiting'}, status=200)
        
        elif data.get('status') == '2':  # Status 0 means payment pending
            try:
                custom_data = json.loads(data.get('custom'))  # Our custom product info
            except json.JSONDecodeError:
                print("Error parsing custom data")
                return JsonResponse({'error': 'Invalid custom data'}, status=400)

            name = custom_data.get('name')
            email = custom_data.get('email')
            txn_id = data.get('txn_id')  

            print(f"Payment completed for: {name}, Email: {email}, txn_id: {txn_id}")
            return JsonResponse({'status': 'Complete'}, status=200)
        
        elif data.get('status') == '1':  # Status 0 means payment pending
            try:
                custom_data = json.loads(data.get('custom'))  # Our custom product info
            except json.JSONDecodeError:
                print("Error parsing custom data")
                return JsonResponse({'error': 'Invalid custom data'}, status=400)

            name = custom_data.get('name')
            email = custom_data.get('email')
            txn_id = data.get('txn_id')  

            print(f"Payment completed for: {name}, Email: {email}, txn_id: {txn_id} | Funds are being sent to you! (Owner)")
            return JsonResponse({'status': 'Sending you the funds!'}, status=200)

        else:
            status_text = data.get('status_text', 'Unknown status')
            print(f"Payment not complete. Status: {data.get('status')}, Message: {status_text}")
            return JsonResponse({'error': 'Payment not complete'}, status=400)

    # Invalid request method (not POST)
    print("Received non-POST request")
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required
def products(request):
    # Get all categories and unlimited products for the logged-in user
    categories = OneTimeProductCategory.objects.filter(user=request.user)
    unlimited_products = UnlimitedProduct.objects.filter(user=request.user)

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
            
            # Upload category image to Supabase if it exists
            if 'category_image' in request.FILES:
                category_image_url = upload_to_supabase(request.FILES['category_image'], folder='categories')
                category.category_image_url = category_image_url  # Save URL to a URLField or CharField
            
            category.save()
            return redirect('products')
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
        form = OneTimeProductForm(request.POST, request.FILES)
        if form.is_valid():
            one_time_product = form.save(commit=False)
            one_time_product.category = category

            # Create the product in Stripe
            try:
                stripe_product = stripe.Product.create(
                    name=one_time_product.title,
                    description=one_time_product.description,
                    metadata={
                        'django_product_id': one_time_product.id 
                    }
                )

                # Create a one-time price for the product in Stripe
                stripe_price = stripe.Price.create(
                    product=stripe_product.id,
                    unit_amount=int(one_time_product.price * 100),  
                    currency=one_time_product.currency.lower(),
                    recurring=None, 
                )

                # Store the Stripe product and price IDs in the Django model
                one_time_product.stripe_product_id = stripe_product.id
                one_time_product.stripe_price_id = stripe_price.id
                one_time_product.save()

            except stripe.error.StripeError as e:
                print(f"Stripe error: {e}")
                return JsonResponse({'error': f"Stripe error: {e}"}, status=400)

            return redirect('category_detail', category_id=category.id)
    else:
        form = OneTimeProductForm()
    
    return render(request, 'features/products/add_product_to_category.html', {'form': form, 'category': category})

@login_required
def edit_one_time_product(request, pk):
    one_time_product = get_object_or_404(OneTimeProduct, pk=pk)

    if request.method == 'POST':
        form = OneTimeProductForm(request.POST, request.FILES, instance=one_time_product)
        if form.is_valid():
            updated_product = form.save(commit=False)

            if one_time_product.stripe_product_id:
                try:
                    # Update the product details in Stripe
                    stripe.Product.modify(
                        one_time_product.stripe_product_id,
                        name=updated_product.title,
                        description=updated_product.description,
                    )

                    # Retrieve current Stripe price and check for changes in price or currency
                    current_stripe_price = stripe.Price.retrieve(one_time_product.stripe_price_id)
                    if (updated_product.price * 100 != current_stripe_price.unit_amount) or (updated_product.currency.lower() != current_stripe_price.currency):
                        # Deactivate the old price
                        stripe.Price.modify(
                            one_time_product.stripe_price_id,
                            active=False
                        )

                        # Create a new price with updated price and/or currency
                        new_price = stripe.Price.create(
                            product=one_time_product.stripe_product_id,
                            unit_amount=int(updated_product.price * 100),  # Convert to cents
                            currency=updated_product.currency.lower(),
                            recurring=None,  # One-time payment
                        )

                        # Update the product with new Stripe price ID
                        updated_product.stripe_price_id = new_price.id

                except stripe.error.StripeError as e:
                    print(f"Stripe error: {e}")
                    return JsonResponse({'error': f"Stripe error: {e}"}, status=400)

            return redirect('category_detail', category_id=one_time_product.category.id)
    else:
        form = OneTimeProductForm(instance=one_time_product)

    return render(request, 'features/products/edit_one_time_product.html', {'form': form})

@login_required
def edit_unlimited_product(request, pk):
    product = get_object_or_404(UnlimitedProduct, pk=pk)

    if request.method == 'POST':
        form = UnlimitedProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            updated_product = form.save(commit=False)

            if 'product_image' in request.FILES:
                product_image_url = upload_to_supabase(request.FILES['product_image'], folder='unlimited_products')
                updated_product.product_image_url = product_image_url  # Save the Supabase URL to a URLField

            if product.stripe_product_id:
                try:
                    # Update the product in Stripe
                    stripe.Product.modify(
                        product.stripe_product_id,
                        name=updated_product.title,
                        description=updated_product.description,
                    )

                    # Retrieve the current Stripe price
                    current_stripe_price = stripe.Price.retrieve(product.stripe_price_id)
                    if (updated_product.price * 100 != current_stripe_price.unit_amount) or (updated_product.currency.lower() != current_stripe_price.currency):
                        # Deactivate the old price
                        stripe.Price.modify(
                            product.stripe_price_id,
                            active=False
                        )

                        # Create a new price with updated price and/or currency
                        new_price = stripe.Price.create(
                            product=product.stripe_product_id,
                            unit_amount=int(updated_product.price * 100),  # Convert to cents
                            currency=updated_product.currency.lower(),
                        )

                        # Update the product with the new price ID
                        updated_product.stripe_price_id = new_price.id

                except stripe.error.StripeError as e:
                    print(f"Stripe error: {e}")
                    return JsonResponse({'error': f"Stripe error: {e}"}, status=400)

            updated_product.save()
            return redirect('products')
    else:
        form = UnlimitedProductForm(instance=product)

    return render(request, 'features/products/edit_unlimited_product.html', {'form': form})

@login_required
def edit_category(request, pk):
    category = get_object_or_404(OneTimeProductCategory, pk=pk)

    if request.method == 'POST':
        form = OneTimeProductCategoryForm(request.POST, request.FILES, instance=category)
        if form.is_valid():
            form.save()
            return redirect('category_detail', category_id=category.id)  # Ensure correct redirect
    else:
        form = OneTimeProductCategoryForm(instance=category)

    return render(request, 'features/products/edit_category.html', {'form': form})  # Template updated

@login_required
def delete_one_time_product(request, pk):
    product = get_object_or_404(OneTimeProduct, pk=pk, category__user=request.user)
    category_id = product.category.id

    # Archive the product on Stripe before deleting it from the database
    if product.stripe_product_id:
        try:
            stripe.Product.modify(
                product.stripe_product_id,
                active=False
            )
        except stripe.error.StripeError as e:
            print(f"Error archiving one-time product on Stripe: {e}")

    # Delete the product from the database
    product.delete()

    return redirect('category_detail', category_id=category_id)

@login_required
def delete_category(request, pk):
    category = get_object_or_404(OneTimeProductCategory, pk=pk, user=request.user)
    
    # Retrieve all one-time products in this category
    one_time_products = OneTimeProduct.objects.filter(category=category)
    
    for product in one_time_products:
        # Archive the product on Stripe
        if product.stripe_product_id:
            try:
                stripe.Product.modify(
                    product.stripe_product_id,
                    active=False  # Archive (set inactive) in Stripe
                )
            except stripe.error.StripeError as e:
                print(f"Error archiving product {product.title} on Stripe: {e}")
        
        # Delete the product from the database
        product.delete()

    # After archiving and deleting the one-time products, delete the category
    category.delete()

    return redirect('products')

@login_required
def add_product_options(request):
    return render(request, "features/products/add_product_options.html")

# Unlimited product-related views
@login_required
def add_unlimited_product(request):
    if request.method == 'POST':
        form = UnlimitedProductForm(request.POST, request.FILES)
        if form.is_valid():
            unlimited_product = form.save(commit=False)
            unlimited_product.user = request.user
            if 'product_image' in request.FILES:
                product_image_url = upload_to_supabase(request.FILES['product_image'], folder='unlimited_products')
                unlimited_product.product_image_url = product_image_url  # Assuming `product_image_url` is a URL field


            unlimited_product.save()

            # Create the product in Stripe
            stripe_product = stripe.Product.create(
                name=unlimited_product.title,
                description=unlimited_product.description,
                metadata={
                    'django_product_id': unlimited_product.id  
                }
            )

            # Create a one-time price for the product in Stripe
            stripe_price = stripe.Price.create(
                product=stripe_product.id,
                unit_amount=int(unlimited_product.price * 100), 
                currency=unlimited_product.currency.lower(),
                recurring=None,  
            )

            # Store the Stripe product and price IDs in the Django model
            unlimited_product.stripe_product_id = stripe_product.id
            unlimited_product.stripe_price_id = stripe_price.id
            unlimited_product.save()

            return redirect('products')  
    else:
        form = UnlimitedProductForm()

    return render(request, 'features/products/add_unlimited_product.html', {'form': form})

@login_required
def delete_unlimited_product(request, pk):
    product = get_object_or_404(UnlimitedProduct, pk=pk, user=request.user)

    # Archive the product on Stripe before deleting it from the database
    if product.stripe_product_id:
        try:
            stripe.Product.modify(
                product.stripe_product_id,
                active=False
            )
        except stripe.error.StripeError as e:
            print(f"Error archiving unlimited product on Stripe: {e}")
    # Deletes the product from the database.
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

def product_detail(request, product_id):
    product = get_object_or_404(UnlimitedProduct, id=product_id)

    # Renders the product detail page with the product and Stripe publishable key.
    return render(request, 'features/products/product_detail.html', {
        'product': product,
        'STRIPE_PUBLISHABLE_KEY': STRIPE_PUBLISHABLE_KEY 
    })

@csrf_exempt
def create_checkout_session(request, product_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        product = get_object_or_404(UnlimitedProduct, id=product_id)
        customer_name = data.get('name')
        customer_email = data.get('email')

        # Store the previous URL in session
        previous_url = request.META.get('HTTP_REFERER')
        request.session['previous_url'] = previous_url

        try:
            # Creates a Stripe Checkout session
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card', 'paypal'],
                line_items=[{
                    'price': product.stripe_price_id, 
                    'quantity': 1,
                }],
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
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

def update_user_income(user, amount, currency):
    user_income, created = UserIncome.objects.get_or_create(user=user)
    user_income.update_income(Decimal(str(amount)), currency)

# Checkout Success View
def checkout_success(request):
    session_id = request.GET.get('session_id')
    session = stripe.checkout.Session.retrieve(session_id)

    # Get product and customer details from Stripe metadata
    product_id = session.metadata.get('product_id')
    customer_name = session.metadata.get('customer_name')
    customer_email = session.metadata.get('customer_email')

    unlimited_product = UnlimitedProduct.objects.filter(id=product_id).first()

    if unlimited_product:
        # Record the sale in the database
        ProductSale.objects.create(
            user=unlimited_product.user,
            unlimited_product=unlimited_product,
            stripe_session_id=session_id,
            amount=session.amount_total / 100,
            currency=session.currency.upper(),
            customer_name=customer_name,
            customer_email=customer_email
        )

        # Send confirmation email to the customer
        send_mail(
            subject=f"Your purchase of {unlimited_product.title}",
            message=f"Hi {customer_name},\n\nThank you for your purchase! You can download your product using the following link: {unlimited_product.link}\n\nThank you for your purchase!",
            from_email=EMAIL_HOST_USER,
            recipient_list=[customer_email],
        )

        # Notify the product owner about the sale via email
        owner_email = unlimited_product.user.email
        send_mail(
            subject=f"DiscAuto Order confirmation for: {unlimited_product.price} {unlimited_product.currency} from {customer_name}",
            message=f"Congratulation on your sale {unlimited_product.user.username}! \nOrder Details: \nProduct: {unlimited_product.title} \nPurchased by {customer_name} \nCustomer Email:({customer_email}).\n\nThank you for Selling With DiscAuto!",
            from_email=EMAIL_HOST_USER,
            recipient_list=[owner_email],
        )

        # Fetch the product owner's profile to get the Pushover user key
        profile, created = UserProfile.objects.get_or_create(user=unlimited_product.user)

        # Send push notification only if the pushover_user_key exists
        owner_pushover_key = profile.pushover_user_key

        if owner_pushover_key:
            message = f"🎉 {customer_name} Ordered 1 item from your store!"
            send_pushover_notification(owner_pushover_key, message)
            update_user_income(unlimited_product.user, session.amount_total / 100, session.currency.upper())
        else:
            print(f"No Pushover key found for {unlimited_product.user.username}, skipping push notification.")

    else:
        return JsonResponse({'error': 'Product not found'}, status=400)

    # Redirect to the previous page
    previous_url = request.session.get('previous_url', '/')
    request.session.pop('previous_url', None)
    return redirect(previous_url)

def checkout_cancel(request):
    return render(request, 'checkout/cancel.html')

def one_time_product_detail(request, product_id):
    # Get the one-time product
    product = get_object_or_404(OneTimeProduct, id=product_id)

    # Get the first product in the same category
    first_product_in_category = product.category.products.first()

    # Save the previous URL (landing page) to the session if it's available
    if 'HTTP_REFERER' in request.META:
        request.session['previous_url'] = request.META.get('HTTP_REFERER')

    context = {
        'product': product,
        'first_product': first_product_in_category,
        'previous_url': request.session.get('previous_url'),
        'STRIPE_PUBLISHABLE_KEY': os.getenv('STRIPE_PUBLISHABLE_KEY')
    }

    return render(request, 'features/products/one_time_product_detail.html', context)

# Product page for Unlimited Product
def unlimited_product_detail(request, product_id):
    product = get_object_or_404(UnlimitedProduct, id=product_id)

    return render(request, 'features/products/unlimited_product_detail.html', {
        'product': product,
        'STRIPE_PUBLISHABLE_KEY': STRIPE_PUBLISHABLE_KEY  
    })

@login_required
def refresh_sales(request):
    # Get all Stripe checkout sessions for the user's products
    products = UnlimitedProduct.objects.filter(user=request.user)

    for product in products:
        stripe_sessions = stripe.checkout.Session.list(payment_status='paid')
        for session in stripe_sessions:
            # Check if the session is for this product and doesn't already exist in the database
            if session.metadata['product_id'] == str(product.id) and not ProductSale.objects.filter(stripe_session_id=session.id).exists():
                # Create a sale record in the database
                ProductSale.objects.create(
                    user=request.user,
                    product=product,
                    stripe_session_id=session.id,
                    amount=session.amount_total / 100,  
                    currency=session.currency.upper(),
                )

    return JsonResponse({'message': 'Sales data refreshed successfully'})

@csrf_exempt
def create_one_time_checkout_session(request, product_id):
    if request.method == 'POST':
        data = json.loads(request.body)

        # Get the correct product from the ID in the URL (this makes sure that it's the one shown)
        current_product = get_object_or_404(OneTimeProduct, id=product_id)

        customer_name = data.get('name')
        customer_email = data.get('email')

        try:
            # Create a Stripe Checkout session for the displayed product
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card', 'paypal'],
                line_items=[{
                    'price': current_product.stripe_price_id,  
                    'quantity': 1,
                }],
                mode='payment',
                success_url=request.build_absolute_uri(reverse('one_time_checkout_success')) + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=request.build_absolute_uri(reverse('checkout_cancel')),
                customer_email=customer_email,
                metadata={
                    'product_id': current_product.id, 
                    'customer_name': customer_name,
                    'customer_email': customer_email,
                }
            )

            return JsonResponse({'id': checkout_session.id})

        except stripe.error.StripeError as e:
            return JsonResponse({'error': str(e)}, status=400)

def one_time_checkout_success(request):
    session_id = request.GET.get('session_id')
    session = stripe.checkout.Session.retrieve(session_id)

    # Get product and customer details from Stripe metadata
    product_id = session.metadata.get('product_id')
    customer_name = session.metadata.get('customer_name')
    customer_email = session.metadata.get('customer_email')

    # Get the product
    product = get_object_or_404(OneTimeProduct, id=product_id)

    # Log the sale in the database
    ProductSale.objects.create(
        user=product.category.user,  
        product=product, 
        stripe_session_id=session_id,
        amount=session.amount_total / 100, 
        currency=session.currency.upper(),
        customer_name=customer_name, 
        customer_email=customer_email 
    )

    # Send the product content to the customer's email
    send_mail(
        subject=f"Your purchase of {product.title}",
        message=f"Hi {customer_name},\n\nThank you for buying! Here is your product:\n\n{product.product_content}\n\nRegards,",
        from_email=EMAIL_HOST_USER,
        recipient_list=[customer_email],
    )

    update_user_income(product.category.user, session.amount_total / 100, session.currency.upper())

    # Archive the product on Stripe
    try:
        stripe.Product.modify(
            product.stripe_product_id,
            active=False 
        )
    except stripe.error.StripeError as e:
        print(f"Error archiving product on Stripe: {e}")

    # Delete the product from the database
    product.delete()

    # Redirect the user to the previous landing page
    previous_url = request.session.get('previous_url', '/')
    return redirect(previous_url)

@login_required
def add_one_time_product_to_category(request, category_id):
    category = get_object_or_404(OneTimeProductCategory, id=category_id, user=request.user)

    if request.method == 'POST':
        form = OneTimeProductForm(request.POST, request.FILES)
        if form.is_valid():
            one_time_product = form.save(commit=False)
            one_time_product.category = category
            one_time_product.save()  

            try:
                # Create the product in Stripe
                stripe_product = stripe.Product.create(
                    name=one_time_product.title,
                    description=one_time_product.description,
                    metadata={
                        'django_product_id': one_time_product.id
                    }
                )

                # Create the price in Stripe
                stripe_price = stripe.Price.create(
                    product=stripe_product.id,
                    unit_amount=int(one_time_product.price * 100),  
                    currency=one_time_product.currency.lower(),
                    recurring=None  
                )

                # Update the product with Stripe IDs and save
                one_time_product.stripe_product_id = stripe_product.id
                one_time_product.stripe_price_id = stripe_price.id
                one_time_product.save() 

            except stripe.error.StripeError as e:
                # If Stripe fails, print the error and return a JSON error response
                print(f"Stripe error: {e}")
                return JsonResponse({'error': f"Stripe error: {e}"}, status=400)

            # Redirect to the category details page after successful creation
            return redirect('category_detail', category_id=category.id)
    else:
        form = OneTimeProductForm()

    return render(request, 'features/products/add_product_to_category.html', {'form': form, 'category': category})
