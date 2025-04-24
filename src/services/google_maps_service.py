import requests
import time
import openai
import json
import re
from src.config import config

# === GLOBAL API KEYS ===
api_key = None
openai_api_key = None
search_api_key = None 

# === INIT API KEYS ===
def init_api_key(key):
    """Initialize the Google Maps API key"""
    global api_key
    api_key = config.GOOGLE_API_KEY
    return key


def init_openai_key(key):
    """Initialize OpenAI API key"""
    global openai_api_key
    openai.api_key = config.OPENAI_API_KEY
    return key


def init_search_api_key(key):
    """Initialize SearchAPI.io API key"""
    global search_api_key
    search_api_key = config.SEARCHAPI_API_KEY
    return key


# === GOOGLE PLACES TEXT SEARCH ===
def search_places(query=None, page_token=None):
    base_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {'key': get_api_key()}

    if page_token is not None:
        params['pagetoken'] = page_token
    elif query is not None:
        params['query'] = query
    else:
        raise ValueError("Either query or page_token must be provided")

    try:
        max_attempts = 3
        for attempt in range(max_attempts):
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            data = response.json()

            if data['status'] == 'INVALID_REQUEST' and page_token and attempt < max_attempts - 1:
                time.sleep(2 * (attempt + 1))
                continue

            if data['status'] not in ('OK', 'ZERO_RESULTS'):
                if data['status'] == 'INVALID_REQUEST' and page_token and attempt == max_attempts - 1:
                    return {'results': [], 'next_page_token': None}
                raise ValueError(f"API Error: {data['status']}")

            return {'results': data.get('results', []), 'next_page_token': data.get('next_page_token')}
    except requests.RequestException as e:
        raise Exception(f"Request failed: {str(e)}")


# === GET GOOGLE API KEY ===
def get_api_key():
    global api_key
    if api_key is None:
        raise ValueError("API key not initialized. Call init_api_key first.")
    return api_key


# === GET SEARCH API KEY ===
def get_search_api_key():
    global search_api_key
    if search_api_key is None:
        raise ValueError("SearchAPI.io key not initialized. Call init_search_api_key first.")
    return search_api_key


# === GET PLACE DETAILS ===
def get_place_details(place_id, fields=None):
    if not api_key:
        raise ValueError("Google Maps API key is not initialized. Call init_api_key first.")

    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "key": api_key
    }
    if fields:
        params["fields"] = ",".join(fields)

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if data["status"] != "OK":
            raise Exception(f"API error: {data.get('error_message', data['status'])}")
        return data.get("result", {})
    except requests.RequestException as e:
        raise Exception(f"Failed to call Google Maps API: {str(e)}")


# === GET REVIEWS FOR A PLACE ===
def get_place_reviews(place_id, max_reviews=20):
    fields = ["review", "name", "rating", "user_ratings_total", "formatted_address", "types", "url"]
    place_details = get_place_details(place_id, fields=fields)
    reviews = place_details.get("reviews", [])
    return reviews[:max_reviews]

def get_place_reviews_all(place_id):
    fields = ["review", "name", "rating", "user_ratings_total", "formatted_address", "types", "url"]
    place_details = get_place_details(place_id, fields=fields)
    reviews = place_details.get("reviews", [])
    return reviews

# === SEARCH VIA SEARCHAPI.IO (replacing SerpAPI) ===
def search_business_with_search_api(keyword, location="Indonesia", max_results=5):
    # Get the SearchAPI.io key
    api_key_searchapi = get_search_api_key()
    
    # SearchAPI.io endpoint for Google Maps
    search_url = "https://www.searchapi.io/api/v1/search"
    
    params = {
        "engine": "google_maps",
        "q": keyword,
        "location": location,
        "api_key": api_key_searchapi,
        "num": max_results  # Number of results to return
    }

    try:
        response = requests.get(search_url, params=params)
        response.raise_for_status()
        results = response.json()

        businesses = []
        for biz in results.get("local_results", [])[:max_results]:
            businesses.append({
                "title": biz.get("title"),
                "address": biz.get("address"),
                "place_id": biz.get("place_id"),
                "gps_coordinates": biz.get("gps_coordinates", {}),
                "rating": biz.get("rating"),
                "reviews_count": biz.get("reviews"),
                "google_maps_url": biz.get("link")
            })

        return businesses

    except Exception as e:
        raise RuntimeError(f"SearchAPI.io request failed: {str(e)}")


