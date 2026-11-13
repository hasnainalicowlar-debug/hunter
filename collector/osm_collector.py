"""
OpenStreetMap / Nominatim Data Collector for Pakistan Food Service Businesses
Discovers verified food establishments across all Pakistani provinces, districts, and cities.
"""

import requests
import time
import json
import uuid
import re

HEADERS = {
    'User-Agent': 'PakistanFoodBusinessIntelligence/1.0 (Enterprise Research Platform; contact: info@pakistanfoodpos.org)'
}

CITY_TARGETS = [
    # Punjab
    {"city": "Lahore", "district": "Lahore", "province": "Punjab", "queries": ["restaurant in Lahore", "cafe in Lahore", "bakery in Lahore", "fast food in Lahore", "dhaba in Lahore", "pizza in Lahore"]},
    {"city": "Rawalpindi", "district": "Rawalpindi", "province": "Punjab", "queries": ["restaurant in Rawalpindi", "cafe in Rawalpindi", "bakery in Rawalpindi", "fast food in Rawalpindi"]},
    {"city": "Faisalabad", "district": "Faisalabad", "province": "Punjab", "queries": ["restaurant in Faisalabad", "cafe in Faisalabad", "bakery in Faisalabad"]},
    {"city": "Multan", "district": "Multan", "province": "Punjab", "queries": ["restaurant in Multan", "cafe in Multan", "bakery in Multan"]},
    {"city": "Gujranwala", "district": "Gujranwala", "province": "Punjab", "queries": ["restaurant in Gujranwala", "bakery in Gujranwala"]},
    {"city": "Sialkot", "district": "Sialkot", "province": "Punjab", "queries": ["restaurant in Sialkot", "cafe in Sialkot"]},
    {"city": "Murree", "district": "Murree", "province": "Punjab", "queries": ["restaurant in Murree", "cafe in Murree"]},
    {"city": "Bahawalpur", "district": "Bahawalpur", "province": "Punjab", "queries": ["restaurant in Bahawalpur"]},

    # Sindh
    {"city": "Karachi", "district": "Karachi South", "province": "Sindh", "queries": ["restaurant in Karachi", "cafe in Karachi", "bakery in Karachi", "fast food in Karachi", "dhaba in Karachi"]},
    {"city": "Hyderabad", "district": "Hyderabad", "province": "Sindh", "queries": ["restaurant in Hyderabad", "cafe in Hyderabad", "bakery in Hyderabad"]},
    {"city": "Sukkur", "district": "Sukkur", "province": "Sindh", "queries": ["restaurant in Sukkur", "cafe in Sukkur"]},

    # Islamabad Capital Territory
    {"city": "Islamabad", "district": "Islamabad", "province": "Islamabad Capital Territory", "queries": ["restaurant in Islamabad", "cafe in Islamabad", "bakery in Islamabad", "fast food in Islamabad"]},

    # Khyber Pakhtunkhwa
    {"city": "Peshawar", "district": "Peshawar", "province": "Khyber Pakhtunkhwa", "queries": ["restaurant in Peshawar", "cafe in Peshawar", "bakery in Peshawar", "fast food in Peshawar"]},
    {"city": "Abbottabad", "district": "Abbottabad", "province": "Khyber Pakhtunkhwa", "queries": ["restaurant in Abbottabad", "cafe in Abbottabad"]},
    {"city": "Mingora", "district": "Swat", "province": "Khyber Pakhtunkhwa", "queries": ["restaurant in Swat", "hotel in Swat"]},

    # Balochistan
    {"city": "Quetta", "district": "Quetta", "province": "Balochistan", "queries": ["restaurant in Quetta", "cafe in Quetta", "bakery in Quetta"]},
    {"city": "Gwadar", "district": "Gwadar", "province": "Balochistan", "queries": ["restaurant in Gwadar", "hotel in Gwadar"]},

    # Azad Jammu & Kashmir
    {"city": "Muzaffarabad", "district": "Muzaffarabad", "province": "Azad Jammu and Kashmir", "queries": ["restaurant in Muzaffarabad", "hotel in Muzaffarabad"]},
    {"city": "Mirpur", "district": "Mirpur", "province": "Azad Jammu and Kashmir", "queries": ["restaurant in Mirpur", "bakery in Mirpur"]},

    # Gilgit-Baltistan
    {"city": "Gilgit", "district": "Gilgit", "province": "Gilgit-Baltistan", "queries": ["restaurant in Gilgit", "hotel in Gilgit"]},
    {"city": "Skardu", "district": "Skardu", "province": "Gilgit-Baltistan", "queries": ["restaurant in Skardu", "hotel in Skardu"]},
    {"city": "Hunza", "district": "Hunza", "province": "Gilgit-Baltistan", "queries": ["restaurant in Hunza", "cafe in Hunza"]}
]

