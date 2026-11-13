"""
Intelligent Deduplication & Branch Distinction Engine
Prevents duplicate outlet records while properly preserving separate physical branches of the same brand.
"""

import re
import math

def normalize_text(text):
    if not text:
        return ""
    # Lowercase, strip non-alphanumeric except spaces
    cleaned = re.sub(r'[^a-zA-Z0-9\s]', ' ', text.lower())
    return " ".join(cleaned.split())

normalize_name = normalize_text

def normalize_phone(phone):
    if not phone:
        return ""
    # Extract digits only
    digits = re.sub(r'\D', '', phone)
    # If starts with 0092, strip to 92
    if digits.startswith('0092'):
        digits = '92' + digits[4:]
    elif digits.startswith('0'):
        digits = '92' + digits[1:]
    return digits

def calculate_distance_km(lat1, lon1, lat2, lon2):
    if not lat1 or not lon1 or not lat2 or not lon2:
        return 9999.0
    R = 6371.0 # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def is_duplicate_outlet(existing_outlet, new_outlet):
    """
    Checks if new_outlet is an exact duplicate of existing_outlet.
    Returns (is_duplicate, reason)
    Note: If it's a different branch (e.g. different city, or distance > 500m, or different branch name),
    it is NOT a duplicate.
    """
    # 1. Exact external ID match (e.g. same OSM node)
    if existing_outlet.get('external_id') and existing_outlet.get('external_id') == new_outlet.get('external_id'):
        return True, "Identical external source ID"

    norm_name1 = normalize_text(existing_outlet.get('name', ''))
    norm_name2 = normalize_text(new_outlet.get('name', ''))
    
    # Check phone match
    phone1 = normalize_phone(existing_outlet.get('phone', ''))
    phone2 = normalize_phone(new_outlet.get('phone', ''))
    
    same_phone = (phone1 and phone2 and phone1 == phone2)

    # Coordinates distance
    lat1, lon1 = existing_outlet.get('latitude'), existing_outlet.get('longitude')
    lat2, lon2 = new_outlet.get('latitude'), new_outlet.get('longitude')
    dist = calculate_distance_km(lat1, lon1, lat2, lon2)

    # Same city check
    city1 = normalize_text(existing_outlet.get('city', ''))
    city2 = normalize_text(new_outlet.get('city', ''))
    same_city = (city1 and city2 and city1 == city2)

    # If different cities, they are distinct branches, NOT duplicates
    if city1 and city2 and city1 != city2:
        return False, "Different cities (Separate physical branches)"

    # If within 50 meters and same name -> Duplicate
    if norm_name1 == norm_name2 and dist < 0.05:
        return True, f"Identical name and coordinates within 50 meters ({dist*1000:.1f}m)"

    # If same phone and same name in same city -> Duplicate
    if same_phone and (norm_name1 in norm_name2 or norm_name2 in norm_name1) and dist < 0.2:
        return True, "Identical phone number and business name at same location"

    return False, "Unique outlet"
