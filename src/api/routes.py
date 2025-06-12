import traceback
from flask import Blueprint, request, current_app
from flasgger import swag_from
from ..core.workflow import Workflow
from ..utils.response import api_response, error_response
from .schemas import input_schema, search_schema, scrape_schema, analyze_schema, control_schema
from ..docs import input, scrape, search, control, analyze
api_bp = Blueprint('api', __name__)
workflow = Workflow()

@api_bp.route('/input', methods=['POST'])
# @swag_from(input_schema)
@swag_from(input.input_param)
def handle_input():
    data = request.get_json()
    if not data: return error_response("Invalid JSON payload")
    try: return api_response(workflow.start(data))
    except Exception as e: current_app.logger.error(traceback.format_exc()); return error_response(f"Input failed: {e}", 500)

@api_bp.route('/search', methods=['POST'])
# @swag_from(search_schema)
@swag_from(search.search_param)
def handle_search():
    data = request.get_json()
    try: return api_response(workflow.search(data))
    except Exception as e: current_app.logger.error(traceback.format_exc()); return error_response(f"Search failed: {e}", 500)

@api_bp.route('/scrape', methods=['POST'])
# @swag_from(scrape_schema)
@swag_from(scrape.scrape_param)
def handle_scrape():
    data = request.get_json()
    try: return api_response(workflow.scrape(data))
    except Exception as e: current_app.logger.error(traceback.format_exc()); return error_response(f"Scrape failed: {e}", 500)

@api_bp.route('/analyze', methods=['POST'])
# @swag_from(analyze_schema)
@swag_from(analyze.analyze_param)
def handle_analyze():
    data = request.get_json()
    try: return api_response(workflow.analyze(data))
    except Exception as e: current_app.logger.error(traceback.format_exc()); return error_response(f"Analysis failed: {e}", 500)

@api_bp.route('/control', methods=['POST'])
# @swag_from(control_schema)
@swag_from(control.control_param)
def handle_control():
    data = request.get_json()
    try: return api_response(workflow.control(data))
    except Exception as e: current_app.logger.error(traceback.format_exc()); return error_response(f"Control flow failed: {e}", 500)