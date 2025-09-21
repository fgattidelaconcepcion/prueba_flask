"""
Archivo principal de la API en Flask.
Acá conecto todo: recibo input, expando keywords, obtengo SERPs,
armo clusters, clasifico y calculo competidores.
"""

from flask import Flask, request, jsonify
import os
import requests
from dotenv import load_dotenv

# Importo las funciones de serp_client
from serp_client import expand_keywords, cluster_keywords, classify_clusters, top_competitors

# Cargo las variables de entorno
load_dotenv()

# Inicializo Flask
app = Flask(__name__)

# Modo mock desactivado (la prueba pide datos reales)
MOCK_MODE = False

# API Key de SerpAPI
SERPAPI_KEY = os.getenv("SERPAPI_KEY")


@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        # Input
        data = request.get_json()
        print(" Recibido:", data)

        topic = data.get("topic")
        domain = data.get("domain")
        country = data.get("country", "us")
        language = data.get("language", "en")

        # 1. Expando keywords (hasta 30 relacionadas)
        keywords_raw = expand_keywords(topic, country=country, language=language, mock=MOCK_MODE)[:30]

        keywords = [kw["text"] if isinstance(kw, dict) and "text" in kw else str(kw) for kw in keywords_raw]
        print(" Keywords normalizadas:", keywords)

        serp_top10 = {}
        serp_top20 = {}

        # 2. SERP Top 100 por keyword
        for kw in keywords:
            url = "https://serpapi.com/search.json"
            params = {
                "q": kw,
                "num": 100,
                "engine": "google",
                "api_key": SERPAPI_KEY,
                "hl": language,
                "gl": country
            }
            resp = requests.get(url, params=params)
            print(f"{kw} → status:", resp.status_code)

            if resp.status_code != 200:
                print("Error en SerpAPI:", resp.text)
                continue

            results = resp.json()
            urls = [r.get("link") for r in results.get("organic_results", []) if "link" in r]
            print(f"➡ {kw}: {len(urls)} resultados")

            serp_top10[kw] = urls[:10]
            serp_top20[kw] = urls[:20]

        # 3. Clusters con threshold = 2
        clusters_raw = cluster_keywords(keywords, serp_top10, threshold=2)
        print(" Clusters generados:", clusters_raw)

        # 4. Clasifico clusters
        clusters = classify_clusters(clusters_raw, domain, serp_top20)

        # 5. Competidores
        competitors = top_competitors(serp_top20, exclude_domain=domain, top_n=3)

        # 6. Respuesta final
        response = {
            "topic": topic,
            "domain": domain,
            "keywords": keywords,
            "clusters": clusters,
            "top_competitors": competitors
        }
        return jsonify(response)

    except Exception as e:
        print("Error en analyze:", str(e))
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
