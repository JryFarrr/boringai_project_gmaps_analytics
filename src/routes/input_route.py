from flask import request, jsonify
from src.utils.response_utils import error_response

def input_route():
    """Handle the input task endpoint"""
    data = request.get_json()
    if not data:
        return error_response("Invalid JSON payload")

    required_fields = ["businessType", "location", "numberOfLeads"]
    for field in required_fields:
        if field not in data:
            return error_response(f"Missing required field: {field}")

    # Validasi input
    if not isinstance(data["businessType"], str) or not data["businessType"].strip():
        return error_response("businessType must be a non-empty string")
    if not isinstance(data["location"], str) or not data["location"].strip():
        return error_response("location must be a non-empty string")
    if not isinstance(data["numberOfLeads"], int) or data["numberOfLeads"] <= 0:
        return error_response("numberOfLeads must be a positive integer")

    # Inisialisasi state awal
    initial_state = {
        "businessType": data["businessType"],
        "location": data["location"],
        "numberOfLeads": data["numberOfLeads"],
        "leadCount": 0,
        "searchOffset": 0,
        "remainingPlaceIds": []
    }

    response = {
        "state": initial_state,
        "next": {
            "key": "search",
            "payload": {
                "businessType": "$state.businessType",
                "location": "$state.location",
                "searchOffset": "$state.searchOffset",
                "numberOfLeads": "$state.numberOfLeads"
            }
        },
        "result": None,
        "done": False,
        "error": None
    }
    return jsonify(response), 200
