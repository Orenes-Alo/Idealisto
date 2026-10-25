"""IndexNow: avisa a Bing, Yandex, Seznam y Naver (y a los buscadores con IA que
beben de Bing) de las URLs nuevas o cambiadas, sin esperar a que rastreen.

La clave es pública por diseño: se publica en /<clave>.txt y el buscador la
comprueba. Se lanza al terminar la regeneración semanal de zonas
(idealisto-zonas.service, ExecStartPost) y a mano tras un despliegue:

    python -m app.indexnow            # todas las URLs de los sitemaps
    python -m app.indexnow /guias/    # solo las indicadas
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

INDEXNOW_KEY = os.getenv("INDEXNOW_KEY", "5b0f7d2c9a4e4f1b8c3d6e2a7f9b1c4d")
# Bing comparte cada aviso con el resto de buscadores del protocolo. api.indexnow.org
# respondía 403 a la primera verificación de la clave (25-10-2026); Bing, 200.
ENDPOINT = os.getenv("INDEXNOW_ENDPOINT", "https://www.bing.com/indexnow")
MAX_URLS = 10000  # límite por petición del protocolo


def enviar(site_url: str, urls: list[str]) -> list[int]:
    """Envía las URLs en lotes; devuelve el código HTTP de cada lote (200/202 = aceptado)."""
    host = site_url.split("://", 1)[-1].rstrip("/")
    codigos = []
    for i in range(0, len(urls), MAX_URLS):
        cuerpo = json.dumps({"host": host, "key": INDEXNOW_KEY, "keyLocation": f"{site_url}/{INDEXNOW_KEY}.txt",
                             "urlList": urls[i:i + MAX_URLS]}).encode()
        req = urllib.request.Request(ENDPOINT, data=cuerpo, method="POST",
                                     headers={"Content-Type": "application/json; charset=utf-8"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                codigos.append(r.status)
        except urllib.error.HTTPError as e:  # 400/403/422/429: se registra y se sigue
            codigos.append(e.code)
    return codigos


def _urls_sitemap(site_url: str) -> list[str]:
    import re
    def leer(u: str) -> str:
        with urllib.request.urlopen(u, timeout=30) as r:
            return r.read().decode()
    indice = leer(f"{site_url}/sitemap.xml")
    urls: list[str] = []
    for sm in re.findall(r"<loc>([^<]+)</loc>", indice):
        urls += re.findall(r"<loc>([^<]+)</loc>", leer(sm))
    return urls


if __name__ == "__main__":
    site = os.getenv("SITE_URL", "https://idealisto.es").rstrip("/")
    rutas = sys.argv[1:]
    lista = [site + r for r in rutas] if rutas else _urls_sitemap(site)
    print(f"IndexNow: {len(lista)} URLs → {enviar(site, lista)}")
