from django.db import models
from django.utils import timezone


class Place(models.Model):
    address = models.CharField(
        'адрес места',
        max_length=250,
        blank=True,
        unique=True
    )
    latitude = models.FloatField('широта')
    longitude = models.FloatField('долгота')
    updated_at = models.DateTimeField(
        'обновлен в',
        default=timezone.now,
    )

    def __str__(self):
        return f'({self.latitude}, {self.longitude})'