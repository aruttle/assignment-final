"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from activities import views as activities_views
from accounts.views import me_dashboard

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls", namespace="core")),
    path("activities/", include("activities.urls", namespace="activities")),
    path("accounts/", include("accounts.urls", namespace="accounts")),     
    path("accounts/", include("django.contrib.auth.urls")),                
    path("safety/", include("safety.urls", namespace="safety")),
    path("buddies/", include("buddies.urls", namespace="buddies")),
    path("me/bookings/", activities_views.my_bookings, name="my_bookings"),
    path("me/", me_dashboard, name="me_dashboard"),
]

