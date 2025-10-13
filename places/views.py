from django.shortcuts import render
from django.utils import timezone

from places.models import Place

import requests


def fetch_coordinates(apikey, address):
    place = Place.objects.filter(address=address).first()

    if place and place.updated_at:
        return place.longitude, place.latitude

    base_url = "https://geocode-maps.yandex.ru/1.x"
    response = requests.get(base_url, params={
        "geocode": address,
        "apikey": apikey,
        "format": "json",
    })
    response.raise_for_status()
    found_places = response.json()['response']['GeoObjectCollection']['featureMember']

    if not found_places:
        return None

    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")

    Place.objects.update_or_create(
        address=address,
        defaults={
            'longitude': lon,
            'latitude': lat,
            'updated_at': timezone.now
        }
    )
    return lon, lat
