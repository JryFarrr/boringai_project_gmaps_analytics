from flask import request, jsonify, current_app
from src.utils.response_utils import error_response
from src.services.scrape_service import (
    search_and_get_place_id,
    process_place_details,
    create_scrape_response
)

def scrape_route():
    """
    Handle the scrape task endpoint with SearchAPI.io integration
    
    Retrieves business details from Google Maps API using either:
    1. A direct place_id provided in the request
    2. A keyword search that returns a place_id to query
    
    The endpoint retrieves details such as business name, contact info,
    address, ratings, reviews, and business hours.
    
    Returns:
        tuple: JSON response and status code
    """
    try:
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
                place_id = search_and_get_place_id(keyword, location)
                
                if not place_id:
                    return error_response("No valid Place ID found in search results", 404)
                    
                current_app.logger.info(f"Found place ID: {place_id} for keyword '{keyword}'")

            # Now we have a place_id, get the details
            current_app.logger.info(f"Scraping place ID: {place_id} (leadCount={lead_count}, skippedCount={skipped_count})")
            
            # Process place details
            place_data = process_place_details(place_id)
            current_app.logger.info(f"Retrieved details for place: {place_data.get('placeName', 'Unknown')}")

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

            # Create response
            response = create_scrape_response(place_data, lead_count, skipped_count, number_of_leads)
            return jsonify(response), 200
            
        except Exception as e:
            current_app.logger.error(f"Scrape failed: {str(e)}")
            return error_response(f"Scrape failed: {str(e)}", 500)
    except Exception as e:
        current_app.logger.error(f"Scrape route failed: {str(e)}")
        return error_response(f"Scrape route failed: {str(e)}", 500)