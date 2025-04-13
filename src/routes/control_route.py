# Modified control_route.py
from flask import request, jsonify, current_app
from src.utils.response_utils import error_response

def control_route():
    """
    Handle the control task endpoint with improved lead collection strategy
    
    Scenarios:
    A. Continue with the next placeId - When there are remaining place IDs
    B. Need more leads, check next page token or increment search
    C. Reached target leads - End the workflow
    D. Skip current place due to constraints not being met
    
    Returns:
        tuple: JSON response and status code
    """
    data = request.get_json()
    if not data:
        return error_response("Invalid JSON payload")

    # Validate required fields
    required_fields = ["numberOfLeads"]
    for field in required_fields:
        if field not in data:
            return error_response(f"Missing required field: {field}")
    
    # Extract data with defaults for optional fields
    lead_count = data.get("leadCount", 0)
    number_of_leads = data.get("numberOfLeads", 0)
    remaining_place_ids = data.get("remainingPlaceIds", [])
    search_offset = data.get("searchOffset", 0)
    next_page_token = data.get("nextPageToken")
    business_type = data.get("businessType")
    location = data.get("location")
    skipped_constraints = data.get("skippedConstraints", False)
    skipped_count = data.get("skippedCount", 0)  # Get skipped count
    
    # Log current state
    current_app.logger.info(f"Control state: leadCount={lead_count}, numberOfLeads={number_of_leads}, skippedCount={skipped_count}")
    current_app.logger.info(f"Remaining place IDs: {len(remaining_place_ids)}")
    
    # SCENARIO C: Reached target leads → end workflow
    if lead_count >= number_of_leads:
        current_app.logger.info(f"Target reached! Lead count {lead_count} >= requested {number_of_leads}. Ending workflow.")
        response = {
            "state": None,
            "result": None,
            "next": None,
            "done": True,
            "error": None
        }
        return jsonify(response), 200
    
    # SCENARIO D: Skip current place and check next due to constraints not being met
    elif skipped_constraints:
        current_app.logger.info("Handling skipped constraint scenario")
        # If we have more place IDs, go to the next one
        if remaining_place_ids:
            next_place_id = remaining_place_ids[0]
            new_remaining = remaining_place_ids[1:]
            
            current_app.logger.info(f"Using next place ID from remaining ({len(new_remaining)} left)")
            response = {
                "state": {
                    "remainingPlaceIds": new_remaining,
                    "nextPageToken": next_page_token,
                    "searchOffset": search_offset,
                    "leadCount": lead_count,
                    "businessType": business_type,
                    "location": location,
                    "numberOfLeads": number_of_leads,
                    "skippedCount": skipped_count  # Pass skipped count
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
            return jsonify(response), 200
        
        # If no more place IDs but we have a next page token, get more results
        elif next_page_token:
            current_app.logger.info(f"No more place IDs but have next_page_token. Searching with token.")
            response = {
                "state": None,
                "result": None,
                "next": {
                    "key": "search",
                    "payload": {
                        "businessType": business_type,
                        "location": location,
                        "nextPageToken": next_page_token,
                        "numberOfLeads": number_of_leads,
                        "searchOffset": search_offset,
                        "leadCount": lead_count,
                        "skippedCount": skipped_count  # Pass skipped count
                    }
                },
                "done": False,
                "error": None
            }
            return jsonify(response), 200
        
        # If no more place IDs and no next page token, start a new search
        else:
            current_app.logger.info(f"No more place IDs and no next_page_token. Starting new search.")
            response = {
                "state": None,
                "result": None,
                "next": {
                    "key": "search",
                    "payload": {
                        "businessType": business_type,
                        "location": location,
                        "searchOffset": search_offset,
                        "numberOfLeads": number_of_leads,
                        "leadCount": lead_count,
                        "skippedCount": skipped_count  # Pass skipped count
                    }
                },
                "done": False,
                "error": None
            }
            return jsonify(response), 200
    
    # SCENARIO A: Continue with the next placeId (normal flow)
    elif remaining_place_ids:
        # Get the next place ID to process
        next_place_id = remaining_place_ids[0]
        new_remaining = remaining_place_ids[1:]
        
        current_app.logger.info(f"Normal flow: Using next place ID from remaining ({len(new_remaining)} left)")
        response = {
            "state": {
                "remainingPlaceIds": new_remaining,
                "leadCount": lead_count,  # Explicitly include leadCount
                "numberOfLeads": number_of_leads,  # Explicitly include numberOfLeads
                "businessType": business_type,
                "location": location,
                "searchOffset": search_offset,
                "nextPageToken": next_page_token,
                "skippedCount": skipped_count  # Preserve skipped count in state
            },
            "result": None,
            "next": {
                "key": "scrape",
                "payload": {
                    "placeId": next_place_id,
                    "skippedCount": skipped_count,  # Pass skipped count
                    "leadCount": lead_count,
                    "numberOfLeads": number_of_leads
                }
            },
            "done": False,
            "error": None
        }
        return jsonify(response), 200
    
    # SCENARIO B: Need more leads (normal flow)
    else:
        current_app.logger.info(f"Need more leads. Leading search for more places.")
        response = {
            "state": None,
            "result": None,
            "next": {
                "key": "search",
                "payload": {
                    "businessType": business_type,
                    "location": location,
                    "searchOffset": search_offset,
                    "numberOfLeads": number_of_leads,
                    "leadCount": lead_count,
                    "skippedCount": skipped_count  # Pass skipped count
                }
            },
            "done": False,
            "error": None
        }
        return jsonify(response), 200