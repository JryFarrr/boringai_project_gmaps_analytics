search_param = {
    "tags": ["Workflow"],
    "summary": "Search for leads based on criteria",
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['state'],
                'properties': {
                    'state': {
                        'type': 'object',
                        'required': ['business_type', 'location'],
                        'properties': {
                            'business_type': {
                                'type': 'string',
                                'example': 'restaurant'
                            },
                            'location': {
                                'type': 'string',
                                'example': 'Jakarta Selatan'
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
                            },
                            'searchOffset': {
                                'type': 'integer',
                                'example': 0
                            },
                            'nextPageToken': {
                                'type': ['string', 'null'],
                                'example': None
                            }
                        }
                    }
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
                    'state': {'type': 'object'},
                    'result': {'type': 'object', 'nullable': True},
                    'next': {
                        'type': 'object',
                        'properties': {
                            'key': {'type': 'string', 'example': 'control'},
                            'payload': {
                                'type': 'object',
                                'properties': {
                                    'state': {'type': 'string', 'example': '$state'}
                                }
                            }
                        }
                    },
                    'done': {'type': 'boolean', 'example': False},
                    'error': {'type': 'string', 'nullable': True, 'example': None}
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
