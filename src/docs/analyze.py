analyze_dict = {
    'tags': ['Task'],
    'summary': 'Analyze and generate business insights',
    'description': 'Analyze business information, match percentage, and generate insights using OpenAI',
    'parameters': [
        {
            'name': 'data',
            'in': 'body',
            'description': 'Details for analysis and lead handling',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'leadCount': {
                        'type': 'integer',
                        'example': 0
                    },
                    'numberOfLeads': {
                        'type': 'integer',
                        'example': 3
                    },
                    'placeDetails': {
                        'type': 'object',
                        'properties': {
                            'placeName': {
                                'type': 'string',
                                'example': 'Demandailing Cafe'
                            },
                            'address': {
                                'type': 'string',
                                'example': 'Jl. Raya Jemursari No.71, Surabaya'
                            },
                            'businessHours': {
                                'type': 'array',
                                'items': {'type': 'string'},
                                'example': [
                                    "Monday: 8:00\u202fAM\u2009\u2013\u200910:00\u202fPM",
                                    "Tuesday: 8:00\u202fAM\u2009\u2013\u200910:00\u202fPM",
                                    "Wednesday: 8:00\u202fAM\u2009\u2013\u200910:00\u202fPM",
                                    "Thursday: 8:00\u202fAM\u2009\u2013\u200910:00\u202fPM",
                                    "Friday: 8:00\u202fAM\u2009\u2013\u200910:00\u202fPM",
                                    "Saturday: 8:00\u202fAM\u2009\u2013\u200910:00\u202fPM",
                                    "Sunday: 8:00\u202fAM\u2009\u2013\u200910:00\u202fPM"
                                ]
                            },
                            'businessType': {
                                'type': 'array',
                                'items': {'type': 'string'},
                                'example': ['cafe', 'restaurant', 'food',]
                            },
                            'contact': {
                                'type': 'object',
                                'properties': {
                                    'phone': {
                                        'type': 'string',
                                        'example': '(031) 8480367'
                                    },
                                    'website': {
                                        'type': 'string',
                                        'example': 'http://instagram.com/demandailingcafe'
                                    }
                                }
                            },
                            'location': {
                                'type': 'object',
                                'properties': {
                                    'lat': {
                                        'type': 'number',
                                        'format': 'float',
                                        'example': -7.3225321
                                    },
                                    'lng': {
                                        'type': 'number',
                                        'format': 'float',
                                        'example': 112.7423232
                                    }
                                }
                            },
                            'positiveReviews': {
                                'type': 'array',
                                'items': {'type': 'string'},
                                'example': [ 
                                    "Always like being here...\nA couple years ago, celebrate every moment here with friend, family or coworker\nThe have a wow portion, for 2-3 person per serving\nYou may enjoy it with friends\nMy kids always love their millecrepes and waffles\nOverall about this place is the menu never failed",
                                    "It was my very first visit to Demandailing Cafe. I went here with my friends and their babies, but we didn't reserve for a table. The staffs directly led us to a table with long couches, so the babies can sleep there. Love how attentive they are!\n\nNot to forget the food, it was so yummy. And fit those with big appetite. Overall it's a good place for having a lunch.",
                                    "Good services and kind staff. Nice atmosphere. Located beside main road. Easy to find. Large park. Arabica coffee.",   
                                    "Best pancake I've ever tasted.\nThe place more spaces than Klampis branch had.\nThe services was great. The meals came after waiting Less than 5 minutes."
                                ]
                            },
                            'negativeReviews': {
                                'type': 'array',
                                'items': {'type': 'string'},
                                'example': ["The cashier & greater are not friendly.  The smoking area is dirty and smells like a cat's poop."]
                            },
                            'priceRange': {'type': 'string','example': '$$'
                            },
                            'rating': {'type': 'number','format': 'float','example': 4.5
                            },
                            'totalRatings': {'type': 'integer','example': 4202
                            }
                        }
                    },
                    'skippedCount': {
                        'type': 'integer',
                        'example': 0
                    },
                    'constraints': {
                        'type': 'object',
                        'properties': {
                            'min_rating': {'type': 'number','format': 'float','example': 4.0
                            },
                            'min_reviews': {'type': 'integer','example': 50
                            },
                            'max_reviews': {'type': 'integer','example': 100
                            },
                            'price_range': {'type': 'string','example': '$$'
                            },
                            'business_hours': {'type': 'string','example': 'anytime'
                            },
                            'keywords': {'type': 'string','example': 'cocok buat nugas'
                            }
                        }
                    }
                },
                'required': ['placeDetails', 'leadCount']
            }
        }
    ],
    'responses': {
        '200': {
            'description': 'Successful analysis and insights',
            'schema': {
                'type': 'object',
                'properties': {
                    'placeName': {'type': 'string'},
                    'matchPercentage': {'type': 'number'},
                    'strengths': {'type': 'array', 'items': {'type': 'string'}},
                    'weaknesses': {'type': 'array', 'items': {'type': 'string'}},
                    'fitScore': {'type': 'number'},
                    'fitReason': {'type': 'string'}
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