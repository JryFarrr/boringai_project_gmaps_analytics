input_dict = {
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
                    'business_type': {'type': 'string','example': 'cafe'
                    },
                    'location': {'type': 'string','example': 'Surabaya'
                    },
                    'numberOfLeads': {'type': 'integer','example': 3
                    },
                    'min_rating': {'type': 'number','format': 'float','example': 4.0
                    },
                    'min_reviews': {'type': 'integer','example': 50
                    },
                    'max_reviews': {'type': 'integer','example': 100
                    },
                    'price_range': {'type': 'string','example': '25rb-50rb'
                    },
                    'keywords': {'type': 'string','example': 'cocok buat nugas'
                    },
                    'business_hours': {'type': 'string', 'example': 'anytime'}
                },
                'required': ['business_type', 'location']
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
                        "location": "Surabaya",
                        "numberOfLeads": 10,
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
}