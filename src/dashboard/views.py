from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Count
from products.models import ProductSale
from autoad.models import Channels
from colddm.models import ColdDM, UserColdDMStats
from autosell.models import AutoSellView  # Import AutoSellView for tracking views
from django.db.models.functions import TruncDay
import os
import requests
from decimal import Decimal
from .forms import PayoutRequestForm
from django.contrib import messages
from products.models import UserIncome

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

    # Convert the product price to USD if the currency is not USD
    sale.amount_in_usd = convert_to_usd(product_price, product_currency, rates)

def get_sales_data_by_day(start_date, end_date, user, exchange_rates):
    # Fetch sales within the date range, grouped by day
    sales = ProductSale.objects.filter(
        user=user,
        created_at__range=[start_date, end_date]
    ).select_related('product', 'unlimited_product').annotate(day=TruncDay('created_at'))

    daily_sales = {}

    # Loop through each sale and process it
    for sale in sales:
        day_name = sale.day.strftime('%A')

        # Initialize the sales amount for the day if not already set
        if day_name not in daily_sales:
            daily_sales[day_name] = 0

        # Handle supported currencies
        if sale.currency in SUPPORTED_CURRENCIES:
            # Add the sale amount directly (converted to USD)
            daily_sales[day_name] += convert_to_usd(float(sale.amount), sale.currency, exchange_rates)
        else:
            # Handle unsupported currencies by using product price
            if sale.product:
                product_price = sale.product.price
                product_currency = sale.product.currency
            elif sale.unlimited_product:
                product_price = sale.unlimited_product.price
                product_currency = sale.unlimited_product.currency
            else:
                print(f"Error: No product or unlimited product found for sale ID {sale.id}")
                continue

            # Convert the product price to USD and add it to the total sales for the day
            daily_sales[day_name] += convert_to_usd(float(product_price), product_currency, exchange_rates)

    # Convert the dictionary to a sorted list to return it
    daily_sales_list = [{'day': day, 'total_sales': total_sales} for day, total_sales in daily_sales.items()]
    daily_sales_list.sort(key=lambda x: x['day'])  # Sort by day for proper graphing
    return daily_sales_list

def get_total_sales_by_currency(user):
    # Fetch total sales amounts grouped by currency directly from the ProductSale model
    sales_by_currency = ProductSale.objects.filter(user=user).values('currency').annotate(total_amount=Sum('amount'))

    # Initialize a dictionary to store totals
    total_sales_by_currency = {
        "USD": 0,
        "GBP": 0,
        "EUR": 0,
        "LTC": 0,
        "BTC": 0,
        "USDT": 0,
        "SOL": 0
    }

    print(f"Total sales by currency: {total_sales_by_currency}")

    # Populate the dictionary with actual values from the database
    for entry in sales_by_currency:
        currency = entry['currency']
        amount = entry['total_amount']
        if currency in total_sales_by_currency:
            total_sales_by_currency[currency] = amount

    return total_sales_by_currency

def format_decimal(value):
    """Remove trailing zeros from a Decimal and convert to string."""
    return value.quantize(Decimal(1)) if value == value.to_integral() else value.normalize()

