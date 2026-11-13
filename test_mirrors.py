import requests

mirrors = [
    'https://overpass.kumi.systems/api/interpreter',
    'https://maps.mail.ru/osm/tools/overpass/api/interpreter',
    'https://overpass.private.coffee/api/interpreter',
    'https://overpass-api.de/api/interpreter'
]

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
query = """
[out:json][timeout:15];
(
  node["amenity"="restaurant"](31.50,74.30,31.55,74.35);
);
out 5;
"""

for m in mirrors:
    try:
        r = requests.post(m, data={'data': query}, headers=headers, timeout=8)
        print(m, r.status_code)
        if r.status_code == 200:
            print("Success!", len(r.json().get('elements', [])))
            break
    except Exception as e:
        print(m, "Failed:", e)
