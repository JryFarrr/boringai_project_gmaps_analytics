def validate_input_payload(data):
    """
    Validates the input payload for the lead generation workflow
    
    Checks for required fields and validates their types and values.
    
    Args:
        data (dict): The JSON payload to validate
        
    Returns:
        str or None: Error message if validation fails, None if validation passes
    """
    # Check for required fields
    required_fields = ["businessType", "location", "numberOfLeads"]
    for field in required_fields:
        if field not in data:
            return f"Missing required field: {field}"
    
    # Validate business type
    if not isinstance(data["businessType"], str) or not data["businessType"].strip():
        return "businessType must be a non-empty string"
    
    # Validate location
    if not isinstance(data["location"], str) or not data["location"].strip():
        return "location must be a non-empty string"
    
    # Validate number of leads
    if not isinstance(data["numberOfLeads"], int) or data["numberOfLeads"] <= 0:
        return "numberOfLeads must be a positive integer"
    
    # If all validations pass
    return None

def validate_search_payload(data):
    """
    Validates the input payload for the search endpoint
    
    Args:
        data (dict): The request payload to validate
    
    Returns:
        str or None: Error message if validation fails, None if validation passes
    """
    # Check required fields
    required_fields = ["businessType", "location", "searchOffset", "numberOfLeads"]
    for field in required_fields:
        if field not in data:
            return f"Missing required field: {field}"
    
    # Validate business type
    if not isinstance(data["businessType"], str) or not data["businessType"].strip():
        return "businessType must be a non-empty string"
    
    # Validate location
    if not isinstance(data["location"], str) or not data["location"].strip():
        return "location must be a non-empty string"
    
    # Validate search offset
    if not isinstance(data["searchOffset"], int) or data["searchOffset"] < 0:
        return "searchOffset must be a non-negative integer"
    
    # Validate number of leads
    if not isinstance(data["numberOfLeads"], int) or data["numberOfLeads"] <= 0:
        return "numberOfLeads must be a positive integer"
    
    # If all validations pass
    return None