def map_category(query, display_name):
    lower_q = (query + " " + display_name).lower()
    if 'cafe' in lower_q or 'coffee' in lower_q or 'tea' in lower_q:
        return ('CAFE', 'Cafes & Coffee Shops')
    elif 'bakery' in lower_q or 'baker' in lower_q or 'cake' in lower_q:
        return ('BAKERY', 'Bakeries & Confectioneries')
    elif 'pizza' in lower_q:
        return ('PIZZA', 'Pizza Outlets & Pizzerias')
    elif 'burger' in lower_q or 'fast food' in lower_q or 'fried chicken' in lower_q or 'shawarma' in lower_q:
        return ('FAST_FOOD', 'Fast Food & QSR')
    elif 'dhaba' in lower_q or 'dhabba' in lower_q or 'chai' in lower_q:
        return ('DHABA', 'Dhabas & Highway Food Points')
    elif 'bbq' in lower_q or 'barbecue' in lower_q or 'sajji' in lower_q or 'tikka' in lower_q:
        return ('BBQ', 'BBQ & Sajji Outlets')
    elif 'sweet' in lower_q or 'halwa' in lower_q or 'mithai' in lower_q:
        return ('SWEETS', 'Sweet & Halwai Shops (Mithai)')
    elif 'hotel' in lower_q or 'resort' in lower_q or 'motel' in lower_q:
        return ('HOTEL_DINING', 'Hotels with Dining Services')
    elif 'ice cream' in lower_q or 'gelato' in lower_q:
        return ('ICE_CREAM', 'Ice Cream & Dessert Parlors')
    elif 'juice' in lower_q or 'shake' in lower_q:
        return ('JUICE_BAR', 'Juice Bars & Shake Corners')
    else:
        return ('RESTAURANT', 'Restaurants & Fine Dining')

def clean_business_name(raw_name):
    # Extract clean English and clean Urdu names
    parts = [p.strip() for p in raw_name.split(',') if p.strip()]
    if not parts:
        return "Food Establishment"
    name = parts[0]
    # Remove any stray prefix or street words if it caught road name first
    return name

def fetch_nominatim(query, limit=10):
    url = 'https://nominatim.openstreetmap.org/search'
    params = {
        'q': query,
        'format': 'json',
        'limit': limit,
        'addressdetails': 1
    }
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=12)
        if r.status_code == 200:
            return r.json()
        elif r.status_code == 429:
            print("Rate limited by Nominatim. Sleeping 5s...")
            time.sleep(5)
            return []
        else:
            print(f"Nominatim returned {r.status_code} for query: {query}")
            return []
    except Exception as e:
        print(f"Error querying {query}: {e}")
        return []

def collect_osm_data(max_targets=None):
    results = []
    targets = CITY_TARGETS if max_targets is None else CITY_TARGETS[:max_targets]
    
    print(f"Starting OSM Data Collection across {len(targets)} location centers...")
    for target in targets:
        city = target['city']
        district = target['district']
        province = target['province']
        
        for q in target['queries']:
            print(f"Querying: '{q}' in {city}, {province}...")
            items = fetch_nominatim(q, limit=6)
            for item in items:
                display_name = item.get('display_name', '')
                addr = item.get('address', {})
                
                # Check if it has a real name
                name = item.get('name') or addr.get('amenity') or addr.get('shop') or clean_business_name(display_name)
                if not name or name.lower() in ['restaurant', 'cafe', 'fast food', 'bakery', 'hotel']:
                    # Extract first segment of display name
                    name = display_name.split(',')[0].strip()
                
                lat = float(item.get('lat', 0.0))
                lon = float(item.get('lon', 0.0))
                osm_id = str(item.get('osm_id', ''))
                cat_code, cat_name = map_category(q, name + " " + display_name)
                
                # Generate Google Maps URL
                gmaps_url = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
                
                # Extract postal code, road, area
                postcode = addr.get('postcode', '')
                road = addr.get('road', '')
                suburb = addr.get('suburb', '') or addr.get('neighbourhood', '') or addr.get('quarter', '') or ''
                
                results.append({
                    'source': 'OpenStreetMap Nominatim',
                    'external_id': f"osm_{osm_id}",
                    'name': name,
                    'category_code': cat_code,
                    'category_name': cat_name,
                    'province': province,
                    'district': district,
                    'city': city,
                    'area': suburb or road or city,
                    'full_address': display_name,
                    'postal_code': postcode,
                    'latitude': lat,
                    'longitude': lon,
                    'google_maps_url': gmaps_url,
                    'osm_type': item.get('osm_type', 'node')
                })
            # Respect Nominatim 1 query per second usage policy
            time.sleep(1.2)
            
    print(f"Discovered {len(results)} raw establishments via OpenStreetMap.")
    return results

if __name__ == '__main__':
    data = collect_osm_data(max_targets=4)
    print(f"Sample items: {len(data)}")
    if data:
        print(json.dumps(data[0], indent=2))
