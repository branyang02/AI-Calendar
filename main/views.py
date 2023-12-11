from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
import os
from django.http import JsonResponse, Http404
from main.utils.chatgpt import ChatGPT
from .models import Event, Person, FavoriteLocation
from icalendar import Calendar
from django.views.generic import ListView
from django.contrib.auth.models import Group, User
from datetime import datetime, timedelta
from django.utils import timezone
from typing import List, Dict
from django.contrib.auth.decorators import login_required
from .Forms import ChangeForm
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.views.decorators.http import require_POST
import uuid
from .Forms import FavoriteForm
from django.core import serializers

chat_instance_dict = {}


def get_daily_schedule(user) -> List[Event]:
    """
    Return a list (from model.Events) of today's events for the given user
    """
    todays_events = []

    # Dictionary to map full day names to abbreviations
    day_abbr_map = {
        "MONDAY": "MO",
        "TUESDAY": "TU",
        "WEDNESDAY": "WE",
        "THURSDAY": "TH",
        "FRIDAY": "FR",
        "SATURDAY": "SA",
        "SUNDAY": "SU",
    }

    # Get today's date and time using timezone-aware datetimes
    today_start = timezone.localtime().replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    today_end = today_start + timezone.timedelta(days=1)

    # Filter non-recurring events for today
    todays_events = Event.objects.filter(
        user=user, start_date__lte=today_end, end_date__gte=today_start
    )

    # Handle recurring events
    recurring_events = Event.objects.filter(user=user).exclude(frequency__isnull=True)

    for event in recurring_events:
        if event.frequency == "WEEKLY":
            # check if today is between start date and until date
            if event.start_date <= today_start and (
                not event.until or event.until >= today_start
            ):
                # Also check if today's day matches the event's recurring days using abbreviations
                if day_abbr_map[today_start.strftime("%A").upper()] in (
                    event.byday or ""
                ).split(","):
                    # print("Adding weekly event: " + event.name)
                    # print(event.byday)
                    todays_events |= Event.objects.filter(id=event.id)

    # Return the list of today's events
    return todays_events.order_by("start_date")


def structure_ical(ical) -> List[Dict]:
    """Prepare the ical data for saving to the database"""
    events = []
    for event in ical.walk("vevent"):
        event_data = {}
        event_data["uid"] = str(event.get("uid"))
        event_data["summary"] = str(event.get("summary"))
        event_data["dtstart"] = str(event.get("dtstart").dt)
        event_data["dtend"] = str(event.get("dtend").dt)
        event_data["description"] = (
            str(event.get("description")) if event.get("description") else None
        )
        event_data["location"] = (
            str(event.get("location")) if event.get("location") else None
        )
        rrule = event.get("rrule")

        if rrule:
            rrule_dict = rrule.to_ical().decode("utf-8").split(";")
            event_data["freq"] = [
                item.split("=")[1] for item in rrule_dict if item.startswith("FREQ=")
            ][0]
            event_data["byday"] = (
                [
                    item.split("=")[1]
                    for item in rrule_dict
                    if item.startswith("BYDAY=")
                ][0]
                if "BYDAY=" in rrule.to_ical().decode("utf-8")
                else None
            )
            event_data["count"] = (
                [
                    item.split("=")[1]
                    for item in rrule_dict
                    if item.startswith("COUNT=")
                ][0]
                if "COUNT=" in rrule.to_ical().decode("utf-8")
                else None
            )
            if "UNTIL=" in rrule.to_ical().decode("utf-8"):
                until_str = [
                    item.split("=")[1]
                    for item in rrule_dict
                    if item.startswith("UNTIL=")
                ][0]
                # Convert to datetime object
                until_dt = datetime.strptime(until_str, "%Y%m%dT%H%M%S")
                # Format to a more readable string
                event_data["until"] = until_dt.strftime("%Y-%m-%d %H:%M:%S")

        events.append(event_data)

    return events


def parse_calendar(calendar_text, user) -> None:
    """
    Parse and SAVE events to the Event Table
    """
    ical = Calendar.from_ical(calendar_text)
    structured_events = structure_ical(ical)

    # Only allow one calendar per user. Delete all existing events before parsing new events.
    Event.objects.filter(user=user).delete()

    for event_data in structured_events:
        frequency = event_data.get("freq")
        byday = event_data.get("byday")
        until_str = event_data.get("until")
        until = datetime.strptime(until_str, "%Y-%m-%d %H:%M:%S") if until_str else None

        # Convert string datetime to datetime object
        start_date = datetime.fromisoformat(event_data["dtstart"])
        end_date = datetime.fromisoformat(event_data["dtend"])

        e = Event(
            user=user,
            name=event_data["summary"],
            start_date=start_date,
            end_date=end_date,
            description=event_data["description"],
            location=event_data["location"],
            frequency=frequency,
            byday=byday,
            until=until,
        )
        e.save()


