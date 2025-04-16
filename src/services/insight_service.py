import json
from src.services.api_clients.factory import create_client

def generate_business_insights(place_details, match_percentage, match_analysis=None):
    """
    Generate business insights and recommendations using OpenAI
    
    Args:
        place_details (dict): Details about the business
        match_percentage (float): Match percentage calculated
        match_analysis (dict): Analysis of the match percentage
    
    Returns:
        dict: Dictionary containing insights and recommendations
    """
    try:
        # Create client for OpenAI
        client, headers, provider = create_client(provider="openai")
        
        # Extract key information for the prompt
        business_name = place_details.get("placeName", "")
        business_type = place_details.get("businessType", [])
        rating = place_details.get("rating", 0)
        total_ratings = place_details.get("totalRatings", 0)
        price_range = place_details.get("priceRange", "")
        
        # Get positive and negative reviews
        positive_reviews = place_details.get("positiveReviews", [])[:3]  # Limit to first 3
        negative_reviews = place_details.get("negativeReviews", [])[:3]  # Limit to first 3
        
        positive_text = "\n".join(positive_reviews) if positive_reviews else ""
        negative_text = "\n".join(negative_reviews) if negative_reviews else ""
        
        # Include match analysis if available
        analysis_text = ""
        if match_analysis and "reasoning" in match_analysis:
            analysis_text = f"Match Analysis: {match_analysis['reasoning']}"
        
        # Prepare prompt for OpenAI
        prompt = f"""Analyze the following business information and provide insights:

        Business Name: {business_name}
        Business Type: {', '.join(business_type) if isinstance(business_type, list) else business_type}
        Rating: {rating}/5 (from {total_ratings} reviews)
        Price Range: {price_range}
        Match Percentage: {match_percentage}%
        {analysis_text}
        
        Sample Positive Reviews:
        {positive_text}
        
        Sample Negative Reviews:
        {negative_text}
        
        Please provide:
        1. A brief assessment of the business's strengths (2-3 points)
        2. A brief assessment of the business's weaknesses (2-3 points)
        3. Potential fit score (0-100) as a lead and a brief explanation why
        
        Format your response as JSON with the keys: "strengths", "weaknesses", "fitScore", and "fitReason".
        """
        
        # Call OpenAI API with JSON mode enabled
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a business analyst that provides insights in JSON format only."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            max_tokens=300
        )
        
        # Extract and return the insights
        insights_json = response.choices[0].message.content.strip()
        insights = json.loads(insights_json)
        
        return insights
        
    except Exception as e:
        print(f"Error generating business insights: {str(e)}")
        # Fallback to basic insights
        return {
            "strengths": ["Based on available reviews"],
            "weaknesses": ["Insufficient data for detailed analysis"],
            "fitScore": int(match_percentage),
            "fitReason": "Score based on match percentage only"
        }