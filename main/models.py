from django.db import models
from django.contrib.auth.models import User


# Create your models here.
class Event(models.Model):
    """
    Specifically designed for SIS Ical Events
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    name = models.CharField(max_length=255)  # Maps to SUMMARY
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    description = models.TextField(null=True, blank=True)  # Maps to DESCRIPTION
    location = models.CharField(max_length=255)  # Maps to LOCATION

    # Recurring information
    FREQUENCY_CHOICES = [
        ('DAILY', 'Daily'),
        ('WEEKLY', 'Weekly'),
        ('MONTHLY', 'Monthly'),
        ('YEARLY', 'Yearly'),
    ]
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES, null=True, blank=True)
    until = models.DateTimeField(null=True, blank=True)
    byday = models.CharField(max_length=50, null=True, blank=True)  # Days of the week
    requestDescription = models.TextField(null=True, blank=True)
    requestGranted = models.BooleanField(default=False)


class Person(models.Model):
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=500)


class FavoriteLocation(models.Model):
    address = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
