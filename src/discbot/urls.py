from django.contrib import admin
from django.urls import path
from auth import views as auth_views
from .views import home_view,about_view

urlpatterns = [
    path("register/", auth_views.register_view),
    path("hello-world/", home_view),
    path("login/", auth_views.login_view),
    path("about/", about_view),
    path("", home_view),
    path('admin/', admin.site.urls),
]
