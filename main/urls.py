from django.urls import path
from . import views

urlpatterns = [
    path('', views.map, name="map"),
    path('chat/', views.chat_endpoint, name='chat_endpoint'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('about/', views.about_view, name="about"),
    path('addfavorite/', views.favorite, name="favorite"),
    path('unapproved-events/', views.unapproved_events, name='unapproved_events'),
    path('approve-event/<int:event_id>/', views.approve_event, name='approve_event'),
    path('delete-event/<int:event_id>/', views.delete_event, name='delete_event'),
    path('add-to-admin-group/<int:user_id>/', views.add_to_admin_group, name='add_to_admin_group'),
    path('remove-favorite-locations', views.remove_favorite_locations, name='remove_favorite_locations'),
    path('remove-location/<int:location_id>', views.remove_location, name='remove_location'),
]