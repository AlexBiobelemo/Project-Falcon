"""Weather service for fetching real-time weather data.

This module provides integration with Open-Meteo API for weather data.
"""

import logging
import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Dict, Optional
from django.core.cache import cache
from datetime import datetime

logger = logging.getLogger(__name__)


def _http_get_json(url: str, params: Dict[str, object], timeout: int = 5) -> Dict[str, object]:
    """Small HTTP JSON helper to avoid depending on `requests`.

    Using stdlib keeps the dependency surface smaller (and avoids Dependabot
    alerts tied to `requests`).
    """
    qs = urllib.parse.urlencode({k: str(v) for k, v in params.items()})
    full_url = f"{url}?{qs}"
    req = urllib.request.Request(
        full_url,
        headers={"User-Agent": "blue-falcon/1.0 (+weather)"},
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        if getattr(resp, "status", 200) != 200:
            raise urllib.error.HTTPError(full_url, resp.status, "HTTP error", resp.headers, None)
        raw = resp.read().decode("utf-8", errors="replace")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("Expected JSON object response")
    return data


class WeatherService:
    """Service for fetching weather data from Open-Meteo API."""
    
    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    
    # Common airport coordinates for fallback
    AIRPORT_COORDINATES = {
        'ATL': {'latitude': 33.6407, 'longitude': -84.4277},  # Atlanta
        'LAX': {'latitude': 33.9416, 'longitude': -118.4085},  # Los Angeles
        'ORD': {'latitude': 41.9742, 'longitude': -87.9073},  # Chicago O'Hare
        'DFW': {'latitude': 32.8998, 'longitude': -97.0403},  # Dallas/Fort Worth
        'DEN': {'latitude': 39.8561, 'longitude': -104.6737},  # Denver
        'JFK': {'latitude': 40.6413, 'longitude': -73.7781},  # New York JFK
        'SFO': {'latitude': 37.6213, 'longitude': -122.3790},  # San Francisco
        'LAS': {'latitude': 36.0840, 'longitude': -115.1537},  # Las Vegas
        'SEA': {'latitude': 47.4502, 'longitude': -122.3088},  # Seattle
        'MIA': {'latitude': 25.7959, 'longitude': -80.2870},  # Miami
        'BOS': {'latitude': 42.3656, 'longitude': -71.0096},  # Boston
        'PHX': {'latitude': 33.4373, 'longitude': -112.0078},  # Phoenix
        'IAH': {'latitude': 29.9902, 'longitude': -95.3368},  # Houston
        'MCO': {'latitude': 28.4312, 'longitude': -81.3081},  # Orlando
        'EWR': {'latitude': 40.6895, 'longitude': -74.1745},  # Newark
        'LHR': {'latitude': 51.4700, 'longitude': -0.4543},  # London Heathrow
        'CDG': {'latitude': 49.0097, 'longitude': 2.5479},  # Paris CDG
        'FRA': {'latitude': 50.0379, 'longitude': 8.5622},  # Frankfurt
        'AMS': {'latitude': 52.3105, 'longitude': 4.7683},  # Amsterdam
        'DXB': {'latitude': 25.2532, 'longitude': 55.3657},  # Dubai
        'HND': {'latitude': 35.5494, 'longitude': 139.7798},  # Tokyo Haneda
        'SIN': {'latitude': 1.3644, 'longitude': 103.9915},  # Singapore
        'ICN': {'latitude': 37.4602, 'longitude': 126.4407},  # Seoul Incheon
        'LOS': {'latitude': 6.5774, 'longitude': 3.3212},  # Lagos
        'ABV': {'latitude': 9.0068, 'longitude': 7.2632},  # Abuja
        'PHC': {'latitude': 5.0155, 'longitude': 6.9496},  # Port Harcourt
        'KAN': {'latitude': 11.9581, 'longitude': 8.5247},  # Kano
    }
    
    # Weather code descriptions with theme info
    WEATHER_CODES = {
        0: {'condition': 'Clear Sky', 'icon': 'sun', 'theme': 'sunny', 'night_icon': 'moon'},
        1: {'condition': 'Mainly Clear', 'icon': 'sun', 'theme': 'sunny', 'night_icon': 'moon'},
        2: {'condition': 'Partly Cloudy', 'icon': 'cloud-sun', 'theme': 'cloudy', 'night_icon': 'cloud-moon'},
        3: {'condition': 'Overcast', 'icon': 'cloud', 'theme': 'cloudy', 'night_icon': 'cloud'},
        45: {'condition': 'Fog', 'icon': 'smog', 'theme': 'cloudy', 'night_icon': 'smog'},
        48: {'condition': 'Depositing Rime Fog', 'icon': 'smog', 'theme': 'cloudy', 'night_icon': 'smog'},
        51: {'condition': 'Light Drizzle', 'icon': 'cloud-rain', 'theme': 'rainy', 'night_icon': 'cloud-rain'},
        53: {'condition': 'Moderate Drizzle', 'icon': 'cloud-rain', 'theme': 'rainy', 'night_icon': 'cloud-rain'},
        55: {'condition': 'Dense Drizzle', 'icon': 'cloud-showers-heavy', 'theme': 'rainy', 'night_icon': 'cloud-showers-heavy'},
        61: {'condition': 'Slight Rain', 'icon': 'cloud-rain', 'theme': 'rainy', 'night_icon': 'cloud-rain'},
        63: {'condition': 'Moderate Rain', 'icon': 'cloud-rain', 'theme': 'rainy', 'night_icon': 'cloud-rain'},
        65: {'condition': 'Heavy Rain', 'icon': 'cloud-showers-heavy', 'theme': 'rainy', 'night_icon': 'cloud-showers-heavy'},
        71: {'condition': 'Slight Snow', 'icon': 'snowflake', 'theme': 'snowy', 'night_icon': 'snowflake'},
        73: {'condition': 'Moderate Snow', 'icon': 'snowflake', 'theme': 'snowy', 'night_icon': 'snowflake'},
        75: {'condition': 'Heavy Snow', 'icon': 'snowflake', 'theme': 'snowy', 'night_icon': 'snowflake'},
        77: {'condition': 'Snow Grains', 'icon': 'snowflake', 'theme': 'snowy', 'night_icon': 'snowflake'},
        80: {'condition': 'Slight Rain Showers', 'icon': 'cloud-rain', 'theme': 'rainy', 'night_icon': 'cloud-rain'},
        81: {'condition': 'Moderate Rain Showers', 'icon': 'cloud-rain', 'theme': 'rainy', 'night_icon': 'cloud-rain'},
        82: {'condition': 'Violent Rain Showers', 'icon': 'cloud-showers-heavy', 'theme': 'rainy', 'night_icon': 'cloud-showers-heavy'},
        85: {'condition': 'Slight Snow Showers', 'icon': 'snowflake', 'theme': 'snowy', 'night_icon': 'snowflake'},
        86: {'condition': 'Heavy Snow Showers', 'icon': 'snowflake', 'theme': 'snowy', 'night_icon': 'snowflake'},
        95: {'condition': 'Thunderstorm', 'icon': 'bolt', 'theme': 'stormy', 'night_icon': 'bolt'},
        96: {'condition': 'Thunderstorm with Hail', 'icon': 'bolt', 'theme': 'stormy', 'night_icon': 'bolt'},
        99: {'condition': 'Thunderstorm with Heavy Hail', 'icon': 'bolt', 'theme': 'stormy', 'night_icon': 'bolt'},
    }
    
    def is_nighttime(self, latitude: float, longitude: float) -> bool:
        """Determine if it's currently night at the given location."""
        try:
            # Use Open-Meteo's sunrise/sunset endpoint
            params = {
                'latitude': latitude,
                'longitude': longitude,
                'daily': 'sunrise,sunset',
                'timezone': 'auto',
            }
            data = _http_get_json(self.BASE_URL, params=params, timeout=5)
            
            daily = data.get('daily', {})
            sunrise_str = daily.get('sunrise', [None])[0]
            sunset_str = daily.get('sunset', [None])[0]
            
            if not sunrise_str or not sunset_str:
                return False
            
            # Parse times
            now = datetime.now()
            sunrise = datetime.fromisoformat(sunrise_str.replace('Z', '+00:00'))
            sunset = datetime.fromisoformat(sunset_str.replace('Z', '+00:00'))
            
            # Check if current time is between sunrise and sunset
            return not (sunrise <= now <= sunset)
            
        except Exception as e:
            logger.warning(f"Failed to determine day/night: {e}")
            return False
    
    def get_weather(self, airport_code: str, latitude: Optional[float] = None, 
                    longitude: Optional[float] = None) -> Dict:
        """
        Get current weather for an airport.
        
        Args:
            airport_code: IATA airport code
            latitude: Airport latitude (optional, will use fallback if not provided)
            longitude: Airport longitude (optional, will use fallback if not provided)
            
        Returns:
            Dictionary with weather data including theme information
        """
        # Get coordinates - always use real coordinates
        if latitude is None or longitude is None:
            coords = self.AIRPORT_COORDINATES.get(airport_code.upper())
            if coords:
                latitude = coords['latitude']
                longitude = coords['longitude']
            else:
                # Use a default location (Kansas, USA center) if airport not found
                latitude = 39.8283
                longitude = -98.5795
        
        try:
            params = {
                'latitude': latitude,
                'longitude': longitude,
                'current': 'temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,wind_direction_10m,is_day',
                'timezone': 'auto',
            }
            
            data = _http_get_json(self.BASE_URL, params=params, timeout=5)
            
            current = data.get('current', {})
            weather_code = current.get('weather_code', 0)
            is_day = current.get('is_day', 1) == 1
            
            # Determine if nighttime
            is_night = not is_day
            
            weather_info = self.WEATHER_CODES.get(int(weather_code), 
                                                   {'condition': 'Unknown', 'icon': 'question', 'theme': 'cloudy', 'night_icon': 'question'})
            
            # Select appropriate icon based on day/night
            icon = weather_info['night_icon'] if is_night else weather_info['icon']
            
            # Determine theme
            theme = weather_info.get('theme', 'cloudy')
            
            weather_data = {
                'temperature': round(current.get('temperature_2m', 59)),
                'condition': weather_info['condition'],
                'icon': icon,
                'theme': theme,
                'is_night': is_night,
                'wind_speed': round(current.get('wind_speed_10m', 5)),
                'humidity': round(current.get('relative_humidity_2m', 50)),
                'visibility': 10,  # Default visibility in miles
                'airport_code': airport_code,
                'source': 'Open-Meteo',
                'latitude': latitude,
                'longitude': longitude,
            }
            
            return weather_data
            
        except (urllib.error.URLError, urllib.error.HTTPError, ValueError) as e:
            logger.warning(f"Failed to fetch weather for {airport_code}: {e}")
            # Return minimal fallback with real coordinates still used
            return {
                'temperature': 59,  # Default moderate temperature
                'condition': 'Data Unavailable',
                'icon': 'cloud',
                'theme': 'cloudy',
                'is_night': False,
                'wind_speed': 5,
                'humidity': 50,
                'visibility': 10,
                'airport_code': airport_code,
                'source': 'offline',
                'latitude': latitude,
                'longitude': longitude,
            }
    
    def search_locations(self, query: str) -> list:
        """
        Search for locations by name.
        
        Args:
            query: Search query (city name, airport code, etc.)
            
        Returns:
            List of matching locations with coordinates
        """
        try:
            # Use Open-Meteo's geocoding API
            geocoding_url = "https://geocoding-api.open-meteo.com/v1/search"
            params = {
                'name': query,
                'count': 10,
                'language': 'en',
                'format': 'json',
            }
            
            data = _http_get_json(geocoding_url, params=params, timeout=5)
            
            results = data.get('results', [])
            locations = []
            
            for result in results:
                locations.append({
                    'name': result.get('name'),
                    'country': result.get('country', ''),
                    'admin1': result.get('admin1', ''),  # State/region
                    'latitude': result.get('latitude'),
                    'longitude': result.get('longitude'),
                    'elevation': result.get('elevation'),
                })
            
            return locations
            
        except (urllib.error.URLError, urllib.error.HTTPError, ValueError) as e:
            logger.warning(f"Failed to search locations: {e}")
            return []
    
    def get_weather_by_coordinates(self, latitude: float, longitude: float,
                                    location_name: str = "Location") -> Dict:
        """Get weather by specific coordinates - always fetches real data."""
        weather = self.get_weather(
            airport_code=location_name.replace(' ', '_'),
            latitude=latitude,
            longitude=longitude
        )
        # Add full location name field (don't truncate)
        weather['location_name'] = location_name
        return weather


# Singleton instance
weather_service = WeatherService()
