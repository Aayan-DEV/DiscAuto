from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
import requests
import json
from .forms import DataForm, StopBotForm
from auths.models import DiscordToken

get_slowmode_url = "http://127.0.0.1:5001/get_slowmode"
get_channel_name_url = "http://127.0.0.1:5001/get_channel_name"
get_server_name_url = "http://127.0.0.1:5001/get_server_name"

@login_required
def auto_ad(request):
    if 'slowmode_info' not in request.session:
        request.session['slowmode_info'] = []
    slowmode_info = request.session['slowmode_info']
    error_messages = []

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

                    existing_entry = next((info for info in slowmode_info if info['channel_id'] == channel_id), None)
                    if existing_entry:
                        if 'usernames' not in existing_entry:
                            existing_entry['usernames'] = []
                        if username not in existing_entry['usernames']:
                            existing_entry['usernames'].append(username)
                    else:
                        slowmode_info.append({
                            'channel_id': channel_id,
                            'usernames': [username],
                            'slowmode_duration': slowmode_duration,
                            'channel_name': channel_name,
                            'server_name': server_name,
                        })
                else:
                    username = DiscordToken.objects.get(token=token).username
                    error_messages.append(f"Error retrieving info for username {username}")

            request.session['slowmode_info'] = slowmode_info
            request.session.modified = True
            form = DataForm(user=request.user)
        else:
            messages.error(request, "Form is not valid. Please correct the errors.")
    else:
        form = DataForm(user=request.user)

    return render(request, 'features/auto-ad/auto-ad.html', {'form': form, 'slowmode_info': slowmode_info, 'error_messages': error_messages})

@login_required
def remove_box(request):
    if request.method == 'POST':
        try:
            request_data = json.loads(request.body)
            channel_id = request_data.get('channel_id')
            slowmode_info = request.session.get('slowmode_info', [])
            updated_info = [info for info in slowmode_info if str(info['channel_id']) != channel_id]
            request.session['slowmode_info'] = updated_info
            request.session.modified = True
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'failed', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'failed'}, status=400)
