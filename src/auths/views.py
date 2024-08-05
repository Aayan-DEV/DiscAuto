from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import DiscordToken
import requests

@login_required
def auths(request):
    discord_tokens = DiscordToken.objects.filter(user=request.user)

    if request.method == 'POST' and 'token' in request.POST:
        token = request.POST.get('token')
        url = 'http://127.0.0.1:5001/get_username'  # Replace with the actual URL of the external server
        data = {'token': token}
        response = requests.post(url, json=data)
        response_data = response.json()

        if response_data.get('status') == 'success':
            username = response_data.get('username')
            
            if DiscordToken.objects.filter(user=request.user, token=token).exists():
                messages.error(request, 'This token already exists.')
            else:
                DiscordToken.objects.create(user=request.user, token=token, username=username)
                messages.success(request, f'Discord account "{username}" retrieved and stored successfully.')
        else:
            error_message = response_data.get('message')
            messages.error(request, f'Error: {error_message}')
        return redirect('auths')

    return render(request, 'features/auths/auths.html', {'discord_tokens': discord_tokens})

@login_required
def delete_discord_token(request, token_id):
    discord_token = DiscordToken.objects.get(id=token_id, user=request.user)
    if discord_token:
        discord_token.delete()
        messages.success(request, 'Token deleted successfully.')
    return redirect('auths')

@login_required
def start_bot(request, token_id):
    discord_token = DiscordToken.objects.get(id=token_id, user=request.user)
    if discord_token:
        url = 'http://127.0.0.1:5001/send_data'
        data = {'token': discord_token.token, 'channel_id': 'YOUR_CHANNEL_ID'}  # Replace YOUR_CHANNEL_ID with the actual channel ID
        response = requests.post(url, json=data)
        response_data = response.json()

        if response_data.get('status') == 'success':
            messages.success(request, 'Bot started successfully.')
        else:
            messages.error(request, f"Error: {response_data.get('message')}")
    return redirect('auths')

@login_required
def stop_bot(request, token_id):
    discord_token = DiscordToken.objects.get(id=token_id, user=request.user)
    if discord_token:
        url = 'http://127.0.0.1:5001/stop_bot'
        data = {'tokens': [discord_token.token]}
        response = requests.post(url, json=data)
        response_data = response.json()

        if response_data.get('status') == 'success':
            messages.success(request, 'Bot stopped successfully.')
        else:
            messages.error(request, f"Error: {response_data.get('message')}")
    return redirect('auths')
