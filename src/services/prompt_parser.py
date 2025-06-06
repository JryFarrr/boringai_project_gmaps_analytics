"""
Module for parsing user prompts and extracting search parameters with enhanced paraphrase detection
"""

import json
import re
from src.config.config import DEFAULT_SEARCH_PARAMS
from src.services.api_clients.factory import create_client
from src.utils.response_utils import error_response

def get_system_prompt():
    """
    Get the system prompt for parameter extraction with enhanced keyword detection
    
    Returns:
        str: System prompt
    """
    return """You are an expert system for extracting structured business search parameters from user queries in both English and Indonesian.

Your job is to analyze a search query and extract precise parameters for a business discovery system.

LANGUAGE HANDLING:
You can process queries in both English and Indonesian. Be aware of these language-specific nuances:
- In Indonesian, descriptive terms often come after the noun (e.g., "hotel mewah" = "luxury hotel")
- Paraphrasing and synonyms should be recognized in both languages
- Detect keywords even when they are expressed indirectly or through implication

KEYWORD DETECTION:
1. Extract explicit keywords mentioned directly (e.g., "with keywords: cozy, stylish")
2. Detect implicit keywords from context and descriptions (e.g., "I want a place that feels homey" → keyword: "homey")
3. Capture paraphrased concepts (e.g., "a place with a relaxed atmosphere" → keyword: "relaxed")
4. Recognize both English and Indonesian descriptive terms:
   - English examples: cozy, luxury, affordable, high-end, family-friendly
   - Indonesian examples: mewah (luxury), nyaman (comfortable), terjangkau (affordable), ramah keluarga (family-friendly)
5. Include attribute-value pairs when mentioned (e.g., "with outdoor seating" → keyword: "outdoor seating")
6. Extract keywords from subjective descriptions (e.g., "a restaurant with amazing views" → keyword: "amazing views")

PRICE RANGE CLASSIFICATION:
When encountering price information in any currency or format, classify it into standard price level symbols ($, $$, $$$, $$$$) based on relative affordability within the local context.

Follow these guidelines:
1. Analyze the price information relative to the business type and location mentioned
2. Convert any price format (numerical values, ranges, or descriptive terms) into the appropriate price level symbol
3. Consider local economic context when determining affordability
4. For any currency, classify based on relative expense level:
   • $ = Budget/Inexpensive (bottom 25% price range for that business type in that location)
   • $$ = Moderate (25-50% price range)
   • $$$ = Upscale (50-75% price range)
   • $$$$ = Luxury/Premium (top 25% price range)
5. For text descriptions without numbers:
   • Terms like "cheap," "budget," "affordable," "murah," "terjangkau" → $
   • Terms like "moderate," "standard," "average," "sedang," "standar" → $$
   • Terms like "upscale," "premium," "high-end," "premium," "kelas atas" → $$$
   • Terms like "luxury," "exclusive," "VIP," "mewah," "eksklusif" → $$$$
6. Always normalize the output to use only standard price level symbols regardless of input format

INPUT FORMAT:
The user will provide a query in either English or Indonesian that describes their business search requirements. 
Examples:
- "Find a luxury hotel in Bali with at least 4.5 rating"
- "Cari restoran Indonesia di Jakarta dengan harga terjangkau dan rating minimal 4.2"
- "I need a pet-friendly café in Seattle that's open late"
- "Temukan salon kecantikan di Bandung dengan suasana yang nyaman dan pelayanan ramah"

OUTPUT FORMAT:
You must return ONLY a valid JSON object with these exact fields (no explanations or other text):
{
  "business_type": "The core business type or category",
  "location": "The exact location mentioned", 
  "min_rating": float, // The minimum rating as a decimal number (e.g., 4.2)
  "min_reviews": int, // The minimum number of reviews as an integer
  "max_reviews": int, // The maximum number of reviews as an integer, null if not mentioned
  "price_range": "The exact price range mentioned (e.g., '$', '$$', '$$$')",
  "business_hours": "The exact business hours requirement",
  "keywords": "All descriptive adjectives or specific qualities mentioned, comma-separated",
  "numberOfLeads": "" // The number of establishments to search from
}

RULES:
1. Return ONLY valid JSON - no explanations, intro text, or markdown
2. Convert text numbers to numeric types (e.g., "four point five" → 4.5, "empat koma lima" → 4.5)
3. If a parameter is missing, use these defaults:
   - min_rating: 0
   - min_reviews: 0
   - max_reviews: null (indicating no upper limit)
   - price_range: "" (empty string)
   - business_hours: "anytime"
   - keywords: "" (empty string)
   - numberOfLeads: "" (empty string if not explicitly mentioned)
4. For business hours, preserve the exact wording (e.g., "open now", "buka 24 jam")
5. For "numberOfLeads", extract the total number of establishments to search from
6. For "business_type", extract the core business type
7. For "keywords", include:
   - Any descriptive adjectives found throughout the query
   - Environmental factors (e.g., "quiet", "tenang", "with a view", "dengan pemandangan")
   - Service qualities (e.g., "friendly staff", "pelayanan ramah")
   - Facility features (e.g., "free wifi", "wifi gratis", "outdoor seating", "tempat duduk luar")
   - Atmospherics (e.g., "romantic", "romantis", "lively", "ramai")
   - Special accommodations (e.g., "pet-friendly", "ramah hewan peliharaan")
   - Customer experience factors (e.g., "quick service", "layanan cepat")
8. If a descriptive term like "luxury" or "mewah" is used and no explicit price range is provided, infer an appropriate price_range.
9. **Conditional Price Range:** Only extract or infer a `price_range` if the `business_type` is 'restaurant', 'cafe', 'bar', 'hotel', or their direct synonyms and translations (e.g., 'restoran', 'kafe', 'kedai kopi', 'warung'). For ALL other business types (like 'salon', 'workshop', 'store', 'bengkel', 'toko'), you MUST set `price_range` to an empty string (""), even if the query mentions price-related terms like 'cheap' or 'expensive'.

EXAMPLES:

Input: "Find 3 luxury hotels in Surabaya that has a rating of at least 4.5 and at least 100 reviews."
Output: {"business_type":"hotels","location":"Surabaya","min_rating":4.5,"min_reviews":100,"max_reviews":null,"price_range":"$$$$","business_hours":"anytime","keywords":"luxury","numberOfLeads":3}

Input: "Temukan 5 warung makan di Yogyakarta dengan harga di bawah Rp20.000 per porsi dan suasana tradisional."
Output: {"business_type":"warung makan","location":"Yogyakarta","min_rating":0,"min_reviews":0,"max_reviews":null,"price_range":"$","business_hours":"anytime","keywords":"harga terjangkau, suasana tradisional","numberOfLeads":5}

Input: "Find a salon in Bandung that has a rating of at least 4.2 and at most 50 reviews. Additional Requirements: • The business must have a price range of Rp50.000 - Rp100.000. • The business operates at open now. • Business reviews and descriptions must include 'premium, luxury, service'."
Output: {"business_type":"salon","location":"Bandung","min_rating":4.2,"min_reviews":0,"max_reviews":50,"price_range":"$$","business_hours":"open now","keywords":"premium, luxury, service","numberOfLeads":""}

Input: "Cari salon kecantikan yang murah di Surabaya"
Output: {"business_type":"salon kecantikan","location":"Surabaya","min_rating":0,"min_reviews":0,"max_reviews":null,"price_range":"","business_hours":"anytime","keywords":"murah","numberOfLeads":""}

Input: "Butuh restoran di Surabaya yang makanannya enak dan tempatnya nyaman untuk kumpul dengan teman-teman."
Output: {"business_type":"restoran","location":"Surabaya","min_rating":0,"min_reviews":0,"max_reviews":null,"price_range":"","business_hours":"anytime","keywords":"makanan enak, tempat nyaman, kumpul dengan teman-teman","numberOfLeads":""}
"""

