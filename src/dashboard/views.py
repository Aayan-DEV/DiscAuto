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
from django.core.exceptions import ObjectDoesNotExist
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

@login_required
def dashboard_view(request):
    # First we get the current time and store it in "today"
    today = timezone.now()

    # Then we calculate the start of the week (Monday) for filtering data
    start_of_week = today - timedelta(days=today.weekday())

    # Then we set the end of the week to today
    end_of_week = today

    # Then we get the latest exchange rates for currency conversion
    exchange_rates = get_exchange_rates()

    try:
        # Here we try to get the user's income data from the database
        user_income = UserIncome.objects.get(user=request.user)
    except ObjectDoesNotExist:
        # If no income data exists for the user, we just set the user_income to none.
        user_income = None

    # Here we format the user's income data so that it can be displayed in the dashboard.
    if user_income:
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
    else:
        # If no income data exists, we put all values to 0
        formatted_income = {
            'usd_total': format_decimal(0),
            'gbp_total': format_decimal(0),
            'eur_total': format_decimal(0),
            'btc_total': format_decimal(0),
            'ltc_total': format_decimal(0),
            'sol_total': format_decimal(0),
            'eth_total': format_decimal(0),
            'usdt_bep20_total': format_decimal(0),
            'usdt_erc20_total': format_decimal(0),
            'usdt_prc20_total': format_decimal(0),
            'usdt_trc20_total': format_decimal(0),
            'usdt_sol_total': format_decimal(0),
            'ltct_total': format_decimal(0)
        }

    # Here we get the user's recent sales to display on the dashboard.
    recent_sales = ProductSale.objects.filter(
        user=request.user
    ).select_related('user', 'product', 'unlimited_product').order_by('-created_at')

    # Then we get the sales data grouped by day for the current week
    sales_data_by_day = get_sales_data_by_day(start_of_week, end_of_week, request.user, exchange_rates)

    # Then we get the data related to Cold DMs sent during the week
    cold_dm_data = ColdDM.objects.filter(
        saved_by=request.user,
        created_at__range=[start_of_week, end_of_week]
    ).annotate(day=TruncDay('created_at')).values('day').annotate(total_dms=Count('id')).order_by('day')

    # Then we get the ads sent for the week
    ads_data = Channels.objects.filter(
        user=request.user,
        start_time__range=[start_of_week, end_of_week]
    ).annotate(day=TruncDay('start_time')).values('day').annotate(total_ads=Sum('ad_count')).order_by('day')

    # Then we get the views sent for the week
    views_data = AutoSellView.objects.filter(
        autosell__user=request.user,
        view_date__range=[start_of_week, end_of_week]
    ).annotate(day=TruncDay('view_date')).values('day').annotate(total_views=Count('id')).order_by('day')

    # Here we generate a list of day names (Monday to Sunday) for the current week
    days = [(start_of_week + timedelta(days=i)).strftime('%A') for i in range(7)]

    # Here we initialize dictionaries to store total counts for sales, ads, DMs, and views per day
    total_sales_per_day = {day: 0 for day in days}
    total_ads_per_day = {day: 0 for day in days}
    total_dms_per_day = {day: 0 for day in days}
    total_views_per_day = {day: 0 for day in days}

    # Then we set the dictionaries with data gotten earlier
    for data in sales_data_by_day:
        day_name = data['day']
        total_sales_per_day[day_name] += data['total_sales']

    for data in ads_data:
        day_name = data['day'].strftime('%A')
        total_ads_per_day[day_name] = data['total_ads']

    for data in cold_dm_data:
        day_name = data['day'].strftime('%A')
        total_dms_per_day[day_name] = data['total_dms']

    for data in views_data:
        day_name = data['day'].strftime('%A')
        total_views_per_day[day_name] = data['total_views']

    # Here we handle the payout form submissions from the dashboard
    if request.method == 'POST' and 'payout_form' in request.POST:
        payout_form = PayoutRequestForm(request.POST, user=request.user)
        if payout_form.is_valid():
            # We save the payout request and update the user's income
            payout_request = payout_form.save(commit=False)
            payout_request.user = request.user

            # We get the requested currency and amount for payout
            currency = payout_request.currency
            amount = Decimal(payout_request.amount)

            # We also get the user's balance for the selected currency
            currency_attribute = f"{currency.lower().replace('.', '_')}_total"
            user_income_balance = getattr(user_income, currency_attribute, None)

            if user_income_balance is not None and amount <= user_income_balance:
                # If the user has enough balance, we minus the requested amount from the user's balance
                setattr(user_income, currency_attribute, user_income_balance - amount)
                user_income.save()

                # Then we save the payout request and show a success message
                payout_request.save()
                messages.success(request, 'Your payout request has been received. You will receive your funds within 24 hours.')
                return redirect('dashboard')
            else:
                # Here we show an error message if the user has insufficient funds, meaning less than what was requested.
                messages.error(request, 'Insufficient funds for the requested payout.')
        else:
            # We also show an error message if the form is invalid
            messages.error(request, 'Invalid payout request form.')
    else:
        # If there was no submission, we initialize an empty payout form!
        payout_form = PayoutRequestForm(user=request.user)

    # Finally we render the dashboard template with all the collected data
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



