from flask import jsonify

def api_response(data, status_code=200):
    """Membuat respons JSON standar."""
    if 'done' not in data:
        data['done'] = data.get('next') is None
    return jsonify(data), status_code

def error_response(message, status_code=400):
    """Membuat respons error standar."""
    return jsonify({
        "state": None, "result": None, "next": None,
        "done": True, "error": message
    }), status_code