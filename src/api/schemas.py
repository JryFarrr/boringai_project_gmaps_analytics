input_schema = {
    'tags': ['Workflow'], 'summary': 'Start the lead generation workflow',
    'parameters': [{'in': 'body', 'name': 'body', 'required': True, 'schema': {
        'type': 'object', 'required': ['business_type', 'location', 'numberOfLeads'],
        'properties': {
            'business_type': {'type': 'string', 'example': 'cafe'},
            'location': {'type': 'string', 'example': 'Surabaya'},
            'numberOfLeads': {'type': 'integer', 'example': 3},
            'min_rating': {'type': 'number'}, 'min_reviews': {'type': 'integer'},
            'price_range': {'type': 'string'}, 'keywords': {'type': 'string'}
        }}}], 'responses': {'200': {'description': 'Workflow started'}}
}
search_schema = {
    'tags': ['Workflow'], 'summary': 'Search for business place IDs',
    'parameters': [{'in': 'body', 'name': 'body', 'required': True, 'schema': {
        'type': 'object', 'properties': {'state': {'type': 'object'}}}}],
    'responses': {'200': {'description': 'Search successful'}}
}
scrape_schema = {
    'tags': ['Workflow'], 'summary': 'Scrape details for a place ID',
    'parameters': [{'in': 'body', 'name': 'body', 'required': True, 'schema': {
        'type': 'object', 'properties': {'state': {'type': 'object'}}}}],
    'responses': {'200': {'description': 'Scrape successful'}}
}
analyze_schema = {
    'tags': ['Workflow'], 'summary': 'Analyze scraped data',
    'parameters': [{'in': 'body', 'name': 'body', 'required': True, 'schema': {
        'type': 'object', 'properties': {'state': {'type': 'object'}}}}],
    'responses': {'200': {'description': 'Analysis successful'}}
}
control_schema = {
    'tags': ['Workflow'], 'summary': 'Control the workflow execution',
    'parameters': [{'in': 'body', 'name': 'body', 'required': True, 'schema': {
        'type': 'object', 'properties': {'state': {'type': 'object'}}}}],
    'responses': {'200': {'description': 'Control flow determined'}}
}