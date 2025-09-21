"""
En este archivo me ocupo de:
- Agrupar keywords en clusters por solape de URLs (Top 10 normalizado).
- Clasificar cada cluster en present/missing según presencia del dominio en Top 20.
- Contar competidores (visibilidad 1 por keyword), excluyendo el dominio analizado.
"""

import networkx as nx
from collections import Counter, defaultdict
from urllib.parse import urlparse, urlunparse


# Helpers de normalización

def _normalize_domain(d: str) -> str:
    """Dejo el dominio en minúsculas y sin 'www.'; si me pasan una URL, extraigo netloc."""
    if not d:
        return ""
    d = d.strip().lower()
    # Si viene una URL completa, extraigo su dominio
    if d.startswith("http://") or d.startswith("https://"):
        try:
            d = urlparse(d).netloc
        except Exception:
            pass
    # Quito puerto si lo hubiera
    d = d.split(":")[0]
    # Quito www.
    if d.startswith("www."):
        d = d[4:]
    return d

def _extract_domain_from_url(url: str) -> str:
    """Extraigo netloc y lo normalizo (minúsculas, sin www)."""
    try:
        netloc = urlparse(url).netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return netloc
    except Exception:
        return ""

def _same_domain(target_base: str, url_domain: str) -> bool:
    """Considero mismo dominio si coincide exacto o es subdominio del target."""
    if not target_base or not url_domain:
        return False
    return url_domain == target_base or url_domain.endswith("." + target_base)

def _normalize_for_overlap(url: str) -> str:
    """
    Normalizo URL para comparar solapes:
    - Bajo dominio a minúsculas, quito www
    - Quito query y fragment
    - Quito '/' final del path
    - Devuelvo 'dominio + path' como string canónico
    """
    try:
        p = urlparse(url)
        netloc = p.netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        path = (p.path or "").rstrip("/")
        # reconstruyo sin query/fragment
        clean = urlunparse((p.scheme, netloc, path, "", "", ""))
        # No necesito el scheme para comparar
        return f"{netloc}{path}"
    except Exception:
        return url or ""


# Clustering por solape de Top-10 normalizado

def cluster_keywords(keywords, serp_top10, threshold=5):
    """
    Construyo un grafo de keywords.
    Creo aristas si comparten ≥ threshold URLs en el Top10 (tras normalización).
    Devuelvo clusters (componentes conexas).
    """
    # Pre-normalizo conjuntos Top-10 por keyword para no recalcular mil veces
    norm10 = {}
    for kw in keywords:
        urls = serp_top10.get(kw, []) or []
        norm10[kw] = { _normalize_for_overlap(u) for u in urls if u }

    G = nx.Graph()
    G.add_nodes_from(keywords)

    n = len(keywords)
    for i in range(n):
        for j in range(i+1, n):
            kw1, kw2 = keywords[i], keywords[j]
            overlap = len(norm10.get(kw1, set()) & norm10.get(kw2, set()))
            if overlap >= threshold:
                G.add_edge(kw1, kw2)

    clusters = list(nx.connected_components(G))
    return [list(c) for c in clusters]


# Clasificación present/missing sobre Top-20 normal

def classify_clusters(clusters, domain, serp_top20):
    """
    Marco un cluster como present si el dominio aparece en Top20 de alguna keyword.
    Caso contrario, lo marco como missing.
    Además guardo las URLs exactas y posiciones (1-based).
    """
    target = _normalize_domain(domain)
    classified = []

    for cluster in clusters:
        details = []
        missing = True
        for kw in cluster:
            urls = serp_top20.get(kw, []) or []
            for i, u in enumerate(urls, start=1):
                u_dom = _extract_domain_from_url(u)
                if _same_domain(target, u_dom):
                    details.append({"keyword": kw, "url": u, "position": i})
                    missing = False

        classified.append({
            "cluster_keywords": cluster,
            "status": "missing" if missing else "present",
            "details": details
        })

    return classified


# Top competidores (visibilidad = 1 por keyword)

def top_competitors(serp_top20, exclude_domain, top_n=3):
    """
    Para cada keyword cuento visibilidad de dominios en Top-20:
    - Cada dominio suma como mucho 1 por keyword (aunque tenga varias URLs).
    - Excluyo el dominio analizado (comparación robusta por dominio base).
    Devuelvo los top_n más frecuentes.
    """
    target = _normalize_domain(exclude_domain)
    counter = Counter()

    for kw, urls in serp_top20.items():
        seen_this_kw = set()
        for u in urls or []:
            d = _extract_domain_from_url(u)
            if not d:
                continue
            if _same_domain(target, d):
                continue  # excluyo mi dominio (incluye subdominios)
            # normalizo a dominio base ya limpio
            if d not in seen_this_kw:
                seen_this_kw.add(d)
        # al final de la keyword, incremento 1 por dominio visto
        counter.update(seen_this_kw)

    return counter.most_common(top_n)
