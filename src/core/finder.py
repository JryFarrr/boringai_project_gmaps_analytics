from ..services.gmaps import GmapsService
from ..services.searchapi import SearchApiService
from ..utils.formatter import Formatter

class Finder:
    def __init__(self):
        self.gmaps = GmapsService()
        self.searchapi = SearchApiService()
        self.formatter = Formatter()

    def find_business_ids(self, state):
        query = f"{state['business_type']} in {state['location']}"
        results, next_page_token = self.gmaps.text_search(query, page_token=state.get('nextPageToken'))
        return [place['place_id'] for place in results], next_page_token

    # Menerima constraints untuk bisa mengambil keywords
    def get_business_details(self, place_id, constraints):
        raw_details = self.gmaps.get_place_details(place_id)
        if not raw_details:
            return None
            
        # 1. Ambil daftar teks review
        reviews_data = self.searchapi.get_reviews(place_id)
        
        # 2. Ambil hasil pencarian keyword (yang berisi histogram)
        keywords = constraints.get("keywords", "")
        keyword_match_n, place_result = self.searchapi.get_keyword_match_count(place_id, keywords)

        # 3. Teruskan semua data yang relevan ke Formatter
        return self.formatter.format_place_details(
            details=raw_details,
            all_reviews=reviews_data,
            keyword_n=keyword_match_n,
            place_result=place_result
        )