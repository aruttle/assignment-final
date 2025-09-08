from django.urls import path
from . import views

app_name = "activities"
urlpatterns = [
    path("", views.activity_list, name="list"),
    path("<int:pk>/", views.activity_detail, name="detail"),
    path("<int:pk>/availability/", views.activity_availability, name="availability"),
    path("<int:pk>/book/", views.booking_create, name="book"),
    path("bookings/<int:pk>/cancel/", views.booking_cancel, name="booking_cancel"),  
]