from django.shortcuts import render
from dashboard.views import dashboard_view

def landing_dashboard_page_view(request):
    if request.user.is_authenticated:
        return dashboard_view(request)

    return render(request, 'landing/main.html', {'current_page': 'home'})

'''
Citation:
("Python Tutorial: Build a SaaS App") -> Lines 4 - 8
'''