# === OPENAI: SUMMARIZE & EXTRACT KEYWORDS ===
def summarize_and_extract_keywords(reviews):
    if not openai.api_key:
        raise ValueError("OpenAI API key not initialized. Call init_openai_key first.")

    review_texts = [r.get("text", "") for r in reviews if r.get("text")]
    joined_reviews = "\n".join(review_texts[:10])

    prompt = f"""
    I have the following customer reviews:\n{joined_reviews}\n
    Please provide:
    1. A concise summary of overall customer sentiment and experiences.
    2. A list of key topics and keywords mentioned by customers.
    Format your response in JSON with 'summary' and 'keywords' keys.
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": "You are a helpful business analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=500
        )

        result_text = response['choices'][0]['message']['content']
        return json.loads(result_text)
    except Exception as e:
        raise RuntimeError(f"OpenAI request failed: {str(e)}")

# === FUNGSI BARU: MENCARI SINONIM DAN KATA TERKAIT DENGAN OPENAI ===
def find_related_keywords(keyword):
    """
    Menggunakan OpenAI untuk mencari sinonim dan kata-kata terkait
    
    Args:
        keyword (str): Kata kunci yang ingin dicari sinonimnya
        
    Returns:
        list: Daftar kata terkait dan sinonim
    """
    if not openai.api_key:
        raise ValueError("OpenAI API key not initialized. Call init_openai_key first.")
    
    prompt = f"""
    Berikan daftar kata-kata yang berhubungan atau memiliki makna serupa dengan kata "{keyword}" dalam bahasa Indonesia.
    Misalnya jika kata kuncinya adalah "kumpul bareng", berarti kata-kata seperti "nongkrong", "hangout", "gathering", dsb.
    Berikan hanya daftar kata tanpa penjelasan, dalam format JSON dengan key "related_words".
    """
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": "Anda adalah asisten bahasa Indonesia yang membantu menemukan kata-kata terkait."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=300
        )
        
        result_text = response['choices'][0]['message']['content']
        # Extract JSON from potential text
        json_pattern = r'{[\s\S]*}'
        match = re.search(json_pattern, result_text)
        if match:
            result_text = match.group(0)
            
        result = json.loads(result_text)
        return result.get("related_words", [])
    except Exception as e:
        # Jika gagal, kembalikan setidaknya keyword asli
        return [keyword]

# === FUNGSI BARU: EKSTRAK KATA KUNCI DARI REVIEW DENGAN AI ===
def extract_keywords_from_reviews(reviews, main_keyword):
    """
    Menggunakan OpenAI untuk mengekstrak kata kunci dari review yang terkait dengan main_keyword
    
    Args:
        reviews (list): Daftar review dari tempat
        main_keyword (str): Kata kunci utama yang dicari
        
    Returns:
        dict: Hasil analisis kata kunci dari review
    """
    if not openai.api_key:
        raise ValueError("OpenAI API key not initialized. Call init_openai_key first.")
    
    # Ambil teks dari 10 review pertama
    review_texts = [r.get("text", "") for r in reviews if r.get("text")][:10]
    joined_reviews = "\n".join(review_texts)
    
    prompt = f"""
    Analisis review berikut dan temukan kata-kata yang terkait dengan "{main_keyword}".
    
    Reviews:
    {joined_reviews}
    
    Identifikasi kata-kata atau frasa dalam review yang memiliki makna serupa atau berhubungan dengan "{main_keyword}".
    Contoh jika keyword adalah "kumpul bareng", temukan kata seperti "nongkrong", "hangout", "gathering", dll.
    
    Format respon dalam JSON dengan key:
    1. "extracted_keywords": [daftar kata kunci yang ditemukan dalam review]
    2. "synonym_mapping": {{kata yang ditemukan: hubungannya dengan "{main_keyword}"}}
    3. "occurrences": jumlah total kata terkait yang ditemukan
    """
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": "Anda adalah asisten analisis konten yang membantu mengidentifikasi kata kunci dalam review."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=500
        )
        
        result_text = response['choices'][0]['message']['content']
        # Extract JSON from potential text
        json_pattern = r'{[\s\S]*}'
        match = re.search(json_pattern, result_text)
        if match:
            result_text = match.group(0)
            
        return json.loads(result_text)
    except Exception as e:
        return {
            "extracted_keywords": [],
            "synonym_mapping": {},
            "occurrences": 0,
            "error": str(e)
        }

# === DIAGNOSTIC FUNCTIONS ===
def inspect_review_data(reviews):
    """
    Diagnostic function to inspect review data structure and content
    """
    print(f"\n=== REVIEW DATA INSPECTION ===")
    print(f"Number of reviews: {len(reviews)}")
    
    # Check the type of the overall reviews container
    print(f"Type of reviews container: {type(reviews)}")
    
    # Inspect a few reviews
    for i, review in enumerate(reviews[:3]):
        print(f"\nReview #{i+1} inspection:")
        print(f"Type: {type(review)}")
        
        if isinstance(review, dict):
            print(f"Keys: {list(review.keys())}")
            if "text" in review:
                print(f"Text type: {type(review['text'])}")
                print(f"Text length: {len(review['text'])}")
                print(f"Text sample: {review['text'][:100]}...")
            else:
                print("WARNING: No 'text' key found in this review!")
                print(f"Available data: {review}")
        elif isinstance(review, str):
            print(f"String length: {len(review)}")
            print(f"String sample: {review[:100]}...")
        else:
            print(f"Unexpected type. Str representation: {str(review)[:100]}...")
    
    return {
        "total_reviews": len(reviews),
        "has_valid_structure": any(isinstance(r, dict) and "text" in r for r in reviews) or 
                              any(isinstance(r, str) for r in reviews)
    }

def test_keyword_detection(keyword, reviews):
    """
    Simple test function to check if keywords are present in reviews
    """
    print(f"\n=== KEYWORD DETECTION TEST ===")
    print(f"Testing keyword: '{keyword}'")
    print(f"Total reviews to check: {len(reviews)}")
    
    keyword_lower = keyword.lower()
    found_count = 0
    matches_by_review = []
    
    # Print first few characters of each review
    print("\nSample of reviews:")
    for i, review in enumerate(reviews[:3]):  # Show first 3 reviews
        if isinstance(review, dict) and "text" in review:
            review_text = review["text"]
        elif isinstance(review, str):
            review_text = review
        else:
            try:
                review_text = str(review)
            except:
                review_text = "ERROR: Could not convert to string"
            
        print(f"Review {i}: {review_text[:50]}...")
    
    # Check each review
    for i, review in enumerate(reviews):
        try:
            # Extract text based on type
            if isinstance(review, dict) and "text" in review:
                review_text = review["text"]
            elif isinstance(review, str):
                review_text = review
            else:
                review_text = str(review)
                
            # Convert to lowercase
            review_text_lower = review_text.lower()
            
            # Simple substring check
            if keyword_lower in review_text_lower:
                found_count += 1
                # Show the context where keyword appears
                start_idx = review_text_lower.find(keyword_lower)
                context_start = max(0, start_idx - 20)
                context_end = min(len(review_text), start_idx + len(keyword_lower) + 20)
                context = review_text[context_start:context_end]
                matches_by_review.append(f"Review {i}: ...{context}...")
        except Exception as e:
            print(f"Error processing review {i}: {str(e)}")
    
    print(f"\nFound keyword in {found_count} reviews")
    
    if found_count > 0:
        print("\nMatches with context:")
        for match in matches_by_review[:5]:  # Show up to 5 matches
            print(match)
    else:
        print("\nNo matches found. Try these debugging steps:")
        print("1. Check if your keyword is spelled correctly")
        print("2. Check if reviews contain the expected text")
        print("3. Try a different, more common keyword as a test")
        print("4. Check if the reviews are in the same language as your keyword")
    
    return found_count > 0

# FIXED FUNCTION: Improved to ensure proper keyword detection
def count_keyword_in_reviews(keyword, reviews):
    """
    Fixed function for counting keyword occurrences in reviews
    
    Args:
        keyword (str): Kata kunci yang ingin dihitung
        reviews (list): Daftar review dari tempat
        
    Returns:
        dict: Berisi jumlah kemunculan keyword dan total review
    """
    # Run diagnostic tests first
    inspect_review_data(reviews)
    has_matches = test_keyword_detection(keyword, reviews)
    
    if not keyword or not reviews:
        return {
            "keywordMatches": 0,
            "totalReviews": len(reviews) if reviews else 0,
            "message": f"0 keyword found from 0 reviews",
            "foundKeywords": {},
            "relatedKeywords": []
        }
    
    total_reviews = len(reviews)
    keyword_count = 0
    
    # Clean and standardize keyword
    keyword = keyword.strip()
    keyword_lower = keyword.lower()
    
    # Initialize tracking variables
    found_keywords = {}
    review_with_keywords = 0
    
    # Check each review for keyword matches (original keyword)
    for review in reviews:
        if isinstance(review, dict) and "text" in review:
            review_text = review["text"].lower()
        elif isinstance(review, str):
            review_text = review.lower()
        else:
            try:
                review_text = str(review).lower()
            except:
                continue
        
        # Count occurrences of original keyword
        matches = review_text.count(keyword_lower)
        if matches > 0:
            keyword_count += matches
            if keyword not in found_keywords:
                found_keywords[keyword] = matches
            else:
                found_keywords[keyword] += matches
            review_with_keywords += 1
    
    # Get related keywords only if we have OpenAI and main keyword wasn't found much
    related_keywords = []
    if 'openai' in globals() and openai.api_key and (keyword_count == 0 or keyword_count < 3):
        try:
            print("\nSearching for related keywords with OpenAI...")
            related_keywords = find_related_keywords(keyword)
            print(f"Found related keywords: {related_keywords}")
            
            # Search for each related keyword
            for related_word in related_keywords:
                if related_word.lower() == keyword_lower:
                    continue  # Skip if it's the same as original
                
                related_word_lower = related_word.lower()
                related_count = 0
                
                for review in reviews:
                    if isinstance(review, dict) and "text" in review:
                        review_text = review["text"].lower()
                    elif isinstance(review, str):
                        review_text = review.lower()
                    else:
                        try:
                            review_text = str(review).lower()
                        except:
                            continue
                    
                    # Count occurrences
                    matches = review_text.count(related_word_lower)
                    if matches > 0:
                        related_count += matches
                
                if related_count > 0:
                    found_keywords[related_word] = related_count
                    keyword_count += related_count
        except Exception as e:
            print(f"Error finding related keywords: {str(e)}")
    
    # Prepare result
    return {
        "keywordMatches": keyword_count,
        "totalReviews": total_reviews,
        "reviewsWithKeywords": review_with_keywords,
        "message": f"{keyword_count} keyword related to '{keyword}' found from {total_reviews} reviews",
        "foundKeywords": found_keywords,
        "relatedKeywords": related_keywords if related_keywords else [keyword]
    }

# === MAIN SCRAPE TASK WITH IMPROVED KEYWORD COUNTING ===
def scrape_business_data_by_keyword(keyword, max_places=5, max_reviews_per_place=10):
    all_data = []
    businesses = search_business_with_search_api(keyword, max_results=max_places)

    for biz in businesses:
        place_id = biz.get("place_id")
        if not place_id:
            continue

        details = get_place_details(place_id, fields=[
            "name", "place_id", "rating", "formatted_address", "types", "url"
        ])
        reviews = get_place_reviews_all(place_id)  # Get all available reviews
        
        print(f"\n=== Processing business: {details.get('name', 'Unknown')} ===")
        print(f"Found {len(reviews)} reviews")
        
        # Add diagnostic test before main function
        test_keyword_detection(keyword, reviews)
        
        # Count keyword occurrences in reviews with the fixed function
        keyword_analysis = count_keyword_in_reviews(keyword, reviews)
        
        try:
            analysis = summarize_and_extract_keywords(reviews[:max_reviews_per_place])  # Only use limited reviews for sentiment analysis
        except Exception as e:
            analysis = {"summary": None, "keywords": [], "error": str(e)}

        all_data.append({
            "business": details,
            "reviews": reviews[:max_reviews_per_place],  # Limit the reviews returned in result
            "analysis": analysis,
            "keywordAnalysis": keyword_analysis  # Add the enhanced keyword counting result
        })

    return all_data