@login_required
def map(request):
    """
    Google Maps API Rendering
    """
    key = settings.GOOGLE_MAPS_API_KEY
    daily_events = get_daily_schedule(request.user)

    favorite_locations = serializers.serialize("json", FavoriteLocation.objects.all())

    unapproved_events = Event.objects.filter(user=request.user, requestGranted=False)

    map_filter = "default"

    path = request.path
    split_path = path.split("/")
    split_path = [i for i in split_path if i]

    if len(split_path) > 1:
        map_filter = split_path[-1]
        if map_filter == "":
            map_filter = "default"

    context = {
        "key": key,
        "events": daily_events,
        "filter": map_filter,
        "favorite_locations": favorite_locations,
        "unapproved_events": unapproved_events,
    }

    return render(request, "main/map.html", context)


@login_required
def chat_endpoint(request):
    """
    POST Request to ChatGPT for AI Assistance
    """
    if 'chat_instance_id' not in request.session:
        chat_instance = ChatGPT(request.user)
        chat_instance_id = str(uuid.uuid4())
        chat_instance_dict[chat_instance_id] = chat_instance
        request.session['chat_instance_id'] = chat_instance_id
    else:
        chat_instance_id = request.session['chat_instance_id']
        chat_instance = chat_instance_dict.get(chat_instance_id)

        if chat_instance is None:
            chat_instance = ChatGPT(request.user)
            chat_instance_dict[chat_instance_id] = chat_instance
            request.session['chat_instance_id'] = chat_instance_id

    if request.method == "POST":
        message = request.POST.get("message")
        response = chat_instance.query_message(message)
        return JsonResponse({
            "response": response.get("response"),
            "addresses": response.get("addresses")
        })


@login_required
def calendar_view(request):
    events = Event.objects.filter(user=request.user)
    if request.method == "POST" and "calendar" in request.FILES:
        calendar_file = request.FILES["calendar"]
        calendar_text = calendar_file.read().decode("utf-8")
        try:
            parse_calendar(calendar_text, request.user)
            # Refresh the events after parsing
            events = Event.objects.filter(user=request.user)
        except Exception as e:
            raise Http404(f"Failed to parse calendar: {str(e)}")

        return redirect("calendar")

    return render(request, "main/calendar.html", {"events": events})


@login_required
def about_view(request):
    return render(request, "main/about.html")


@login_required
def unapproved_events(request):
    events = Event.objects.filter(requestGranted=False)
    return render(request, 'main/unapproved_events.html', {'events': events})


@require_POST
def approve_event(request, event_id):
    print("Approving EVENE")
    event = get_object_or_404(Event, pk=event_id)
    event.requestGranted = True
    event.save()
    return redirect('unapproved_events')


@require_POST
def delete_event(request, event_id):
    print("deleting EVENE")

    event = get_object_or_404(Event, pk=event_id)
    event.delete()
    return redirect('unapproved_events')


@login_required
def add_to_admin_group(request, user_id):
    user = User.objects.get(pk=user_id)

    admin_users_group, created = Group.objects.get_or_create(name='Admin_Users')

    user.groups.add(admin_users_group)
    return redirect('/map/')


@login_required
def favorite(request):
    if request.method == "POST":
        form = FavoriteForm(request.POST)

        if form.is_valid():
            form_address = form.cleaned_data["address"]
            form_name = form.cleaned_data["name"]
            favorite_location = FavoriteLocation(address=form_address, name=form_name)
            favorite_location.save()

        return HttpResponseRedirect(reverse("map"))

    elif request.method == "GET":
        return render(request, "main/favorite.html", context={"form": FavoriteForm})


@login_required
def remove_favorite_locations(request):
    locations = FavoriteLocation.objects.all()
    return render(request, 'main/remove_favorite_locations.html', {'locations': locations})


@require_POST
def remove_location(request, location_id):
    location = get_object_or_404(FavoriteLocation, pk=location_id)
    location.delete()
    return redirect('remove_favorite_locations')
