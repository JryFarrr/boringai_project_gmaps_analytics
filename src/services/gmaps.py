import requests
from config import Config

class GmapsService:
    def __init__(self):
        self.gmaps_key = Config.Maps_API_KEY
        self.searchapi_key = Config.SEARCHAPI_API_KEY
        if not self.gmaps_key: raise ValueError("Maps_API_KEY is not set. Please check your .env file.")
        if not self.searchapi_key: raise ValueError("SEARCHAPI_API_KEY is not set. Please check your .env file.")
        self.gmaps_search_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        self.gmaps_details_url = "https://maps.googleapis.com/maps/api/place/details/json"
        self.searchapi_url = "https://www.searchapi.io/api/v1/search"

    def text_search(self, query, page_token=None):
        params = {'key': self.gmaps_key, 'language': 'id'}
        if page_token: params['pagetoken'] = page_token
        else: params['query'] = query
        response = requests.get(self.gmaps_search_url, params=params)
        response.raise_for_status()
        data = response.json()
        if data['status'] not in ('OK', 'ZERO_RESULTS'): raise Exception(f"Google API Error: {data.get('error_message', data['status'])}")
        return data.get('results', []), data.get('next_page_token')

    def get_place_details(self, place_id):
        params = {"place_id": place_id, "key": self.gmaps_key, "fields": "place_id,name,formatted_address,formatted_phone_number,website,rating,user_ratings_total,price_level,opening_hours,types", "language": "id"}
        response = requests.get(self.gmaps_details_url, params=params)
        response.raise_for_status()
        data = response.json()
        if data['status'] != "OK": raise Exception(f"Google Details Error: {data.get('error_message', data['status'])}")
        return data.get("result", {})

    def get_reviews_from_searchapi(self, place_id):
        params = {"engine": "Maps_reviews", "place_id": place_id, "api_key": self.searchapi_key, "hl": "id"}
        try:
            response = requests.get(self.searchapi_url, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get('reviews', [])
        except requests.RequestException: return []