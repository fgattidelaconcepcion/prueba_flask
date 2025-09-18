import os
from dotenv import load_dotenv
import requests

load_dotenv()

def expand_keywords(topic, rapidapi_key=None, country="us", language="en", mock=False):
    if mock:
        return [f"{topic} ejemplo1", f"{topic} ejemplo2"]

    if rapidapi_key is None:
        rapidapi_key = os.getenv("RAPIDAPI_KEY")

    url = "https://google-keyword-insight1.p.rapidapi.com/keysuggest/"
    headers = {
        "x-rapidapi-host": "google-keyword-insight1.p.rapidapi.com",
        "x-rapidapi-key": rapidapi_key
    }
    params = {"keyword": topic, "location": country, "lang": language}

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    data = response.json()

    # Devuelvo solo la lista de keywords
    return [item["text"] for item in data]
