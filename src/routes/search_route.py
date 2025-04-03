from flask import request, jsonify
from src.utils.response_utils import error_response
from src.services.google_maps_service import search_places

def search_route():
    """Handle the search task endpoint using direct API approach"""
    data = request.get_json()
    if not data:
        return error_response("Invalid JSON payload")

    # Validasi field yang diperlukan
    required_fields = ["businessType", "location", "searchOffset", "numberOfLeads"]
    for field in required_fields:
        if field not in data:
            return error_response(f"Missing required field: {field}")

    # Ambil data dari request
    business_type = data["businessType"]
    location = data["location"]
    search_offset = data["searchOffset"]
    number_of_leads = data["numberOfLeads"]
    next_page_token = data.get("nextPageToken")

    try:
        # Tentukan berapa banyak lead yang masih dibutuhkan
        remaining_leads_needed = number_of_leads - search_offset
        if remaining_leads_needed <= 0:
            return error_response("No more leads needed", 200)

        # Panggil Google Maps API untuk mencari tempat
        if next_page_token:
            response = search_places(page_token=next_page_token)
        else:
            query = f"{business_type} in {location}"
            response = search_places(query=query)

        # Ambil place_ids dari hasil pencarian
        place_ids = [place['place_id'] for place in response['results']]
        new_next_page_token = response.get('next_page_token')

        if not place_ids:
            return error_response("No businesses found", 404)

        # Batasi place_ids sesuai kebutuhan (opsional untuk batching)
        # Misalnya, jika hanya perlu 10 lead dan offset 0, ambil 10 saja
        if remaining_leads_needed < len(place_ids):
            place_ids = place_ids[:remaining_leads_needed]

        # Ambil ID pertama untuk dikirim ke payload
        next_place_id = place_ids[0]
        # Hapus ID tersebut dari remaining place IDs untuk mencegah infinite loop
        remaining_place_ids = place_ids[1:]

        # Siapkan respons sesuai unified contract
        response = {
            "state": {
                "remainingPlaceIds": remaining_place_ids,
                "nextPageToken": new_next_page_token if new_next_page_token else None,
                "searchOffset": search_offset + len(place_ids)
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
    except Exception as e:
        return error_response(f"Search failed: {str(e)}", 500)

    return jsonify(response), 200