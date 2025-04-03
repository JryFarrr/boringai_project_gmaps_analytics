from flask import jsonify

def error_response(message, status_code=400):
    """Helper function for error responses"""
    return jsonify({
        "state": None,
        "result": None,
        "next": None,
        "done": True,
        "error": message
    }), status_code
