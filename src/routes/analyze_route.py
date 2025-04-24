from flask import request, jsonify, current_app
from flasgger import swag_from
import json
import traceback
from src.utils.response_utils import error_response
from src.services.match_services import check_place_constraints
from src.services.review_service import generate_review_summaries, extract_key_themes_from_reviews
from src.services.insight_service import generate_business_insights
# Import fungsi untuk menghitung keyword dari library yang sudah dimodifikasi
from src.services.google_maps_service import count_keyword_in_reviews

@swag_from({
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
                    'leadCount': {'type': 'integer', 'example': 0},
                    'searchKeyword': {'type': 'string', 'example': 'instagramable'}
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
                    'fitReason': {'type': 'string'},
                    'keywordAnalysis': {
                        'type': 'object',
                        'properties': {
                            'keywordMatches': {'type': 'integer'},
                            'totalReviews': {'type': 'integer'},
                            'message': {'type': 'string'},
                            'foundKeywords': {'type': 'object'},
                            'relatedKeywords': {'type': 'array', 'items': {'type': 'string'}},
                            'synonymMapping': {'type': 'object'}
                        }
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
})
def analyze_route():
    """
    Handle the analyze task endpoint
    - Processes place details and constraints
    - Calculates match percentage based on various criteria
    - Uses OpenAI to generate insightful review summaries
    - Counts keyword matches in reviews
    - Returns formatted response with match results
    """
    try:
        data = request.get_json()
        if not data or "placeDetails" not in data or "leadCount" not in data:
            return error_response("Missing required fields: placeDetails or leadCount")

        place_details = data["placeDetails"]
        lead_count = data["leadCount"]
        constraints = data.get("constraints", {})
        skipped_count = data.get("skippedCount", 0)
        
        # Mendapatkan keyword pencarian jika ada
        search_keyword = data.get("searchKeyword", "")
        
        # Check if place meets constraints
        meets_constraints, match_percentage, match_analysis = check_place_constraints(place_details, constraints)
        
        # If constraints not met, return skip response
        if not meets_constraints:
            response = create_skip_response(lead_count, skipped_count)
            return jsonify(response), 200
        
        # Process reviews and generate summaries
        positive_reviews = place_details.get("positiveReviews", [])
        negative_reviews = place_details.get("negativeReviews", [])
        all_reviews = positive_reviews + negative_reviews
        
        # Get summaries and key themes
        summaries = generate_review_summaries(positive_reviews, negative_reviews)
        key_themes = extract_key_themes_from_reviews(all_reviews)
        
        # Generate business insights
        insights = generate_business_insights(place_details, match_percentage, match_analysis)

        # Hitung keyword matches jika ada search keyword
        keyword_analysis = {
            "keywordMatches": 0,
            "totalReviews": len(all_reviews),
            "message": "0 keyword found from 0 reviews",
            "foundKeywords": {},
            "relatedKeywords": [],
            "synonymMapping": {}
        }
        
        # Fungsi untuk menampilkan semua review
        def print_all_reviews(reviews):
            """Print semua review untuk debugging"""
            results = []
            for i, review in enumerate(reviews):
                if isinstance(review, dict) and "text" in review:
                    review_text = review["text"]
                elif isinstance(review, str):
                    review_text = review
                else:
                    review_text = str(review)
                
                # Potong review jika terlalu panjang
                if len(review_text) > 100:
                    review_text = review_text[:100] + "..."
                    
                results.append(f"Review #{i+1}: {review_text}")
            
            return "\n".join(results)
        
                # Di dalam fungsi analyze_route, bagian yang menangani keyword analysis:
        if search_keyword and all_reviews:
            try:
                current_app.logger.info(f"Search keyword: '{search_keyword}'")
                current_app.logger.info(f"Total reviews: {len(all_reviews)}")
                
                # Format review untuk kompatibilitas
                formatted_reviews = []
                for review_text in all_reviews:
                    if isinstance(review_text, str):
                        formatted_reviews.append({"text": review_text})
                    elif isinstance(review_text, dict) and "text" in review_text:
                        formatted_reviews.append(review_text)
                    else:
                        formatted_reviews.append({"text": str(review_text)})
                
                # Log format review
                current_app.logger.info(f"Raw review sample: {all_reviews[0] if all_reviews else 'No reviews'}")
                current_app.logger.info(f"Formatted review sample: {formatted_reviews[0] if formatted_reviews else 'No reviews'}")
                
                # Coba dengan fungsi asli terlebih dahulu
                try:
                    keyword_analysis = count_keyword_in_reviews(search_keyword, formatted_reviews)
                    current_app.logger.info(f"Original keyword analysis result: {json.dumps(keyword_analysis)}")
                except Exception as e:
                    current_app.logger.error(f"Original keyword analysis failed: {str(e)}")
                    # Jika gagal, gunakan fungsi manual sebagai fallback
                    keyword_analysis = manual_count_keyword_in_reviews(search_keyword, formatted_reviews)
                    current_app.logger.info(f"Manual keyword analysis result: {json.dumps(keyword_analysis)}")
                
                
                # Periksa format review
                if formatted_reviews:
                    sample_review = formatted_reviews[0]
                    if isinstance(sample_review, dict) and "text" in sample_review:
                        current_app.logger.info("Review format appears correct - contains 'text' key")
                    else:
                        current_app.logger.error(f"Review format may be incorrect: {sample_review}")
                        # Coba perbaiki format
                        fixed_reviews = []
                        for review in formatted_reviews:
                            if isinstance(review, str):
                                fixed_reviews.append({"text": review})
                            elif isinstance(review, dict) and "text" not in review:
                                fixed_reviews.append({"text": str(review)})
                            else:
                                fixed_reviews.append(review)
                        formatted_reviews = fixed_reviews
                        current_app.logger.info(f"Fixed review format sample: {formatted_reviews[0]}")
                
                # Fungsi debug untuk memeriksa apakah keyword benar-benar ada dalam review
                def debug_keyword_search(search_keyword, reviews):
                    """Fungsi debug untuk memeriksa apakah keyword benar-benar ada dalam review"""
                    found_matches = []
                    keyword_lower = search_keyword.lower()
                    
                    for i, review in enumerate(reviews):
                        review_text = review.get("text", "").lower()
                        if keyword_lower in review_text:
                            found_matches.append({
                                "review_index": i,
                                "review_text": review_text[:100] + "...",  # Truncate long review
                                "position": review_text.find(keyword_lower)
                            })
                    
                    return {
                        "keyword": search_keyword,
                        "matches_found": len(found_matches),
                        "match_details": found_matches[:3]  # Limit to first 3 matches
                    }
                
                # Panggil fungsi debug
                debug_result = debug_keyword_search(search_keyword, formatted_reviews)
                current_app.logger.info(f"DEBUG SEARCH RESULT: {json.dumps(debug_result, indent=2)}")
                
                # Ubah fungsi manual_count_keyword_in_reviews di route handler
                def manual_count_keyword_in_reviews(keyword, reviews):
                    total_reviews = len(reviews)
                    keyword_count = 0
                    found_keywords = {}
                    
                    if not keyword or not reviews:
                        return {
                            "keywordMatches": 0,
                            "totalReviews": total_reviews,
                            "message": f"0 keyword found from {total_reviews} reviews",
                            "foundKeywords": {},
                            "relatedKeywords": [],
                            "synonymMapping": {}
                        }
                    
                    # Case insensitive search
                    keyword_lower = keyword.lower()
                    
                    # Standardize review format
                    standardized_reviews = []
                    for review in reviews:
                        if isinstance(review, dict) and "text" in review:
                            standardized_reviews.append(review)
                        elif isinstance(review, str):
                            standardized_reviews.append({"text": review})
                        else:
                            try:
                                standardized_reviews.append({"text": str(review)})
                            except:
                                continue
                    
                    # Track matching reviews and occurrences
                    matching_reviews = []
                    
                    for review in standardized_reviews:
                        # Extract text based on review format
                        review_text = review.get("text", "").lower()
                        
                        # Count keyword occurrences
                        matches = review_text.count(keyword_lower)
                        if matches > 0:
                            keyword_count += matches
                            matching_reviews.append(review_text[:100] + "...")  # Save partial review text
                            
                            # Update found_keywords
                            if keyword not in found_keywords:
                                found_keywords[keyword] = 0
                            found_keywords[keyword] += matches
                    
                    message = f"{keyword_count} instances of '{keyword}' found in {len(matching_reviews)} out of {total_reviews} reviews"
                    
                    return {
                        "keywordMatches": keyword_count,
                        "totalReviews": total_reviews,
                        "message": message,
                        "foundKeywords": found_keywords,
                        "relatedKeywords": [keyword],
                        "synonymMapping": {},
                        "matchingReviews": matching_reviews[:3]  # For debugging
                    }
                # Gunakan fungsi manual
                keyword_analysis = manual_count_keyword_in_reviews(search_keyword, formatted_reviews)
                current_app.logger.info(f"Manual keyword analysis result: {json.dumps(keyword_analysis)}")
                
                # Coba juga menggunakan fungsi asli (hanya sebagai perbandingan untuk debugging)
                try:
                    original_analysis = count_keyword_in_reviews(search_keyword, formatted_reviews)
                    current_app.logger.info(f"Original keyword analysis result: {json.dumps(original_analysis)}")
                    
                    # Jika original_analysis berhasil dan mengembalikan hasil yang lebih baik, gunakan itu
                    if original_analysis and "keywordMatches" in original_analysis and original_analysis["keywordMatches"] > 0:
                        keyword_analysis = original_analysis
                except Exception as e:
                    current_app.logger.error(f"Original keyword analysis failed: {str(e)}")
                
                # Hapus data debugging yang tidak perlu dikembalikan ke client
                if "matchingReviews" in keyword_analysis:
                    del keyword_analysis["matchingReviews"]
                
            except Exception as e:
                current_app.logger.error(f"Error in keyword analysis: {str(e)}")
                current_app.logger.error(traceback.format_exc())
        
        # Create and return response
        result = create_result_object(place_details, match_percentage, match_analysis, 
                                      summaries, key_themes, insights, keyword_analysis,
                                      search_keyword)
        
        response = {
            "state": {
                "leadCount": lead_count + 1,
                "skippedCount": skipped_count,
                "searchKeyword": search_keyword  # Tambahkan keyword ke state untuk digunakan di next request
            },
            "result": result,
            "next": {
                "key": "control",
                "payload": {
                    "leadCount": "$state.leadCount",
                    "numberOfLeads": "$state.numberOfLeads",
                    "remainingPlaceIds": "$state.remainingPlaceIds",
                    "searchOffset": "$state.searchOffset",
                    "nextPageToken": "$state.nextPageToken",
                    "businessType": "$state.businessType",
                    "location": "$state.location",
                    "skippedCount": "$state.skippedCount",
                    "searchKeyword": "$state.searchKeyword"  # Tambahkan keyword ke next payload
                }
            },
            "done": False,
            "error": None
        }
        return jsonify(response), 200

    except Exception as e:
        current_app.logger.error(f"Analyze route failed: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        return error_response(f"Analyze route failed: {str(e)}", 500)

def create_skip_response(lead_count, skipped_count):
    """
    Creates a response object for skipping a place that doesn't meet constraints
    
    Args:
        lead_count (int): Current count of leads
        skipped_count (int): Current count of skipped places
        
    Returns:
        dict: Response object with skip signal
    """
    return {
        "state": {
            "leadCount": lead_count,
            "skippedConstraints": True,
            "skippedCount": skipped_count + 1
        },
        "result": None,
        "next": {
            "key": "control",
            "payload": {
                "leadCount": "$state.leadCount",
                "numberOfLeads": "$state.numberOfLeads",
                "remainingPlaceIds": "$state.remainingPlaceIds",
                "searchOffset": "$state.searchOffset",
                "nextPageToken": "$state.nextPageToken",
                "businessType": "$state.businessType",
                "location": "$state.location",
                "skippedConstraints": True,
                "skippedCount": "$state.skippedCount",
                "searchKeyword": "$state.searchKeyword"  # Tambahkan keyword ke payload
            }
        },
        "done": False,
        "error": None
    }

def create_result_object(place_details, match_percentage, match_analysis, summaries, key_themes, insights, keyword_analysis, search_keyword=""):
    """
    Creates the result object with all business analysis data
    
    Args:
        place_details (dict): Details about the business
        match_percentage (float): Match percentage calculated
        match_analysis (dict): Analysis of the match percentage
        summaries (dict): Summaries of positive and negative reviews
        key_themes (list): Key themes extracted from reviews
        insights (dict): Business insights and recommendations
        keyword_analysis (dict): Hasil analisis kemunculan keyword dalam review
        search_keyword (str): Kata kunci yang digunakan untuk pencarian
        
    Returns:
        dict: Formatted result object
    """
    result = {
        "placeName": place_details["placeName"],
        "matchPercentage": match_percentage,
        "businessType": place_details.get("businessType", []),
        "rating": place_details.get("rating", 0),
        "totalRatings": place_details.get("totalRatings", 0),
        "priceLevel": place_details.get("priceRange", "")
    }
    
    # Tambahkan hasil analisis keyword dengan data lengkap dari fungsi yang sudah diperbarui
    if keyword_analysis:
        result["keywordAnalysis"] = {
            "keywordMatches": keyword_analysis.get("keywordMatches", 0),
            "totalReviews": keyword_analysis.get("totalReviews", 0),
            "message": keyword_analysis.get("message", f"0 keyword found from 0 reviews"),
            "searchKeyword": search_keyword
        }
        
        # Tambahkan informasi baru dari fungsi yang diperbarui
        if "foundKeywords" in keyword_analysis:
            result["keywordAnalysis"]["foundKeywords"] = keyword_analysis["foundKeywords"]
            
        if "relatedKeywords" in keyword_analysis:
            result["keywordAnalysis"]["relatedKeywords"] = keyword_analysis["relatedKeywords"]
            
        if "synonymMapping" in keyword_analysis:
            result["keywordAnalysis"]["synonymMapping"] = keyword_analysis["synonymMapping"]
    
    # Add match analysis reasoning if available
    if match_analysis and "reasoning" in match_analysis:
        result["matchReasoning"] = match_analysis["reasoning"]
    
    # Add detailed factor scores if available
    if match_analysis and "analysis" in match_analysis:
        result["matchFactors"] = match_analysis["analysis"]
    
    # Add summaries if they exist
    if "positive" in summaries and summaries["positive"]:
        result["summaryPositiveReviews"] = summaries["positive"]
    if "negative" in summaries and summaries["negative"]:
        result["summaryNegativeReviews"] = summaries["negative"]
    
    # Add key themes
    if key_themes:
        result["keyThemes"] = key_themes
    
    # Add insights
    if insights:
        result["strengths"] = insights.get("strengths", [])
        result["weaknesses"] = insights.get("weaknesses", [])
        result["fitScore"] = insights.get("fitScore", match_percentage)
        result["fitReason"] = insights.get("fitReason", "")
        
    # Add contact information if available
    if "contact" in place_details:
        result["contact"] = place_details["contact"]
        
    # Add address if available
    if "address" in place_details:
        result["address"] = place_details["address"]
    
    # Add business hours if available
    if "businessHours" in place_details:
        result["businessHours"] = place_details["businessHours"]
        
    return result