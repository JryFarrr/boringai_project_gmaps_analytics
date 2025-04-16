from flask import Flask
from src.routes import blueprints

# Create Flask app
app = Flask(__name__)

# Register blueprints
for blueprint in blueprints:
    app.register_blueprint(blueprint)

__all__ = ['app']
