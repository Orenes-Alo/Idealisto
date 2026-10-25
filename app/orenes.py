"""Cliente de los endpoints internos del backend de Orenes (mismo VPS).

Prueba los dos colores del despliegue blue/green (3001 y 3002): fuera de un
deploy solo uno está vivo y el otro rechaza la conexión al instante. Un 404
sin cuerpo = ese color aún no tiene el endpoint (deploy a medias) → siguiente.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

BASES = [u.rsplit("/internal/", 1)[0] for u in os.getenv(
    "AVM_URLS", "http://127.0.0.1:3001/internal/avm/rc,http://127.0.0.1:3002/internal/avm/rc").split(",") if u]
TOKEN = os.getenv("IDEALISTO_AVM_TOKEN", "")


class OrenesError(Exception):
    def __init__(self, status: int, data: dict | None = None):
        super().__init__(f"orenes {status} {data or ''}")
        self.status = status
        self.data = data or {}


def llamar(metodo: str, ruta: str, cuerpo: dict | None = None, timeout: float = 30, crudo: bool = False):
    """JSON (o bytes si crudo=True) de `ruta` (p. ej. "/internal/idealisto/lead")."""
    if not TOKEN:
        raise OrenesError(503, {"error": "sin_token"})
    ultimo: Exception | None = None
    for base in BASES:
        req = urllib.request.Request(
            base + ruta, method=metodo,
            data=json.dumps(cuerpo).encode() if cuerpo is not None else None,
            headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                datos = r.read()
            return datos if crudo else json.loads(datos.decode() or "{}")
        except urllib.error.HTTPError as e:
            texto = e.read().decode(errors="replace")
            if e.code == 404 and not texto.strip():
                ultimo = e
                continue
            try:
                info = json.loads(texto or "{}")
            except ValueError:
                info = {"detalle": texto[:200]}
            raise OrenesError(e.code, info)
        except (urllib.error.URLError, ConnectionError, TimeoutError) as e:
            ultimo = e
    raise OrenesError(502, {"detalle": str(ultimo)})
