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
            'payout_amount': float(sale.payout_amount) if sale.payout_amount else 0,
            'converted_amount_eur': float(sale.amount_in_eur) if hasattr(sale, 'amount_in_eur') and sale.amount_in_eur else 0
        }
        
        return JsonResponse(data)
    except ProductSale.DoesNotExist:
        return JsonResponse({'error': 'Sale not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def dashboard_view(request):
    # Get current time
    today = timezone.now()
    exchange_rates = get_exchange_rates()
    default_currency = 'EUR'
    
    # Get or create user income record
    try:
        user_income = UserIncome.objects.get(user=request.user)
        print(f"Found user income for {request.user.username}: EUR_TOTAL={user_income.EUR_TOTAL}")
    except UserIncome.DoesNotExist:
        user_income = UserIncome.objects.create(
            user=request.user,
            EUR_TOTAL=Decimal('0.00'),
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
    
    # Get formatted income values
    formatted_income = user_income.get_formatted_values()
    print(f"User income: {formatted_income}")

    # Get recent sales
    recent_sales = ProductSale.objects.filter(
        user=request.user
    ).select_related('user', 'product', 'unlimited_product').order_by('-created_at')

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
        'recent_sales': recent_sales,
        'payout_form': payout_form,
        'user_income': user_income,
        'formatted_income': formatted_income,
        'currencies': ['USD', 'EUR', 'GBP'],
        'default_currency': default_currency
    })

@login_required
def refresh_income(request):
    try:
        # Get the user's income record
        user_income, created = UserIncome.objects.get_or_create(user=request.user)
        
        # Format the cryptocurrency balances using correct field names
        formatted_income = {
            'BTC_TOTAL': str(user_income.BTC_TOTAL) if user_income.BTC_TOTAL else "0.00",
            'ETH_TOTAL': str(user_income.ETH_TOTAL) if user_income.ETH_TOTAL else "0.00",
            'LTC_TOTAL': str(user_income.LTC_TOTAL) if user_income.LTC_TOTAL else "0.00",
            'SOL_TOTAL': str(user_income.SOL_TOTAL) if user_income.SOL_TOTAL else "0.00",
            'USDT_TRC20_TOTAL': str(user_income.USDT_TRC20_TOTAL) if user_income.USDT_TRC20_TOTAL else "0.00",
            'USDT_ERC20_TOTAL': str(user_income.USDT_ERC20_TOTAL) if user_income.USDT_ERC20_TOTAL else "0.00",
            'USDT_BEP20_TOTAL': str(user_income.USDT_BEP20_TOTAL) if user_income.USDT_BEP20_TOTAL else "0.00",
            'USDT_SOL_TOTAL': str(user_income.USDT_SOL_TOTAL) if user_income.USDT_SOL_TOTAL else "0.00",
            'USDT_PRC20_TOTAL': str(user_income.USDT_PRC20_TOTAL) if user_income.USDT_PRC20_TOTAL else "0.00",
            'LTCT_TOTAL': str(user_income.LTCT_TOTAL) if user_income.LTCT_TOTAL else "0.00"
        }

        return JsonResponse({
            'success': True,
            'income': formatted_income
        })
        
    except Exception as e:
        print(f"Error in refresh_income: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
def get_summary_data(request):
    """
    Get summary data for dashboard display:
    - Today's views and sales
    - This week's views and sales
    - Last 30 days views and sales
    """
    # Get current time and define time periods
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = now - timedelta(days=7)
    month_start = now - timedelta(days=30)
    
    # Get today's sales
    today_sales = ProductSale.objects.filter(
        user=request.user,
        created_at__gte=today_start,
        created_at__lte=now
    ).aggregate(total=Sum('payout_amount'))
    today_sales_amount = today_sales['total'] or Decimal('0.00')
    
    # Get today's views
    today_views = AutoSellView.objects.filter(
        auto_sell__user=request.user,
        timestamp__gte=today_start,
        timestamp__lte=now
    ).count()
    
    # Get this week's sales
    week_sales = ProductSale.objects.filter(
        user=request.user,
        created_at__gte=week_start,
        created_at__lte=now
    ).aggregate(total=Sum('payout_amount'))
    week_sales_amount = week_sales['total'] or Decimal('0.00')
    
    # Get this week's views
    week_views = AutoSellView.objects.filter(
        auto_sell__user=request.user,
        timestamp__gte=week_start,
        timestamp__lte=now
    ).count()
    
    # Get last 30 days sales
    month_sales = ProductSale.objects.filter(
        user=request.user,
        created_at__gte=month_start,
        created_at__lte=now
    ).aggregate(total=Sum('payout_amount'))
    month_sales_amount = month_sales['total'] or Decimal('0.00')
    
    # Get last 30 days views
    month_views = AutoSellView.objects.filter(
        auto_sell__user=request.user,
        timestamp__gte=month_start,
        timestamp__lte=now
    ).count()
    
    # Format all amounts to 2 decimal places
    today_sales_amount = float(today_sales_amount.quantize(Decimal('0.01')))
    week_sales_amount = float(week_sales_amount.quantize(Decimal('0.01')))
    month_sales_amount = float(month_sales_amount.quantize(Decimal('0.01')))
    
    # Return the summary data
    return JsonResponse({
        'today': {
            'views': today_views,
            'sales': today_sales_amount
        },
        'this_week': {
            'views': week_views,
            'sales': week_sales_amount
        },
        'last_30_days': {
            'views': month_views,
            'sales': month_sales_amount
        }
    })