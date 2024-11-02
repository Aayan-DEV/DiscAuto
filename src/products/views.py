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
import uuid
from dotenv import load_dotenv, dotenv_values
from auths.models import UserProfile
import requests
from .models import UserIncome
from decimal import Decimal
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from autosell.models import AutoSell  # Import AutoSell model from the autosell app

# Load environment variables from .env and override if necessary
if not os.getenv('RAILWAY_ENVIRONMENT'):
    load_dotenv(override=True)  # Override all env vars from .env
    os.environ.update(dotenv_values())  # Ensure any pre-existing vars are overwritten

# Load variables with fallback to ensure they exist
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
COINPAYMENTS_PUBLIC_KEY = os.getenv('COINPAYMENTS_PUBLIC_KEY')
COINPAYMENTS_PRIVATE_KEY = os.getenv('COINPAYMENTS_PRIVATE_KEY')

stripe.api_key = STRIPE_SECRET_KEY

coinpayments_client = CoinPayments(
    public_key=COINPAYMENTS_PUBLIC_KEY,
    private_key=COINPAYMENTS_PRIVATE_KEY
)

def send_pushover_notification(user_key, message):
    pushover_token = os.getenv('PUSHOVER_API_TOKEN') 
    if not pushover_token or not user_key:
        print("Pushover App Token or User Key is missing in the environment file.")
        return

    url = "https://api.pushover.net/1/messages.json"
    data = {
        "token": pushover_token, 
        "user": user_key, 
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

        if product_type == 'one_time':
            product = get_object_or_404(OneTimeProduct, id=product_id)
        else:
            product = get_object_or_404(UnlimitedProduct, id=product_id)

        name = data.get('name')
        email = data.get('email')
        crypto_choice = data.get('crypto_choice')

        if not name or not email:
            return JsonResponse({'error': 'Name and email are required'}, status=400)

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
            return JsonResponse({'error': 'Invalid cryptocurrency selected'}, status=400)

        if not price_in_crypto:
            return JsonResponse({'error': f"No price set for {crypto_choice}"}, status=400)

        try:
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

            print(f"CoinPayments response: {response}")

            if response.get('error') == 'ok':
                return JsonResponse({'checkout_url': response['checkout_url']})
            else:
                return JsonResponse({'error': f"CoinPayments error: {response['error']}"}, status=400)

        except Exception as e:
            print(f"Exception occurred: {str(e)}") 
            return JsonResponse({'error': f"Failed to create transaction: {str(e)}"}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@csrf_exempt
def coinpayments_ipn(request):
    if request.method == 'POST':
        data = request.POST

        print("IPN Data Received:", data)

        merchant_id = os.getenv('COINPAYMENTS_MERCHANT_ID')
        if data.get('merchant') != merchant_id:
            print("Invalid merchant ID received")
            return JsonResponse({'error': 'Invalid merchant ID'}, status=400)

        if data.get('status') == '100': 
            custom_field = data.get('custom')
            if not custom_field:
                print("Missing 'custom' field in IPN data")
                return JsonResponse({'error': 'Missing custom field'}, status=400)

            try:
                custom_data = json.loads(custom_field)  
            except (json.JSONDecodeError, TypeError):
                print("Error parsing custom data")
                return JsonResponse({'error': 'Invalid custom data'}, status=400)

            product_id = custom_data.get('product_id')
            product_type = custom_data.get('product_type')
            name = custom_data.get('name')
            email = custom_data.get('email')
            txn_id = data.get('txn_id')
            amount = Decimal(data.get('amount1'))
            currency = data.get('currency1').upper()

            if ProductSale.objects.filter(stripe_session_id=txn_id).exists():
                print(f"Duplicate IPN received for transaction {txn_id}.")
                return JsonResponse({'status': 'Transaction already processed'}, status=200)

            if product_type == 'one_time':
                product = get_object_or_404(OneTimeProduct, id=product_id)
                ProductSale.objects.create(
                    user=product.category.user,
                    product=product,
                    stripe_session_id=txn_id,
                    amount=amount,
                    currency=currency,
                    customer_name=name,
                    customer_email=email
                )

                update_user_income(product.category.user, Decimal(data.get('amount1')), data.get('currency1').upper())

                profile = UserProfile.objects.filter(user=product.category.user).first()
                if profile and profile.pushover_user_key:
                    send_pushover_notification(profile.pushover_user_key, f"🎉 {name} Ordered 1 item from your store!")

                product = get_object_or_404(OneTimeProduct, id=product_id)
                user = product.category.user
                # Retrieve AutoSell info
                autosell_info = AutoSell.objects.filter(user=user).first()
                from_name = autosell_info.name if autosell_info else "Mystorelink"
                from_email = f"{from_name} <{EMAIL_HOST_USER}>"

                customer_subject = f"Your purchase of {product.title}"
                customer_html_content = render_to_string("emails/crypto_one_time_purchase_confirmation.html", {
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
                customer_email_message.attach_alternative(customer_html_content, "text/html")
                customer_email_message.send()
                print(f"Email sent for transaction {txn_id} (One-time product).")

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

            elif product_type == 'unlimited':
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

                update_user_income(product.user, Decimal(data.get('amount1')), data.get('currency1').upper())

                profile = UserProfile.objects.filter(user=product.user).first()
                if profile and profile.pushover_user_key:
                    send_pushover_notification(profile.pushover_user_key, f"🎉 {name} Ordered 1 item from your store!")

                product = get_object_or_404(UnlimitedProduct, id=product_id)
                user = product.user
                autosell_info = AutoSell.objects.filter(user=user).first()
                from_name = autosell_info.name if autosell_info else "Mystorelink"
                from_email = f"{from_name} <{EMAIL_HOST_USER}>"

                customer_subject = f"Your purchase of {product.title}"
                customer_html_content = render_to_string("emails/crypto_purchase_confirmation.html", {
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
                customer_email_message.attach_alternative(customer_html_content, "text/html")
                customer_email_message.send()
                print(f"Email sent for transaction {txn_id} (Unlimited product).")

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

            else:
                print(f"Unknown product type: {product_type}")
                return JsonResponse({'error': 'Unknown product type'}, status=400)

            return JsonResponse({'status': 'success'}, status=200)

        elif data.get('status') == '2':  
            print(f"Withdrawal complete for txn_id: {data.get('txn_id')}")
            return JsonResponse({'status': 'Complete'}, status=200)
        
        elif data.get('status') == '-1':  
            try:
                custom_data = json.loads(data.get('custom'))  #
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

        else:
            status_text = data.get('status_text', 'Unknown status')
            print(f"Payment not complete. Status: {data.get('status')}, Message: {status_text}")
            return JsonResponse({'error': 'Payment not complete'}, status=400)

    print("Received non-POST request")
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required
def products(request):
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
            
            # Upload to Supabase
            if 'category_image' in request.FILES:
                category_image_url = upload_to_supabase(request.FILES['category_image'], folder='categories')
                category.category_image_url = category_image_url 
            
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

            # Upload to Supabase
            if 'product_image' in request.FILES:
                product_image_url = upload_to_supabase(request.FILES['product_image'], folder='one_time_products')
                one_time_product.product_image_url = product_image_url 
            one_time_product.save()

            try:
                stripe_product = stripe.Product.create(
                    name=one_time_product.title,
                    description=one_time_product.description,
                    metadata={
                        'django_product_id': one_time_product.id 
                    }
                )
                stripe_price = stripe.Price.create(
                    product=stripe_product.id,
                    unit_amount=int(one_time_product.price * 100),  
                    currency=one_time_product.currency.lower(),
                    recurring=None, 
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
    
    return render(request, 'features/products/add_product_to_category.html', {'form': form, 'category': category})

@login_required
def edit_one_time_product(request, pk):
    one_time_product = get_object_or_404(OneTimeProduct, pk=pk)

    if request.method == 'POST':
        form = OneTimeProductForm(request.POST, request.FILES, instance=one_time_product)
        if form.is_valid():
            updated_product = form.save(commit=False)

            # Upload to Supabase if new image provided
            if 'product_image' in request.FILES:
                product_image_url = upload_to_supabase(request.FILES['product_image'], folder='one_time_products')
                updated_product.product_image_url = product_image_url 
            updated_product.save()

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
                        )

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

            # Upload to Supabase if new image provided
            if 'product_image' in request.FILES:
                product_image_url = upload_to_supabase(request.FILES['product_image'], folder='unlimited_products')
                updated_product.product_image_url = product_image_url 

            updated_product.save()
            # Handle Stripe product update logic
            if product.stripe_product_id:
                try:
                    stripe.Product.modify(
                        product.stripe_product_id,
                        name=updated_product.title,
                        description=updated_product.description,
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
                        )

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
            updated_category = form.save(commit=False)

            # Upload the new image to Supabase if provided
            if 'category_image' in request.FILES:
                category_image_url = upload_to_supabase(request.FILES['category_image'], folder='category_images')
                updated_category.category_image_url = category_image_url

            updated_category.save()
            return redirect('category_detail', category_id=category.id)  
    else:
        form = OneTimeProductCategoryForm(instance=category)

    return render(request, 'features/products/edit_category.html', {'form': form})

@login_required
def delete_one_time_product(request, pk):
    product = get_object_or_404(OneTimeProduct, pk=pk, category__user=request.user)
    category_id = product.category.id

    if product.stripe_product_id:
        try:
            stripe.Product.modify(
                product.stripe_product_id,
                active=False
            )
        except stripe.error.StripeError as e:
            print(f"Error archiving one-time product on Stripe: {e}")

    product.delete()

    return redirect('category_detail', category_id=category_id)

@login_required
def delete_category(request, pk):
    category = get_object_or_404(OneTimeProductCategory, pk=pk, user=request.user)
    
    one_time_products = OneTimeProduct.objects.filter(category=category)
    
    for product in one_time_products:
        if product.stripe_product_id:
            try:
                stripe.Product.modify(
                    product.stripe_product_id,
                    active=False  
                )
            except stripe.error.StripeError as e:
                print(f"Error archiving product {product.title} on Stripe: {e}")
        
        product.delete()

    category.delete()

    return redirect('products')

@login_required
def add_product_options(request):
    return render(request, "features/products/add_product_options.html")

@login_required
def add_unlimited_product(request):
    if request.method == 'POST':
        form = UnlimitedProductForm(request.POST, request.FILES)
        if form.is_valid():
            unlimited_product = form.save(commit=False)
            unlimited_product.user = request.user

            # Upload to Supabase
            if 'product_image' in request.FILES:
                product_image_url = upload_to_supabase(request.FILES['product_image'], folder='unlimited_products')
                unlimited_product.product_image_url = product_image_url 

            unlimited_product.save()
            stripe_product = stripe.Product.create(
                name=unlimited_product.title,
                description=unlimited_product.description,
                metadata={
                    'django_product_id': unlimited_product.id  
                }
            )
            stripe_price = stripe.Price.create(
                product=stripe_product.id,
                unit_amount=int(unlimited_product.price * 100), 
                currency=unlimited_product.currency.lower(),
                recurring=None,  
            )
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
    if product.stripe_product_id:
        try:
            stripe.Product.modify(
                product.stripe_product_id,
                active=False
            )
        except stripe.error.StripeError as e:
            print(f"Error archiving unlimited product on Stripe: {e}")
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

        previous_url = request.META.get('HTTP_REFERER')
        request.session['previous_url'] = previous_url

        try:
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

def checkout_success(request):
    session_id = request.GET.get('session_id')
    session = stripe.checkout.Session.retrieve(session_id)
    product_id = session.metadata.get('product_id')
    customer_name = session.metadata.get('customer_name')
    customer_email = session.metadata.get('customer_email')

    unlimited_product = UnlimitedProduct.objects.filter(id=product_id).first()

    if unlimited_product:
        user = unlimited_product.user
        
        # Retrieve AutoSell info
        autosell_info = AutoSell.objects.filter(user=user).first()
        from_name = autosell_info.name if autosell_info else "Mystorelink"
        from_email = f"{from_name} <{EMAIL_HOST_USER}>"

        ProductSale.objects.create(
            user=unlimited_product.user,
            unlimited_product=unlimited_product,
            stripe_session_id=session_id,
            amount=session.amount_total / 100,
            currency=session.currency.upper(),
            customer_name=customer_name,
            customer_email=customer_email
        )

        # Generate unique ID for invisible content
        unique_hash = str(uuid.uuid4())

        # Customer email (HTML template)
        customer_subject = f"Your purchase of {unlimited_product.title}"
        customer_html_content = render_to_string("emails/purchase_confirmation.html", {
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
        customer_email_message.attach_alternative(customer_html_content, "text/html")
        customer_email_message.send()

        # Owner email (HTML template)
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

        # Push notification logic remains unchanged
        profile, created = UserProfile.objects.get_or_create(user=unlimited_product.user)
        owner_pushover_key = profile.pushover_user_key
        if owner_pushover_key:
            message = f"🎉 {customer_name} Ordered 1 item from your store!"
            send_pushover_notification(owner_pushover_key, message)
            update_user_income(unlimited_product.user, session.amount_total / 100, session.currency.upper())
        else:
            print(f"No Pushover key found for {unlimited_product.user.username}, skipping push notification.")
    
    else:
        return JsonResponse({'error': 'Product not found'}, status=400)

    previous_url = request.session.get('previous_url', '/')
    request.session.pop('previous_url', None)
    return redirect(previous_url)

def checkout_cancel(request):
    return render(request, 'checkout/cancel.html')

def one_time_product_detail(request, product_id):
    product = get_object_or_404(OneTimeProduct, id=product_id)

    first_product_in_category = product.category.products.first()

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
    products = UnlimitedProduct.objects.filter(user=request.user)

    for product in products:
        stripe_sessions = stripe.checkout.Session.list(payment_status='paid')
        for session in stripe_sessions:
            if session.metadata['product_id'] == str(product.id) and not ProductSale.objects.filter(stripe_session_id=session.id).exists():
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

        current_product = get_object_or_404(OneTimeProduct, id=product_id)

        customer_name = data.get('name')
        customer_email = data.get('email')

        try:
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

    product_id = session.metadata.get('product_id')
    customer_name = session.metadata.get('customer_name')
    customer_email = session.metadata.get('customer_email')

    product = get_object_or_404(OneTimeProduct, id=product_id)

    ProductSale.objects.create(
        user=product.category.user,  
        product=product, 
        stripe_session_id=session_id,
        amount=session.amount_total / 100, 
        currency=session.currency.upper(),
        customer_name=customer_name, 
        customer_email=customer_email 
    )

    # Retrieve AutoSell info
    user = product.category.user
    autosell_info = AutoSell.objects.filter(user=user).first()
    from_name = autosell_info.name if autosell_info else "Mystorelink"
    from_email = f"{from_name} <{EMAIL_HOST_USER}>"

    unique_hash = str(uuid.uuid4())

    # Customer email with product content directly included
    customer_subject = f"Your purchase of {product.title}"
    customer_html_content = render_to_string("emails/one_time_product_purchase_confirmation.html", {
        "customer_name": customer_name,
        "product_title": product.title,
        "product_content": product.product_content,  # Use product content directly
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
    customer_email_message.attach_alternative(customer_html_content, "text/html")
    customer_email_message.send()

    # Owner email notification
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

    # Check for pushover_user_key and send push notification if available
    profile, created = UserProfile.objects.get_or_create(user=product.category.user)
    owner_pushover_key = profile.pushover_user_key
    if owner_pushover_key:
        message = f"🎉 {customer_name} ordered 1 item from your store!"
        send_pushover_notification(owner_pushover_key, message)

    update_user_income(product.category.user, session.amount_total / 100, session.currency.upper())

    # Archive the product in Stripe and delete it from the database
    try:
        stripe.Product.modify(product.stripe_product_id, active=False)
    except stripe.error.StripeError as e:
        print(f"Error archiving product on Stripe: {e}")

    product.delete()

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
                stripe_product = stripe.Product.create(
                    name=one_time_product.title,
                    description=one_time_product.description,
                    metadata={
                        'django_product_id': one_time_product.id
                    }
                )

                stripe_price = stripe.Price.create(
                    product=stripe_product.id,
                    unit_amount=int(one_time_product.price * 100),  
                    currency=one_time_product.currency.lower(),
                    recurring=None  
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

    return render(request, 'features/products/add_product_to_category.html', {'form': form, 'category': category})
