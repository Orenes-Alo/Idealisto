"""Buscador de referencia catastral por dirección.

Provincia → municipio → calle → número → inmuebles (RC de 20, planta, puerta,
uso, superficie). Las consultas al callejero JSON del Catastro pasan por el
backend de Orenes (/internal/catastro/callejero/:metodo, con su proxy y su
límite de concurrencia), nunca directamente desde la IP del VPS. Caché en
SQLite de 30 días: el callejero apenas cambia.
"""
from __future__ import annotations

import json
import sqlite3
import threading
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

PROVINCIAS = [
    ["15", "A CORUÑA"], ["03", "ALACANT"], ["02", "ALBACETE"], ["04", "ALMERIA"], ["33", "ASTURIAS"],
    ["05", "AVILA"], ["06", "BADAJOZ"], ["08", "BARCELONA"], ["09", "BURGOS"], ["10", "CACERES"],
    ["11", "CADIZ"], ["39", "CANTABRIA"], ["12", "CASTELLO"], ["51", "CEUTA"], ["13", "CIUDAD REAL"],
    ["14", "CORDOBA"], ["16", "CUENCA"], ["17", "GIRONA"], ["18", "GRANADA"], ["19", "GUADALAJARA"],
    ["21", "HUELVA"], ["22", "HUESCA"], ["07", "ILLES BALEARS"], ["23", "JAEN"], ["26", "LA RIOJA"],
    ["35", "LAS PALMAS"], ["24", "LEON"], ["25", "LLEIDA"], ["27", "LUGO"], ["28", "MADRID"],
    ["29", "MALAGA"], ["52", "MELILLA"], ["30", "MURCIA"], ["32", "OURENSE"], ["34", "PALENCIA"],
    ["36", "PONTEVEDRA"], ["38", "S.C. TENERIFE"], ["37", "SALAMANCA"], ["40", "SEGOVIA"],
    ["41", "SEVILLA"], ["42", "SORIA"], ["43", "TARRAGONA"], ["44", "TERUEL"], ["45", "TOLEDO"],
    ["46", "VALENCIA"], ["47", "VALLADOLID"], ["49", "ZAMORA"], ["50", "ZARAGOZA"],
]
NOMBRES_PROV = {n for _, n in PROVINCIAS}
TTL = 30 * 86400
USOS = {"Residencial": "Vivienda", "Almacen-Estacionamiento": "Garaje / trastero", "Comercial": "Local",
        "Industrial": "Industrial", "Oficinas": "Oficina", "Suelo sin edif.": "Suelo"}


class CallejeroError(Exception):
    pass


def norm(s: str) -> str:
    """Mayúsculas sin tildes (salvo Ñ), como el callejero del Catastro."""
    s = (s or "").strip().upper().replace("Ñ", "\0")
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    return " ".join(s.replace("\0", "Ñ").split())[:80]


def _lista(x) -> list:
    if x is None:
        return []
    return x if isinstance(x, list) else [x]


