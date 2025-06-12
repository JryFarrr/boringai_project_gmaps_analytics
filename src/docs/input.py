input_param = {
    "tags": ["Workflow"],
    "summary": "Start the lead generation workflow",
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': [
                    'business_type',
                    'location',
                    'numberOfLeads'
                ],
                'properties': {
                    'business_type': {
                        'type': 'string',
                        'example': 'restaurant'
                    },
                    'location': {
                        'type': 'string',
                        'example': 'Jakarta Selatan'
                    },
                    'min_rating': {
                        'type': 'number',
                        'format': 'float',
                        'example': 4.5
                    },
                    'min_reviews': {
                        'type': 'integer',
                        'example': 30
                    },
                    'max_reviews': {
                        'type': 'integer',
                        'example': 50
                    },
                    'price_range': {
                        'type': 'string',
                        'example': '$'
                    },
                    'business_hours': {
                        'type': 'string',
                        'example': '9 AM - 10 PM'
                    },
                    'keywords': {
                        'type': 'string',
                        'example': 'terjangkau'
                    },
                    'numberOfLeads': {
                        'type': 'integer',
                        'example': 23
                    }
                }
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Berhasil membuat initial state dan step berikutnya',
            'examples': {
                'application/json': {
                    "state": {
                        "business_type": "restaurant",
                        "location": "Jakarta Selatan",
                        "numberOfLeads": 23,
                        "leadCount": 0,
                        "searchOffset": 0,
                        "remainingPlaceIds": []
                    },
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
            }
        },
        500: {
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
}
