from django.contrib import admin
from django.urls import path

from .views import home_view,about_view

urlpatterns = [
    path("hello-world/", home_view),
    path("about/", about_view),
    path("", home_view),
    path('admin/', admin.site.urls),
]
