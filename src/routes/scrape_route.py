from flask import request, jsonify, current_app
from src.utils.response_utils import error_response
from src.services.google_maps_service import get_place_details

def scrape_route():
    """Handle the scrape task endpoint with consistent output and priceRange as $ symbols"""
    data = request.get_json()
    if not data or "placeId" not in data:
        return error_response("Missing required field: placeId")

    place_id = data["placeId"]
    # Get skipped count and other important state values
    skipped_count = data.get("skippedCount", 0)
    lead_count = data.get("leadCount", 0)  # Pass lead count through
    number_of_leads = data.get("numberOfLeads", 0)  # Pass number of leads through

    current_app.logger.info(f"Scraping place ID: {place_id} (leadCount={lead_count}, skippedCount={skipped_count})")

    try:
        # Tentukan field yang diinginkan dari Google Maps API
        fields = [
            "name",
            "formatted_phone_number",
            "website",
            "price_level",
            "reviews",
            "formatted_address",
            "geometry",
            "rating",
            "user_ratings_total",
            "opening_hours",
            "types"
        ]
        place_details = get_place_details(place_id, fields=fields)
        current_app.logger.info(f"Retrieved details for place: {place_details.get('name', 'Unknown')}")

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
            "address": place_details.get('formatted_address', 'N/A'),
            "location": place_details.get('geometry', {}).get('location', {}),
            "rating": place_details.get('rating', 0.0),
            "totalRatings": place_details.get('user_ratings_total', 0),
            "businessHours": place_details.get('opening_hours', {}).get('weekday_text', []),
            "businessType": place_details.get('types', []),
            "priceRange": price_range,  # Menggunakan simbol dolar
            "positiveReviews": [
                r['text'] for r in place_details.get('reviews', []) if r.get('rating', 0) >= 4
            ],  # Default: list kosong jika tidak ada ulasan
            "negativeReviews": [
                r['text'] for r in place_details.get('reviews', []) if r.get('rating', 0) < 4
            ]  # Default: list kosong jika tidak ada ulasan
        }

        # Check if we've already reached the target (to handle race conditions)
        if lead_count >= number_of_leads:
            current_app.logger.info(f"Target already reached during scrape! Lead count {lead_count} >= requested {number_of_leads}. Ending workflow.")
            return jsonify({
                "state": None,
                "result": None,
                "next": None,
                "done": True,
                "error": None
            }), 200

        # Respons sesuai unified contract
        response = {
            "state": {
                "skippedCount": skipped_count,  # Preserve skipped count in state
                "leadCount": lead_count,  # Explicitly pass leadCount through
                "numberOfLeads": number_of_leads  # Explicitly pass numberOfLeads through
            },
            "result": None,
            "next": {
                "key": "analyze",
                "payload": {
                    "placeDetails": place_data,
                    "leadCount": "$state.leadCount",
                    "skippedCount": "$state.skippedCount",  # Pass skipped count to analyze
                    "numberOfLeads": "$state.numberOfLeads"  # Pass numberOfLeads to analyze
                }
            },
            "done": False,
            "error": None
        }
    except Exception as e:
        current_app.logger.error(f"Scrape failed: {str(e)}")
        return error_response(f"Scrape failed: {str(e)}", 500)

    return jsonify(response), 200