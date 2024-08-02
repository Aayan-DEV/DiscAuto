import pathlib
from django.shortcuts import render
from django.http import HttpResponse, Http404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from visits.models import PageVisits
from django.conf import settings
from subscriptions.models import UserSubscription
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from forms.contact_form import ContactForm


LOGIN_URL = settings.LOGIN_URL

this_dir = pathlib.Path(__file__).resolve().parent

def home_view(request, *args, **kwargs):
    if request.user.is_authenticated:
        print(request.user.username)
    return about_view(request, *args, **kwargs)

def about_view(request, *args, **kwargs):
    qs = PageVisits.objects.all()
    page_qs = PageVisits.objects.filter(path=request.path)
    try:
        percent = (page_qs.count() * 100.0) / qs.count()
    except:
        percent = 0    

    my_title = "Home"
    html_template = "home.html"
    my_context = {
        "page_title": my_title,
        "Page_visit_count": page_qs.count(),
        "Percent": percent,
        "Total_visit_count": qs.count(),
    }
    html_template = "home.html"
    PageVisits.objects.create(path=request.path)
    return render(request, html_template, my_context, {'current_page': 'home'})

VALID_CODE = "abcd1234"

def pw_proted_view(request, *args, **kwargs):
    is_allowed = request.session.get('protected_page_allowed') or 0
    if request.method == "POST":
        user_pw_sent = request.POST.get("code") or None        
        if user_pw_sent == VALID_CODE:
            is_allowed = 1
            request.session['protected_page_allowed'] = is_allowed         
    if is_allowed:
        return render(request, "protected/view.html", {})
    return render(request, "protected/entry.html", {})

@login_required
def user_only_view(request, *args, **kwargs):
    return render(request, "protected/user-only.html", {})

@staff_member_required(login_url = LOGIN_URL)
def staff_only_view(request, *args, **kwargs):
    return render(request, "protected/user-only.html", {})

def auto_ad(request, *args, **kwargs):
    return render(request, "features/auto-ad/auto-ad.html", {})

@login_required
def cold_dm(request, *args, **kwargs):
    user_subscription = UserSubscription.objects.filter(user=request.user).first()
    if not user_subscription or user_subscription.subscription.name.lower() != "pro plan":
        raise Http404("This page does not exist.")
    return render(request, "features/cold-dm/cold-dm.html", {})

def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            message = form.cleaned_data['message']
            full_message = f"Name: {name}\nEmail: {email}\nMessage:\n{message}"
            
            send_mail(
                'New Contact Form Submission',
                full_message,
                email,  # sender's email
                [settings.EMAIL_HOST_USER],  # receiver's email
            )
            messages.success(request, 'Your message has been sent successfully!')
            return redirect('contact')
    else:
        form = ContactForm()
    
    return render(request, 'contact/contact.html', {
        'form': form,
        'current_page': 'contact',        
        },)