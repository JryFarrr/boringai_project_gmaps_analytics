import time
from flask import current_app
from src.services.google_maps_service import search_places

def collect_place_ids(business_type, location, total_needed, remaining_place_ids=None, next_page_token=None):
    """
    Collects place IDs by using existing IDs, next page token, or new search
    
    Uses a multi-step approach to efficiently collect the required number of place IDs:
    1. First uses any existing place IDs from previous searches
    2. If more are needed, uses pagination with next_page_token if available
    3. Finally performs new searches if necessary
    
    Args:
        business_type (str): Type of business to search for
        location (str): Location to search in
        total_needed (int): Total number of place IDs needed
        remaining_place_ids (list): Any existing place IDs from previous searches
        next_page_token (str): Next page token for pagination
    
    Returns:
        dict: Dictionary containing collected place IDs and next page token
    """
    all_place_ids = []
    current_next_page_token = next_page_token
    
    # First, use any existing place_ids from previous searches
    if remaining_place_ids:
        current_app.logger.info(f"Using {len(remaining_place_ids)} previously found place IDs")
        all_place_ids.extend(remaining_place_ids)
        # Reset token if we have enough IDs already
        if len(all_place_ids) >= total_needed:
            current_next_page_token = None
    
    # Keep collecting place_ids until we have enough or run out of results
    page_count = 0
    max_pages = 3  # Limit the number of pages to avoid excessive API calls
    
    while len(all_place_ids) < total_needed and page_count < max_pages:
        page_count += 1
        
        try:
            # Call Google Maps API to search for places
            if current_next_page_token:
                current_app.logger.info(f"Searching with page token (page {page_count}): {current_next_page_token[:30]}...")
                response = search_places(page_token=current_next_page_token)
            else:
                query = f"{business_type} in {location}"
                current_app.logger.info(f"Searching for: {query} (page {page_count})")
                response = search_places(query=query)
            
            # Extract new place_ids and add to our collection
            new_place_ids = [place['place_id'] for place in response.get('results', [])]
            
            # If we didn't get any new place_ids, exit the loop
            if not new_place_ids:
                current_app.logger.info(f"No new place IDs found on page {page_count}")
                break
                
            current_app.logger.info(f"Found {len(new_place_ids)} new place IDs on page {page_count}")
            all_place_ids.extend(new_place_ids)
            
            # Update next_page_token for potential next iteration
            current_next_page_token = response.get('next_page_token')
            
            # If no nextPageToken or already have enough place_ids, exit loop
            if not current_next_page_token:
                current_app.logger.info("No next page token available, ending search")
                break
            
            # Log progress
            current_app.logger.info(f"Collected {len(all_place_ids)} place IDs so far, need {total_needed}")
            
            # Add a delay before the next iteration if we're going to use the page token
            if current_next_page_token and len(all_place_ids) < total_needed:
                current_app.logger.info("Waiting 2 seconds before fetching next page...")
                time.sleep(2)
        
        except Exception as search_error:
            current_app.logger.error(f"Error fetching page {page_count}: {str(search_error)}")
            # If we have some results already, continue with what we have
            if all_place_ids:
                current_app.logger.info(f"Continuing with {len(all_place_ids)} place IDs already collected")
                current_next_page_token = None
                break
            else:
                # Re-raise the exception if we have no results at all
                raise
    
    # Limit place_ids based on total needed
    if len(all_place_ids) > total_needed:
        all_place_ids = all_place_ids[:total_needed]
    
    return {
        "place_ids": all_place_ids,
        "next_page_token": current_next_page_token
    }

def create_search_response(place_ids, next_page_token, search_offset, lead_count, skipped_count, 
                          business_type, location, number_of_leads):
    """
    Creates the response object for the search endpoint
    
    Args:
        place_ids (list): Collected place IDs
        next_page_token (str): Next page token for pagination
        search_offset (int): Current search offset
        lead_count (int): Current count of leads
        skipped_count (int): Current count of skipped places
        business_type (str): Type of business being searched
        location (str): Location being searched
        number_of_leads (int): Target number of leads
    
    Returns:
        dict: Formatted response object with state and next action
    """
    # Take the first place ID to send to payload
    first_place_id = place_ids[0]
    new_remaining = place_ids[1:]
    
    # Prepare state object
    state = {
        "remainingPlaceIds": new_remaining,
        "searchOffset": search_offset + len(place_ids),
        "nextPageToken": next_page_token,
        "skippedCount": skipped_count,
        "leadCount": lead_count,
        "businessType": business_type,
        "location": location,
        "numberOfLeads": number_of_leads
    }
    
    # Prepare response
    return {
        "state": state,
        "result": None,
        "next": {
            "key": "scrape",
            "payload": {
                "placeId": first_place_id,
                "skippedCount": skipped_count,
                "leadCount": lead_count,
                "numberOfLeads": number_of_leads
            }
        },
        "done": False,
        "error": None
    }

def create_target_reached_response():
    """
    Creates a response object indicating the target number of leads has been reached
    
    Returns:
        dict: Response object indicating workflow completion
    """
    return {
        "state": None,
        "result": None,
        "next": None,
        "done": True,
        "error": None
    }