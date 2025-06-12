scrape_param = {
    "tags": ["Workflow"],
    "summary": "Scrape details for a place ID",
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['placeId', 'constraints'],
                'properties': {
                    'placeId': {
                        'type': 'string',
                        'example': 'ChIJU80L2nbxaS4R_m_3MgI5JiM'
                    },
                    'constraints': {
                        'type': 'object',
                        'properties': {
                            'business_hours': {
                                'type': 'string',
                                'example': '9 AM - 10 PM'
                            },
                            'keywords': {
                                'type': 'string',
                                'example': 'terjangkau'
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
                            }
                        }
                    }
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
                                            'placeName': {
                                                'type': 'string',
                                                'example': 'Cafe Delight'
                                            },
                                            'contact': {
                                                'type': 'object',
                                                'properties': {
                                                    'phone': {
                                                        'type': 'string',
                                                        'example': '123-456-7890'
                                                    },
                                                    'website': {
                                                        'type': 'string',
                                                        'example': 'https://cafedelight.com'
                                                    }
                                                }
                                            },
                                            'priceRange': {
                                                'type': 'string',
                                                'example': '$$'
                                            },
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
                                    'leadCount': {
                                        'type': 'string',
                                        'example': '$state.leadCount'
                                    }
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
