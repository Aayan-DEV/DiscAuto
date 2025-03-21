from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Count
from products.models import ProductSale
from autosell.models import AutoSellView  # Import AutoSellView for tracking views
from django.db.models.functions import TruncDay
import os
from django.core.exceptions import ObjectDoesNotExist
import requests
from decimal import Decimal
from .forms import PayoutRequestForm
from django.contrib import messages
from products.models import UserIncome
from django.http import JsonResponse

# Your API key from the ExchangeRate-API service
# Gets the API key from environment variables for security purpose.
API_KEY = os.getenv('EXCHANGE_RATE_API_KEY')  
# Here it makes the API URL to fetch exchange rates to USD from other currencies
EXCHANGE_RATE_URL = f"https://v6.exchangerate-api.com/v6/{API_KEY}/latest/USD" 
# Define supported currencies
SUPPORTED_CURRENCIES = ['GBP', 'USD', 'EUR']  

def get_exchange_rates():
    # Gets live exchange rates from the API and returns them as a dictionary.
    try:
        # First it makes an HTTP request to the ExchangeRate API.
        response = requests.get(EXCHANGE_RATE_URL)
        # Then it puts the json response into data. 
        data = response.json() 
        # It then checks if the API response says success or not. 
        if data.get('result') == 'success':  
            # If its a success, it returns the conversion rates dictionary
            return data.get('conversion_rates', {})  
        else:
            # Otherwise it logs the error type if the request fails
            print(f"Error fetching exchange rates: {data.get('error-type')}")  
            # Returns an empty dictionary if the request fails or the API response is not successful. 
            return {}
    except Exception as e:
        # Here it handles any exception which might occur during the request
        print(f"Error fetching exchange rates: {e}")  
        # Returns an empty dictionary if an exception occurs during the request.
        return {}

def convert_to_usd(amount, currency, rates):
    # Converts any currency to USD using live exchange rates.
    # Ensure `amount` is treated as a Decimal
    amount = Decimal(amount)
    # Convert the rate to Decimal to match the `amount` type
    exchange_rate = Decimal(rates.get(currency, 1))
    # Otherwise, convert the amount to USD using the exchange rate for the given currency. 
    # If the currency isn't in rates, return the original amount.
    return round(amount / exchange_rate, 2)

def handle_unsupported_currency(sale, rates):
    # Try to handle OneTimeProduct first
    if sale.product:
        product_price = Decimal(sale.product.price)  # Convert to Decimal
        product_currency = sale.product.currency
    elif sale.unlimited_product:
        # Handle UnlimitedProduct if OneTimeProduct is not available
        product_price = Decimal(sale.unlimited_product.price)  # Convert to Decimal
        product_currency = sale.unlimited_product.currency
    else:
        # If both are missing, raise an exception or log the issue
        print(f"Error: No product or unlimited product found for sale ID {sale.id}")
        return

    # Always convert the product price to EUR for storage
    if product_currency != 'EUR':
        # Get EUR rate from USD rates
        eur_rate = Decimal(rates.get('EUR', 1))
        
        # Convert to EUR via USD (since our rates are based on USD)
        if product_currency == 'USD':
            sale.amount_in_eur = product_price * (eur_rate / Decimal(1))
        else:
            currency_rate = Decimal(rates.get(product_currency, 1))
            sale.amount_in_eur = product_price * (eur_rate / currency_rate)
    else:
        sale.amount_in_eur = product_price

