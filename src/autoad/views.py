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

get_slowmode_url = "http://127.0.0.1:5001/get_slowmode"
get_channel_name_url = "http://127.0.0.1:5001/get_channel_name"
get_server_name_url = "http://127.0.0.1:5001/get_server_name"
send_data_url = "http://127.0.0.1:5001/send_data"
stop_autoad_url = "http://127.0.0.1:5001/stop_autoad"

@login_required
def auto_ad(request):
    data_form = DataForm(user=request.user)
    universal_form = UniversalMessageForm()
    if 'slowmode_info' not in request.session:
        request.session['slowmode_info'] = []
    slowmode_info = request.session['slowmode_info']
    error_messages = []

    user_tokens = DiscordToken.objects.filter(user=request.user)
    if not user_tokens.exists():
        return render(request, 'features/auto-ad/auto-ad.html', {'no_users': True})

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
                            username = DiscordToken.objects.get(token=token).username

                            existing_entry = next((info for info in slowmode_info if info['channel_id'] == channel_id and info['token'] == token), None)
                            if existing_entry:
                                if 'usernames' not in existing_entry:
                                    existing_entry['usernames'] = []
                                if username not in existing_entry['usernames']:
                                    existing_entry['usernames'].append(username)
                                existing_entry['universal_message'] = universal_message
                            else:
                                box_number = len(slowmode_info) + 1  # Assign a number to the new box
                                slowmode_info.append({
                                    'box_number': box_number,  # Add the box number here
                                    'channel_id': channel_id,
                                    'usernames': [username],
                                    'slowmode_duration': slowmode_duration,
                                    'channel_name': channel_name,
                                    'server_name': server_name,
                                    'universal_message': universal_message,
                                    'custom_message': '',
                                    'bot_running': False,
                                    'token': token,
                                })
                        else:
                            username = DiscordToken.objects.get(token=token).username
                            error_messages.append(f"Error retrieving info for username {username}")
                    except (RequestException, ConnectionError) as e:
                        error_messages.append(f"Server unreachable. Please try again later. Error: {str(e)}")

                request.session['slowmode_info'] = slowmode_info
                request.session.modified = True
            else:
                messages.error(request, "Form is not valid. Please correct the errors.")
        elif 'confirm_universal' in request.POST:
            universal_form = UniversalMessageForm(request.POST)
            if universal_form.is_valid():
                universal_message = universal_form.cleaned_data['universal_message']
                for info in slowmode_info:
                    if info['custom_message']:
                        error_messages.append(f"Remove custom message for channel {info['channel_id']} before setting universal message.")
                        break
                else:
                    for info in slowmode_info:
                        info['universal_message'] = universal_message
                    request.session['slowmode_info'] = slowmode_info
                    request.session.modified = True
        elif 'stop_bot' in request.POST or 'start_bot' in request.POST:
            channel_id = int(request.POST.get('channel_id') or 0)
            action = 'stop_bot' if 'stop_bot' in request.POST else 'start_bot'
            for info in slowmode_info:
                if info['channel_id'] == channel_id:
                    if action == 'stop_bot':
                        info['bot_running'] = False
                        data = {
                            "token": info['token'],
                            "channel_id": channel_id
                        }
                        try:
                            response = requests.post(stop_autoad_url, json=data)
                            if response.status_code != 200:
                                error_messages.append(f"Error stopping bot for channel {channel_id}")
                        except (RequestException, ConnectionError) as e:
                            error_messages.append(f"Server unreachable. Please try again later. Error: {str(e)}")
                    else:
                        message = info['custom_message'] if info['custom_message'] else info['universal_message']
                        if not message:
                            error_messages.append(f"No message provided for channel {channel_id}")
                        else:
                            info['bot_running'] = True
                            data = {
                                "token": info['token'],
                                "channel_id": info['channel_id'],
                                "message": message,
                                "infinite_loop": True
                            }
                            try:
                                response = requests.post(send_data_url, json=data)
                                if response.status_code != 200:
                                    error_messages.append(f"Error starting bot for channel {channel_id}")
                            except (RequestException, ConnectionError) as e:
                                error_messages.append(f"Server unreachable. Please try again later. Error: {str(e)}")
                    break
            request.session['slowmode_info'] = slowmode_info
            request.session.modified = True
        elif 'delete_box' in request.POST:
            channel_id = int(request.POST.get('channel_id') or 0)
            slowmode_info = [info for info in slowmode_info if info['channel_id'] != channel_id]
            request.session['slowmode_info'] = slowmode_info
            request.session.modified = True
        elif 'set_custom_message' in request.POST:
            channel_id = int(request.POST.get('channel_id') or 0)
            custom_message = request.POST.get('custom_message', '')
            for info in slowmode_info:
                if info['channel_id'] == channel_id:
                    info['custom_message'] = custom_message
                    break
            request.session['slowmode_info'] = slowmode_info
            request.session.modified = True
        elif 'remove_custom_message' in request.POST:
            channel_id = int(request.POST.get('channel_id') or 0)
            for info in slowmode_info:
                if info['channel_id'] == channel_id:
                    info['custom_message'] = ''
                    break
            request.session['slowmode_info'] = slowmode_info
            request.session.modified = True
        elif 'clear_universal' in request.POST:
            for info in slowmode_info:
                info['universal_message'] = ''
            request.session['slowmode_info'] = slowmode_info
            request.session.modified = True
        elif 'remove_universal' in request.POST:
            for info in slowmode_info:
                info['universal_message'] = ''
            request.session['slowmode_info'] = slowmode_info
            request.session.modified = True
            universal_form = UniversalMessageForm()  # Clear the form

    return render(request, 'features/auto-ad/auto-ad.html', {'data_form': data_form, 'universal_form': universal_form, 'slowmode_info': slowmode_info, 'error_messages': error_messages})

@login_required
def remove_box(request):
    if request.method == 'POST':
        try:
            request_data = json.loads(request.body)
            channel_id = request_data.get('channel_id')
            if channel_id is None:
                raise ValueError("Channel ID is required")
            slowmode_info = request.session.get('slowmode_info', [])
            updated_info = [info for info in slowmode_info if str(info['channel_id']) != str(channel_id)]
            request.session['slowmode_info'] = updated_info
            request.session.modified = True
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'failed', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'failed'}, status=400)
