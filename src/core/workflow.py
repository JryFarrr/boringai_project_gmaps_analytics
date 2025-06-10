from .finder import Finder
from .analyzer import Analyzer
from ..utils.validators import validate_payload

class Workflow:
    def __init__(self):
        self.finder = Finder()
        self.analyzer = Analyzer()

    def start(self, params):
        """Menginisialisasi state dari parameter plain JSON."""
        validation_error = validate_payload(params, ["business_type", "location", "numberOfLeads"])
        if validation_error:
            raise ValueError(validation_error)

        constraints = {
            "min_rating": params.get("min_rating"), "min_reviews": params.get("min_reviews"),
            "max_reviews": params.get("max_reviews"), "price_range": params.get("price_range"),
            "keywords": params.get("keywords"), "business_hours": params.get("business_hours", "anytime"),
        }
        initial_state = {
            "business_type": params["business_type"], "location": params["location"],
            "numberOfLeads": params["numberOfLeads"], "leadCount": 0, "searchOffset": 0,
            "remainingPlaceIds": [], "constraints": constraints,
            "nextPageToken": None  # Inisialisasi nextPageToken
        }
        return {
            "state": initial_state,
            "next": {
                "key": "search",
                "payload": { # Payload untuk search pertama kali
                    "business_type": "$state.business_type", "location": "$state.location",
                    "searchOffset": "$state.searchOffset", "constraints": "$state.constraints",
                    "nextPageToken": "$state.nextPageToken"
                }
            },
            "result": None, "done": False, "error": None
        }

    def search(self, params):
        """Menerima parameter pencarian, mengelola paginasi dan offset dengan benar."""
        # Finder akan menggunakan 'nextPageToken' dari params untuk paginasi
        place_ids, new_next_page_token = self.finder.find_business_ids(params)

        if not place_ids:
            return {"done": True, "error": "No new businesses found.", "state": None, "result": None, "next": None}
        
        # --- PERBAIKAN LOGIKA ---
        # 1. Update searchOffset dengan benar
        current_offset = params.get('searchOffset', 0)
        new_offset = current_offset + len(place_ids)

        # 2. Ambil satu ID untuk di-scrape, sisanya simpan di state
        next_place_to_scrape = place_ids.pop(0)
        
        return {
            "state": {
                "remainingPlaceIds": place_ids, # Hanya berisi sisa ID dari pencarian ini
                "searchOffset": new_offset,      # Akumulasi total ID yang ditemukan
                "nextPageToken": new_next_page_token # Simpan token baru untuk pencarian berikutnya
            },
            "next": {
                "key": "scrape",
                "payload": {"placeId": next_place_to_scrape, "constraints": "$state.constraints"}
            },
            "result": None, "done": False, "error": None
        }

    def scrape(self, params):
        """Menerima placeId dan constraints dalam plain JSON."""
        place_id = params['placeId']
        constraints = params.get('constraints', {})
        details = self.finder.get_business_details(place_id, constraints)

        if not details:
            return {
                "state": None,
                "next": {
                    "key": "control", "payload": { "state": "$state" }
                },
                "result": None, "done": False, "error": f"Failed to scrape details for placeId: {place_id}"
            }

        return {
            "state": None,
            "next": {
                "key": "analyze",
                "payload": {
                    "placeDetails": details, "leadCount": "$state.leadCount", "constraints": "$state.constraints"
                }
            },
            "result": None, "done": False, "error": None
        }

    def analyze(self, params):
        """Menerima detail tempat dalam plain JSON."""
        details = params['placeDetails']
        constraints = params.get('constraints', {})
        analysis_result = self.analyzer.run(details, constraints)
        
        return {
            "state": {"leadCount": params.get('leadCount', 0) + 1},
            "result": analysis_result,
            "next": { "key": "control", "payload": {"state": "$state"} },
            "done": False, "error": None
        }

    def control(self, params):
        """Menerima parameter kontrol (bagian dari state) dalam plain JSON."""
        # --- PERBAIKAN: Menggunakan `params` secara langsung ---
        if params['leadCount'] >= params['numberOfLeads']:
            return {"state": None, "next": None, "result": None, "done": True, "error": None}

        if params.get('remainingPlaceIds'):
            remaining_ids = params['remainingPlaceIds']
            next_place_id = remaining_ids.pop(0)
            return {
                "state": {"remainingPlaceIds": remaining_ids},
                "next": {
                    "key": "scrape",
                    "payload": {"placeId": next_place_id, "constraints": "$state.constraints"}
                },
                "result": None, "done": False, "error": None
            }
        else:
            return {
                "state": None,
                "next": {
                    "key": "search",
                    "payload": {
                        "business_type": "$state.business_type", "location": "$state.location",
                        "searchOffset": "$state.searchOffset", "constraints": "$state.constraints",
                        "nextPageToken": "$state.nextPageToken"
                    }
                },
                "result": None, "done": False, "error": None
            }