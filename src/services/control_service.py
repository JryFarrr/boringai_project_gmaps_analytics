def handle_target_reached():
    """
    Handles the scenario when the target number of leads has been reached
    
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

def handle_skipped_constraints(params):
    """
    Handles the scenario when current place is skipped due to constraints not being met
    
    Args:
        params (dict): Dictionary containing control parameters:
            - remaining_place_ids (list): Remaining place IDs to process
            - next_page_token (str): Token for pagination in search results
            - search_offset (int): Current search offset
            - lead_count (int): Current lead count
            - business_type (str): Type of business being searched
            - location (str): Location for the search
            - number_of_leads (int): Target number of leads
            - skipped_count (int): Count of skipped places
    
    Returns:
        dict: Response object with next action to take
    """
    remaining_place_ids = params["remaining_place_ids"]
    next_page_token = params["next_page_token"]
    search_offset = params["search_offset"]
    lead_count = params["lead_count"]
    business_type = params["business_type"]
    location = params["location"]
    number_of_leads = params["number_of_leads"]
    skipped_count = params["skipped_count"]
    
    # If we have more place IDs, go to the next one
    if remaining_place_ids:
        next_place_id = remaining_place_ids[0]
        new_remaining = remaining_place_ids[1:]
        
        return {
            "state": {
                "remainingPlaceIds": new_remaining,
                "nextPageToken": next_page_token,
                "searchOffset": search_offset,
                "leadCount": lead_count,
                "business_type": business_type,
                "location": location,
                "numberOfLeads": number_of_leads,
                "skippedCount": skipped_count
            },
            "result": None,
            "next": {
                "key": "scrape",
                "payload": {
                    "business_type": business_type,  # Make sure this is included
                    "location": location,   
                    "placeId": next_place_id,
                    "skippedCount": skipped_count,
                    "leadCount": lead_count,
                    "numberOfLeads": number_of_leads
                }
            },
            "done": False,
            "error": None
        }
    
    # If no more place IDs but we have a next page token, get more results
    elif next_page_token:
        return {
            "state": None,
            "result": None,
            "next": {
                "key": "search",
                "payload": {
                    "business_type": business_type,
                    "location": location,
                    "nextPageToken": next_page_token,
                    "numberOfLeads": number_of_leads,
                    "searchOffset": search_offset,
                    "leadCount": lead_count,
                    "skippedCount": skipped_count
                }
            },
            "done": False,
            "error": None
        }
    
    # If no more place IDs and no next page token, start a new search
    else:
        return {
            "state": None,
            "result": None,
            "next": {
                "key": "search",
                "payload": {
                    "business_type": business_type,
                    "location": location,
                    "searchOffset": search_offset,
                    "numberOfLeads": number_of_leads,
                    "leadCount": lead_count,
                    "skippedCount": skipped_count
                }
            },
            "done": False,
            "error": None
        }

def handle_next_place_id(params):
    """
    Handles the normal flow scenario when there are remaining place IDs to process
    
    Args:
        params (dict): Dictionary containing control parameters:
            - remaining_place_ids (list): Remaining place IDs to process
            - next_page_token (str): Token for pagination in search results
            - search_offset (int): Current search offset
            - lead_count (int): Current lead count
            - business_type (str): Type of business being searched
            - location (str): Location for the search
            - number_of_leads (int): Target number of leads
            - skipped_count (int): Count of skipped places
    
    Returns:
        dict: Response object with next action to take
    """
    remaining_place_ids = params["remaining_place_ids"]
    next_page_token = params["next_page_token"]
    search_offset = params["search_offset"]
    lead_count = params["lead_count"]
    business_type = params["business_type"]
    location = params["location"]
    number_of_leads = params["number_of_leads"]
    skipped_count = params["skipped_count"]
    
    # Get the next place ID to process
    next_place_id = remaining_place_ids[0]
    new_remaining = remaining_place_ids[1:]
    
    return {
        "state": {
            "remainingPlaceIds": new_remaining,
            "leadCount": lead_count,
            "numberOfLeads": number_of_leads,
            "business_type": business_type,
            "location": location,
            "searchOffset": search_offset,
            "nextPageToken": next_page_token,
            "skippedCount": skipped_count
        },
        "result": None,
        "next": {
            "key": "scrape",
            "payload": {
                "placeId": next_place_id,
                "skippedCount": skipped_count,
                "leadCount": lead_count,
                "numberOfLeads": number_of_leads
            }
        },
        "done": False,
        "error": None
    }

def handle_need_more_leads(params):
    """
    Handles the scenario when more leads are needed and a new search should be initiated
    
    Args:
        params (dict): Dictionary containing control parameters:
            - business_type (str): Type of business being searched
            - location (str): Location for the search
            - search_offset (int): Current search offset
            - number_of_leads (int): Target number of leads
            - lead_count (int): Current lead count
            - skipped_count (int): Count of skipped places
    
    Returns:
        dict: Response object with next action to take
    """
    business_type = params["business_type"]
    location = params["location"]
    search_offset = params["search_offset"]
    number_of_leads = params["number_of_leads"]
    lead_count = params["lead_count"]
    skipped_count = params["skipped_count"]
    
    return {
        "state": None,
        "result": None,
        "next": {
            "key": "search",
            "payload": {
                "business_type": business_type,
                "location": location,
                "searchOffset": search_offset,
                "numberOfLeads": number_of_leads,
                "leadCount": lead_count,
                "skipped_count": skipped_count
            }
        },
        "done": False,
        "error": None
    }