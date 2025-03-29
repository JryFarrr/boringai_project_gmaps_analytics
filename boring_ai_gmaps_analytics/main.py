from boring_ai_gmaps_analytics.map_leads import MapLeadsAI
from datetime import datetime
import json
import os
import sys

def main():
    # Baca API keys dari file konfigurasi, environment variable, atau command line
    google_api_key = None
    openrouter_api_key = None
    
    # Try from environment variables first
    if os.environ.get('GOOGLE_API_KEY') and os.environ.get('OPENROUTER_API_KEY'):
        google_api_key = os.environ.get('GOOGLE_API_KEY')
        openrouter_api_key = os.environ.get('OPENROUTER_API_KEY')
        print("Using API keys from environment variables")
    
    # If not in environment, try from config file
    if not google_api_key or not openrouter_api_key:
        try:
            # Determine file path - look in current directory and parent directory
            config_paths = ['config.json', '../config.json', './config.json']
            config_file = None
            
            for path in config_paths:
                if os.path.exists(path):
                    config_file = path
                    break
            
            if not config_file:
                print("Warning: No config.json found in current or parent directory")
                raise FileNotFoundError
                
            with open(config_file, 'r') as f:
                config = json.load(f)
                google_api_key = config.get('google_api_key')
                openrouter_api_key = config.get('openrouter_api_key')
                print(f"Using API keys from {config_file}")
        except FileNotFoundError:
            print("Warning: Could not find config.json file.")
        except json.JSONDecodeError:
            print("Error: Invalid JSON in config.json file.")

    # Validate keberadaan API keys
    if not google_api_key or not openrouter_api_key:
        print("Error: API keys not found. Please set them in config.json or as environment variables:")
        print("  - GOOGLE_API_KEY")
        print("  - OPENROUTER_API_KEY")
        return

    try:
        map_leads = MapLeadsAI(google_api_key, openrouter_api_key)
        
        # Contoh prompt dengan variasi
        prompt_examples = {
            "agency_marketing": """
            Find a salon in Bandung that has a rating of at least 4.2 and at least 50 number of reviews.
            Additional Requirements:
            • The business must have a price range of "rupiah" + "$$".
            • The business operates at open now.
            • Business reviews and descriptions must include "premium, luxury, service".
            """,
            
            "food_supplier": """
            Find a restaurant in Surabaya that has a rating of at least 4.0.
            """,
            
            "property_agent": """
            Find a shopping mall in Bali that has a rating of at least 4.3 and at least 300 number of reviews.
            Additional Requirements:
            • The business must have a price range of "rupiah" + "$$".
            • The business operates at anytime.
            • Business reviews and descriptions must include "strategic, parking, international".
            """
        }
        
        # Select prompt to use (default or from command line)
        prompt_key = "food_supplier"  # Default prompt
        
        # If command line argument is provided, use that prompt key
        if len(sys.argv) > 1 and sys.argv[1] in prompt_examples:
            prompt_key = sys.argv[1]
        
        selected_prompt = prompt_examples[prompt_key]
        print(f"Running search with prompt type: {prompt_key}")
        print(f"Prompt: {selected_prompt}")
        
        # Run search
        results = map_leads.run_search(selected_prompt)
        
        # Display results
        print("\nSearch Results:")
        print(results)
        
        # Save to CSV
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"map_leads_results_{timestamp}.csv"
        results.to_csv(filename, index=False)
        print(f"\nResults saved to {filename}")
        
        # Display brief analysis
        if not results.empty:
            print("\nQuick Analysis:")
            print(f"Total businesses found: {len(results)}")
            
            if 'Rating' in results.columns and not results['Rating'].empty:
                # Convert ratings to numeric, handling 'N/A' values
                ratings = results['Rating'].replace('N/A', '0')
                ratings = ratings.astype(float)
                
                if not ratings.empty:
                    max_rating_idx = ratings.idxmax()
                    print(f"Highest rated business: {results.iloc[max_rating_idx]['Name']} with rating {results.iloc[max_rating_idx]['Rating']}")
            
            if 'Total_Reviews' in results.columns and not results['Total_Reviews'].empty:
                # Convert reviews to numeric, handling 'N/A' values
                reviews = results['Total_Reviews'].replace('N/A', '0')
                reviews = reviews.astype(float)
                
                if not reviews.empty:
                    max_reviews_idx = reviews.idxmax()
                    print(f"Business with most reviews: {results.iloc[max_reviews_idx]['Name']} with {results.iloc[max_reviews_idx]['Total_Reviews']} reviews")
            
            if 'Overall_Match' in results.columns:
                # Remove % sign and convert to numeric
                match_percentages = results['Overall_Match'].str.rstrip('%').astype(float)
                avg_match = match_percentages.mean()
                print(f"Average match percentage: {avg_match:.2f}%")
    
    except Exception as e:
        print(f"Error in search process: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()