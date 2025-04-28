from src.services.google_maps_service import get_place_details, scrape_business_data_by_keyword
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
    businesses = scrape_business_data_by_keyword(keyword, location=location, max_results=max_results)
    
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
    if not place_id:
            print("Error: place_id is empty or None")
            return {
                "placeName": "Unknown",
                "formattedAddress": "",
                "rating": 0,
                "totalRatings": 0,
                "reviews": []
            }
        
    # Get basic place details from Google Maps API
    try:
        place_details = get_place_details(place_id)
        if not place_details:
            print(f"Warning: No place details returned for place_id: {place_id}")
            place_details = {}
    except Exception as e:
        print(f"Error getting place details: {str(e)}")
        place_details = {}
        
        # Create a structured response with defaults for missing data
    processed_data = {
        "placeId": place_id,
        "placeName": place_details.get("name", "Unknown"),
        "formattedAddress": place_details.get("formatted_address", ""),
        "phone": place_details.get("formatted_phone_number", ""),
        "website": place_details.get("website", ""),
        "rating": place_details.get("rating", 0),
        "totalRatings": place_details.get("user_ratings_total", 0),
        "businessStatus": place_details.get("business_status", ""),
    }
        
        # Handle location data with error checking
    try:
        location = place_details.get("geometry", {}).get("location", {})
        processed_data["location"] = {
            "lat": location.get("lat", 0),
            "lng": location.get("lng", 0)
        }
    except Exception as e:
        print(f"Error processing location data: {str(e)}")
        processed_data["location"] = {"lat": 0, "lng": 0}
        
    # Handle additional fields
    processed_data["types"] = place_details.get("types", [])
        
        # Include reviews with validation
    reviews = place_details.get("reviews", [])
    if not isinstance(reviews, list):
        print(f"Warning: reviews is not a list. Type: {type(reviews)}")
        reviews = []
    processed_data["reviews"] = reviews
        
    return processed_data

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
                "constraints": place_data.get("constraints", {}),
                "skippedCount": "$state.skippedCount",
                "numberOfLeads": "$state.numberOfLeads"
            }
        },
        "done": False,
        "error": None
    }
