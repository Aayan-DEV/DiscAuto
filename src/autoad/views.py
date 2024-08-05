from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
import requests
import json
from .forms import DataForm, StopBotForm
from auths.models import DiscordToken

get_slowmode_url = "http://127.0.0.1:5001/get_slowmode"  # Update with your Flask server IP

@login_required
def auto_ad(request):
    slowmode_info = []
    if request.method == 'POST':
        form = DataForm(request.POST, user=request.user)
        if form.is_valid():
            channel_id = form.cleaned_data['channel_id']
            tokens = form.cleaned_data['token']

            if 'all' in tokens:
                tokens = DiscordToken.objects.filter(user=request.user).values_list('token', flat=True)

            for token in tokens:
                headers = {
                    "Content-Type": "application/json"
                }
                data = {
                    "token": token,
                    "channel_id": channel_id
                }

                response = requests.post(get_slowmode_url, headers=headers, data=json.dumps(data))
                response_data = response.json()

                if response.status_code == 200:
                    slowmode_duration = response_data.get('slowmode_duration')
                    username = DiscordToken.objects.get(token=token).username
                    slowmode_info.append({'token': token, 'username': username, 'slowmode_duration': slowmode_duration})
                else:
                    messages.error(request, response_data.get('message', 'Error retrieving slow mode info'))

    else:
        form = DataForm(user=request.user)

    return render(request, 'features/auto-ad/auto-ad.html', {'form': form, 'slowmode_info': slowmode_info})
