import requests
from flask import current_app
from config import Config

class SearchApiService:
    def __init__(self):
        self.api_key = Config.SEARCHAPI_API_KEY
        if not self.api_key:
            raise ValueError("SEARCHAPI_API_KEY is not set or not loaded correctly from .env file.")
        self.base_url = "https://www.searchapi.io/api/v1/search"

    def get_reviews(self, place_id, max_reviews=None):
        if max_reviews is None:
            max_reviews = Config.DEFAULT_MAX_REVIEWS
        all_reviews = []
        params = {
            "api_key": self.api_key, "engine": "google_maps_reviews",
            "place_id": place_id, "hl": "en",
        }
        while len(all_reviews) < max_reviews:
            try:
                response = requests.get(self.base_url, params=params, timeout=45)
                if response.status_code != 200: break
                data = response.json()
                reviews_on_page = data.get("reviews", [])
                if not reviews_on_page: break
                all_reviews.extend(reviews_on_page)
                if "next_page_token" in data.get("pagination", {}):
                    params["next_page_token"] = data["pagination"]["next_page_token"]
                else: break
            except requests.exceptions.RequestException as e:
                current_app.logger.error(f"SearchApi.io (get_reviews) failed: {e}")
                break
        return all_reviews[:max_reviews]

    def get_keyword_match_count(self, place_id, keywords):
        if not keywords or not place_id:
            return 0, {}
        search_query = keywords.split(",")[0].strip()
        params = {
            "api_key": self.api_key, "engine": "google_maps_reviews",
            "place_id": place_id, "search_query": search_query,
            "hl": "en", "num": Config.SEARCHAPI_NUM_REVIEWS
        }
        try:
            response = requests.get(self.base_url, params=params, timeout=45)
            if response.status_code != 200:
                response.raise_for_status()
            data = response.json()
            matching_review_count = len(data.get("reviews", []))
            # --- PERBAIKAN: Kembalikan seluruh objek 'place_result' ---
            place_result_obj = data.get("place_result", {})
            return matching_review_count, place_result_obj
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"SearchApi.io (keyword_count) failed: {e}")
            return -1, {}