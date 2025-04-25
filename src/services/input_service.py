def create_initial_state(data):
    """
    Creates the initial state for the lead generation workflow
    
    Takes validated input data and constructs the initial state object
    with default values for workflow management.
    
    Args:
        data (dict): Validated input data containing business type, 
                     location, and number of leads
        
    Returns:
        dict: Initial state object with all necessary parameters
    """
    return {
        "business_type": data["business_type"],
        "location": data["location"],
        "numberOfLeads": data["numberOfLeads"],
        "business_hours": data.get("business_hours", None),
        "min_rating": data.get("min_rating", None),
        "min_reviews": data.get("min_reviews", None),
        "max_reviews": data.get("max_reviews", None),
        "price_range": data.get("price_range", None),
        "keywords": data.get("keywords", None),
        "leadCount": 0,
        "searchOffset": 0,
        "remainingPlaceIds": [],
        "skippedCount": 0  # Adding skipped count to be consistent with other modules
    }

def create_input_response(initial_state):
    """
    Creates the response object for the input endpoint
    
    Structures the response with the initial state and next action to take
    in the workflow.
    
    Args:
        initial_state (dict): The initial state object for the workflow
        
    Returns:
        dict: Formatted response object with state and next action
    """
    return {
        "state": initial_state,
        "next": {
            "key": "search",
            "payload": {
                "business_type": "$state.business_type",
                "location": "$state.location",
                "searchOffset": "$state.searchOffset",
                "numberOfLeads": "$state.numberOfLeads"
            }
        },
        "result": None,
        "done": False,
        "error": None
    }