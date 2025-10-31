from django.conf import settings
from django.utils import timezone
from geopy import distance

from places.models import Place

import requests
import logging


logger = logging.getLogger(__name__)


def fetch_coordinates(addresses):
    apikey = settings.YANDEX_API_KEY
    coordinates = {}

    existing_places = Place.objects.filter(address__in=addresses)
    existing_dict = {place.address: (place.latitude, place.longitude) for place in existing_places}

    coordinates.update(existing_dict)

    missing_addresses = [address for address in addresses if address not in existing_dict]

    for address in missing_addresses:
        base_url = "https://geocode-maps.yandex.ru/1.x"
        response = requests.get(base_url, params={
            "geocode": address,
            "apikey": apikey,
            "format": "json",
        })
        response.raise_for_status()

        found_places = response.json()['response']['GeoObjectCollection']['featureMember']
        if not found_places:
            continue

        most_relevant = found_places[0]
        lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")

        Place.objects.update_or_create(
            address=address,
            defaults={
                'longitude': lon,
                'latitude': lat,
                'updated_at': timezone.now()
            }
        )

        coordinates[address] = (float(lat), float(lon))

    return coordinates


def count_distance_to_restaurants(orders):
    order_addresses = [order.address for order in orders]
    restaurant_addresses = []
    for order in orders:
        for restaurant in order.available_restaurants:
            restaurant_addresses.append(restaurant.address)
    all_addresses = list(set(order_addresses + restaurant_addresses))

    address_coords = fetch_coordinates(all_addresses)

    for order in orders:
        client_coords = address_coords.get(order.address)
        if not client_coords:
            order.available_restaurants = []
            continue

        distances = []
        for restaurant in order.available_restaurants:
            restaurant_coords = address_coords.get(restaurant.address)
            if not restaurant_coords:
                continue

            dist = round(distance.distance(client_coords, restaurant_coords).km, 2)
            distances.append(f"{restaurant.name} — {dist} км")

        order.available_restaurants = distances