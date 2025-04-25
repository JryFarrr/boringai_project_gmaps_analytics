from flask import request, jsonify, current_app
from flasgger import swag_from
from src.utils.response_utils import error_response
from src.utils.validation_utils import validate_input_payload
from src.services.input_service import create_initial_state, create_input_response

@swag_from({
    'tags': ['Task'],
    'description': 'Memulai task input untuk pencarian lead.',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'businessType': {'type': 'string','example': 'cafe'
                    },
                    'location': {'type': 'string','example': 'Surabaya'
                    },
                    'numberOfLeads': {'type': 'integer','example': 3
                    },
                    'minRating': {'type': 'number','format': 'float','example': 4.0
                    },
                    'minReviews': {'type': 'integer','example': 50
                    },
                    'priceRange': {'type': 'string','example': '$$'
                    },
                    'keywords': {'type': 'string','example': 'cocok buat nugas'
                    },
                    'business_hours': {'type': 'string', 'example': 'anytime'}
                },
                'required': ['businessType', 'location']
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Berhasil membuat initial state dan step berikutnya',
            'examples': {
                'application/json': {
                    "state": {
                        "businessType": "restaurant",
                        "location": "Surabaya",
                        "numberOfLeads": 10,
                        "leadCount": 0,
                        "searchOffset": 0,
                        "remainingPlaceIds": []
                    },
                    "next": {
                        "key": "search",
                        "payload": {
                            "businessType": "$state.businessType",
                            "location": "$state.location",
                            "searchOffset": "$state.searchOffset",
                            "numberOfLeads": "$state.numberOfLeads"
                        }
                    },
                    "result": None,
                    "done": False,
                    "error": None
                }
            }
        },
        '500': {
            'description': 'Internal server error',
            'schema': {
                'type': 'object',
                'properties': {
                    'state': {'type': 'object'},
                    'result': {'type': 'object'},
                    'next': {
                        'type': 'object',
                        'properties': {
                            'key': {'type': 'string'},
                            'payload': {'type': 'object'}
                        }
                    },
                    'done': {'type': 'boolean'},
                    'error': {'type': 'string'}
                }
            }
        }
    }
})
def input_route():
    """
    Handle the input task endpoint
    
    Processes the initial input for the workflow, validates required fields,
    and sets up the initial state for the lead generation process.
    
    Returns:
        tuple: JSON response and status code
    """
    try:
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

    except Exception as e:
        current_app.logger.error(f"Input route failed: {str(e)}")
        return error_response(f"Input route failed: {str(e)}", 500)