from flask import request, jsonify, current_app
from flasgger import swag_from
from src.utils.response_utils import error_response
from src.services.control_service import (
    handle_target_reached,
    handle_skipped_constraints,
    handle_next_place_id,
    handle_need_more_leads
)
from src.docs.control import control_dict

@swag_from(control_dict)
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
    try:
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
        business_type = data.get("business_type")
        location = data.get("location")
        skipped_constraints = data.get("skippedConstraints", False)
        skipped_count = data.get("skippedCount", 0)
        
        # Log current state
        current_app.logger.info(f"Control state: leadCount={lead_count}, number_of_leads={number_of_leads}, skippedCount={skipped_count}")
        current_app.logger.info(f"Remaining place IDs: {len(remaining_place_ids)}")
        
        # Create control parameters dictionary for services
        control_params = {
            "lead_count": lead_count,
            "number_of_leads": number_of_leads,
            "remaining_place_ids": remaining_place_ids,
            "search_offset": search_offset,
            "next_page_token": next_page_token,
            "business_type": business_type,
            "location": location,
            "skipped_constraints": skipped_constraints,
            "skipped_count": skipped_count
        }
        
        # SCENARIO C: Reached target leads → end workflow
        if lead_count >= number_of_leads:
            current_app.logger.info(f"Target reached! Lead count {lead_count} >= requested {number_of_leads}. Ending workflow.")
            response = handle_target_reached()
            return jsonify(response), 200
        
        # SCENARIO D: Skip current place and check next due to constraints not being met
        elif skipped_constraints:
            current_app.logger.info("Handling skipped constraint scenario")
            response = handle_skipped_constraints(control_params)
            return jsonify(response), 200
        
        # SCENARIO A: Continue with the next placeId (normal flow)
        elif remaining_place_ids:
            current_app.logger.info(f"Normal flow: Using next place ID from remaining ({len(remaining_place_ids)-1} left)")
            response = handle_next_place_id(control_params)
            return jsonify(response), 200
        
        # SCENARIO B: Need more leads (normal flow)
        else:
            current_app.logger.info(f"Need more leads. Leading search for more places.")
            response = handle_need_more_leads(control_params)
            return jsonify(response), 200

    except Exception as e:
        current_app.logger.error(f"Control route failed: {str(e)}")
        return error_response(f"Control route failed: {str(e)}", 500)