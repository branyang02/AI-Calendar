import json
import time
from typing import Tuple
import openai
from openai import OpenAI
import os
from django.utils import timezone
from main.models import Event
import requests
from django.conf import settings


openai.api_key = os.getenv("OPENAI_API_KEY")
return_message = {}


def get_suggestions(search_criteria: str, relative_location: str):
    """Get Places suggestion based on a relative location. This function calls the Google Maps Places API.

    Args:
        search_criteria (str): The POI that is being searched for. For example, "Restaurants" or "Coffee Shops".
        relative_location (str): The relative location to search around. For example, "Rice Hall, Charlottesville, Virginia".

    Returns:
        JSON String: JSON String of the Google Maps Places API response.
        Ex:
        {
            "places": [
            {
                "formattedAddress": "367 Pitt St, Sydney NSW 2000, Australia",
                "priceLevel": "PRICE_LEVEL_MODERATE",
                "displayName": {
                "text": "Mother Chu's Vegetarian Kitchen",
                "languageCode": "en"
                }
            },
            {
                "formattedAddress": "115 King St, Newtown NSW 2042, Australia",
                "priceLevel": "PRICE_LEVEL_MODERATE",
                "displayName": {
                "text": "Green Mushroom",
                "languageCode": "en"
                }
            },
            ...
            ]
        }
    """
    print("Search Criteria: ", search_criteria)
    print("Relative Location: ", relative_location)

    # 1: get lat and long of relative location
    api_url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": relative_location,
        "key": settings.GOOGLE_MAPS_API_KEY,
    }
    response = requests.get(api_url, params=params)
    if response.status_code == 200:
        ans = response.json()
        lat = ans["results"][0]["geometry"]["location"]["lat"]
        lng = ans["results"][0]["geometry"]["location"]["lng"]
    else:
        print("Error:", response.status_code, response.text)
        return None

    # 2. Call Google Maps Places API with prompt and location bias, return JSON of places
    api_url = "https://places.googleapis.com/v1/places:searchText"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": settings.GOOGLE_MAPS_API_KEY,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress",
    }
    data = {
        "textQuery": search_criteria,
        "maxResultCount": 5,
        "locationBias": {
            "circle": {
                "center": {
                    "latitude": lat,
                    "longitude": lng,
                },
                "radius": 500.0
            }
        },
    }
    response = requests.post(api_url, headers=headers, data=json.dumps(data))
    # print(response.status_code)
    if response.status_code == 200:
        # 2. Search for Top place in JSON and Pin it on map
        ans = response.json()
        addresses = []
        location_names = []
        for place in ans["places"]:
            addresses.append(place["formattedAddress"])
            location_names.append(place["displayName"]["text"])
        return_message["addresses"] = {
            "addresses": addresses,
            "location_names": location_names,
        }
        return json.dumps(ans)
    else:
        print("Error:", response.status_code, response.text)
        return None


class ChatGPT:
    def __init__(self, user):
        global return_message
        self.messages = [
            {
                "role": "system",
                "content": "You are an intelligent assistant. You are helping students at UVA plan their day. You have acces to their daily schedule. If the user does not have anything in their schedule, please tell them that they do not have any events planned for the day. Always be complete, concise, and clear. Tell the user every step you are doing, such as the class names.",
            }
        ]
        self.user = user
        self.client = OpenAI()
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_suggestions",
                    "description": "Retrieve a list of places based on specific search criteria and a relative location. This function utilizes the Google Maps Places API to find points of interest (e.g., restaurants, coffee shops) near a given location. It first converts the relative location into latitude and longitude coordinates using the Google Maps Geocoding API, then searches for places matching the criteria near these coordinates. The response is a JSON string detailing various places, including their formatted addresses, price levels, and names in specified languages.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "search_criteria": {
                                "type": "string",
                                "description": "The type of point of interest to search for, such as 'Restaurants' or 'Coffee Shops'.",
                            },
                            "relative_location": {
                                "type": "string",
                                "description": "The relative location around which to search, described in a human-readable format, e.g., 'Rice Hall, Charlottesville, Virginia'.",
                            },
                        },
                        "required": ["search_criteria", "relative_location"],
                    },
                },
            }
        ]

    def query_message(self, message):
        # Get daily schedule.
        self.messages.append(
            {
                "role": "system",
                "content": f"These are the events that the user has today: {self._get_daily_schedule()}",
            }
        )
        # Place holder for local testing
        if (
            os.getenv("DEPLOY_ENV") != "production"
            and os.getenv("CHAT_TEST") == "False"
        ):
            time.sleep(1.5)
            return "You are seeing this message because you are in development mode. This message is a placeholder for the response from the GPT-3 API. Please set the DEPLOY_ENV environment variable to 'production' to use the GPT-3 API."

        # Get suggestions from GPT-3 API
        if message:
            # Step 1: send the conversation and available functions to the model
            self.messages.append({"role": "user", "content": message})
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo-1106",
                messages=self.messages,
                tools=self.tools,
                tool_choice="auto",  # auto is default, but we'll be explicit
            )
            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls

            # Step 2: check if the model wanted to call a function
            if tool_calls:
                # Step 3: call the function
                available_functions = {
                    "get_suggestions": get_suggestions,
                }
                self.messages.append(response_message)
                # Step 4: send the info for each function call and function response to the model
                # Includes parallel function calls and responses
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    function_to_call = available_functions[function_name]
                    function_args = json.loads(tool_call.function.arguments)
                    function_response = function_to_call(
                        search_criteria=function_args.get("search_criteria"),
                        relative_location=function_args.get("relative_location"),
                    )
                    self.messages.append(
                        {
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": function_response,
                        }
                    )  # extend conversation with function response
                second_response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo-1106",
                    messages=self.messages,
                )  # get a new response from the model where it can see the function response
                # print("Response message: ", response_message)
                # print("second message: ", second_response.choices[0].message.content)
                # print(return_message)
                return_message["response"] = second_response.choices[0].message.content
                print(return_message)
                return return_message
            else:
                return_message["addresses"] = []
                return_message["response"] = response_message.content
                return return_message

            # Depracated with the latest OpenAI update.
            # self.messages.append({"role": "user", "content": message})
            # chat = openai.ChatCompletion.create(
            #     model="gpt-3.5-turbo", messages=self.messages
            # )
            # reply = chat.choices[0].message.content
            # self.messages.append({"role": "assistant", "content": reply})
            # return reply

    def _get_daily_schedule(self) -> Tuple[str, str, str, str, str]:
        """Return the daily schedule for the Current user. Becuase the applicaiton is not
        REST, this is fed into the chatbot everytime the user sends a message.

        Returns:
            Tuple[str, str, str, str, str]: (
                Name,
                Start Time,
                End Time,
                Description,
                Location,
            )
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
            user=self.user, start_date__lte=today_end, end_date__gte=today_start
        )

        # Handle recurring events
        recurring_events = Event.objects.filter(user=self.user).exclude(
            frequency__isnull=True
        )

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

        ordered_events = todays_events.order_by("start_date")

        # convert to String
        events = []
        for event in ordered_events:
            local_start = timezone.localtime(event.start_date)
            local_end = timezone.localtime(event.end_date)

            events.append(
                (
                    event.name,
                    local_start.strftime("%H:%M"),
                    local_end.strftime("%H:%M"),
                    event.description,
                    event.location,
                )
            )

        return events


# 1. suggest
# 2. get recommended
# 3. display recommended pins
# 4. get route to recommended pin
