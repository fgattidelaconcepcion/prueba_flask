from flask import Flask, request, jsonify
from serp_client import expand_keywords  # importo la función real
import os

app = Flask(__name__)

# Modo real, no mock
MOCK_MODE = False  

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    topic = data.get("topic")
    domain = data.get("domain")
    country = data.get("country", "us")
    language = data.get("language", "en")

    try:
        # Llamo a la función real en serp_client.py
        keywords = expand_keywords(topic, country=country, language=language, mock=MOCK_MODE)

        response = {
            "topic": topic,
            "domain": domain,
            "keywords": keywords[:20],  # recorto a ~20
            "clusters": [],             # por ahora vacío, se llena con clusterización real
            "top_competitors": []       # se llena cuando metas el análisis de SERPs
        }
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
