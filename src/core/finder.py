from ..services.gmaps import GmapsService
from ..utils.formatter import Formatter

class Finder:
    """
    Menemukan dan mengambil data bisnis dari sumber eksternal.
    """
    def __init__(self):
        self.gmaps = GmapsService()
        self.formatter = Formatter()

    def find_business_ids(self, state):
        """Mencari bisnis dan mengembalikan daftar Place ID."""
        query = f"{state['business_type']} in {state['location']}"
        results, next_page_token = self.gmaps.text_search(query, page_token=state.get('nextPageToken'))
        
        place_ids = [place['place_id'] for place in results]
        return place_ids, next_page_token

    def get_business_details(self, place_id):
        """Mengambil dan memformat detail untuk satu bisnis."""
        raw_details = self.gmaps.get_place_details(place_id)
        if not raw_details:
            return None
            
        reviews_data = self.gmaps.get_reviews_from_searchapi(place_id)
        raw_details['reviews_from_searchapi'] = reviews_data
        
        return self.formatter.format_place_details(raw_details)