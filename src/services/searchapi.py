import requests
from flask import current_app
from config import Config

class SearchApiService:
    def __init__(self):
        self.api_key = Config.SEARCHAPI_API_KEY
        if not self.api_key:
            raise ValueError("SEARCHAPI_API_KEY is not set or not loaded correctly from .env file.")
        self.base_url = "https://www.searchapi.io/api/v1/search"

    # --- FUNGSI BARU UNTUK MENGAMBIL REVIEW DITAMBAHKAN DI SINI ---
    def get_reviews(self, place_id, max_reviews=30):
        """
        Mengambil daftar review dari SearchAPI dengan paginasi.
        """
        all_reviews = []
        params = {
            "api_key": self.api_key,
            "engine": "google_maps_reviews",
            "place_id": place_id,
            "hl": "en",
        }
        
        while len(all_reviews) < max_reviews:
            try:
                response = requests.get(self.base_url, params=params, timeout=45)
                if response.status_code != 200:
                    current_app.logger.error(f"SearchAPI (get_reviews) returned {response.status_code}: {response.text}")
                    break # Keluar dari loop jika ada error
                
                data = response.json()
                reviews_on_page = data.get("reviews", [])
                if not reviews_on_page:
                    break # Tidak ada review lagi

                all_reviews.extend(reviews_on_page)

                # Siapkan untuk halaman selanjutnya
                if "next_page_token" in data.get("pagination", {}):
                    params["next_page_token"] = data["pagination"]["next_page_token"]
                else:
                    break # Tidak ada halaman selanjutnya
            
            except requests.exceptions.RequestException as e:
                current_app.logger.error(f"SearchApi.io (get_reviews) request failed for {place_id}: {e}")
                break # Keluar dari loop jika ada error

        return all_reviews[:max_reviews]

    def get_keyword_match_count(self, place_id, keywords):
        """
        Menggunakan SearchApi.io untuk menemukan jumlah review yang cocok dengan keyword.
        """
        if not keywords or not place_id:
            return 0, 0

        search_query = keywords.split(",")[0].strip()
        params = {
            "api_key": self.api_key,
            "engine": "google_maps_reviews",  # Ensure this matches the SearchAPI.io documentation
            "place_id": place_id,
            "search_query": search_query,
            "hl": "en",
            "num": Config.SEARCHAPI_NUM_REVIEWS
        }
        try:
            response = requests.get(self.base_url, params=params, timeout=45)
            if response.status_code != 200:
                current_app.logger.error(f"SearchAPI (keyword_count) returned {response.status_code}: {response.text}")
                response.raise_for_status()
            data = response.json()
            matching_review_count = len(data.get("reviews", []))
            total_review_count = data.get("place_result", {}).get("reviews", 0)
            return matching_review_count, total_review_count
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"SearchApi.io (keyword_count) request failed for {place_id}: {e}")
            return -1, -1