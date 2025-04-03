from flask import Flask
from src.routes import blueprints
from src.services.google_maps_service import init_api_key
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def create_app(api_key=None):
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Get API key from environment variable if not provided
    if api_key is None:
        api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    
    # Initialize API key for direct Google Maps API calls
    init_api_key(api_key)
    
    # Register all blueprints
    for blueprint in blueprints:
        app.register_blueprint(blueprint)
        
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