def get_sales_data_by_day(start_date, end_date, user, exchange_rates):
    # Here we get the sales data for a specific date range, and then organize it by day.
    sales = ProductSale.objects.filter(
        user=user,
        created_at__range=[start_date, end_date]
        # TruncDay only extracts the date from the created_at field.
    ).select_related('product', 'unlimited_product').annotate(day=TruncDay('created_at'))

    # Initialize an empty dictionary to store all the daily sales data.
    daily_sales = {}

    # Here we loop through each sale so that we can calculate the daily totals.
    for sale in sales:
        # First we convert the sale's timestamp to the day's name (monday, etc).
        day_name = sale.day.strftime('%A')

        # If not already in the dictionary, we initialize the day's total. 
        if day_name not in daily_sales:
            daily_sales[day_name] = 0

        # Then we add the sale amount to the daily total, also also converting to USD if necessary.
        if sale.currency in SUPPORTED_CURRENCIES:
            daily_sales[day_name] += convert_to_usd(float(sale.amount), sale.currency, exchange_rates)
        else:
            # If the currency is not supported, meaning a crypto currency, first it checks if the product is an 
            # unlimited product or 1 time product.
            if sale.product:
                # If the product is one time, it gets its price.
                product_price = sale.product.price
                # Then it gets the products currency. 
                product_currency = sale.product.currency
            elif sale.unlimited_product:
                # If the product is unlimited, it gets its price.
                product_price = sale.unlimited_product.price
                # Then it gets the products currency.
                product_currency = sale.unlimited_product.currency
            else:
                # If both are missing, raise an exception or log the issue
                print(f"Error: No product or unlimited product found for sale ID {sale.id}")
                continue
            # Then it converts the price to USD.
            daily_sales[day_name] += convert_to_usd(float(product_price), product_currency, exchange_rates)

    # Then it converts the dictionary of daily sales (day_name: total_sales) into a list of dictionaries
    # so that each dictionary in the list will have a day and the its corresponding total sales amount!
    daily_sales_list = [{'day': day, 'total_sales': total_sales} for day, total_sales in daily_sales.items()]

    # Finally we sort the list of daily sales dictionaries by the day (Monday, Tuesday, etc...)
    # This makes sure that the data is in order.
    daily_sales_list.sort(key=lambda x: x['day'])

    # Then we return the sorted list of daily sales dictionaries as the final output for graphs.
    return daily_sales_list

def get_total_sales_by_currency(user):
    # First we get tje total sales amounts grouped by currency for a specific user.
    sales_by_currency = ProductSale.objects.filter(user=user).values('currency').annotate(total_amount=Sum('amount'))

    # Then we initialize a dictionary to store total sales for each currency, will be used later in frontend.
    total_sales_by_currency = {
        "USD": 0,
        "GBP": 0,
        "EUR": 0,
        "LTC": 0,
        "BTC": 0,
        "USDT": 0,
        "SOL": 0
    }

    # I also made it to print the values for debugging.
    print(f"Total sales by currency: {total_sales_by_currency}")

    # Then we loop through the sales data and update the total sales for each currency
    for entry in sales_by_currency:
        # First get the currency type (USD, GBP, etc..)
        currency = entry['currency']  
        # Then get the total sales amount for that currency
        amount = entry['total_amount']
        if currency in total_sales_by_currency:
            # Then we update the total sales for the matching currency
            total_sales_by_currency[currency] = amount

    # At the end we return the updated dictionary of total sales grouped by currency!
    return total_sales_by_currency

def format_decimal(value):
    """Remove trailing zeros from a Decimal and convert to string."""
    # Makes sure that the value is a Decimal, even if an int or float is passed
    value = Decimal(value)
    # Here we return the value without trailing zeros if it's a whole number
    return value.quantize(Decimal(1)) if value == value.to_integral() else value.normalize()

