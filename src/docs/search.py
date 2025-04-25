search_dict = {
    'tags': ['Task'],
    'summary': 'Search for businesses using Google Maps API',
    'description': 'Collect place IDs from Google Maps based on business type and location. Handles pagination and lead skipping.',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['businessType', 'location', 'numberOfLeads'],
                'properties': {
                    'businessType': {'type': 'string', 'example': 'coffee shop'},
                    'location': {'type': 'string', 'example': 'surabaya'},
                    'searchOffset': {'type': 'integer', 'example': 0},
                    'numberOfLeads': {'type': 'integer', 'example': 10},
                }
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Successful search',
            'schema': {
                'type': 'object',
                'properties': {
                    'state': {
                        'type': 'object',
                        'properties': {
                            'remainingPlaceIds': {
                                'type': 'array','items': {'type': 'string','example': ['abc123', 'def456']}
                            },
                            'searchOffset': {'type': 'integer','example': 0},
                        }
                    },
                    'result': {'type': 'object','nullable': True
                    },
                    'next': {
                        'type': 'object',
                        'properties': {
                            'key': {'type': 'string', 'example': 'scrape'},
                            'payload': {
                                'type': 'object',
                                'properties': {
                                    'placeId': {'type': 'string', 'example': 'abc123'},
                                    'skippedCount': {'type': 'integer', 'example': 1},
                                    'leadCount': {'type': 'integer', 'example': 5},
                                    'numberOfLeads': {'type': 'integer', 'example': 20}
                                }
                            }
                        }
                    },
                    'done': {'type': 'boolean','example': False
                    },
                    'error': {'type': 'string','nullable': True,'example': None
                    }
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