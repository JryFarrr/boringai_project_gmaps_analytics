from flask import request, jsonify
from src.utils.response_utils import error_response

def analyze_route():
    """Handle the analyze task endpoint"""
    data = request.get_json()
    if not data or "placeDetails" not in data or "leadCount" not in data:
        return error_response("Missing required fields: placeDetails or leadCount")

    place_details = data["placeDetails"]
    lead_count = data["leadCount"]

    # Analisis sederhana berdasarkan ulasan
    positive_count = len(place_details.get("positiveReviews", []))
    negative_count = len(place_details.get("negativeReviews", []))
    total_reviews = positive_count + negative_count
    match_percentage = (positive_count / total_reviews * 100) if total_reviews > 0 else 0

    result = {
        "placeName": place_details["placeName"],
        "matchPercentage": round(match_percentage, 2)
    }

    response = {
        "state": {
            "leadCount": lead_count + 1
        },
        "result": result,
        "next": {
            "key": "control",
            "payload": {
                "leadCount": "$state.leadCount",
                "numberOfLeads": "$state.numberOfLeads",
                "remainingPlaceIds": "$state.remainingPlaceIds",
                "searchOffset": "$state.searchOffset"
            }
        },
        "done": False,
        "error": None
    }
    return jsonify(response), 200
