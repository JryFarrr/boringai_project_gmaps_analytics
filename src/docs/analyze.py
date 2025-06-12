analyze_param = {
    "tags": ["Workflow"],
    "summary": "Analyze place details with user-defined constraints",
    "parameters": [
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "properties": {
                    "constraints": {
                        "type": "object",
                        "properties": {
                            "business_hours": {"type": "string", "example": "9 AM - 10 PM"},
                            "keywords": {"type": "string", "example": "terjangkau"},
                            "max_reviews": {"type": "integer", "example": 50},
                            "min_rating": {"type": "number", "example": 4.5},
                            "min_reviews": {"type": "integer", "example": 30},
                            "price_range": {"type": "string", "example": "$"}
                        }
                    },
                    "leadCount": {"type": "integer", "example": 0},
                    "placeDetails": {
                        "type": "object",
                        "properties": {
                            "address": {"type": "string"},
                            "businessHours": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "businessType": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "contact": {
                                "type": "object",
                                "properties": {
                                    "phone": {"type": "string"},
                                    "website": {"type": "string"}
                                }
                            },
                            "keywordFoundCount": {"type": "integer"},
                            "keywordMatch": {"type": "string"},
                            "negativeReviews": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "placeId": {"type": "string"},
                            "placeName": {"type": "string"},
                            "positiveReviews": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "priceRange": {"type": "string"},
                            "rating": {"type": "number"},
                            "totalRatings": {"type": "integer"}
                        }
                    }
                }
            }
        }
    ],
    "responses": {
        200: {
            "description": "Successful analysis",
            "schema": {
                "type": "object",
                "properties": {
                    "state": {"type": "object"},
                    "result": {"type": "object", "nullable": True},
                    "next": {
                        "type": "object",
                        "properties": {
                            "key": {"type": "string", "example": "control"},
                            "payload": {
                                "type": "object",
                                "properties": {
                                    "state": {"type": "string", "example": "$state"}
                                }
                            }
                        }
                    },
                    "done": {"type": "boolean", "example": False},
                    "error": {"type": "string", "nullable": True, "example": None}
                }
            }
        },
        500: {
            "description": "Internal server error",
            "schema": {
                "type": "object",
                "properties": {
                    "state": {"type": "object"},
                    "result": {"type": "object"},
                    "next": {
                        "type": "object",
                        "properties": {
                            "key": {"type": "string"},
                            "payload": {"type": "object"}
                        }
                    },
                    "done": {"type": "boolean"},
                    "error": {"type": "string"}
                }
            }
        }
    }
}
