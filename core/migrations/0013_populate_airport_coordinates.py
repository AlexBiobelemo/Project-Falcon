"""Populate airport coordinates from known data.

This migration adds latitude/longitude coordinates to existing airports
using the built-in airport coordinates database.
"""

from django.db import migrations

# Airport coordinates database
AIRPORT_COORDINATES = {
    'ATL': (33.6407, -84.4277),
    'LAX': (33.9416, -118.4085),
    'ORD': (41.9742, -87.9073),
    'DFW': (32.8998, -97.0403),
    'DEN': (39.8561, -104.6737),
    'JFK': (40.6413, -73.7781),
    'SFO': (37.6213, -122.3790),
    'LAS': (36.0840, -115.1537),
    'SEA': (47.4502, -122.3088),
    'MIA': (25.7959, -80.2870),
    'BOS': (42.3656, -71.0096),
    'PHX': (33.4373, -112.0078),
    'IAH': (29.9902, -95.3368),
    'MCO': (28.4312, -81.3081),
    'EWR': (40.6895, -74.1745),
    'LHR': (51.4700, -0.4543),
    'CDG': (49.0097, 2.5479),
    'FRA': (50.0379, 8.5622),
    'AMS': (52.3105, 4.7683),
    'DXB': (25.2532, 55.3657),
    'HND': (35.5494, 139.7798),
    'SIN': (1.3644, 103.9915),
    'ICN': (37.4602, 126.4407),
    'LOS': (6.5774, 3.3212),
    'ABV': (9.0068, 7.2632),
    'PHC': (5.0155, 6.9496),
    'KAN': (11.9581, 8.5247),
}


def populate_airport_coordinates(apps, schema_editor):
    """Populate coordinates for existing airports."""
    Airport = apps.get_model('core', 'Airport')
    
    for airport in Airport.objects.all():
        coords = AIRPORT_COORDINATES.get(airport.code.upper())
        if coords:
            airport.latitude = coords[0]
            airport.longitude = coords[1]
            airport.save(update_fields=['latitude', 'longitude'])


def reverse_populate_airport_coordinates(apps, schema_editor):
    """Reverse: clear coordinates."""
    Airport = apps.get_model('core', 'Airport')
    Airport.objects.all().update(latitude=None, longitude=None)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_airport_latitude_airport_longitude'),
    ]

    operations = [
        migrations.RunPython(
            populate_airport_coordinates,
            reverse_populate_airport_coordinates,
        ),
    ]
