import requests
import json

headers = {'User-Agent': 'PakistanFoodIntelPlatform/1.0'}
# Bounding box for Lahore: 31.40, 74.20 to 31.65, 74.45
query = """
[out:json][timeout:25];
(
  node["amenity"~"restaurant|cafe|fast_food"](31.45,74.25,31.60,74.40);
);
out 10;
"""
try:
    r = requests.post('https://overpass-api.de/api/interpreter', data={'data': query}, headers=headers, timeout=20)
    print("Status:", r.status_code)
    data = r.json()
    elements = data.get('elements', [])
    print(f"Found {len(elements)} elements in sample box")
    for el in elements[:3]:
        print(el.get('tags', {}).get('name'), el.get('tags', {}).get('amenity'), el.get('lat'), el.get('lon'))
except Exception as e:
    print("Error:", e)
