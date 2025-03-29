# BoringAIGmapsAnalytics

BoringAIGmapsAnalytics is an AI-powered business discovery tool developed by AI Engineers from AVALON AI and Boring AI that uses Google Places API to search and analyze businesses based on complex search criteria.

## Features

- Search businesses using natural language prompts
- Filter by rating, review count, price range, and more
- Analyze business data with AI processing
- Web interface for easy searching
- API endpoints for integration with other systems

## Installation

### Option 1: Using pip

```bash
pip install .
```

### Option 2: Using Docker

```bash
docker-compose up
```

## Configuration

Before using the application, you need to set up your API keys:

1. Create a `.env` file in the project root (copy from `.env.template`)
2. Add your Google Places API key and OpenRouter API key:

```
GOOGLE_API_KEY=your_google_api_key_here
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

Alternatively, create a `config.json` file:

```json
{
    "google_api_key": "your_google_api_key_here",
    "openrouter_api_key": "your_openrouter_api_key_here"
}
```

## Usage

### Command Line Interface

```bash
python -m boring_ai_gmaps_analytics.main
```

You can also specify a preset prompt type:

```bash
python -m boring_ai_gmaps_analytics.main food_supplier
```

### Python API

```python
from boring_ai_gmaps_analytics.map_leads import MapLeadsAI

# Initialize with your API keys
map_leads = MapLeadsAI(google_api_key, openrouter_api_key)

# Run a search
results = map_leads.run_search("Find a restaurant in Surabaya with rating above 4.0")
```

### Web Interface

Run the Flask app:

```bash
flask run
```

Or with Docker:

```bash
docker-compose up
```

Then open your browser to http://localhost:9975

## API Endpoints

### `/api/search` (POST)

Search for businesses using a natural language prompt.

**Request Body:**
```json
{
  "prompt": "Find a restaurant in Surabaya that has a rating of at least 4.0"
}
```

**Response:**
```json
{
  "results": [
    {
      "Name": "Business Name",
      "Address": "Business Address",
      "Rating": "4.5",
      ...
    },
    ...
  ],
  "analysis": {
    "total": 10,
    "highest_rated": "Business Name",
    "max_rating": 4.8,
    "most_reviews": "Business Name"
  }
}
```

### `/healthcheck` (GET)

Check if the API is running correctly.

## Development

1. Clone the repository
2. Create a virtual environment
3. Install dependencies:
```bash
pip install -r requirements.txt
pip install -e .
```

## Deployment

The project is Docker-ready for easy deployment. 

1. Build the Docker image:
```bash
docker build -t boring-ai-gmaps-analytics .
```

2. Run the container:
```bash
docker run -p 9975:9975 -e GOOGLE_API_KEY=your_key -e OPENROUTER_API_KEY=your_key boring-ai-gmaps-analytics
```

## License

MIT License