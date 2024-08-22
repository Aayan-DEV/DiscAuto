# autoad/views.py
import os
from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
import requests
import json
from requests.exceptions import RequestException, ConnectionError
from .forms import DataForm, UniversalMessageForm
from auths.models import DiscordToken
from .models import AutoAdUser, AutoAdConfig, AutoAdDetail

SERVER_URL = os.getenv('SERVER_URL')

get_slowmode_url = f"{SERVER_URL}/get_slowmode"
get_channel_name_url = f"{SERVER_URL}/get_channel_name"
get_server_name_url = f"{SERVER_URL}/get_server_name"
send_data_url = f"{SERVER_URL}/send_data"
stop_autoad_url = f"{SERVER_URL}/stop_autoad"

@login_required
def auto_ad(request):
    data_form = DataForm(user=request.user)
    universal_form = UniversalMessageForm()
    error_messages = []

    user_tokens = DiscordToken.objects.filter(user=request.user)
    if not user_tokens.exists():
        return render(request, 'features/auto-ad/auto-ad.html', {'no_users': True})

    auto_ad_user, created = AutoAdUser.objects.get_or_create(user=request.user, defaults={'username': request.user.username})
    auto_ad_config, created = AutoAdConfig.objects.get_or_create(user=auto_ad_user)

    if request.method == 'POST':
        if 'start_autoad' in request.POST:
            data_form = DataForm(request.POST, user=request.user)
            if data_form.is_valid():
                universal_message = data_form.cleaned_data['universal_message']
                channel_id = data_form.cleaned_data['channel_id']
                tokens = data_form.cleaned_data['token']

                if 'all' in tokens:
                    tokens = user_tokens.values_list('token', flat=True)

                for token in tokens:
                    headers = {
                        "Content-Type": "application/json"
                    }
                    data = {
                        "token": token,
                        "channel_id": channel_id,
                        "message": universal_message,
                        "infinite_loop": True
                    }

                    try:
                        response_slowmode = requests.post(get_slowmode_url, headers=headers, data=json.dumps(data))
                        response_channel_name = requests.post(get_channel_name_url, headers=headers, data=json.dumps(data))
                        response_server_name = requests.post(get_server_name_url, headers=headers, data=json.dumps(data))

                        if (response_slowmode.status_code == 200 and 
                            response_channel_name.status_code == 200 and 
                            response_server_name.status_code == 200):

                            slowmode_duration = response_slowmode.json().get('slowmode_duration')
                            channel_name = response_channel_name.json().get('channel_name')
                            server_name = response_server_name.json().get('server_name')
                            username = DiscordToken.objects.filter(token=token).first().username

                            existing_entry = AutoAdDetail.objects.filter(config=auto_ad_config, channel_id=channel_id, token=token).first()
                            if existing_entry:
                                error_messages.append(f"A box with Channel ID:{channel_id} and Username:{username} already exists. Please use a different combination or update the existing box.")
                            else:
                                box_number = AutoAdDetail.objects.filter(config=auto_ad_config).count() + 1
                                AutoAdDetail.objects.create(
                                    config=auto_ad_config,
                                    channel_id=channel_id,
                                    usernames=username,
                                    slowmode_duration=slowmode_duration,
                                    channel_name=channel_name,
                                    server_name=server_name,
                                    universal_message=universal_message,
                                    custom_message='',
                                    bot_running=False,
                                    token=token,
                                    box_number=box_number
                                )
                        else:
                            username = DiscordToken.objects.filter(token=token).first().username
                            error_messages.append(f"Error retrieving info for username {username}")
                    except (RequestException, ConnectionError) as e:
                        error_messages.append(f"Server unreachable. Please try again later. Error: {str(e)}")

        elif 'confirm_universal' in request.POST:
            universal_form = UniversalMessageForm(request.POST)
            if universal_form.is_valid():
                universal_message = universal_form.cleaned_data['universal_message']
                for info in auto_ad_config.details.all():
                    if info.custom_message:
                        error_messages.append(f"Remove custom message for channel {info.channel_id} before setting universal message.")
                        break
                else:
                    auto_ad_config.universal_message = universal_message
                    auto_ad_config.save()
                    for info in auto_ad_config.details.all():
                        info.universal_message = universal_message
                        info.save()

        elif 'stop_bot' in request.POST or 'start_bot' in request.POST:
            channel_id = int(request.POST.get('channel_id') or 0)
            action = 'stop_bot' if 'stop_bot' in request.POST else 'start_bot'
            detail = auto_ad_config.details.filter(channel_id=channel_id).first()
            if detail:
                if action == 'stop_bot':
                    detail.bot_running = False
                    data = {
                        "token": detail.token,
                        "channel_id": channel_id
                    }
                    try:
                        response = requests.post(stop_autoad_url, json=data)
                        if response.status_code != 200:
                            error_messages.append(f"Error stopping bot for channel {channel_id}")
                    except (RequestException, ConnectionError) as e:
                        error_messages.append(f"Server unreachable. Please try again later. Error: {str(e)}")
                else:
                    message = detail.custom_message if detail.custom_message else detail.universal_message
                    if not message:
                        error_messages.append(f"No message provided for channel {channel_id}")
                    else:
                        detail.bot_running = True
                        data = {
                            "token": detail.token,
                            "channel_id": detail.channel_id,
                            "message": message,
                            "infinite_loop": True
                        }
                        try:
                            response = requests.post(send_data_url, json=data)
                            if response.status_code != 200:
                                error_messages.append(f"Error starting bot for channel {channel_id}")
                        except (RequestException, ConnectionError) as e:
                            error_messages.append(f"Server unreachable. Please try again later. Error: {str(e)}")
                detail.save()

        elif 'delete_box' in request.POST:
            channel_id = int(request.POST.get('channel_id') or 0)
            auto_ad_config.details.filter(channel_id=channel_id).delete()

        elif 'set_custom_message' in request.POST:
            channel_id = int(request.POST.get('channel_id') or 0)
            custom_message = request.POST.get('custom_message', '')
            detail = auto_ad_config.details.filter(channel_id=channel_id).first()
            if detail:
                detail.custom_message = custom_message
                detail.save()

        elif 'remove_custom_message' in request.POST:
            channel_id = int(request.POST.get('channel_id') or 0)
            detail = auto_ad_config.details.filter(channel_id=channel_id).first()
            if detail:
                detail.custom_message = ''
                detail.save()

        elif 'clear_universal' in request.POST:
            universal_form = UniversalMessageForm() 
            auto_ad_config.universal_message = '' 
            auto_ad_config.save()

        elif 'remove_universal' in request.POST:
            for info in auto_ad_config.details.all():
                info.universal_message = ''
                info.save()

    slowmode_info = auto_ad_config.details.all()

    return render(request, 'features/auto-ad/auto-ad.html', {
        'data_form': data_form,
        'universal_form': universal_form,
        'slowmode_info': slowmode_info,
        'error_messages': error_messages
    })

@login_required
def remove_box(request):
    if request.method == 'POST':
        try:
            request_data = json.loads(request.body)
            channel_id = request_data.get('channel_id')
            if channel_id is None:
                raise ValueError("Channel ID is required")
            
            auto_ad_user = AutoAdUser.objects.get(user=request.user)
            auto_ad_config = AutoAdConfig.objects.get(user=auto_ad_user)
            detail = auto_ad_config.details.filter(channel_id=channel_id).first()

            if detail:
                if detail.bot_running:
                    data = {
                        "token": detail.token,
                        "channel_id": channel_id
                    }
                    try:
                        response = requests.post(stop_autoad_url, json=data)
                        if response.status_code != 200:
                            return JsonResponse({'status': 'failed', 'message': f"Error stopping bot for channel {channel_id}. Please Stop the bot First!"}, status=400)
                    except (RequestException, ConnectionError) as e:
                        return JsonResponse({'status': 'failed', 'message': f"Server unreachable. Please try again later. Error: {str(e)}"}, status=400)
                
                detail.delete()

            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'failed', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'failed'}, status=400)
