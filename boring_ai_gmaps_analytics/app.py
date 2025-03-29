from flask import Flask, request, jsonify, send_from_directory
from boring_ai_gmaps_analytics.map_leads import MapLeadsAI
import json
import pandas as pd
import os
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static')

# Read configuration from various sources
def load_config():
    # First check environment variables
    google_api_key = os.environ.get('GOOGLE_API_KEY')
    openrouter_api_key = os.environ.get('OPENROUTER_API_KEY')
    
    # If not in environment, try from config file
    if not google_api_key or not openrouter_api_key:
        config_paths = ['config.json', '../config.json', './config.json']
        
        for path in config_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        config = json.load(f)
                        google_api_key = google_api_key or config.get('google_api_key')
                        openrouter_api_key = openrouter_api_key or config.get('openrouter_api_key')
                        logger.info(f"Loaded API keys from {path}")
                        break
                except (json.JSONDecodeError, IOError) as e:
                    logger.error(f"Error reading config file {path}: {e}")
    
    if not google_api_key or not openrouter_api_key:
        logger.warning("API keys not configured properly")
    
    return google_api_key, openrouter_api_key

# Initialize API keys
GOOGLE_API_KEY, OPENROUTER_API_KEY = load_config()

# Lazy initialization of MapLeadsAI to handle missing API keys gracefully
map_leads = None

def get_map_leads():
    global map_leads, GOOGLE_API_KEY, OPENROUTER_API_KEY
    
    if map_leads is None:
        if not GOOGLE_API_KEY or not OPENROUTER_API_KEY:
            # Reload config in case it was updated
            GOOGLE_API_KEY, OPENROUTER_API_KEY = load_config()
            
        if GOOGLE_API_KEY and OPENROUTER_API_KEY:
            map_leads = MapLeadsAI(GOOGLE_API_KEY, OPENROUTER_API_KEY)
        else:
            raise ValueError("API keys not configured. Please set GOOGLE_API_KEY and OPENROUTER_API_KEY.")
    
    return map_leads

# Route for serving index.html
@app.route('/')
def home():
    try:
        return send_from_directory('.', 'index.html')
    except Exception as e:
        logger.error(f"Error serving index.html: {e}")
        # Fallback message if index.html is not found
        return """
        <html><body>
            <h1>Map Leads AI API</h1>
            <p>API is running. Use /api/search endpoint for queries.</p>
            <p>Index.html file not found in the current directory.</p>
        </body></html>
        """

@app.route('/api/search', methods=['POST'])
def search():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON data'}), 400
            
        prompt = data.get('prompt', '')
        
        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400
        
        # Get MapLeadsAI instance
        try:
            map_leads_instance = get_map_leads()
        except ValueError as e:
            return jsonify({'error': str(e)}), 500
            
        # Run search
        results = map_leads_instance.run_search(prompt)
        
        # Convert to JSON format
        results_json = results.to_dict(orient='records')
        
        # Analysis data with column existence checks
        analysis_data = {
            'total': len(results),
            'highest_rated': 'N/A',
            'max_rating': 0,
            'most_reviews': 'N/A'
        }
        
        if not results.empty:
            if 'Rating' in results.columns:
                ratings = results['Rating'].replace('N/A', '0').astype(float)
                if not ratings.empty and ratings.max() > 0:
                    max_rating_idx = ratings.idxmax()
                    analysis_data['highest_rated'] = results.iloc[max_rating_idx]['Name']
                    analysis_data['max_rating'] = float(ratings.max())
            
            if 'Total_Reviews' in results.columns:
                reviews = results['Total_Reviews'].replace('N/A', '0').astype(float)
                if not reviews.empty:
                    max_reviews_idx = reviews.idxmax()
                    analysis_data['most_reviews'] = results.iloc[max_reviews_idx]['Name']
        
        return jsonify({
            'results': results_json,
            'analysis': analysis_data
        })
        
    except Exception as e:
        logger.error(f"Error in search endpoint: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/healthcheck', methods=['GET'])
def healthcheck():
    """Endpoint to check if the API is running correctly"""
    try:
        # Check if we can initialize MapLeadsAI
        get_map_leads()
        return jsonify({
            'status': 'ok',
            'google_api_configured': bool(GOOGLE_API_KEY),
            'openrouter_api_configured': bool(OPENROUTER_API_KEY)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'google_api_configured': bool(GOOGLE_API_KEY),
            'openrouter_api_configured': bool(OPENROUTER_API_KEY)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('FLASK_RUN_PORT', 9975))
    host = os.environ.get('FLASK_RUN_HOST', '0.0.0.0')
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')
    
    logger.info(f"Starting Flask app on {host}:{port} (debug={debug})")
    app.run(debug=debug, port=port, host=host)