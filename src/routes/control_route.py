from flask import request, jsonify
from src.utils.response_utils import error_response

def control_route():
    """
    Handle the control task endpoint
    
    This route determines the next action in the workflow based on:
    - Current lead count vs target number of leads
    - Remaining place IDs to process
    - Search offset for pagination
    
    Scenarios:
    A. Continue with the next placeId - When there are remaining place IDs
    B. Need more leads, but buffer is empty - Return to search with incremented offset
    C. Reached target leads - End the workflow
    
    Returns:
        tuple: JSON response and status code
    """
    data = request.get_json()
    if not data:
        return error_response("Invalid JSON payload")

    # Validate required fields
    required_fields = ["leadCount", "numberOfLeads"]
    for field in required_fields:
        if field not in data:
            return error_response(f"Missing required field: {field}")
    
    # Extract data with defaults for optional fields
    lead_count = data.get("leadCount", 0)
    number_of_leads = data.get("numberOfLeads", 0)
    remaining_place_ids = data.get("remainingPlaceIds", [])
    search_offset = data.get("searchOffset", 0)
    
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
    
    # SCENARIO B: Need more leads, but buffer is empty → go back to search
    else:
        # Increment search offset for pagination
        new_offset = search_offset + 20  # Assuming page size of 20
        
        response = {
            "state": {
                "searchOffset": new_offset
            },
            "result": None,
            "next": {
                "key": "search",
                "payload": {
                    "businessType": "$state.businessType",
                    "location": "$state.location",
                    "searchOffset": "$state.searchOffset",
                    "numberOfLeads": "$state.numberOfLeads",
                    "nextPageToken": "$state.nextPageToken"
                }
            },
            "done": False,
            "error": None
        }
        return jsonify(response), 200