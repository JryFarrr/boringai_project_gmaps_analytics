from flask import request, jsonify
from src.utils.response_utils import error_response
from src.utils.validation_utils import validate_input_payload
from src.services.input_service import create_initial_state, create_input_response

def input_route():
    """
    Handle the input task endpoint
    
    Processes the initial input for the workflow, validates required fields,
    and sets up the initial state for the lead generation process.
    
    Returns:
        tuple: JSON response and status code
    """
    # Get and validate JSON payload
    data = request.get_json()
    if not data:
        return error_response("Invalid JSON payload")

    # Validate required fields and their types
    validation_error = validate_input_payload(data)
    if validation_error:
        return error_response(validation_error)

    # Create initial state from validated input
    initial_state = create_initial_state(data)
    
    # Create and return response with initial state
    response = create_input_response(initial_state)
    return jsonify(response), 200