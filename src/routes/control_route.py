# Modified control_route.py
from flask import request, jsonify
from src.utils.response_utils import error_response

def control_route():
    """
    Handle the control task endpoint with improved lead collection strategy
    
    Scenarios:
    A. Continue with the next placeId - When there are remaining place IDs
    B. Need more leads, check next page token or increment search
    C. Reached target leads - End the workflow
    
    Returns:
        tuple: JSON response and status code
    """
    data = request.get_json()
    if not data:
        return error_response("Invalid JSON payload")

    # Validate required fields
    required_fields = ["numberOfLeads"]
    for field in required_fields:
        if field not in data:
            return error_response(f"Missing required field: {field}")
    
    # Extract data with defaults for optional fields
    lead_count = data.get("leadCount", 0)
    number_of_leads = data.get("numberOfLeads", 0)
    remaining_place_ids = data.get("remainingPlaceIds", [])
    search_offset = data.get("searchOffset", 0)
    next_page_token = data.get("nextPageToken")
    business_type = data.get("businessType")
    location = data.get("location")
    
    # SCENARIO C: Reached target leads → end workflow
    if lead_count >= number_of_leads:
        response = {
            "state": None,
            "result": None,
            "next": None,
            "done": True,
            "error": None
        }
        return jsonify(response), 200
    
    # SCENARIO A: Continue with the next placeId
    elif remaining_place_ids:
        # Get the next place ID to process
        next_place_id = remaining_place_ids[0]
        new_remaining = remaining_place_ids[1:]
        
        response = {
            "state": {
                "remainingPlaceIds": new_remaining
            },
            "result": None,
            "next": {
                "key": "scrape",
                "payload": {
                    "placeId": next_place_id
                }
            },
            "done": False,
            "error": None
        }
        return jsonify(response), 200
    
    # SCENARIO B: Need more leads, check next page token or do new search
    else:
        # Simplified response format for Scenario B according to sample
        response = {
            "state": None,
            "result": None,
            "next": {
                "key": "search",
                "payload": {
                    "searchOffset": "$state.searchOffset"
                }
            },
            "done": False,
            "error": None
        }
        return jsonify(response), 200