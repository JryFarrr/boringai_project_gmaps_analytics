import requests
from src.config import config

url = "https://www.searchapi.io/api/v1/search"
params = {
  "engine": "google_maps_reviews",
  "data_id": "0x89c25a21fb011c85:0x33df10e49762f8e4",
  "api_key": config.AP
}

response = requests.get(url, params=params)
print(response.text)
