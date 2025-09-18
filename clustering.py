"""
En este archivo me ocupo de agrupar keywords en clusters
según el criterio de URLs compartidas en Top 10,
y de clasificar cada cluster en present/missing,
además de contar los competidores más frecuentes.
"""

import networkx as nx
from collections import Counter
from urllib.parse import urlparse

def domain_from_url(url):
    try:
        return urlparse(url).netloc
    except Exception:
        return ""

def cluster_keywords(keywords, serp_top10, threshold=5):
    """
    Construyo un grafo de keywords. Creo aristas si comparten ≥5 URLs en el Top10.
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