@login_required 
def dashboard_view(request):
    # Get the current time in the user's timezone
    today = timezone.now()  
    start_of_week = today - timedelta(days=today.weekday())  
    end_of_week = today 

    # Get live exchange rates
    exchange_rates = get_exchange_rates()

    # Fetch `UserIncome` for the current user
    user_income = UserIncome.objects.get(user=request.user)

    # Prepare formatted income values
    formatted_income = {
        'usd_total': format_decimal(user_income.usd_total),
        'gbp_total': format_decimal(user_income.gbp_total),
        'eur_total': format_decimal(user_income.eur_total),
        'btc_total': format_decimal(user_income.btc_total),
        'ltc_total': format_decimal(user_income.ltc_total),
        'sol_total': format_decimal(user_income.sol_total),
        'eth_total': format_decimal(user_income.eth_total),
        'usdt_bep20_total': format_decimal(user_income.usdt_bep20_total),
        'usdt_erc20_total': format_decimal(user_income.usdt_erc20_total),
        'usdt_prc20_total': format_decimal(user_income.usdt_prc20_total),
        'usdt_trc20_total': format_decimal(user_income.usdt_trc20_total),
        'usdt_sol_total': format_decimal(user_income.usdt_sol_total),
        'ltct_total': format_decimal(user_income.ltct_total)
    }

    # Get recent sales for display
    recent_sales = ProductSale.objects.filter(user=request.user).select_related('user', 'product', 'unlimited_product').order_by('-created_at')

    # Get sales data for the dashboard graphs
    sales_data_by_day = get_sales_data_by_day(start_of_week, end_of_week, request.user, exchange_rates)

    # Fetch Cold DM, Ads, and View Data for the dashboard
    cold_dm_data = ColdDM.objects.filter(
        saved_by=request.user,
        created_at__range=[start_of_week, end_of_week]
    ).annotate(day=TruncDay('created_at')).values('day').annotate(total_dms=Count('id')).order_by('day')

    ads_data = Channels.objects.filter(
        user=request.user,
        start_time__range=[start_of_week, end_of_week]
    ).annotate(day=TruncDay('start_time')).values('day').annotate(total_ads=Sum('ad_count')).order_by('day')

    views_data = AutoSellView.objects.filter(
        autosell__user=request.user,
        view_date__range=[start_of_week, end_of_week]
    ).annotate(day=TruncDay('view_date')).values('day').annotate(total_views=Count('id')).order_by('day')

    # Prepare the labels (days of the week)
    days = [(start_of_week + timedelta(days=i)).strftime('%A') for i in range(7)]

    # Initialize data structures with 0 values for sales, ads, DMs, and views
    total_sales_per_day = {day: 0 for day in days}
    total_ads_per_day = {day: 0 for day in days}
    total_dms_per_day = {day: 0 for day in days}
    total_views_per_day = {day: 0 for day in days}

    # Process sales data
    for data in sales_data_by_day:
        day_name = data['day']
        total_sales_per_day[day_name] += data['total_sales']

    # Process ads, DMs, and views data
    for data in ads_data:
        day_name = data['day'].strftime('%A')
        total_ads_per_day[day_name] = data['total_ads']

    for data in cold_dm_data:
        day_name = data['day'].strftime('%A')
        total_dms_per_day[day_name] = data['total_dms']

    for data in views_data:
        day_name = data['day'].strftime('%A')
        total_views_per_day[day_name] = data['total_views']

    # Handle payout request form
    if request.method == 'POST' and 'payout_form' in request.POST:
        payout_form = PayoutRequestForm(request.POST, user=request.user)
        if payout_form.is_valid():
            payout_request = payout_form.save(commit=False)
            payout_request.user = request.user

            # Check if user has enough balance for the requested payout
            currency = payout_request.currency
            amount = Decimal(payout_request.amount)

            # Convert currency format: replace periods with underscores
            currency_attribute = f"{currency.lower().replace('.', '_')}_total"

            # Get the balance from UserIncome
            user_income_balance = getattr(user_income, currency_attribute, None)

            if user_income_balance is not None and amount <= user_income_balance:
                # Deduct the requested amount from user's income
                setattr(user_income, currency_attribute, user_income_balance - amount)
                user_income.save()

                payout_request.save()
                messages.success(request, 'Your payout request has been received. You will receive your funds within 24 hours.')
                return redirect('dashboard')
            else:
                messages.error(request, 'Insufficient funds for the requested payout.')
        else:
            messages.error(request, 'Invalid payout request form.')
    else:
        payout_form = PayoutRequestForm(user=request.user)

    # Pass data to template
    return render(request, 'dashboard/main.html', {
        'days': days,
        'total_sales': [float(total_sales_per_day[day]) for day in days],
        'total_clicks': [float(total_views_per_day[day]) for day in days],
        'total_ads': [float(total_ads_per_day[day]) for day in days],
        'total_dms': [float(total_dms_per_day[day]) for day in days],
        'recent_sales': recent_sales,
        'payout_form': payout_form,
        'user_income': formatted_income
    })
