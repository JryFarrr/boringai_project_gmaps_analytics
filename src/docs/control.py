control_dict =  {
    'tags': ['Task'],
    'summary': 'Handle control task workflow',
    'parameters': [
        {
            'name': 'data',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'leadCount': {'type': 'integer','example': 5
                    },
                    'numberOfLeads': {'type': 'integer','example': 10
                    },
                    'remainingPlaceIds': {
                        'type': 'array',
                        'items': {
                            'type': 'string'
                        },
                        'example': ['placeId1', 'placeId2', 'placeId3']
                    },
                    'searchOffset': {'type': 'integer','example': 2
                    },
                    'nextPageToken': {'type': 'string','example': 'nextPageTokenExample'
                    },
                    'business_type': {'type': 'string','example': 'restaurant'
                    },
                    'location': {'type': 'string','example': 'New York, NY'
                    },
                    'skippedConstraints': {'type': 'boolean','example': True
                    },
                    'skippedCount': {'type': 'integer','example': 1
                    }
                },
                'required': ['leadCount', 'numberOfLeads']
            }
        }
    ],
    'responses': {
        '200': {
            'description': 'Successfully handled the control flow.',
            'schema': {
                'type': 'object',
                'properties': {
                    'state': {'type': 'object'},
                    'result': {'type': 'object'},
                    'next': {
                        'type': 'object',
                        'properties': {
                            'key': {'type': 'string'},
                            'payload': {
                                'type': 'object',
                                'properties': {
                                    'placeId': {'type': 'string'},
                                    'leadCount': {'type': 'integer'},
                                    'numberOfLeads': {'type': 'integer'},
                                    'skippedCount': {'type': 'integer'}
                                }
                            }
                        }
                    },
                    'done': {'type': 'boolean'},
                    'error': {'type': 'string'}
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