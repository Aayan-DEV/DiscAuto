from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model

User = get_user_model()

@login_required
# Create your views here.
def profile_view(request,  username=None, *args, **kwargs,):
    User.objects.get(username=username) 
    return HttpResponse(f"Profile Page of {username}")