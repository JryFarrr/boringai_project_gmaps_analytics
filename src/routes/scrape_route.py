from flask import request, jsonify, current_app
from src.utils.response_utils import error_response
from src.services.google_maps_service import get_place_details, search_business_with_search_api
def scrape_route():
    """Handle the scrape task endpoint with SearchAPI.io integration"""
    data = request.get_json()
    if not data:
        return error_response("Missing request data")

    # Get state values
    skipped_count = data.get("skippedCount", 0)
    lead_count = data.get("leadCount", 0)
    number_of_leads = data.get("numberOfLeads", 0)

    # Check if we already have a Place ID or need to search by keyword
    place_id = data.get("placeId")
    keyword = data.get("keyword")
    location = data.get("location", "Indonesia")

    # If no placeId is provided, we need a keyword to search
    if not place_id and not keyword:
        return error_response("Either placeId or keyword is required")

    try:
        # If we don't have a place_id but have a keyword, search first
        if not place_id and keyword:
            current_app.logger.info(f"Searching for keyword: {keyword} in {location}")
            businesses = search_business_with_search_api(keyword, location=location, max_results=1)
            
            if not businesses:
                return error_response("No businesses found for the search query", 404)
            
            place_id = businesses[0].get("place_id")
            if not place_id:
                return error_response("No valid Place ID found in search results", 404)
            
            current_app.logger.info(f"Found place ID: {place_id} for keyword '{keyword}'")

        # Now we have a place_id, get the details
        current_app.logger.info(f"Scraping place ID: {place_id} (leadCount={lead_count}, skippedCount={skipped_count})")

        # Define the fields we want from Google Maps API
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

        # Map price_level (integer) to dollar symbols
        price_level = place_details.get('price_level', '')
        price_range_map = {
            0: "",    # No price (empty)
            1: "$",   # Inexpensive
            2: "$$",  # Moderate
            3: "$$$", # Expensive
            4: "$$$$" # Very expensive
        }
        price_range = price_range_map.get(price_level, "") if price_level != '' else ""

        # Consistent data structure with default values
        place_data = {
            "placeName": place_details.get('name', 'Unknown'),
            "contact": {
                "phone": place_details.get('formatted_phone_number', 'N/A'),
                "website": place_details.get('website', 'N/A')
            },
            "address": place_details.get('formatted_address', 'N/A'),
            "location": place_details.get('geometry', {}).get('location', {}),
            "rating": place_details.get('rating', 0.0),
            "totalRatings": place_details.get('user_ratings_total', 0),
            "businessHours": place_details.get('opening_hours', {}).get('weekday_text', []),
            "businessType": place_details.get('types', []),
            "priceRange": price_range,
            "positiveReviews": [
                r['text'] for r in place_details.get('reviews', []) if r.get('rating', 0) >= 4
            ],
            "negativeReviews": [
                r['text'] for r in place_details.get('reviews', []) if r.get('rating', 0) < 4
            ]
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

        # Response according to unified contract
        response = {
            "state": {
                "skippedCount": skipped_count,
                "leadCount": lead_count,
                "numberOfLeads": number_of_leads
            },
            "result": None,
            "next": {
                "key": "analyze",
                "payload": {
                    "placeDetails": place_data,
                    "leadCount": "$state.leadCount",
                    "skippedCount": "$state.skippedCount",
                    "numberOfLeads": "$state.numberOfLeads"
                }
            },
            "done": False,
            "error": None
        }
    except Exception as e:
        current_app.logger.error(f"Scrape failed: {str(e)}")
        return error_response(f"Scrape failed: {str(e)}", 500)

    return jsonify(response), 200