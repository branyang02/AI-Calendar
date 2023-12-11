from django.contrib import admin
from .models import Event

class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'start_date', 'end_date', 'requestGranted')

admin.site.register(Event, EventAdmin)