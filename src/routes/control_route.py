from flask import request, jsonify
from src.utils.response_utils import error_response

def control_route():
    """Handle the control task endpoint"""
    data = request.get_json()
    if not data:
        return error_response("Invalid JSON payload")

    required_fields = ["leadCount", "numberOfLeads", "remainingPlaceIds", "searchOffset"]
    for field in required_fields:
        if field not in data:
            return error_response(f"Missing required field: {field}")

    lead_count = data["leadCount"]
    number_of_leads = data["numberOfLeads"]
    remaining_place_ids = data["remainingPlaceIds"]
    search_offset = data["searchOffset"]

    if lead_count >= number_of_leads:
        # Workflow selesai
        response = {
            "state": None,
            "result": None,
            "next": None,
            "done": True,
            "error": None
        }
    elif remaining_place_ids:
        # Lanjut ke scrape dengan placeId berikutnya
        next_place_id = remaining_place_ids[0]
        new_remaining = remaining_place_ids[1:]
        response = {
            "state": {"remainingPlaceIds": new_remaining},
            "result": None,
            "next": {
                "key": "scrape",
                "payload": {"placeId": next_place_id}
            },
            "done": False,
            "error": None
        }
    else:
        # Kembali ke search untuk mengambil lebih banyak data
        response = {
            "state": None,
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
