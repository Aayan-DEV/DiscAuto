import pathlib
from django.shortcuts import render
from django.http import HttpResponse
from visits.models import PageVisits

this_dir = pathlib.Path(__file__).resolve().parent

def home_view(request, *args, **kwargs):
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
    return render(request, html_template, my_context)