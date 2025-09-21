"""
En este archivo me ocupo de:
- Expandir keywords relacionadas con una API externa
- Agrupar keywords en clusters según URLs compartidas
- Clasificar clusters en present/missing
- Detectar competidores principales
"""

import os
import requests
import networkx as nx
from collections import Counter
from urllib.parse import urlparse
from dotenv import load_dotenv

# Cargo las variables de entorno desde .env
load_dotenv()


def domain_from_url(url):
    """Extraigo solo el dominio de una URL"""
    try:
        return urlparse(url).netloc
    except Exception:
        return ""


# =========================================================
# Función para obtener keywords relacionadas (expand_keywords)
# =========================================================
def expand_keywords(topic, rapidapi_key=None, country="us", language="en", mock=False):
    """
    Obtengo keywords relacionadas usando RapidAPI.
    Intento con Smart Keyword Research API y si falla uso Google Keyword Insight.
    """
    if mock:
        return [f"{topic} ejemplo1", f"{topic} ejemplo2"]

    if rapidapi_key is None:
        rapidapi_key = os.getenv("RAPIDAPI_KEY")

    # --------------------------
    # Intento 1: Smart Keyword Research API (/search)
    # --------------------------
    try:
        url = "https://smart-keyword-research-api.p.rapidapi.com/search"
        headers = {
            "x-rapidapi-host": "smart-keyword-research-api.p.rapidapi.com",
            "x-rapidapi-key": rapidapi_key
        }
        params = {
            "keyword": topic,
            "country": country,
            "languagecode": language
        }

        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict) and "data" in data:
                return [kw.get("keyword", "") for kw in data["data"] if "keyword" in kw]
            if isinstance(data, list):
                return data
        else:
            print("⚠️ Smart Keyword Research API devolvió:", response.status_code, response.text)
    except Exception as e:
        print("❌ Error con Smart Keyword Research API:", str(e))

    # --------------------------
    # Intento 2: Google Keyword Insight API (/keysuggest)
    # --------------------------
    try:
        url = "https://google-keyword-insight1.p.rapidapi.com/keysuggest/"
        headers = {
            "x-rapidapi-host": "google-keyword-insight1.p.rapidapi.com",
            "x-rapidapi-key": rapidapi_key
        }
        params = {
            "keyword": topic,
            "location": country,
            "lang": language
        }

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "suggestions" in data:
            return data["suggestions"]

        return data
    except Exception as e:
        print("❌ Error con Google Keyword Insight API:", str(e))

    return []


# =========================================================
# Función para clusterizar keywords
# =========================================================
def cluster_keywords(keywords, serp_top10, threshold=2):
    """
    Construyo un grafo de keywords. Creo aristas si comparten ≥threshold URLs en el Top10.
    Luego devuelvo clusters de keywords.
    """
    G = nx.Graph()
    G.add_nodes_from(keywords)

    for i in range(len(keywords)):
        for j in range(i+1, len(keywords)):
            kw1, kw2 = keywords[i], keywords[j]
            overlap = len(set(serp_top10.get(kw1, [])) & set(serp_top10.get(kw2, [])))
            if overlap >= threshold:
                G.add_edge(kw1, kw2)

    clusters = list(nx.connected_components(G))
    return [list(c) for c in clusters]


# =========================================================
# Función para clasificar clusters
# =========================================================
def classify_clusters(clusters, domain, serp_top20):
    """
    Marco un cluster como present si el dominio aparece en Top20 de alguna keyword.
    Caso contrario, lo marco como missing.
    """
    classified = []
    for cluster in clusters:
        present = []
        missing = True
        for kw in cluster:
            urls = serp_top20.get(kw, [])
            for i, u in enumerate(urls, start=1):
                if domain in u:
                    present.append({"keyword": kw, "url": u, "position": i})
                    missing = False
        classified.append({
            "cluster_keywords": cluster,
            "status": "missing" if missing else "present",
            "details": present
        })
    return classified


# =========================================================
# Función para detectar competidores
# =========================================================
def top_competitors(serp_top20, exclude_domain, top_n=3):
    """
    Cuento los dominios que aparecen en Top20 (excluyendo el dominio input).
    Devuelvo el top 3.
    """
    domains = []
    for urls in serp_top20.values():
        for u in urls:
            if exclude_domain not in u:
                domains.append(domain_from_url(u))
    counter = Counter(domains)
    return counter.most_common(top_n)
