from flask import request, jsonify
from src.utils.response_utils import error_response
from src.services.google_maps_service import get_place_details

def scrape_route():
    """Handle the scrape task endpoint with consistent output and priceRange as $ symbols"""
    data = request.get_json()
    if not data or "placeId" not in data:
        return error_response("Missing required field: placeId")

    place_id = data["placeId"]

    try:
        # Tentukan field yang diinginkan dari Google Maps API
        fields = [
            "name",
            "formatted_phone_number",
            "website",
            "price_level",
            "reviews"
        ]
        place_details = get_place_details(place_id, fields=fields)
        print(place_details)

        # Mapping price_level (integer) ke simbol dolar
        price_level = place_details.get('price_level', '')  # Default: kosong jika tidak ada
        price_range_map = {
            0: "",    # Tidak ada harga (kosong)
            1: "$",   # Murah
            2: "$$",  # Sedang
            3: "$$$", # Mahal
            4: "$$$$" # Sangat mahal
        }
        price_range = price_range_map.get(price_level, "") if price_level != '' else ""

        # Struktur data konsisten dengan nilai default
        place_data = {
            "placeName": place_details.get('name', 'Unknown'),  # Default: 'Unknown'
            "contact": {
                "phone": place_details.get('formatted_phone_number', 'N/A'),  # Default: 'N/A'
                "website": place_details.get('website', 'N/A')  # Default: 'N/A'
            },
            "priceRange": price_range,  # Menggunakan simbol dolar
            "positiveReviews": [
                r['text'] for r in place_details.get('reviews', []) if r.get('rating', 0) >= 4
            ],  # Default: list kosong jika tidak ada ulasan
            "negativeReviews": [
                r['text'] for r in place_details.get('reviews', []) if r.get('rating', 0) < 4
            ]  # Default: list kosong jika tidak ada ulasan
        }

        # Respons sesuai unified contract
        response = {
            "state": None,
            "result": None,
            "next": {
                "key": "analyze",
                "payload": {
                    "placeDetails": place_data,
                    "leadCount": "$state.leadCount"
                }
            },
            "done": False,
            "error": None
        }
    except Exception as e:
        return error_response(f"Scrape failed: {str(e)}", 500)

    return jsonify(response), 200