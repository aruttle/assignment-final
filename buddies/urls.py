from django.urls import path
from . import views

app_name = "buddies"
urlpatterns = [
    path("", views.session_list, name="list"),
    path("new/", views.session_create, name="create"),
    path("<int:pk>/", views.session_detail, name="detail"),
    path("<int:pk>/edit/", views.session_edit, name="edit"), 
    path("<int:pk>/toggle_join/", views.toggle_join, name="toggle_join"),
    path("<int:pk>/message/", views.post_message, name="message"),
    path("message/<int:msg_id>/delete/", views.delete_message, name="delete_message"),  
    path("<int:pk>/delete/", views.session_delete, name="delete"),
    path("mine/", views.my_sessions, name="my_sessions"),
]
