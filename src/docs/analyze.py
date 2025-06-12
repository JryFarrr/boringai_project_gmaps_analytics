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
                "example": {
                    "constraints": {
                        "business_hours": "9 AM - 10 PM",
                        "keywords": "terjangkau",
                        "max_reviews": 50,
                        "min_rating": 4.5,
                        "min_reviews": 30,
                        "price_range": "$"
                    },
                    "leadCount": 0,
                    "placeDetails": {
                        "address": "Jl. Dharmawangsa Raya No.6, RT.4/RW.2, Pulo, Kec. Kby. Baru, Kota Jakarta Selatan, Daerah Khusus Ibukota Jakarta 12160, Indonesia",
                        "businessHours": [
                            "Senin: 11.00–22.00",
                            "Selasa: 11.00–22.00",
                            "Rabu: 11.00–22.00",
                            "Kamis: 11.00–22.00",
                            "Jumat: 11.00–22.00",
                            "Sabtu: 11.00–22.00",
                            "Minggu: 11.00–22.00"
                        ],
                        "businessType": [
                            "restaurant",
                            "food",
                            "point_of_interest",
                            "establishment"
                        ],
                        "contact": {
                            "phone": "(021) 29044167",
                            "website": "https://plataran.com/property/plataran-dharmawangsa/"
                        },
                        "keywordFoundCount": 10,
                        "keywordMatch": "10 out of 3869 reviews mention the keyword.",
                        "negativeReviews": [],
                        "placeId": "ChIJU80L2nbxaS4R_m_3MgI5JiM",
                        "placeName": "Plataran Dharmawangsa",
                        "positiveReviews": [
                            "A hidden oasis in the heart of the city. Lunch at @plataran.dharmawangsa feels like a little escape, surrounded by lush greenery, warm service, and the calming sounds of traditional live music on the weekends.\nFrom the elegant indoor space to the breezy patio and peaceful outdoor area, the vibe is just right.\nAuthentic Indonesian flavors with premium quality, served beautifully.\nPerfect for a romantic lunch with your partner, a classy after office meet up with colleagues, or a relaxing weekend with family.",
                            "I had lunch with my husband and their service and food is just amazing. We ordered tahu nenek, kangkung belacaan, ox tail soup, nasi goreng kecombrang and dharmawangsa chicken. All the food were delicious, balance clean flavor. Not to mention, their friendly service is just superb."
                        ],
                        "priceRange": "$$$",
                        "rating": 4.6,
                        "totalRatings": 3869
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
