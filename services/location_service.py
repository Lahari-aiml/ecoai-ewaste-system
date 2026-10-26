"""
EcoAI Location Service
Implements the Haversine formula for spherical distance calculations,
spatial provider filtering, and city coordinate lookups.
"""

import math
from database.db import query_db
from config import Config

# Standard coordinate reference for Indian metropolitan areas (fallback when GPS is denied)
CITY_COORDINATES = {
    'bengaluru': {'lat': 12.9716, 'lon': 77.5946, 'name': 'Bengaluru'},
    'bangalore': {'lat': 12.9716, 'lon': 77.5946, 'name': 'Bengaluru'},
    'hyderabad': {'lat': 17.3850, 'lon': 78.4867, 'name': 'Hyderabad'},
    'delhi': {'lat': 28.6139, 'lon': 77.2090, 'name': 'New Delhi'},
    'new delhi': {'lat': 28.6139, 'lon': 77.2090, 'name': 'New Delhi'},
    'noida': {'lat': 28.5355, 'lon': 77.3910, 'name': 'Noida'},
    'mumbai': {'lat': 19.0760, 'lon': 72.8777, 'name': 'Mumbai'},
    'chennai': {'lat': 13.0827, 'lon': 80.2707, 'name': 'Chennai'},
    'pune': {'lat': 18.5204, 'lon': 73.8567, 'name': 'Pune'},
    'kolkata': {'lat': 22.5726, 'lon': 88.3639, 'name': 'Kolkata'},
    'ahmedabad': {'lat': 23.0225, 'lon': 72.5714, 'name': 'Ahmedabad'},
    'jaipur': {'lat': 26.9124, 'lon': 75.7873, 'name': 'Jaipur'}
}

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth in kilometers
    using the Haversine formula.
    """
    R = 6371.0  # Earth's mean radius in kilometers

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)

    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    distance = R * c
    return round(distance, 2)

def get_city_coordinates(city_name: str):
    """Return fallback coordinates for a given city string, or None if unknown."""
    if not city_name:
        return None
    key = city_name.strip().lower()
    return CITY_COORDINATES.get(key)

def find_nearby_providers(user_lat: float, user_lon: float, category_id=None, radius_km=25.0, limit=5, only_active=True):
    """
    Find nearest matching active service providers within radius_km.
    Computes distance using the Haversine formula in Python.
    """
    radius = float(radius_km) if radius_km else Config.DEFAULT_RADIUS_KM

    # Query providers
    sql = """
        SELECT p.id, p.name, p.category_id, p.phone, p.email, p.address, p.city,
               p.latitude, p.longitude, p.offers_pickup, p.is_active, p.verification_status,
               c.category_name, c.badge_color, c.icon
        FROM service_providers p
        JOIN categories c ON p.category_id = c.id
        WHERE 1=1
    """
    params = []
    if only_active:
        sql += " AND p.is_active = 1"
    if category_id:
        sql += " AND p.category_id = ?"
        params.append(int(category_id))

    providers = query_db(sql, tuple(params))
    results = []

    for p in providers:
        try:
            plat = float(p['latitude'])
            plon = float(p['longitude'])
            dist = haversine(user_lat, user_lon, plat, plon)
            p_dict = dict(p)
            p_dict['distance_km'] = dist
            p_dict['distance_formatted'] = f"{dist:.1f} km"
            p_dict['offers_pickup_bool'] = bool(p['offers_pickup'])
            results.append(p_dict)
        except (ValueError, TypeError):
            continue

    # Sort ascending by distance
    results.sort(key=lambda x: x['distance_km'])

    # Filter by radius
    filtered_within_radius = [p for p in results if p['distance_km'] <= radius]

    # Return top 'limit' providers
    return {
        'providers': filtered_within_radius[:limit],
        'total_found_in_radius': len(filtered_within_radius),
        'radius_km': radius,
        'user_location': {'lat': user_lat, 'lon': user_lon},
        'all_closest': results[:limit] # Useful fallback if nothing is within radius
    }
