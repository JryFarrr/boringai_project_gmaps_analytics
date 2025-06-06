import requests
from flask import current_app
from config import Config # <-- Import Config

class SearchApiService:
    def __init__(self):
        self.api_key = Config.SEARCHAPI_API_KEY
        if not self.api_key:
            raise ValueError("SEARCHAPI_API_KEY is not set or not loaded correctly from .env file.")
        self.base_url = "https://www.searchapi.io/api/v1/search"

    def get_keyword_match_count(self, place_id, keywords):
        if not keywords or not place_id:
            return 0, 0

        search_query = keywords.split(",")[0].strip()
        params = {
            "api_key": self.api_key,
            "engine": "google_maps_reviews",  # Ensure this matches the SearchAPI.io documentation
            "place_id": place_id,
            "search_query": search_query,
            "hl": "en",
            # --- PENYESUAIAN: Menggunakan nilai dari config ---
            "num": Config.SEARCHAPI_NUM_REVIEWS
        }
        try:
            response = requests.get(self.base_url, params=params, timeout=45)
            if response.status_code != 200:
                current_app.logger.error(f"SearchAPI.io returned non-200 status: {response.status_code}")
                current_app.logger.error(f"RESPONSE BODY: {response.text}")
                response.raise_for_status()
            data = response.json()
            matching_review_count = len(data.get("reviews", []))
            total_review_count = data.get("place_result", {}).get("reviews", 0)
            return matching_review_count, total_review_count
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"SearchApi.io request failed for place_id {place_id}. Exception: {e}")
            return -1, -1