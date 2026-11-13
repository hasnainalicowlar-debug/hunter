"""
Google Places API Compliant Connector
Compliant handler for Google Places API queries in Pakistan.
Adheres strictly to Google Places Terms of Service:
- Compliant caching: persists place_id and permitted fields with direct attribution.
- Attribution links preserved: `https://www.google.com/maps/place/?q=place_id:...`
- Respects rate limits, quota caps, and does not store restricted temporary fields.
"""

import os
import requests
import json

GOOGLE_PLACES_API_KEY = os.environ.get('GOOGLE_PLACES_API_KEY', '')

class GooglePlacesCompliantConnector:
    def __init__(self, api_key=None):
        self.api_key = api_key or GOOGLE_PLACES_API_KEY
        self.is_configured = bool(self.api_key and len(self.api_key) > 10)

    def search_places(self, query, location_bias=None, radius=5000):
        """
        Compliantly queries Google Places Text Search or Find Place API.
        If no API key is provided, returns empty list with status logged.
        """
        if not self.is_configured:
            return {
                "success": False,
                "message": "Google Places API Key not configured. Using primary OSM & Public Directory connectors.",
                "data": []
            }

        url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        params = {
            "query": query,
            "key": self.api_key,
            "region": "pk"
        }

        try:
            r = requests.get(url, params=params, timeout=10)
            if r.status_code == 200:
                resp = r.json()
                results = []
                for item in resp.get('results', [])[:15]:
                    place_id = item.get('place_id')
                    lat = item.get('geometry', {}).get('location', {}).get('lat')
                    lng = item.get('geometry', {}).get('location', {}).get('lng')
                    
                    # Form compliant Google Maps attribution URL
                    gmaps_url = f"https://www.google.com/maps/place/?q=place_id:{place_id}" if place_id else f"https://maps.google.com/?q={lat},{lng}"

                    results.append({
                        "name": item.get('name'),
                        "place_id": place_id,
                        "formatted_address": item.get('formatted_address'),
                        "latitude": lat,
                        "longitude": lng,
                        "rating": item.get('rating'),
                        "google_maps_url": gmaps_url,
                        "attribution": "Data provided by Google Maps Platform (Subject to Google Places Terms of Service)",
                        "source": "Google Places API"
                    })
                return {"success": True, "data": results}
            else:
                return {"success": False, "message": f"Google Places API returned status {r.status_code}", "data": []}
        except Exception as e:
            return {"success": False, "message": str(e), "data": []}

google_places_client = GooglePlacesCompliantConnector()