# Add this import at the top
from django.http import JsonResponse
@login_required
def get_chart_data(request):
    days_range = int(request.GET.get('days', 7))
    currency = request.GET.get('currency', 'USD')  # Get the selected currency
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days_range)
    
    # Get exchange rates for currency conversion
    exchange_rates = get_exchange_rates()
    
    # Get all sales within the date range using ProductSale
    sales_data = ProductSale.objects.filter(
        user=request.user,  # Filter by the current user
        created_at__gte=start_date,
        created_at__lte=end_date
    ).values('created_at').annotate(
        total=Sum('payout_amount')  # Use payout_amount for consistent values
    ).order_by('created_at')

    # Get all clicks/views within the date range using AutoSellView
    clicks_data = AutoSellView.objects.filter(
        auto_sell__user=request.user,  # Filter by the current user
        timestamp__gte=start_date,
        timestamp__lte=end_date
    ).values('timestamp').annotate(
        total=Count('id')
    ).order_by('timestamp')

    # Convert to dictionaries for easier lookup
    sales_dict = {}
    for item in sales_data:
        date = item['created_at'].date()
        amount = item['total'] or 0
        
        # Convert amount to the selected currency
        if amount > 0:
            # Default is EUR in the database
            if currency == 'USD':
                # Convert EUR to USD
                eur_rate = Decimal(exchange_rates.get('EUR', 1))
                usd_rate = Decimal(exchange_rates.get('USD', 1))
                amount = amount * (usd_rate / eur_rate)
            elif currency == 'GBP':
                # Convert EUR to GBP
                eur_rate = Decimal(exchange_rates.get('EUR', 1))
                gbp_rate = Decimal(exchange_rates.get('GBP', 1))
                amount = amount * (gbp_rate / eur_rate)
            # For EUR, no conversion needed
        
        sales_dict[date] = amount
    
    clicks_dict = {item['timestamp'].date(): item['total'] for item in clicks_data}

    # Generate all dates in range
    date_list = []
    sales_list = []
    clicks_list = []
    
    current_date = start_date.date()
    while current_date <= end_date.date():
        date_list.append(current_date)
        # Ensure consistent decimal places (2 for currency)
        sales_amount = sales_dict.get(current_date, 0)
        sales_list.append(float(Decimal(str(sales_amount)).quantize(Decimal('0.01'))))
        clicks_list.append(clicks_dict.get(current_date, 0))
        current_date += timedelta(days=1)

    # Format dates based on range
    if days_range <= 7:
        formatted_dates = [d.strftime('%b %d') for d in date_list]
    elif days_range <= 30:
        formatted_dates = []
        for i, date in enumerate(date_list):
            if sales_dict.get(date, 0) > 0 or i % 3 == 0:
                formatted_dates.append(date.strftime('%b %d'))
            else:
                formatted_dates.append('')
    else:
        formatted_dates = []
        for i, date in enumerate(date_list):
            if sales_dict.get(date, 0) > 0 or i % 5 == 0:
                formatted_dates.append(date.strftime('%b %d'))
            else:
                formatted_dates.append('')

    return JsonResponse({
        'days': formatted_dates,
        'total_sales': sales_list,
        'total_clicks': clicks_list,
        'currency': currency
    })

