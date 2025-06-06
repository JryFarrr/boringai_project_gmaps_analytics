from .finder import Finder
from .analyzer import Analyzer
from ..utils.validators import validate_payload

class Workflow:
    def __init__(self):
        self.finder = Finder()
        self.analyzer = Analyzer()
    def start(self, params):
        validation_error = validate_payload(params, ["business_type", "location", "numberOfLeads"])
        if validation_error: raise ValueError(validation_error)
        initial_state = {
            "business_type": params["business_type"], "location": params["location"],
            "numberOfLeads": params["numberOfLeads"],
            "constraints": {
                "min_rating": params.get("min_rating"), "min_reviews": params.get("min_reviews"),
                "max_reviews": params.get("max_reviews"), "price_range": params.get("price_range"),
                "keywords": params.get("keywords"), "business_hours": params.get("business_hours", "anytime"),
            },
            "leadCount": 0, "searchOffset": 0, "remainingPlaceIds": [], "skippedCount": 0
        }
        return {"state": initial_state, "next": {"key": "search", "payload": {"state": "$state"}}}
    def search(self, payload):
        state = payload['state']
        place_ids, next_page_token = self.finder.find_business_ids(state)
        if not place_ids and not state.get('remainingPlaceIds'):
            return {"done": True, "error": "No businesses found matching criteria.", "state": state, "result": None}
        state['remainingPlaceIds'].extend(place_ids)
        state['nextPageToken'] = next_page_token
        return {"state": state, "next": {"key": "control", "payload": {"state": "$state"}}}
    def scrape(self, payload):
        state = payload['state']
        place_id = state['currentPlaceId']
        details = self.finder.get_business_details(place_id, state['constraints'])
        if not details:
            state['skippedCount'] += 1
            return {"state": state, "next": {"key": "control", "payload": {"state": "$state"}}}
        state['placeDetails'] = details
        return {"state": state, "next": {"key": "analyze", "payload": {"state": "$state"}}}
    def analyze(self, payload):
        state = payload['state']
        details = state['placeDetails']
        constraints = state['constraints']
        analysis_result, meets_constraints = self.analyzer.run(details, constraints)
        if not meets_constraints:
            state['skippedCount'] += 1
            return {"state": state, "result": analysis_result, "next": {"key": "control", "payload": {"state": "$state"}}}
        state['leadCount'] += 1
        return {"state": state, "result": analysis_result, "next": {"key": "control", "payload": {"state": "$state"}}}
    def control(self, payload):
        state = payload['state']
        
        # Konversi leadCount dan numberOfLeads ke integer untuk perbandingan yang aman
        lead_count = int(state.get('leadCount', 0))
        number_of_leads = int(state.get('numberOfLeads', 1))

        if lead_count >= number_of_leads:
            print("Target number of leads reached.")
            return {"done": True, "state": state, "result": None}
        
        if state.get('remainingPlaceIds'):
            state['currentPlaceId'] = state['remainingPlaceIds'].pop(0)
            return {"state": state, "next": {"key": "scrape", "payload": {"state": "$state"}}}
        
        if state.get('nextPageToken'):
            return {"state": state, "next": {"key": "search", "payload": {"state": "$state"}}}
        
        print("No more potential leads found.")
        return {"done": True, "state": state, "result": None}