class Callejero:
    def __init__(self, base_urls: list[str], token: str, db_path: str):
        self.bases = base_urls
        self.token = token
        self.con = sqlite3.connect(db_path, check_same_thread=False)
        self.con.execute("CREATE TABLE IF NOT EXISTS callejero_cache(k TEXT PRIMARY KEY, ts REAL, v TEXT)")
        self.lock = threading.Lock()

    def _ovc(self, metodo: str, params: dict) -> dict:
        clave = metodo + "?" + urllib.parse.urlencode(sorted(params.items()))
        with self.lock:
            fila = self.con.execute("SELECT ts, v FROM callejero_cache WHERE k=?", (clave,)).fetchone()
        if fila and time.time() - fila[0] < TTL:
            return json.loads(fila[1])
        if not self.token:
            raise CallejeroError("sin token")
        ultimo = None
        for base in self.bases:
            req = urllib.request.Request(f"{base}/{metodo}?{urllib.parse.urlencode(params)}",
                                         headers={"Authorization": f"Bearer {self.token}"})
            try:
                with urllib.request.urlopen(req, timeout=25) as r:
                    txt = r.read().decode()
                break
            except urllib.error.HTTPError as e:
                ultimo = e
                if e.code == 404:          # color sin el endpoint
                    continue
                raise CallejeroError(f"HTTP {e.code}")
            except (urllib.error.URLError, ConnectionError, TimeoutError) as e:
                ultimo = e
        else:
            raise CallejeroError(str(ultimo))
        data = json.loads(txt)
        with self.lock:
            self.con.execute("INSERT OR REPLACE INTO callejero_cache VALUES(?,?,?)", (clave, time.time(), txt))
            self.con.commit()
        return data

    def municipios(self, prov: str, q: str) -> list[str]:
        d = self._ovc("ObtenerMunicipios", {"Provincia": prov, "Municipio": norm(q)})
        r = d.get("consulta_municipieroResult", {})
        nombres = [m.get("nm") for m in _lista(r.get("municipiero", {}).get("muni")) if m.get("nm")]
        qn = norm(q)
        # Coincidencia exacta y luego «empieza por» primero: «Murcia» antes que «Alhama de Murcia».
        nombres.sort(key=lambda n: (n != qn, not n.startswith(qn), n))
        return nombres[:30]

    def calles(self, prov: str, mun: str, q: str) -> list[dict]:
        d = self._ovc("ObtenerCallejero", {"Provincia": prov, "Municipio": mun, "TipoVia": "", "NomVia": norm(q)})
        r = d.get("consulta_callejeroResult", {})
        out, vistos = [], set()
        for c in _lista(r.get("callejero", {}).get("calle")):
            dr = c.get("dir", {})
            nv, tv = dr.get("nv") or "", dr.get("tv") or ""
            calle, _, nucleo = nv.partition("  en  ")
            k = (tv, calle.strip(), nucleo.strip())
            if calle and k not in vistos:
                vistos.add(k)
                out.append({"tv": tv, "calle": calle.strip(), "nucleo": nucleo.strip().title()})
        return out[:40]

    def inmuebles(self, prov: str, mun: str, tv: str, calle: str, num: str) -> dict:
        d = self._ovc("Consulta_DNPLOC", {"Provincia": prov, "Municipio": mun, "Sigla": tv,
                                          "Calle": calle, "Numero": num})
        r = d.get("consulta_dnplocResult", {})
        bis = []
        if r.get("bico"):
            b = r["bico"].get("bi", {})
            bis.append({"rc": b.get("idbi", {}).get("rc"), "dt": b.get("dt", {}), "debi": b.get("debi", {})})
        for x in _lista((r.get("lrcdnp") or {}).get("rcdnp")):
            bis.append({"rc": x.get("rc"), "dt": x.get("dt", {}), "debi": x.get("debi", {})})
        inm = []
        for b in bis:
            rc = b["rc"] or {}
            ref = "".join(rc.get(k, "") for k in ("pc1", "pc2", "car", "cc1", "cc2"))
            if len(ref) != 20:
                continue
            loint = (((b["dt"].get("locs") or {}).get("lous") or {}).get("lourb") or {}).get("loint") or {}
            luso = b["debi"].get("luso") or ""
            sfc = b["debi"].get("sfc")
            inm.append({"rc": ref, "escalera": loint.get("es") or "", "planta": loint.get("pt") or "",
                        "puerta": loint.get("pu") or "", "uso": USOS.get(luso, luso),
                        "superficie": int(sfc) if str(sfc or "").isdigit() else None,
                        "anio": b["debi"].get("ant")})
        numeros = sorted({n.get("num", {}).get("pnp") for n in
                          _lista((r.get("numerero") or {}).get("nump")) if n.get("num", {}).get("pnp") not in (None, "0")},
                         key=lambda s: int(s) if s.isdigit() else 0)
        errores = [e.get("des") for e in _lista(r.get("lerr") if isinstance(r.get("lerr"), list)
                                                 else (r.get("lerr") or {}).get("err"))]
        return {"inmuebles": inm[:400], "numeros": numeros[:60],
                "error": None if inm else ((errores[0] or "").capitalize().rstrip(".") + "." if errores
                                           else "No hay inmuebles en ese número.")}
