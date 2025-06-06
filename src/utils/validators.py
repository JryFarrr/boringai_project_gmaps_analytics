def validate_payload(data, required_fields):
    """Memvalidasi bahwa field yang diperlukan ada dalam payload."""
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return f"Missing required fields: {', '.join(missing_fields)}"
    return None