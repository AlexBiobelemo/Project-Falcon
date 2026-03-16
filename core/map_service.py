"""Map service for airport visualization.

This module provides map data for flights, gates, and airport facilities.
"""

import json
from typing import Dict, List, Optional
from django.core.cache import cache
from .models import Airport, Gate, Flight
from django.utils import timezone
from datetime import timedelta


class MapService:
    """Service for generating map visualization data."""
    
    # Default map center (US)
    DEFAULT_CENTER = {'latitude': 39.8283, 'longitude': -98.5795}
    DEFAULT_ZOOM = 4
    
    # Airport coordinates database (expanded)
    AIRPORT_DATA = {
        'ATL': {'lat': 33.6407, 'lng': -84.4277, 'name': 'Hartsfield-Jackson Atlanta'},
        'LAX': {'lat': 33.9416, 'lng': -118.4085, 'name': 'Los Angeles International'},
        'ORD': {'lat': 41.9742, 'lng': -87.9073, 'name': "O'Hare International"},
        'DFW': {'lat': 32.8998, 'lng': -97.0403, 'name': 'Dallas/Fort Worth'},
        'DEN': {'lat': 39.8561, 'lng': -104.6737, 'name': 'Denver International'},
        'JFK': {'lat': 40.6413, 'lng': -73.7781, 'name': 'John F. Kennedy International'},
        'SFO': {'lat': 37.6213, 'lng': -122.3790, 'name': 'San Francisco International'},
        'LAS': {'lat': 36.0840, 'lng': -115.1537, 'name': 'Harry Reid International'},
        'SEA': {'lat': 47.4502, 'lng': -122.3088, 'name': 'Seattle-Tacoma'},
        'MIA': {'lat': 25.7959, 'lng': -80.2870, 'name': 'Miami International'},
        'BOS': {'lat': 42.3656, 'lng': -71.0096, 'name': "Logan International"},
        'PHX': {'lat': 33.4373, 'lng': -112.0078, 'name': 'Phoenix Sky Harbor'},
        'IAH': {'lat': 29.9902, 'lng': -95.3368, 'name': 'George Bush Intercontinental'},
        'MCO': {'lat': 28.4312, 'lng': -81.3081, 'name': 'Orlando International'},
        'EWR': {'lat': 40.6895, 'lng': -74.1745, 'name': 'Newark Liberty'},
        'LHR': {'lat': 51.4700, 'lng': -0.4543, 'name': 'London Heathrow'},
        'CDG': {'lat': 49.0097, 'lng': 2.5479, 'name': 'Charles de Gaulle'},
        'FRA': {'lat': 50.0379, 'lng': 8.5622, 'name': 'Frankfurt'},
        'AMS': {'lat': 52.3105, 'lng': 4.7683, 'name': 'Amsterdam Schiphol'},
        'DXB': {'lat': 25.2532, 'lng': 55.3657, 'name': 'Dubai International'},
        'HND': {'lat': 35.5494, 'lng': 139.7798, 'name': 'Tokyo Haneda'},
        'SIN': {'lat': 1.3644, 'lng': 103.9915, 'name': 'Singapore Changi'},
        'ICN': {'lat': 37.4602, 'lng': 126.4407, 'name': 'Incheon International'},
        'LOS': {'lat': 6.5774, 'lng': 3.3212, 'name': "Murtala Muhammed"},
        'ABV': {'lat': 9.0068, 'lng': 7.2632, 'name': 'Nnamdi Azikiwe'},
        'PHC': {'lat': 5.0155, 'lng': 6.9496, 'name': 'Port Harcourt'},
        'KAN': {'lat': 11.9581, 'lng': 8.5247, 'name': 'Mallam Aminu Kano'},
    }
    
    def get_airport_coordinates(self, airport_code: str) -> Dict:
        """Get coordinates for an airport."""
        code = airport_code.upper()
        
        # Check if we have it in our database
        if code in self.AIRPORT_DATA:
            return self.AIRPORT_DATA[code]
        
        # Try to get from Django model
        try:
            airport = Airport.objects.get(code=code)
            if airport.latitude and airport.longitude:
                return {
                    'lat': float(airport.latitude),
                    'lng': float(airport.longitude),
                    'name': airport.name,
                }
        except Airport.DoesNotExist:
            pass
        
        # Return None if not found
        return None
    
    def get_active_flights(self, airport_code: Optional[str] = None) -> List[Dict]:
        """
        Get active flights for map display.
        
        Args:
            airport_code: Optional airport code to filter by
            
        Returns:
            List of flight data with position information
        """
        cache_key = f"map_flights_{airport_code or 'all'}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        now = timezone.now()
        today = now.date()
        
        # Get flights for today
        flights_qs = Flight.objects.filter(
            scheduled_departure__date=today
        ).select_related('gate')
        
        if airport_code:
            flights_qs = flights_qs.filter(
                Q(origin=airport_code) | Q(destination=airport_code)
            )
        
        flights_data = []
        for flight in flights_qs:
            # Get origin and destination coordinates
            origin_data = self.get_airport_coordinates(flight.origin)
            dest_data = self.get_airport_coordinates(flight.destination)
            
            if not origin_data or not dest_data:
                continue
            
            # Calculate flight progress
            status_color = self._get_status_color(flight.status)
            
            flight_data = {
                'id': flight.id,
                'flight_number': flight.flight_number,
                'origin': flight.origin,
                'destination': flight.destination,
                'status': flight.status,
                'status_color': status_color,
                'origin_coords': {'lat': origin_data['lat'], 'lng': origin_data['lng']},
                'dest_coords': {'lat': dest_data['lat'], 'lng': dest_data['lng']},
                'gate': flight.gate.gate_id if flight.gate else None,
                'scheduled_departure': flight.scheduled_departure.isoformat(),
                'scheduled_arrival': flight.scheduled_arrival.isoformat(),
            }
            
            # Calculate current position for en-route flights
            if flight.status in ['departed', 'arrived', 'delayed']:
                flight_data['current_position'] = self._calculate_flight_position(
                    origin_data, dest_data, flight.status, flight.scheduled_departure,
                    flight.scheduled_arrival
                )
            
            flights_data.append(flight_data)
        
        cache.set(cache_key, flights_data, 60)  # Cache for 1 minute
        return flights_data
    
    def _calculate_flight_position(self, origin: Dict, dest: Dict, status: str,
                                    departure_time, arrival_time) -> Dict:
        """Calculate approximate flight position based on status and times."""
        now = timezone.now()
        
        # Make times timezone-aware if naive
        if departure_time.tzinfo is None:
            departure_time = timezone.make_aware(departure_time)
        if arrival_time.tzinfo is None:
            arrival_time = timezone.make_aware(arrival_time)
        
        total_duration = (arrival_time - departure_time).total_seconds()
        elapsed = (now - departure_time).total_seconds()
        
        if status == 'arrived' or elapsed >= total_duration:
            return {'lat': dest['lat'], 'lng': dest['lng']}
        
        if status == 'scheduled' or elapsed <= 0:
            return {'lat': origin['lat'], 'lng': origin['lng']}
        
        # Calculate progress (0 to 1)
        progress = min(max(elapsed / total_duration, 0), 1)
        
        # Interpolate position
        lat = origin['lat'] + (dest['lat'] - origin['lat']) * progress
        lng = origin['lng'] + (dest['lng'] - origin['lng']) * progress
        
        return {'lat': lat, 'lng': lng}
    
    def _get_status_color(self, status: str) -> str:
        """Get map marker color based on flight status."""
        colors = {
            'scheduled': '#6c757d',  # Gray
            'boarding': '#0d6efd',   # Blue
            'departed': '#198754',   # Green
            'arrived': '#0dcaf0',    # Cyan
            'delayed': '#ffc107',    # Yellow
            'cancelled': '#dc3545',  # Red
        }
        return colors.get(status, '#6c757d')
    
    def get_gates_data(self, airport_code: Optional[str] = None) -> List[Dict]:
        """Get gates data for map display."""
        gates = Gate.objects.all().order_by('terminal', 'gate_id')
        
        gates_data = []
        for gate in gates:
            gates_data.append({
                'id': gate.id,
                'gate_id': gate.gate_id,
                'terminal': gate.terminal,
                'status': gate.status,
                'capacity': gate.capacity,
                'color': self._get_gate_color(gate.status),
            })
        
        return gates_data
    
    def _get_gate_color(self, status: str) -> str:
        """Get gate marker color based on status."""
        colors = {
            'available': '#198754',      # Green
            'occupied': '#ffc107',       # Yellow
            'maintenance': '#dc3545',    # Red
            'closed': '#6c757d',         # Gray
        }
        return colors.get(status.lower(), '#6c757d')
    
    def get_airports_data(self) -> List[Dict]:
        """Get all airports data for map display."""
        airports = Airport.objects.filter(is_active=True)
        
        airports_data = []
        for airport in airports:
            coords = self.get_airport_coordinates(airport.code)
            if not coords:
                coords = {'lat': 39.8283, 'lng': -98.5795}  # Default to US center
            
            airports_data.append({
                'code': airport.code,
                'name': airport.name,
                'city': airport.city,
                'lat': coords['lat'],
                'lng': coords['lng'],
                'is_active': airport.is_active,
            })
        
        return airports_data
    
    def get_map_config(self) -> Dict:
        """Get map configuration."""
        return {
            'center': self.DEFAULT_CENTER,
            'zoom': self.DEFAULT_ZOOM,
            'min_zoom': 2,
            'max_zoom': 18,
            'tile_layer': 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
            'attribution': '© OpenStreetMap contributors',
        }


# Singleton instance
map_service = MapService()
