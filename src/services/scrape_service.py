from src.services.google_maps_service import get_place_details, search_business_with_search_api
from src.utils.data_mapping_utils import map_price_level, format_place_data

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
    businesses = search_business_with_search_api(keyword, location=location, max_results=max_results)
    
    if not businesses:
        return None
    
    place_id = businesses[0].get("place_id")
    return place_id

def process_place_details(place_id):
    """
    Retrieves and processes place details from Google Maps API
    
    Args:
        place_id (str): The Google Maps place ID
    
    Returns:
        dict: Formatted place data with consistent structure
    """
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
    
    # Get place details from Google Maps API
    place_details = get_place_details(place_id, fields=fields)
    
    # Format the place data with consistent structure
    place_data = format_place_data(place_details)
    
    return place_data

def create_scrape_response(place_data, lead_count, skipped_count, number_of_leads):
    """
    Creates the response object for the scrape endpoint
    
    Args:
        place_data (dict): The formatted place data
        lead_count (int): Current count of leads
        skipped_count (int): Current count of skipped places
        number_of_leads (int): Target number of leads
    
    Returns:
        dict: Formatted response object with state and next action
    """
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
                "placeDetails": place_data,
                "leadCount": "$state.leadCount",
                "skippedCount": "$state.skippedCount",
                "numberOfLeads": "$state.numberOfLeads"
            }
        },
        "done": False,
        "error": None
    }