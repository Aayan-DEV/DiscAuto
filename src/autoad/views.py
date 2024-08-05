# views.py
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
import requests
import json
from .forms import DataForm, StopBotForm
from auths.models import DiscordToken  # Import the DiscordToken model

# URL of the request handler server
request_handler_url = "http://127.0.0.1:5001/send_data"
stop_bot_url = "http://127.0.0.1:5001/stop_bot"  # Add the URL for stopping the bot

@login_required
def auto_ad(request):
    if request.method == 'POST':
        if 'channel_id' in request.POST:  # Changed from 'token' to 'channel_id' to identify the correct form submission
            form = DataForm(request.POST)
            if form.is_valid():
                channel_id = form.cleaned_data['channel_id']

                # Fetch the token from the database for the logged-in user
                try:
                    discord_token = DiscordToken.objects.get(user=request.user)
                    token = discord_token.token

                    data = {
                        "token": token,
                        "channel_id": channel_id
                    }

                    headers = {
                        "Content-Type": "application/json"
                    }

                    response = requests.post(request_handler_url, headers=headers, data=json.dumps(data))

                    if response.status_code == 200:
                        messages.success(request, 'Data sent successfully!')
                    else:
                        messages.error(request, 'Failed to send data.')
                except DiscordToken.DoesNotExist:
                    messages.error(request, 'Discord token not found for the user.')

                return redirect(reverse('auto_ad'))
        elif 'confirm' in request.POST:
            stop_form = StopBotForm(request.POST)
            if stop_form.is_valid():
                data = {
                    "confirm": stop_form.cleaned_data['confirm']
                }

                headers = {
                    "Content-Type": "application/json"
                }

                response = requests.post(stop_bot_url, headers=headers, data=json.dumps(data))

                if response.status_code == 200:
                    messages.success(request, 'Bot stopped successfully!')
                else:
                    messages.error(request, 'Failed to stop bot.')

                return redirect(reverse('auto_ad'))
    else:
        form = DataForm()
        stop_form = StopBotForm()

    return render(request, 'features/auto-ad/auto-ad.html', {'form': form, 'stop_form': stop_form})
