from django.urls import path
from .views import signup, NiceLoginView, me_dashboard

app_name = "accounts"
urlpatterns = [
    path("login/", NiceLoginView.as_view(), name="login"),
    path("signup/", signup, name="signup"),
    path("me/", me_dashboard, name="me"),
]
