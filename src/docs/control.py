control_param = {
    "tags": ["Workflow"],
    "summary": "Control the lead generation workflow",
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    "business_type": {"type": "string", "example": "restaurant"},
                    "constraints": {
                        "type": "object",
                        "properties": {
                            "business_hours": {"type": "string", "example": "9 AM - 10 PM"},
                            "keywords": {"type": "string", "example": "terjangkau"},
                            "max_reviews": {"type": "integer", "example": 50},
                            "min_rating": {"type": "number", "example": 4.5},
                            "min_reviews": {"type": "integer", "example": 30},
                            "price_range": {"type": "string", "example": "$"}
                        },
                        "required": ["business_hours", "keywords", "max_reviews", "min_rating", "min_reviews", "price_range"]
                    },
                    "leadCount": {"type": "integer", "example": 1},
                    "location": {"type": "string", "example": "Jakarta Selatan"},
                    "nextPageToken": {"type": "string", "example": "AXQCQNTAWQHFfEFkUFWQrUDnWFjDEanCUHMmkCXm7-FFeD_YWJitVR1rKAmz9Qb-o8uAuT8c8kpxNZYEEvGFB3e1b7RRm8d8CO-lVDVZqGmyq7pLQYoI2BvLYhENEDXcYAJSJY6XwnjVpL9hwUyKQ6cBdnvvb2IrZ8IWwkWyKeh1vYJGX0vD81fdMZ6TUOa8hkmWEg5HIaR3D96rDWaAqPtdoYGj3XfN2fXM2F4AaIZBKxLUE4eNU7qYluMVKctDgLYhShaHViYlX6kEpAdJmfV-XEoO3JtmyDn-7m3NLt4h0Y7PhWORIeS4S6FuC9LzpGT0G-JrAHpV5s-Pu4cj5kot3XAlBKspUX7yupLuGZuaugpw-wMdAa5Gc4lVr9NB8ju0NJpEDiTmezthDHsLxpEzQEiWbCqm8jke"},
                    "numberOfLeads": {"type": "integer", "example": 23},
                    "remainingPlaceIds": {
                        "type": "array",
                        "items": {"type": "string"},
                        "example": [
                            "ChIJE1GvDtn1aS4RLfcz-MionU8",
                            "ChIJOU-DRF3xaS4RglxqldO_Chc",
                            "ChIJp5VZTgT0aS4R26oBEPT4nUw",
                            "ChIJ9_SrqF7xaS4Rdv0Jh5kKsMU",
                            "ChIJTxAy8WfxaS4Rt0KGZl6HS1Y",
                            "ChIJw5YEX7XxaS4RlLmg9SOZvCQ",
                        ]
                    },
                    "searchOffset": {"type": "integer", "example": 20}
                },
                "required": [
                    "business_type", "constraints", "leadCount", "location",
                    "nextPageToken", "numberOfLeads", "searchOffset"
                ]
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