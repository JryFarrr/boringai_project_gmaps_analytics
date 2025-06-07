from src.services.google_maps_service import get_place_details, scrape_business_data_by_keyword
from src.utils.data_mapping_utils import map_price_level, format_place_data
from flask import current_app # Import current_app for logging

def search_and_get_place_id(keyword, location="Indonesia", max_results=1):
    """
    Searches for a business by keyword and location and returns the place ID
    
    Args:
        keyword (str): The keyword to search for
        location (str): The location to search in
        max_results (int): Maximum number of results to return
    
    Returns:
        str or None: The place ID of the first result, or None if no results
    """
    businesses = scrape_business_data_by_keyword(keyword, location=location, max_results=max_results)
    
    if not businesses:
        return None
    
    place_id = businesses[0].get("place_id")
    return place_id

def process_place_details(place_id):
    """
    Retrieves and processes place details from Google Maps API, ensuring placeId is included.
    
    Args:
        place_id (str): The Google Maps place ID
    
    Returns:
        dict: Formatted place data with consistent structure, including placeId.
    """
    # Define the fields we want from Google Maps API
    fields = [
        "place_id", # Ensure place_id is requested from the API itself
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
    
    # Get place details from Google Maps API
    place_details = get_place_details(place_id, fields=fields)
    
    # Format the place data with consistent structure
    place_data = format_place_data(place_details)

    # --- FIX: Explicitly add placeId to the dictionary --- 
    # Although requested in fields, ensure it's present in the final dict passed along.
    # Use the original place_id passed to the function as the definitive source.
    place_data["placeId"] = place_id 
    current_app.logger.info(f"Added placeId ")
    # --- END FIX --- 

    place_data["types"] = place_details.get("types", [])

    reviews = place_details.get("reviews", [])
    if not isinstance(reviews, list):
        current_app.logger.warning(f"Warning: reviews is not a list. Type: {type(reviews)}")
        reviews = []
    place_data["reviews"] = reviews
    
    return place_data

def create_scrape_response(place_data, lead_count, skipped_count, number_of_leads):
    """
    Creates the response object for the scrape endpoint
    
    Args:
        place_data (dict): The formatted place data (should now include placeId)
        lead_count (int): Current count of leads
        skipped_count (int): Current count of skipped places
        number_of_leads (int): Target number of leads
    
    Returns:
        dict: Formatted response object with state and next action
    """
    # Log to confirm placeId is present before creating response
    if "placeId" not in place_data:
        current_app.logger.error("CRITICAL: placeId missing from place_data in create_scrape_response!")
    else:
        current_app.logger.info(f"Creating scrape response with placeId: {place_data['placeId']}")
        
    return {
        "state": {
            "skippedCount": skipped_count,
            "leadCount": lead_count,
            "numberOfLeads": number_of_leads
        },
        "result": None,
        "next": {
            "key": "analyze",
            "payload": {
                "placeDetails": place_data, # place_data now includes placeId
                "leadCount": "$state.leadCount",
                "constraints": place_data.get("constraints", {}), # Constraints might be passed differently, check workflow
                "skippedCount": "$state.skippedCount",
                "numberOfLeads": "$state.numberOfLeads"
            }
        },
        "done": False,
        "error": None
    }

