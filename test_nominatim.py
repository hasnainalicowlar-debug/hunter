import requests

headers = {'User-Agent': 'PakistanFoodResearch/1.0 (info@pakistanfoodpos.org)'}
url = 'https://nominatim.openstreetmap.org/search'
params = {
    'q': 'restaurant in Lahore',
    'format': 'json',
    'limit': 10,
    'addressdetails': 1
}
try:
    r = requests.get(url, params=params, headers=headers, timeout=10)
    print("Nominatim status:", r.status_code)
    if r.status_code == 200:
        data = r.json()
        print(f"Results: {len(data)}")
        for item in data[:3]:
            print(item.get('display_name'), item.get('lat'), item.get('lon'))
except Exception as e:
    print("Error:", e)