def parse_prompt_with_ai(prompt, client, headers, provider="openai"):
    """
    Parse the user prompt using an LLM API to extract search parameters
    with enhanced keyword detection for paraphrased concepts
    
    Args:
        prompt (str): User prompt in any format (English or Indonesian)
        client: API client (OpenAI)
        headers (dict): Headers for the API request
        provider (str): API provider ("openai" or "openrouter")
        
    Returns:
        dict: Dictionary containing extracted search parameters or None if parsing fails
    """
    try:
        # Common parameters for both APIs
        chat_params = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": get_system_prompt()},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"},  # Force JSON response
            "temperature": 0.2  # Lower temperature for more consistent extraction
        }
        
        # Add extra_headers for OpenRouter
        if provider == "openrouter" and headers:
            chat_params["extra_headers"] = headers
        
        # Make the API call
        completion = client.chat.completions.create(**chat_params)
        
        # Parse the JSON response
        response_text = completion.choices[0].message.content
        parsed_parameters = json.loads(response_text)
        
        # Validate and convert numeric types
        parsed_parameters["min_rating"] = float(parsed_parameters.get("min_rating", 0))
        parsed_parameters["min_reviews"] = int(parsed_parameters.get("min_reviews", 0))
        
        # Handle max_reviews - convert to int if present, otherwise keep as None
        if "max_reviews" in parsed_parameters and parsed_parameters["max_reviews"] is not None:
            parsed_parameters["max_reviews"] = int(parsed_parameters["max_reviews"])
        
        # Ensure numberOfLeads is present but empty if not specified
        if "numberOfLeads" not in parsed_parameters:
            parsed_parameters["numberOfLeads"] = ""
        elif parsed_parameters["numberOfLeads"] not in ["", None]:
            # Try to convert numberOfLeads to integer if it's a string representation of a number
            try:
                parsed_parameters["numberOfLeads"] = int(parsed_parameters["numberOfLeads"])
            except (ValueError, TypeError):
                # Keep it as is if conversion fails
                pass
        
        # Set default values for missing parameters
        for key, default_value in DEFAULT_SEARCH_PARAMS.items():
            if key != "numberOfLeads" and key != "max_reviews" and (key not in parsed_parameters or parsed_parameters[key] is None):
                parsed_parameters[key] = default_value
        
        # Ensure max_reviews is included in the response
        if "max_reviews" not in parsed_parameters:
            parsed_parameters["max_reviews"] = None
                
        return parsed_parameters
        
    except Exception as e:
        print(f"Error in parsing with AI ({provider}): {str(e)}")
        # Fall back to the enhanced regex parsing
        return enhanced_regex_pattern_parsing(prompt)