@login_required
def get_sale_details(request, sale_id):
    """Get sale details directly from the database without calling Stripe API"""
    try:
        sale = ProductSale.objects.get(id=sale_id, user=request.user)
        
        # Format the data for the frontend
        data = {
            'amount': float(sale.amount),
            'currency': sale.currency,
            'stripe_fee': float(sale.stripe_fee) if sale.stripe_fee else 0,
            'platform_fee': float(sale.platform_fee) if sale.platform_fee else 0,
            'payout_amount': float(sale.payout_amount) if sale.payout_amount else 0
        }
        
        return JsonResponse(data)
    except ProductSale.DoesNotExist:
        return JsonResponse({'error': 'Sale not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def dashboard_view(request):
    # First we get the current time and store it in "today"
    today = timezone.now()
    start_of_week = today - timedelta(days=7)  # Default to 7 days
    end_of_week = today
    exchange_rates = get_exchange_rates()
    default_currency = 'EUR'  # Changed default currency to EUR
    
    # Get or create user income record
    try:
        user_income = UserIncome.objects.get(user=request.user)
        print(f"Found user income for {request.user.username}: EUR_TOTAL={user_income.EUR_TOTAL}")
    except UserIncome.DoesNotExist:
        # Create a new UserIncome object with only the fields that exist in the model
        user_income = UserIncome.objects.create(
            user=request.user,
            EUR_TOTAL=Decimal('0.00'),  # Only use EUR_TOTAL for fiat currency
            # Initialize cryptocurrency fields
            BTC_TOTAL=Decimal('0.00000000'),
            ETH_TOTAL=Decimal('0.00000000'),
            LTC_TOTAL=Decimal('0.00000000'),
            SOL_TOTAL=Decimal('0.00000000'),
            USDT_TRC20_TOTAL=Decimal('0.00'),
            USDT_ERC20_TOTAL=Decimal('0.00'),
            USDT_BEP20_TOTAL=Decimal('0.00'),
            USDT_SOL_TOTAL=Decimal('0.00'),
            USDT_PRC20_TOTAL=Decimal('0.00'),
            LTCT_TOTAL=Decimal('0.00000000')
        )
        print(f"Created new user income for {request.user.username}")
    
    # Use get_formatted_values() method instead of the non-existent property
    formatted_income = user_income.get_formatted_values()
    print(f"User income: {formatted_income}")

    recent_sales = ProductSale.objects.filter(
        user=request.user
    ).select_related('user', 'product', 'unlimited_product').order_by('-created_at')

    # Get initial chart data in USD (default)
    sales_data = ProductSale.objects.filter(
        user=request.user,
        created_at__gte=start_of_week,
        created_at__lte=end_of_week
    ).annotate(day=TruncDay('created_at')).values('day').annotate(
        total=Sum('payout_amount')
    ).order_by('day')
    
    # Convert sales data to USD
    sales_by_day = {}
    for item in sales_data:
        day_name = item['day'].strftime('%A')
        amount = item['total'] or 0
        
        # Convert EUR to USD
        if amount > 0:
            eur_rate = Decimal(exchange_rates.get('EUR', 1))
            usd_rate = Decimal(exchange_rates.get('USD', 1))
            amount = amount * (usd_rate / eur_rate)
        
        # Around line 364
        sales_by_day[day_name] = Decimal(str(amount)).quantize(Decimal('0.01'))
    
    # Get views data
    views_data = AutoSellView.objects.filter(
        auto_sell__user=request.user,
        timestamp__gte=start_of_week,
        timestamp__lte=end_of_week
    ).annotate(day=TruncDay('timestamp')).values('day').annotate(
        total_views=Count('id')
    ).order_by('day')
    
    views_by_day = {item['day'].strftime('%A'): item['total_views'] for item in views_data}

    # Generate days of the week
    days = [(start_of_week + timedelta(days=i)).strftime('%A') for i in range(7)]
    
    # Prepare data for the template
    total_sales = [float(sales_by_day.get(day, 0)) for day in days]
    total_clicks = [views_by_day.get(day, 0) for day in days]

    # Handle payout form
    if request.method == 'POST' and 'payout_form' in request.POST:
        payout_form = PayoutRequestForm(request.POST, user=request.user)
        if payout_form.is_valid():
            payout_request = payout_form.save(commit=False)
            payout_request.user = request.user
            
            currency = payout_request.currency
            amount = Decimal(payout_request.amount)
            
            # Get the exchange rates
            exchange_rates = get_exchange_rates()
            
            # Calculate equivalent in EUR (our base currency for storage)
            if currency == 'EUR':
                eur_equivalent = amount
                conversion_fee = Decimal('0.00')  # No conversion fee for EUR
            else:
                # Convert to EUR
                if currency == 'USD':
                    eur_rate = Decimal(exchange_rates.get('EUR', 1))
                    currency_rate = Decimal(exchange_rates.get('USD', 1))
                    eur_equivalent = amount * (eur_rate / currency_rate)
                elif currency == 'GBP':
                    eur_rate = Decimal(exchange_rates.get('EUR', 1))
                    currency_rate = Decimal(exchange_rates.get('GBP', 1))
                    eur_equivalent = amount * (eur_rate / currency_rate)
                else:
                    # For other currencies (crypto)
                    eur_equivalent = amount
                
                # Calculate 2% conversion fee
                conversion_fee = eur_equivalent * Decimal('0.02')
                eur_equivalent = eur_equivalent - conversion_fee
            
            # Check if user has sufficient EUR balance
            if user_income.EUR_TOTAL >= eur_equivalent:
                # Deduct from EUR balance
                user_income.EUR_TOTAL -= eur_equivalent
                user_income.save()
                
                # Save the payout request
                payout_request.eur_equivalent = eur_equivalent
                payout_request.conversion_fee = conversion_fee
                payout_request.save()
                
                messages.success(request, f'Your payout request for {amount} {currency} has been received. You will receive your funds within 24 hours.')
                return redirect('dashboard')
            else:
                messages.error(request, f'Insufficient funds for the requested payout. Your EUR balance is {user_income.EUR_TOTAL}.')
        else:
            messages.error(request, 'Invalid payout request form.')
    else:
        payout_form = PayoutRequestForm(user=request.user)

        return render(request, 'dashboard/main.html', {
        'days': days,
        'total_sales': total_sales,
        'total_clicks': total_clicks,
        'recent_sales': recent_sales,
        'payout_form': payout_form,
        'user_income': user_income,  # Pass the user_income object directly
        'formatted_income': formatted_income,  # Use the formatted_income variable
        'currencies': ['USD', 'EUR', 'GBP'],
        'default_currency': default_currency
    })


@login_required
def refresh_income(request):
    """
    AJAX endpoint to refresh user income data
    """
    user = request.user
    print(f"Refreshing income for user: {user.username}")
    
    # Get all sales for the user
    sales = ProductSale.objects.filter(
        user=user,
        payout_amount__isnull=False,
        payout_processed=False
    )
    print(f"Found {sales.count()} unprocessed sales with payout amounts")
    
    # Debug counters
    eur_sales_count = sales.filter(currency='EUR').count()
    usd_sales_count = sales.filter(currency='USD').count()
    gbp_sales_count = sales.filter(currency='GBP').count()
    sales_with_payout = sales.filter(payout_amount__isnull=False).count()
    total_sales = sales.count()
    
    # Get or create user income record
    try:
        income, created = UserIncome.objects.get_or_create(user=user)
        print(f"User income {'created' if created else 'retrieved'} for {user.username}")
        print(f"Current EUR balance: {income.EUR_TOTAL}")
    except Exception as e:
        print(f"Error getting user income: {e}")
        return JsonResponse({'success': False, 'error': str(e)})
    
    # Process each sale and update income
    for sale in sales:
        try:
            print(f"Processing sale {sale.id}: {sale.payout_amount} {sale.currency}")
            
            # For fiat currencies, directly add to EUR_TOTAL without conversion
            if sale.currency in ['USD', 'EUR', 'GBP']:
                print(f"Before update: EUR_TOTAL = {income.EUR_TOTAL}")
                income.EUR_TOTAL += sale.payout_amount
                print(f"After update: EUR_TOTAL = {income.EUR_TOTAL}")
            else:
                # For cryptocurrencies, update the corresponding field
                crypto_field = f"{sale.currency.replace('.', '_')}_TOTAL"
                print(f"Crypto currency detected, field to update: {crypto_field}")
                
                if hasattr(income, crypto_field):
                    current_value = getattr(income, crypto_field)
                    print(f"Current value of {crypto_field}: {current_value}")
                    setattr(income, crypto_field, current_value + sale.payout_amount)
                    print(f"New value of {crypto_field}: {getattr(income, crypto_field)}")
                else:
                    print(f"Warning: Field {crypto_field} not found in UserIncome model")
            
            # Mark sale as processed
            sale.payout_processed = True
            sale.save(update_fields=['payout_processed'])
            print(f"Sale {sale.id} marked as processed")
            
        except Exception as e:
            print(f"Error processing sale {sale.id}: {e}")
            import traceback
            print(traceback.format_exc())
    
    # Save the updated income
    income.save()
    print(f"Income saved. New EUR balance: {income.EUR_TOTAL}")
    
    # Format the income for the response
    formatted_income = {
        'EUR_TOTAL': str(format_decimal(income.EUR_TOTAL.quantize(Decimal('0.01')))),
        'BTC_TOTAL': str(format_decimal(income.BTC_TOTAL)),
        'ETH_TOTAL': str(format_decimal(income.ETH_TOTAL)),
        'LTC_TOTAL': str(format_decimal(income.LTC_TOTAL)),
        'SOL_TOTAL': str(format_decimal(income.SOL_TOTAL)),
        'USDT_TRC20_TOTAL': str(format_decimal(income.USDT_TRC20_TOTAL)),
        'USDT_ERC20_TOTAL': str(format_decimal(income.USDT_ERC20_TOTAL)),
        'USDT_BEP20_TOTAL': str(format_decimal(income.USDT_BEP20_TOTAL)),
        'USDT_SOL_TOTAL': str(format_decimal(income.USDT_SOL_TOTAL)),
        'USDT_PRC20_TOTAL': str(format_decimal(income.USDT_PRC20_TOTAL)),
        'LTCT_TOTAL': str(format_decimal(income.LTCT_TOTAL)),
    }
    
    return JsonResponse({
        'success': True,
        'income': formatted_income,
        'debug': {
            'eur_sales_count': eur_sales_count,
            'usd_sales_count': usd_sales_count,
            'gbp_sales_count': gbp_sales_count,
            'sales_with_payout': sales_with_payout,
            'total_sales': total_sales,
            'eur_balance': str(income.EUR_TOTAL)
        }
    })