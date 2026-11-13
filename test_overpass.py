import requests
import json

headers = {'User-Agent': 'PakistanFoodIntelPlatform/1.0 (contact: info@foodpos.pk)'}
# Query a major city box or area: Karachi, Lahore, Islamabad, etc.
# Overpass interpreter endpoints:
mirrors = [
    'https://overpass-api.de/api/interpreter',
    'https://maps.mail.ru/osm/tools/overpass/api/interpreter',
    'https://overpass.kumi.systems/api/interpreter'
]

query = """
[out:json][timeout:30];
area["name"="Pakistan"]->.pk;
(
  node["amenity"="restaurant"](area.pk);
);
out count;
"""

for mirror in mirrors:
    try:
        print(f"Testing {mirror}...")
        r = requests.post(mirror, data={'data': query}, headers=headers, timeout=15)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            print("Response:", r.text[:200])
            break
    except Exception as e:
        print(f"Error {mirror}: {e}")
