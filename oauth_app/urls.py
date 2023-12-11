from django.urls import path
from . import views

urlpatterns = [
    path("", views.signin, name="signin"),
    path("logout", views.logout_view, name="logout"),
]