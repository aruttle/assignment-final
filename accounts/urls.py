from django.urls import path
from .views import signup, NiceLoginView

app_name = "accounts"
urlpatterns = [
    path("login/", NiceLoginView.as_view(), name="login"),
    path("signup/", signup, name="signup"),
]
