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
}