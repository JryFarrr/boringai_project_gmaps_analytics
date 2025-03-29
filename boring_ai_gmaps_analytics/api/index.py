from flask import Flask, request, jsonify, send_from_directory
import json
import os
import sys
import pandas as pd

# Tambahkan path proyek ke sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import modul dari package BoringAIGmapsAnalytics
from boring_ai_gmaps_analytics.map_leads import MapLeadsAI

app = Flask(__name__)

# Baca API keys dari environment variables Vercel
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY')

# Fallback ke config.json jika environment variables tidak tersedia
if not GOOGLE_API_KEY or not OPENROUTER_API_KEY:
    try:
        config_paths = ['config.json', './config.json', '../config.json']
        
        for path in config_paths:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    config = json.load(f)
                    GOOGLE_API_KEY = GOOGLE_API_KEY or config.get('google_api_key')
                    OPENROUTER_API_KEY = OPENROUTER_API_KEY or config.get('openrouter_api_key')
                    print(f"Loaded API keys from {path}")
                    break
    except Exception as e:
        print(f"Error loading config: {e}")

# Lazy initialization untuk MapLeadsAI
map_leads = None

def get_map_leads():
    global map_leads, GOOGLE_API_KEY, OPENROUTER_API_KEY
    
    if map_leads is None:
        if not GOOGLE_API_KEY or not OPENROUTER_API_KEY:
            raise ValueError("API keys not found in environment variables or config.json")
            
        map_leads = MapLeadsAI(GOOGLE_API_KEY, OPENROUTER_API_KEY)
    
    return map_leads

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
        
        # Analysis data
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
        print(f"Error in search endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# Fallback route for root
@app.route('/')
def index():
    return send_from_directory('../static', 'index.html')

# Serve static files
@app.route('/static/<path:path>')
def static_files(path):
    return send_from_directory('../static', path)

@app.route('/healthcheck')
def healthcheck():
    return jsonify({
        'status': 'ok',
        'google_api_configured': bool(GOOGLE_API_KEY),
        'openrouter_api_configured': bool(OPENROUTER_API_KEY)
    })

# Handler for Vercel serverless functions
def handler(event, context):
    return app(event, context)

if __name__ == '__main__':
    app.run(debug=True, port=int(os.environ.get('PORT', 9975)))