def enhanced_regex_pattern_parsing(prompt):
    """
    Enhanced fallback method using regex pattern matching to extract search parameters
    with better support for paraphrasing and bilingual detection
    
    Args:
        prompt (str): User prompt in English or Indonesian
        
    Returns:
        dict: Dictionary with extracted parameters
    """
    # Initialize with default values
    parameters = DEFAULT_SEARCH_PARAMS.copy()
    parameters["numberOfLeads"] = ""
    parameters["max_reviews"] = None
    parameters["keywords"] = ""
    
    # Detect language (simple heuristic)
    is_indonesian = bool(re.search(r'\b(cari|temukan|butuh|dengan|yang|dan|di|untuk|harga|minimal|paling|sedikit|banyak)\b', 
                                  prompt.lower()))
    
    # Extract business type and location (English pattern)
    if not is_indonesian:
        match = re.search(r"(?:Find|Looking for|I need|I want|Get me|Show me|Discover)(?: a| an| some)? (.*?) (?:in|near|around|at) ([\w\s]+?)(?:$| that| with| which| having| where| from| \.|,)", prompt, re.IGNORECASE)
        if match:
            parameters['business_type'] = match.group(1).strip()
            parameters['location'] = match.group(2).strip()
    else:
        # Indonesian pattern
        match = re.search(r"(?:Cari|Temukan|Butuh|Saya mencari|Saya ingin|Saya butuh|Tolong carikan)(?: sebuah| beberapa)? (.*?) (?:di|dekat|sekitar|wilayah) ([\w\s]+?)(?:$| yang| dengan| dimana| dari| \.|,)", prompt, re.IGNORECASE)
        if match:
            parameters['business_type'] = match.group(1).strip()
            parameters['location'] = match.group(2).strip()
    
    # Extract number of leads (total to search from)
    leads_patterns = [
        r"(?:Find|Show|Get|Give me) (\d+) (?:.*?) (?:in|near|at)",  # English
        r"(?:Cari|Temukan|Berikan) (\d+) (?:.*?) (?:di|dekat|sekitar)",  # Indonesian
        r"from (\d+) (?:places|businesses|stores|shops|restaurants)",  # English "from N places"
        r"dari (\d+) (?:tempat|bisnis|toko|restoran)"  # Indonesian "dari N tempat"
    ]
    
    for pattern in leads_patterns:
        match = re.search(pattern, prompt, re.IGNORECASE)
        if match:
            parameters['numberOfLeads'] = int(match.group(1))
            break
    
    # Extract minimum rating (both languages)
    rating_patterns = [
        r"rating (?:of |is |)(?:at least|minimal|minimum|paling sedikit) ([0-9,\.]+)",
        r"(?:with|dengan) (?:at least |minimal |minimum |paling sedikit |)(?:a |)rating (?:of |sebesar |)([0-9,\.]+)",
        r"rating (?:above|above|di atas|lebih dari) ([0-9,\.]+)",
        r"(?:rating|nilai) ([0-9,\.]+) (?:ke atas|atau lebih)",
        r"dengan nilai ([0-9,\.]+) (?:ke atas|atau lebih)"
    ]
    
    for pattern in rating_patterns:
        match = re.search(pattern, prompt, re.IGNORECASE)
        if match:
            # Replace Indonesian comma with dot for decimal
            rating_str = match.group(1).replace(',', '.')
            parameters['min_rating'] = float(rating_str)
            break
    
    # Extract review count patterns (both languages)
    # Between X and Y reviews
    between_reviews_patterns = [
        r"between (\d+) and (\d+) reviews",
        r"antara (\d+) (?:dan|hingga|sampai) (\d+) (?:review|ulasan)",
        r"(\d+) (?:to|until|sampai|hingga) (\d+) (?:reviews|review|ulasan)"
    ]
    
    for pattern in between_reviews_patterns:
        match = re.search(pattern, prompt, re.IGNORECASE)
        if match:
            parameters['min_reviews'] = int(match.group(1))
            parameters['max_reviews'] = int(match.group(2))
            break
    
    # If no between pattern matched, try min and max separately
    if parameters['min_reviews'] == 0 and parameters['max_reviews'] is None:
        # Min reviews patterns
        min_reviews_patterns = [
            r"(?:at least|minimal|minimum|paling sedikit) (\d+) (?:number of |)(?:reviews|review|ulasan)",
            r"(?:with|dengan) (?:at least |minimal |minimum |)(\d+) (?:or more |atau lebih |)(?:reviews|review|ulasan)",
            r"(\d+)\+ (?:reviews|review|ulasan)"
        ]
        
        for pattern in min_reviews_patterns:
            match = re.search(pattern, prompt, re.IGNORECASE)
            if match:
                parameters['min_reviews'] = int(match.group(1))
                break
        
        # Max reviews patterns
        max_reviews_patterns = [
            r"(?:at most|no more than|fewer than|less than|maksimal|paling banyak|kurang dari) (\d+) (?:number of |)(?:reviews|review|ulasan)",
            r"(?:reviews|review|ulasan) (?:up to|not exceeding|sampai|hingga|maksimal) (\d+)",
            r"(?:tidak lebih dari|tidak melebihi) (\d+) (?:reviews|review|ulasan)"
        ]
        
        for pattern in max_reviews_patterns:
            match = re.search(pattern, prompt, re.IGNORECASE)
            if match:
                parameters['max_reviews'] = int(match.group(1))
                # If only max is specified without min, set min to 0
                if parameters["min_reviews"] == 0:
                    parameters['min_reviews'] = 0
                break
    
    # Extract price range
    price_patterns = [
        r"price range (?:of |is |sebesar |)([^\.•]+)",
        r"(?:with |dengan |)(?:a |)price(?: range|)(?: of| sebesar|) ([^\.•]+)",
        r"harga (?:sekitar |range |kisaran |)([^\.•]+)",
        r"(?:with |dengan |)(?:prices|harga) (?:between |antara |dari |)([^\.•]+)"
    ]
    
    for pattern in price_patterns:
        match = re.search(pattern, prompt, re.IGNORECASE)
        if match:
            price_text = match.group(1).strip()
            
            # Map common price descriptions to $ symbols
            price_mappings = {
                # English
                "cheap": "$", "budget": "$", "affordable": "$", "inexpensive": "$",
                "moderate": "$$", "average": "$$", "standard": "$$", "mid-range": "$$",
                "expensive": "$$$", "high-end": "$$$", "upscale": "$$$", "premium": "$$$",
                "very expensive": "$$$$", "luxury": "$$$$", "exclusive": "$$$$", "VIP": "$$$$",
                
                # Indonesian
                "murah": "$", "terjangkau": "$", "ekonomis": "$", "hemat": "$",
                "sedang": "$$", "standar": "$$", "rata-rata": "$$", "biasa": "$$",
                "mahal": "$$$", "tinggi": "$$$", "premium": "$$$", 
                "sangat mahal": "$$$$", "mewah": "$$$$", "eksklusif": "$$$$", "VIP": "$$$$"
            }
            
            # Check for direct price descriptions
            for desc, symbol in price_mappings.items():
                if desc.lower() in price_text.lower():
                    parameters['price_range'] = symbol
                    break
            
            # If no mapping found, keep the original text
            if parameters['price_range'] == "":
                parameters['price_range'] = price_text
            break
    
    # Extract business hours
    hours_patterns = [
        r"(?:operates|open|available|buka|beroperasi|tersedia) (?:at|on|during|pada|di|selama) ([^\.•,]+)",
        r"(?:business |)hours (?:of |are |)([^\.•,]+)",
        r"jam (?:buka|operasional|kerja) ([^\.•,]+)"
    ]
    
    for pattern in hours_patterns:
        match = re.search(pattern, prompt, re.IGNORECASE)
        if match:
            parameters['business_hours'] = match.group(1).strip()
            break
    
    # Extract explicit keywords
    keyword_patterns = [
        r"(?:must |harus |)include [\"']?(.*?)[\"']?(?:\.|\Z)",
        r"(?:with |dengan |)keywords?[: ] *([^\.•,]+)",
        r"(?:with |dengan |)kata kunci[: ] *([^\.•,]+)"
    ]
    
    for pattern in keyword_patterns:
        match = re.search(pattern, prompt, re.IGNORECASE)
        if match:
            if parameters['keywords']:
                parameters['keywords'] += ", " + match.group(1).strip()
            else:
                parameters['keywords'] = match.group(1).strip()
    
    # Extract implicit keywords and descriptive adjectives
    # List of common descriptive terms to look for
    descriptive_terms = [
        # English
        "cozy", "luxury", "luxurious", "affordable", "cheap", "expensive", "high-end", 
        "family-friendly", "pet-friendly", "quiet", "lively", "modern", "traditional",
        "romantic", "elegant", "casual", "authentic", "trendy", "popular", "hidden gem",
        "spacious", "intimate", "charming", "rustic", "sophisticated", "stylish",
        "outdoor seating", "view", "waterfront", "rooftop", "garden", "terrace",
        "free wifi", "parking", "vegan options", "gluten-free", "organic",
        "friendly staff", "fast service", "good service", "attentive",
        
        # Indonesian
        "nyaman", "mewah", "terjangkau", "murah", "mahal", "kelas atas",
        "ramah keluarga", "ramah hewan", "tenang", "ramai", "modern", "tradisional",
        "romantis", "elegan", "kasual", "autentik", "trendi", "populer", "tersembunyi",
        "luas", "intim", "menawan", "pedesaan", "canggih", "bergaya",
        "tempat duduk luar", "pemandangan", "tepi pantai", "atap", "taman", "teras",
        "wifi gratis", "parkir", "pilihan vegan", "bebas gluten", "organik",
        "staf ramah", "layanan cepat", "layanan bagus", "perhatian"
    ]
    
    found_keywords = []
    
    for term in descriptive_terms:
        # Create pattern that ensures we match whole words
        pattern = r'\b' + re.escape(term) + r'\b'
        if re.search(pattern, prompt, re.IGNORECASE):
            found_keywords.append(term)
    
    # Add these implicit keywords to any explicit ones
    if found_keywords:
        if parameters['keywords']:
            parameters['keywords'] += ", " + ", ".join(found_keywords)
        else:
            parameters['keywords'] = ", ".join(found_keywords)
    
    return parameters


def parse_prompt(prompt, provider="openai", **kwargs):
    """
    Parse the user prompt to extract search parameters with enhanced paraphrase detection
    
    Args:
        prompt (str): User prompt in any format (English or Indonesian)
        provider (str): The API provider to use ("openai" or "openrouter")
        **kwargs: Additional arguments to pass to the client creation function
        
    Returns:
        dict: Dictionary containing extracted search parameters or error response dictionary
    """
    # Create the appropriate client
    client, headers, actual_provider = create_client(**kwargs)
    
    # Get the full parameters from the prompt using the selected API
    parameters = parse_prompt_with_ai(prompt, client, headers, provider=actual_provider)
    
    # Check if AI parsing failed and regex fallback also failed
    if parameters is None:
        print("Both AI parsing and regex fallback failed. Unable to extract parameters from prompt.")
        # Return an error response using the imported utility function
        response_dict, _ = error_response("Unable to extract parameters from prompt. Please rephrase your query.")
        return response_dict
    
    return parameters