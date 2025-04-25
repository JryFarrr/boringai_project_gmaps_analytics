scrape_dict = {
    'tags': ['Task'],
    'summary': 'Scrape business details using Google Maps API',
    'description': 'Get detailed business information from a Place ID',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['placeId', 'numberOfLeads'],
                'properties': {
                    'placeId': {'type': 'string', 'example': 'ChIJhS6qhGT51y0RUCoksi_dipo'},
                    'numberOfLeads': {'type': 'integer', 'example': 10},
                }
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Successful scrape',
            'schema': {
                'type': 'object',
                'properties': {
                    'state': {'type': 'object', 'nullable': True},
                    'next': {
                        'type': 'object',
                        'properties': {
                            'key': {'type': 'string', 'example': 'analyze'},
                            'payload': {
                                'type': 'object',
                                'properties': {
                                    'placeDetails': {
                                        'type': 'object',
                                        'properties': {
                                            'placeName': {'type': 'string', 'example': 'Cafe Delight'},
                                            'contact': {
                                                'type': 'object',
                                                'properties': {
                                                    'phone': {'type': 'string', 'example': '123-456-7890'},
                                                    'website': {'type': 'string', 'example': 'https://cafedelight.com'}
                                                }
                                            },
                                            'priceRange': {'type': 'string', 'example': '$$'},
                                            'positiveReviews': {
                                                'type': 'array',
                                                'items': {'type': 'string'},
                                                'example': ['Great vibe']
                                            },
                                            'negativeReviews': {
                                                'type': 'array',
                                                'items': {'type': 'string'},
                                                'example': ['Crowded']
                                            }
                                        }
                                    },
                                    'leadCount': {'type': 'string', 'example': '$state.leadCount'}
                                }
                            }
                        }
                    },
                    'result': {'type': 'object', 'nullable': True},
                    'done': {'type': 'boolean', 'example': False},
                    'error': {'type': 'string', 'nullable': True}
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