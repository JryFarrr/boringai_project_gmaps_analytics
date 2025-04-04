"""
Main module for Map Leads AI - Run this file to start the application (Codebase)
"""

import json
from datetime import datetime
import pandas as pd
from config.config import GOOGLE_API_KEY, OPENROUTER_API_KEY, DEFAULT_REFERER_URL, DEFAULT_SITE_NAME
from services.prompt_parser import parse_prompt
from services.business_search import search_businesses
from utils.results_processor import process_results


def run_search(prompt, google_api_key=GOOGLE_API_KEY, openrouter_api_key=OPENROUTER_API_KEY, 
               referer_url=DEFAULT_REFERER_URL, site_name=DEFAULT_SITE_NAME):
    """
    Run the complete search process
    
    Args:
        prompt (str): User prompt for business search
        google_api_key (str): Google Places API key
        openrouter_api_key (str): OpenRouter API key
        referer_url (str): Website URL for OpenRouter rankings
        site_name (str): Site name for OpenRouter rankings
        
    Returns:
        pandas.DataFrame: Search results
    """
    print("Parsing prompt...")
    parameters = parse_prompt(prompt, referer_url, site_name)
    print(f"Search parameters: {json.dumps(parameters, indent=2)}")
    
    print("\nSearching for businesses...")
    businesses = search_businesses(parameters, google_api_key)
    print(f"Found {len(businesses)} matching businesses")
    
    print("\nProcessing results...")
    results_df = process_results(businesses)
    
    return results_df


def display_analysis(results):
    """
    Display sample analysis from results
    
    Args:
        results (pandas.DataFrame): Search results DataFrame
    """
    if results.empty:
        print("No results to analyze.")
        return
        
    print("\nQuick Analysis:")
    print(f"Total businesses found: {len(results)}")
    
    if 'Rating' in results and not results['Rating'].empty and not all(r == 'N/A' for r in results['Rating']):
        ratings = pd.to_numeric(results['Rating'].replace('N/A', 0), errors='coerce')
        max_rating_idx = ratings.idxmax()
        print(f"Highest rated business: {results.iloc[max_rating_idx]['Name']} with rating {results.iloc[max_rating_idx]['Rating']}")
    
    if 'Total_Reviews' in results and not results['Total_Reviews'].empty and not all(r == 'N/A' for r in results['Total_Reviews']):
        reviews = pd.to_numeric(results['Total_Reviews'].replace('N/A', 0), errors='coerce')
        max_reviews_idx = reviews.idxmax()
        print(f"Business with most reviews: {results.iloc[max_reviews_idx]['Name']} with {results.iloc[max_reviews_idx]['Total_Reviews']} reviews")
    
    if 'Overall_Match' in results:
        match_percentages = pd.to_numeric(results['Overall_Match'].str.rstrip('%'), errors='coerce')
        avg_match = match_percentages.mean()
        print(f"Average match percentage: {avg_match:.2f}%")


def save_results(results, prefix="map_leads_results"):
    """
    Save results to CSV file
    
    Args:
        results (pandas.DataFrame): Search results DataFrame
        prefix (str): Filename prefix
        
    Returns:
        str: Filename where results were saved
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_{timestamp}.csv"
    results.to_csv(filename, index=False)
    print(f"\nResults saved to {filename}")
    return filename


def main():
    """Main function to run the application"""
    print("=" * 60)
    print("           WELCOME TO MAP LEADS AI SEARCH")
    print("=" * 60)
    
    # Example prompts for different use cases
    prompt_examples = {
        "1": {
            "name": "Agency Marketing",
            "prompt": """
            Find a salon in Bandung that has a rating of at least 4.2 and at least 50 number of reviews.
            Additional Requirements:
            • The business must have a price range of "rupiah" + "$$".
            • The business operates at open now.
            • Business reviews and descriptions must include "premium, luxury, service".
            """
        },
        "2": {
            "name": "Food Supplier",
            "prompt": """
            Find a sushi restaurant in Tokyo that has a rating of at least 4.5 and at least 100 reviews.
            """
        },
        "3": {
            "name": "Basic Search",
            "prompt": """
            Find a coffee shop in Seattle.
            """
        }
    }
    
    print("\nExample prompts:")
    for key, example in prompt_examples.items():
        print(f"{key}. {example['name']}")
    print("4. Custom prompt")
    
    # Choose prompt
    choice = input("\nChoose an example (1-4) or press Enter for custom prompt: ")
    
    if choice in prompt_examples:
        selected_prompt = prompt_examples[choice]["prompt"]
        print(f"\nSelected example: {prompt_examples[choice]['name']}")
    else:
        print("\nEnter your custom prompt:")
        print("Format: Find a [business type] in [location] that has a rating of at least [rating] and at least [reviews] reviews.")
        print("Additional Requirements: price range, business hours, keywords.")
        selected_prompt = input("\n> ")
    
    print(f"\nRunning search with prompt: {selected_prompt}")
    
    # Run the search
    results = run_search(selected_prompt)
    
    # Display results
    print("\nSearch Results:")
    if not results.empty:
        # Show a limited view of the results (first 5 rows, specific columns)
        display_columns = ['Name', 'Address', 'Rating', 'Total_Reviews', 'Overall_Match']
        print(results[display_columns].head().to_string())
        print(f"\n... and {max(0, len(results) - 5)} more results.")
    else:
        print("No results found.")
    
    # Display analysis
    display_analysis(results)
    
    # Save to CSV
    if not results.empty:
        save_option = input("\nDo you want to save results to CSV? (y/n): ")
        if save_option.lower() == 'y':
            filename = save_results(results)
            print(f"Results saved to {filename}")
    
    print("\nThank you for using Map Leads AI!")


if __name__ == "__main__":
    main()