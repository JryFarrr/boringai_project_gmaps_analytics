from flask import Blueprint

# Import route modules
from .input_route import input_route
from .search_route import search_route
from .scrape_route import scrape_route
from .analyze_route import analyze_route
from .control_route import control_route

# Create blueprints
input_bp = Blueprint('input', __name__)
search_bp = Blueprint('search', __name__)
scrape_bp = Blueprint('scrape', __name__)
analyze_bp = Blueprint('analyze', __name__)
control_bp = Blueprint('control', __name__)

# Register routes with blueprints
input_bp.route('/task/input', methods=['POST'])(input_route)
search_bp.route('/task/search', methods=['POST'])(search_route)
scrape_bp.route('/task/scrape', methods=['POST'])(scrape_route)
analyze_bp.route('/task/analyze', methods=['POST'])(analyze_route)
control_bp.route('/task/control', methods=['POST'])(control_route)

# List of all blueprints
blueprints = [input_bp, search_bp, scrape_bp, analyze_bp, control_bp]
