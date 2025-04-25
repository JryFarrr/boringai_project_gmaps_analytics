from src.services.api_clients.factory import create_client
from src.utils.business_matcher import extract_key_themes

def generate_review_summaries(positive_reviews, negative_reviews):
    """
    Generates summaries for both positive and negative reviews
    
    Args:
        positive_reviews (list): List of positive review texts
        negative_reviews (list): List of negative review texts
        
    Returns:
        dict: Dictionary containing positive and negative summaries
    """
    result = {}
    
    # Get positive review summary
    if positive_reviews:
        result["positive"] = generate_review_summary(positive_reviews, "positive")
    
    # Get negative review summary
    if negative_reviews:
        result["negative"] = generate_review_summary(negative_reviews, "negative")
        
    return result

def generate_review_summary(reviews, review_type="positive", max_length=200):
    """
    Generate a concise summary of reviews using OpenAI
    
    Args:
        reviews (list): List of review texts
        review_type (str): Type of reviews ("positive" or "negative")
        max_length (int): Maximum length of the summary
    
    Returns:
        str: Concise summary of the reviews
    """
    if not reviews:
        return ""
    
    # Limit to first 5 reviews to keep token count reasonable
    reviews_text = "\n\n".join(reviews[:5])
    
    try:
        # Create client for OpenAI
        client, headers, provider = create_client()
        
        # Prepare prompt for OpenAI
        prompt = f"""Summarize the following {review_type} reviews for a business.
        Focus on extracting the key points, recurring themes, and specific elements that customers mention.
        Keep your summary concise (maximum {max_length} characters) and focus on actionable insights.
        
        Reviews:
        {reviews_text}
        """
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes business reviews concisely."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150  # Increased token count for better summaries
        )
        
        # Extract and return the summary
        summary = response.choices[0].message.content.strip()
        
        # Ensure summary is within the max length
        if len(summary) > max_length:
            summary = summary[:max_length-3] + "..."
            
        return summary
        
    except Exception as e:
        print(f"Error generating review summary: {str(e)}")
        
        # Fallback to basic summarization if API call fails
        summary_items = []
        for i, review in enumerate(reviews[:3]):
            summary_items.append(review[:100] + ("..." if len(review) > 100 else ""))
        return " | ".join(summary_items)

def extract_key_themes_from_reviews(reviews):
    """
    Extracts key themes from a list of review texts
    
    Args:
        reviews (list): List of review texts
        
    Returns:
        list: List of key themes extracted from reviews
    """
    if not reviews:
        return []
    
    return extract_key_themes(reviews)