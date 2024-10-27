from django.shortcuts import render
from dashboard.views import dashboard_view

# It shows the dashboard Page when a user is logged in.  
def landing_dashboard_page_view(request):
    if request.user.is_authenticated:
        return dashboard_view(request)

    return render(request, 'landing/main.html', {'current_page': 'home'})