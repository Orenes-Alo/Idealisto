#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Idealisto — tasador de inmuebles por referencia catastral (idealisto.es)
=======================================================================

FastAPI en un proceso (puerto 3201 detrás de nginx). La valoración la hace el
motor de Orenes (POST /internal/avm/rc del backend de inversionnpl.com, mismo
VPS): Catastro + testigos de la zona, el mismo precio justo que Testigos de
venta. Sin AVM configurado, /api/valorar responde 503 (nunca cifras inventadas).

Variables de entorno (fichero .env del repo en el servidor, no versionado):
    IDEALISTO_AVM_TOKEN   token compartido con el backend de Orenes (obligatorio)
    AVM_URLS              por defecto los dos colores blue/green del backend
    DB_PATH               SQLite de valoraciones anónimas y leads
    RESEND_API_KEY, RESEND_FROM   si están, se ofrece el informe por email
    GA4_ID, SAME_AS       opcionales

Arranque local:  uvicorn app.idealisto:app --port 3201
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import threading
import time
import urllib.error
import urllib.request
from collections import defaultdict, deque
from datetime import date, datetime, timezone
from html import escape
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import (FileResponse, HTMLResponse, JSONResponse, PlainTextResponse,
                               RedirectResponse, Response)

from . import calculadoras, contenido, fiscal
from .callejero import NOMBRES_PROV, PROVINCIAS, Callejero, CallejeroError, norm
from .rc import normalizar_rc, validar_rc
from .zonas import Zonas

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────────────────────────────────────────
RAIZ = Path(__file__).resolve().parent.parent
BRAND = "Idealisto"
SITE_URL = os.getenv("SITE_URL", "https://idealisto.es").rstrip("/")
LEGAL_NAME = contenido.RAZON
CONTACT_EMAIL = contenido.EMAIL
AVM_URLS = [u for u in os.getenv(
    "AVM_URLS", "http://127.0.0.1:3001/internal/avm/rc,http://127.0.0.1:3002/internal/avm/rc").split(",") if u]
AVM_TOKEN = os.getenv("IDEALISTO_AVM_TOKEN", "")
AVM_TIMEOUT = float(os.getenv("AVM_TIMEOUT", "45"))
DB_PATH = os.getenv("DB_PATH", str(RAIZ / "data" / "idealisto.sqlite3"))
GA4_ID = os.getenv("GA4_ID", "")
RATE_LIMIT = int(os.getenv("RATE_LIMIT", "20"))            # valoraciones por IP y hora
SAME_AS = [u for u in os.getenv("SAME_AS", "").split(",") if u]
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
RESEND_FROM = os.getenv("RESEND_FROM", "")
EMAIL_ACTIVO = bool(RESEND_API_KEY and RESEND_FROM)
LAST_MOD = date.today().isoformat()
SEDE_BUSQUEDA = "https://www1.sedecatastro.gob.es/CYCBienInmueble/OVCBusqueda.aspx"

# ─────────────────────────────────────────────────────────────────────────────
# AVM (motor de Orenes)
# ─────────────────────────────────────────────────────────────────────────────
class AvmError(Exception):
    def __init__(self, status: int, data: dict | None = None):
        super().__init__(status)
        self.status = status
        self.data = data or {}


def valorar_inmueble(rc: str) -> dict:
    """POST al backend de Orenes. Prueba los dos colores (blue/green): solo uno
    está vivo fuera de un deploy; el caído rechaza la conexión al instante."""
    if not AVM_TOKEN:
        raise AvmError(503)
    ultimo: Exception | None = None
    for url in AVM_URLS:
        req = urllib.request.Request(
            url, data=json.dumps({"rc": rc}).encode(), method="POST",
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {AVM_TOKEN}"})
        try:
            with urllib.request.urlopen(req, timeout=AVM_TIMEOUT) as r:
                data = json.loads(r.read().decode())
            if not data.get("valor_central"):
                raise AvmError(502)
            return data
        except urllib.error.HTTPError as e:
            try:
                cuerpo = json.loads(e.read().decode() or "{}")
            except ValueError:
                cuerpo = {}
            if e.code == 404 and not cuerpo:   # color sin el endpoint (deploy a medias)
                ultimo = e
                continue
            raise AvmError(e.code, cuerpo)
        except (urllib.error.URLError, ConnectionError, TimeoutError) as e:
            ultimo = e
            continue
    raise AvmError(502, {"detalle": str(ultimo)})


USOS = {"vivienda": "Vivienda", "piso": "Vivienda", "casa": "Casa / unifamiliar", "garaje": "Garaje",
        "trastero": "Trastero", "local": "Local", "nave": "Nave", "suelo": "Suelo", "oficina": "Oficina"}


def _uso(t: str | None) -> str | None:
    return USOS.get((t or "").lower(), (t or "").capitalize() or None)


def para_publico(d: dict) -> dict:
    """Solo lo que se enseña; el resto del motor no sale de casa."""
    out = {k: d.get(k) for k in ("valor_central", "valor_min", "valor_max", "eur_m2", "eur_m2_zona",
                                 "superficie_m2", "anio_construccion", "direccion", "confianza",
                                 "cierre_estimado", "testigos", "radio_km")}
    out["uso"] = _uso(d.get("uso"))
    # El backend añadía ", MUNICIPIO" a una dirección del Catastro que ya lo lleva.
    dire, muni = out.get("direccion") or "", d.get("municipio") or ""
    if muni and dire.endswith(", " + muni) and dire.count(muni) > 1:
        out["direccion"] = dire[: -len(", " + muni)]
    return out


# Locales y naves se valoran con otros métodos (rentas, reposición): fuera de la
# herramienta pública, como dicen la metodología y la FAQ.
FUERA_DE_ALCANCE = {"local", "nave"}


# ─────────────────────────────────────────────────────────────────────────────
# Persistencia mínima (valoraciones anónimas + leads)
# ─────────────────────────────────────────────────────────────────────────────
_db_lock = threading.Lock()


def _db():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    con.execute("""CREATE TABLE IF NOT EXISTS valoraciones(
        id INTEGER PRIMARY KEY, ts TEXT, rc_hash TEXT, uso TEXT, provincia TEXT, valor INTEGER,
        ok INTEGER, error TEXT)""")
    con.execute("""CREATE TABLE IF NOT EXISTS leads(
        id INTEGER PRIMARY KEY, ts TEXT, email TEXT, rc TEXT, perfil TEXT,
        motivo TEXT, consentimiento INTEGER, enviado INTEGER DEFAULT 0)""")
    return con


_CON = _db()
CALLEJERO = Callejero([u.replace("/internal/avm/rc", "/internal/catastro/callejero") for u in AVM_URLS],
                      AVM_TOKEN, DB_PATH)


def _log_valoracion(rc: str, data: dict | None, ok: bool, error: str | None = None):
    with _db_lock:
        _CON.execute("INSERT INTO valoraciones(ts,rc_hash,uso,provincia,valor,ok,error) VALUES(?,?,?,?,?,?,?)", (
            datetime.now(timezone.utc).isoformat(),
            hashlib.sha256(rc.encode()).hexdigest()[:16],  # no guardamos la RC en claro
            (data or {}).get("uso"), (data or {}).get("provincia"), (data or {}).get("valor_central"),
            int(ok), error))
        _CON.commit()


# ─────────────────────────────────────────────────────────────────────────────
# Rate limit simple (en memoria; nginx pasa la IP real en X-Real-IP)
# ─────────────────────────────────────────────────────────────────────────────
_hits: dict[str, deque] = defaultdict(deque)


def _ip(request: Request) -> str:
    return (request.headers.get("x-real-ip")
            or request.headers.get("x-forwarded-for", "").split(",")[0].strip()
            or (request.client.host if request.client else "?"))


def _limitado(ip: str, cupo: int = RATE_LIMIT) -> bool:
    now = time.time()
    q = _hits[ip]
    while q and now - q[0] > 3600:
        q.popleft()
    if len(q) >= cupo:
        return True
    q.append(now)
    return False


# ─────────────────────────────────────────────────────────────────────────────
# CONTENIDO (FAQ y HowTo se reutilizan en HTML y en JSON-LD)
# ─────────────────────────────────────────────────────────────────────────────
FAQ = [
    ("¿Cuánto vale mi casa?",
     f"Introduce la referencia catastral de tu vivienda en {BRAND} y en segundos verás su valor de "
     "mercado estimado (con un rango mínimo y máximo), el precio por metro cuadrado y la comparación "
     "con la media de tu zona. No te pedimos metros, habitaciones ni email."),
    ("¿Se puede tasar un piso solo con la referencia catastral?",
     "Sí. La referencia catastral identifica de forma única cada inmueble en España. A partir de ella "
     "obtenemos del Catastro la superficie, el uso, el año de construcción y la ubicación exacta, y los "
     "cruzamos con los inmuebles comparables en venta a su alrededor para estimar su valor."),
    ("¿Dónde encuentro la referencia catastral de mi vivienda?",
     "Está en el recibo del IBI, en la escritura de compraventa y en la nota simple del Registro. "
     "También puedes buscarla gratis por dirección en la Sede Electrónica del Catastro. Son 20 "
     "caracteres, por ejemplo 9872023VH5797S0001WX."),
    ("¿Qué diferencia hay entre valor de mercado, valor de referencia y valor catastral?",
     "El valor de mercado es el precio al que razonablemente se vendería el inmueble hoy. El valor de "
     "referencia lo fija el Catastro cada año y es la base mínima para el ITP y el Impuesto de "
     "Sucesiones y Donaciones desde 2022. El valor catastral es un valor administrativo, normalmente "
     "muy inferior, que se usa para el IBI y el IRPF."),
    ("¿Es una tasación oficial válida para una hipoteca?",
     "No. Es una valoración automática orientativa. Para una hipoteca necesitas una tasación "
     "homologada (Orden ECO/805/2003) realizada por una sociedad de tasación inscrita en el Banco de "
     "España."),
    ("¿Sirve para garajes y trasteros?",
     f"Sí. Además de pisos y casas, {BRAND} valora plazas de garaje y trasteros con referencia "
     "catastral propia. Si no hay suficientes inmuebles comparables cerca para dar una cifra fiable, "
     "te lo decimos en lugar de inventarla."),
    ("¿Puedo valorar un inmueble de una subasta del BOE?",
     "Sí. Copia la referencia catastral que aparece en el edicto de la subasta y obtendrás el valor de "
     "mercado estimado para calcular cuánto descuento ofrece la puja."),
    ("¿Vendéis mis datos a inmobiliarias?",
     "No. Puedes valorar sin dejar ningún dato personal y no cedemos datos a agencias ni a terceros. "
     "Ni siquiera guardamos la referencia catastral que consultas."),
    ("¿Funciona en el País Vasco y Navarra?",
     "Estos territorios tienen catastros forales propios con otro formato de referencia. De momento "
     "valoramos inmuebles del Catastro estatal (resto de España)."),
]

HOWTO = [
    ("Busca tu referencia catastral",
     "Mira el recibo del IBI, la escritura o la nota simple. Son 20 caracteres alfanuméricos."),
    ("Pégala en el valorador",
     "Da igual si la escribes con espacios o guiones: la normalizamos y comprobamos que es válida."),
    ("Recibe el valor al instante",
     "Valor de mercado con rango, €/m², comparación con tu zona y precio de cierre estimado."),
]


# ─────────────────────────────────────────────────────────────────────────────
# JSON-LD
# ─────────────────────────────────────────────────────────────────────────────
def _org() -> dict:
    org = {"@type": "Organization", "@id": f"{SITE_URL}/#org", "name": BRAND, "url": SITE_URL,
           "legalName": contenido.RAZON_TXT, "email": CONTACT_EMAIL, "logo": f"{SITE_URL}/logo.svg"}
    if SAME_AS:
        org["sameAs"] = SAME_AS
    return org


def _ld(graph: list) -> str:
    return json.dumps({"@context": "https://schema.org", "@graph": graph},
                      ensure_ascii=False).replace("</", "<\\/")


def json_ld_home() -> str:
    return _ld([
        _org(),
        {"@type": "WebSite", "@id": f"{SITE_URL}/#web", "url": SITE_URL, "name": BRAND,
         "inLanguage": "es-ES", "publisher": {"@id": f"{SITE_URL}/#org"}},
        {"@type": "WebApplication", "@id": f"{SITE_URL}/#app",
         "name": f"{BRAND} — Valorador de inmuebles por referencia catastral",
         "url": SITE_URL, "applicationCategory": "FinanceApplication", "operatingSystem": "Web",
         "inLanguage": "es-ES", "isAccessibleForFree": True,
         "description": ("Calcula el valor de mercado de una vivienda, casa, garaje o trastero en España "
                         "con solo su referencia catastral."),
         "offers": {"@type": "Offer", "price": "0", "priceCurrency": "EUR"},
         "areaServed": {"@type": "Country", "name": "España"},
         "provider": {"@id": f"{SITE_URL}/#org"}},
        {"@type": "HowTo", "name": "Cómo saber cuánto vale tu casa con la referencia catastral",
         "totalTime": "PT1M",
         "step": [{"@type": "HowToStep", "position": i + 1, "name": n, "text": t}
                  for i, (n, t) in enumerate(HOWTO)]},
        {"@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q,
             "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Inicio", "item": SITE_URL + "/"}]},
    ])


# ─────────────────────────────────────────────────────────────────────────────
# HTML
# ─────────────────────────────────────────────────────────────────────────────
CSS = (RAIZ / "app" / "estilo.css").read_text(encoding="utf-8")

HEAD = r"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<meta name="description" content="__DESC__">
<link rel="canonical" href="__CANON__">
<link rel="alternate" hreflang="es-ES" href="__CANON__">
<link rel="alternate" hreflang="x-default" href="__CANON__">
<meta name="robots" content="__ROBOTS__">
<meta name="theme-color" content="#0f3d3e">
<meta property="og:type" content="website">
<meta property="og:locale" content="es_ES">
<meta property="og:site_name" content="__BRAND__">
<meta property="og:title" content="__OGTITLE__">
<meta property="og:description" content="__OGDESC__">
<meta property="og:url" content="__CANON__">
<meta property="og:image" content="__SITE__/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/icono-192.png">
<link rel="manifest" href="/manifest.webmanifest">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<script type="application/ld+json">__JSONLD__</script>
__GA4__
<style>__CSS__</style>
</head>
<body>
<div class="wrap">
  <header class="top">
    <a class="logo" href="/" aria-label="__BRAND__ inicio"><b>i</b>__BRAND__</a>
    <nav aria-label="principal">
      <a href="/precio-vivienda/">Precios por zona</a>
      <a href="/referencia-catastral/">Referencia catastral</a>
      <a href="/valor-de-referencia/">Valor de referencia</a>
      <a href="/#faq">Preguntas</a>
    </nav>
  </header>
</div>
"""

FOOT = r"""
<footer>
  <div class="wrap cols">
    <div><strong>__BRAND__</strong> · __LEGAL__<br>
      Valoraciones automáticas orientativas. No constituyen una tasación oficial (Orden ECO/805/2003).<br>
      Datos catastrales: Dirección General del Catastro.</div>
    <div><a href="/metodologia/">Metodología</a> · <a href="/precio-vivienda/">Precio de la vivienda por zona</a> · <a href="/calculadoras/">Calculadoras</a> · <a href="/tasacion-referencia-catastral/">Tasación por referencia catastral</a> · <a href="/privacidad/">Privacidad</a> · <a href="/aviso-legal/">Aviso legal</a> · <a href="mailto:__EMAIL__">__EMAIL__</a></div>
  </div>
</footer>
<script>if('serviceWorker' in navigator)addEventListener('load',()=>navigator.serviceWorker.register('/sw.js').catch(()=>{}));</script>
</body>
</html>"""


def _ga4() -> str:
    if not GA4_ID:
        return ""
    return (f'<script async src="https://www.googletagmanager.com/gtag/js?id={escape(GA4_ID)}"></script>'
            f"<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}"
            f"gtag('js',new Date());gtag('config','{escape(GA4_ID)}',{{anonymize_ip:true}});</script>")


def pagina(path: str, title: str, desc: str, cuerpo: str, jsonld: str,
           og_title: str | None = None, og_desc: str | None = None, noindex: bool = False) -> str:
    return ((HEAD + cuerpo + FOOT)
            .replace("__ROBOTS__", "noindex,follow" if noindex else "index,follow,max-snippet:-1,max-image-preview:large")
            .replace("__JSONLD__", jsonld)
            .replace("__CSS__", CSS)
            .replace("__GA4__", _ga4())
            .replace("__TITLE__", escape(title))
            .replace("__DESC__", escape(desc))
            .replace("__OGTITLE__", escape(og_title or title))
            .replace("__OGDESC__", escape(og_desc or desc))
            .replace("__CANON__", escape(SITE_URL + path))
            .replace("__BRAND__", escape(BRAND))
            .replace("__SITE__", escape(SITE_URL))
            .replace("__LEGAL__", contenido.RAZON)
            .replace("__EMAIL__", escape(CONTACT_EMAIL)))


HOME = (RAIZ / "app" / "home.html").read_text(encoding="utf-8")


def render_home() -> str:
    howto = "".join(
        f'<div class="card"><div class="step-n">{i + 1}</div><h3>{escape(n)}</h3><p>{escape(t)}</p></div>'
        for i, (n, t) in enumerate(HOWTO))
    faq = "".join(
        f"<details{' open' if i == 0 else ''}><summary>{escape(q)}</summary><p>{escape(a)}</p></details>"
        for i, (q, a) in enumerate(FAQ))
    cuerpo = (HOME.replace("__HOWTO__", howto).replace("__FAQ__", faq)
              .replace("__SEDE__", SEDE_BUSQUEDA)
              .replace("__BUSCADOR__", buscador("home"))
              .replace("__EMAIL_ACTIVO__", "true" if EMAIL_ACTIVO else "false")
              .replace("__BRAND__", escape(BRAND)))
    return pagina(
        "/", "¿Cuánto vale tu casa? Valoración gratis con ref. catastral",
        ("Valora gratis tu piso, casa, garaje o trastero con solo la referencia catastral. Valor de "
         "mercado con rango, €/m² y comparación con tu zona en segundos. Sin email."),
        cuerpo, json_ld_home(),
        og_title="¿Cuánto vale tu casa? Descúbrelo con la referencia catastral",
        og_desc="20 caracteres, un precio. Valoración gratuita de inmuebles en España.")


MESES = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre",
         "octubre", "noviembre", "diciembre")


def _fecha_es(iso: str) -> str:
    d = date.fromisoformat(iso)
    return f"{d.day} de {MESES[d.month - 1]} de {d.year}"


def render_secundaria(slug: str) -> str:
    p = contenido.PAGINAS[slug]
    path = f"/{slug}/"
    graph = [_org(), {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Inicio", "item": SITE_URL + "/"},
        {"@type": "ListItem", "position": 2, "name": p["miga"], "item": SITE_URL + path}]}]
    if p.get("actualizado"):
        graph.append({"@type": "Article", "headline": p["h1"], "description": p["desc"],
                      "inLanguage": "es-ES", "dateModified": p["actualizado"],
                      "mainEntityOfPage": SITE_URL + path, "image": f"{SITE_URL}/og.png",
                      "author": {"@id": f"{SITE_URL}/#org"}, "publisher": {"@id": f"{SITE_URL}/#org"}})
    if p.get("faq"):
        graph.append({"@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in p["faq"]]})
    if p.get("howto"):
        graph.append({"@type": "HowTo", "name": p["howto"][0], "step": [
            {"@type": "HowToStep", "position": i + 1, "name": n, "text": t}
            for i, (n, t) in enumerate(p["howto"][1])]})
    faq = ""
    if p.get("faq"):
        faq = '<h2>Preguntas frecuentes</h2>' + "".join(
            f"<details><summary>{escape(q)}</summary><p>{escape(a)}</p></details>" for q, a in p["faq"])
    cta = "" if p.get("sin_cta") else (
        '<div class="cta-box"><div><strong>¿Cuánto vale tu inmueble?</strong><br>'
        'Pega su referencia catastral y míralo en segundos, gratis y sin email.</div>'
        '<a class="btn" href="/#valorar">Valorar gratis</a></div>')
    cuerpo = (f'<main class="wrap doc"><p class="crumbs"><a href="/">Inicio</a> › {escape(p["miga"])}</p>'
              f'<h1>{escape(p["h1"])}</h1>'
              + (f'<p class="fecha">Actualizado el {_fecha_es(p["actualizado"])}</p>' if p.get("actualizado") else "")
              + (f'<p class="answer"><strong>Respuesta rápida:</strong> {p["respuesta"]}</p>' if p.get("respuesta") else "")
              + p["html"].replace("__BUSCADOR__", buscador("enlace")) + cta + faq + "</main>")
    return pagina(path, p["title"], p["desc"], cuerpo, _ld(graph))


def buscador(modo: str, prov: str = "", mun: str = "") -> str:
    provs = json.dumps(PROVINCIAS, ensure_ascii=False).replace("</", "<\\/")
    return (f'<script type="application/json" id="provincias-json">{provs}</script>'
            f'<div class="buscador" data-modo="{modo}" data-prov="{prov}" data-mun="{mun}"></div>'
            '<script src="/buscador.js?v=2" defer></script>')


SECUNDARIAS = {slug: render_secundaria(slug) for slug in contenido.PAGINAS}
ZONAS = Zonas(RAIZ / "data" / "zonas.json")


def render_calc(slug: str | None) -> str:
    """/calculadoras/ (slug None) o una calculadora."""
    fiscal_js = json.dumps(fiscal.para_js(), ensure_ascii=False).replace("</", "<\\/")
    if slug is None:
        path, nombre = "/calculadoras/", "Calculadoras"
        tarjetas = "".join(
            f'<a class="card calc-card" href="/calculadoras/{k}/"><h3>{escape(c["nombre"])}</h3><p>{escape(c["desc"])}</p></a>'
            for k, c in calculadoras.CALCS.items())
        cuerpo = (f'<main class="wrap doc ancha"><p class="crumbs"><a href="/">Inicio</a> › Calculadoras</p>'
                  f'<h1>Calculadoras de impuestos y rentabilidad inmobiliaria 2026</h1>'
                  f'<p class="fecha">Actualizado el {_fecha_es(fiscal.ACTUALIZADO)}</p>'
                  '<p class="answer"><strong>Respuesta rápida:</strong> calcula el ITP de tu compra, lo que pagarás por heredar o recibir '
                  'en donación un inmueble, la plusvalía municipal de una venta y la rentabilidad de un piso en alquiler, con los tipos '
                  'de 2026 de cada comunidad autónoma.</p>'
                  f'<div class="grid-calcs">{tarjetas}</div></main>')
        graph = [_org(), {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Inicio", "item": SITE_URL + "/"},
            {"@type": "ListItem", "position": 2, "name": nombre, "item": SITE_URL + path}]}]
        return pagina(path, "Calculadoras inmobiliarias 2026: ITP, Sucesiones y plusvalía",
                      "Calculadoras gratuitas de ITP, Sucesiones y Donaciones, plusvalía municipal y rentabilidad de alquiler con los tipos de 2026.",
                      cuerpo, _ld(graph))
    c = calculadoras.CALCS[slug]
    path = f"/calculadoras/{slug}/"
    html_c = c["html"]
    for marca, fn in calculadoras.TABLAS.items():
        if marca in html_c:
            html_c = html_c.replace(marca, fn())
    faq = "".join(f"<details><summary>{escape(q)}</summary><p>{escape(a)}</p></details>" for q, a in c["faq"])
    cuerpo = (f'<main class="wrap doc ancha"><p class="crumbs"><a href="/">Inicio</a> › <a href="/calculadoras/">Calculadoras</a> › '
              f'{escape(c["nombre"])}</p><h1>{escape(c["h1"])}</h1>'
              f'<p class="fecha">Actualizado el {_fecha_es(fiscal.ACTUALIZADO)}</p>'
              f'<p class="answer"><strong>Respuesta rápida:</strong> {escape(c["respuesta"])}</p>'
              f'<div class="caja-calc">{c["form"]}</div>{html_c}'
              '<div class="cta-box"><div><strong>¿Cuánto vale el inmueble?</strong><br>Pega su referencia catastral y míralo en '
              'segundos, gratis y sin email.</div><a class="btn" href="/#valorar">Valorar gratis</a></div>'
              f'<h2>Preguntas frecuentes</h2>{faq}<p class="hint">Cálculo orientativo con la normativa vigente a la fecha indicada. '
              'No sustituye el asesoramiento de un profesional.</p></main>'
              f'<script type="application/json" id="fiscal-json">{fiscal_js}</script><script src="/calc.js?v=1" defer></script>')
    graph = [_org(),
             {"@type": "WebApplication", "name": c["nombre"], "url": SITE_URL + path, "applicationCategory": "FinanceApplication",
              "operatingSystem": "Web", "inLanguage": "es-ES", "isAccessibleForFree": True,
              "offers": {"@type": "Offer", "price": "0", "priceCurrency": "EUR"}, "dateModified": fiscal.ACTUALIZADO,
              "provider": {"@id": f"{SITE_URL}/#org"}},
             {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
                                                 for q, a in c["faq"]]},
             {"@type": "BreadcrumbList", "itemListElement": [
                 {"@type": "ListItem", "position": 1, "name": "Inicio", "item": SITE_URL + "/"},
                 {"@type": "ListItem", "position": 2, "name": "Calculadoras", "item": SITE_URL + "/calculadoras/"},
                 {"@type": "ListItem", "position": 3, "name": c["nombre"], "item": SITE_URL + path}]}]
    return pagina(path, c["title"][:60], c["desc"][:158], cuerpo, _ld(graph))


CALC_CACHE = {None: render_calc(None), **{k: render_calc(k) for k in calculadoras.CALCS}}
_BUSCADOR_ZONA = re.compile(r"__BUSCADOR__([^|]*)\|(.*?)__")


def render_zona(path: str, tipo: str, code: str | None) -> str:
    z = ZONAS.pagina(tipo, code, SITE_URL)
    cuerpo = _BUSCADOR_ZONA.sub(lambda m: buscador("enlace", m.group(1), m.group(2)), z["cuerpo"])
    return pagina(path, z["title"], z["desc"], cuerpo, _ld([_org()] + z["graph"]), noindex=z["noindex"])
_HOME_CACHE = render_home()

# ─────────────────────────────────────────────────────────────────────────────
# APP
# ─────────────────────────────────────────────────────────────────────────────
app = FastAPI(title=BRAND, docs_url=None, redoc_url=None, openapi_url=None)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    resp = await call_next(request)
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    resp.headers["X-Frame-Options"] = "SAMEORIGIN"
    resp.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
    return resp


@app.get("/", response_class=HTMLResponse)
def home():
    return HTMLResponse(_HOME_CACHE, headers={"Cache-Control": "public, max-age=300"})


@app.get("/health")
def health():
    return {"ok": True, "avm": bool(AVM_TOKEN), "email": EMAIL_ACTIVO}


_MENSAJES = {
    "rc_no_encontrada": "El Catastro no reconoce esa referencia. Revísala o búscala por dirección en la Sede del Catastro.",
    "coords_no_encontradas": "El Catastro localiza el inmueble, pero no su ubicación exacta, y sin ella no podemos buscar comparables.",
    "sin_superficie": "El Catastro no publica la superficie de este inmueble, y sin ella no podemos valorarlo.",
    "sin_comparables": ("No hay suficientes inmuebles comparables en venta cerca de este para dar una cifra fiable. "
                        "Preferimos no inventarla."),
}


@app.post("/api/valorar")
async def api_valorar(request: Request):
    if _limitado(_ip(request)):
        return JSONResponse({"error": "Has hecho muchas valoraciones seguidas. Prueba en un rato."}, 429)
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Petición no válida."}, 400)
    rc = normalizar_rc(str(body.get("rc", "")))
    ok, msg = validar_rc(rc)
    if not ok:
        return JSONResponse({"error": msg}, 422)
    try:
        data = valorar_inmueble(rc)
    except AvmError as e:
        code = str(e.data.get("error") or e.status)
        _log_valoracion(rc, e.data, False, code)
        if code in _MENSAJES:
            ficha = {k: v for k, v in para_publico(e.data).items() if v is not None}
            return JSONResponse({"error": _MENSAJES[code], "codigo": code, "ficha": ficha},
                                404 if code == "rc_no_encontrada" else 422)
        if e.status == 429:
            return JSONResponse({"error": "Mucha gente valorando a la vez. Prueba en un minuto."}, 503)
        return JSONResponse({"error": "El servicio de valoración no está disponible ahora mismo."}, 503)
    if data.get("tipo_amplio") in FUERA_DE_ALCANCE:
        _log_valoracion(rc, data, False, "fuera_de_alcance")
        ficha = {k: v for k, v in para_publico(data).items()
                 if k in ("direccion", "uso", "superficie_m2", "anio_construccion") and v is not None}
        return JSONResponse({"error": ("De momento la herramienta pública valora viviendas, garajes y trasteros. "
                                       f"Para locales y naves, escríbenos a {CONTACT_EMAIL} y lo estudiamos."),
                             "codigo": "fuera_de_alcance", "ficha": ficha}, 422)
    _log_valoracion(rc, data, True)
    return JSONResponse(para_publico(data), headers={"Cache-Control": "no-store"})


_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$")


def _enviar_informe(email: str, rc: str, d: dict) -> bool:
    eur = lambda n: f"{n:,.0f} €".replace(",", ".") if n else "—"
    filas = [("Valor de mercado estimado", eur(d.get("valor_central"))),
             ("Rango", f"{eur(d.get('valor_min'))} – {eur(d.get('valor_max'))}"),
             ("Precio de cierre estimado", eur(d.get("cierre_estimado"))),
             ("Precio por m²", eur(d.get("eur_m2")) + "/m²" if d.get("eur_m2") else "—"),
             ("Media de la zona", eur(d.get("eur_m2_zona")) + "/m²" if d.get("eur_m2_zona") else "—"),
             ("Superficie", f"{d['superficie_m2']} m²" if d.get("superficie_m2") else "—"),
             ("Uso", d.get("uso") or "—"), ("Año", str(d.get("anio_construccion") or "—"))]
    tabla = "".join(f"<tr><td style='padding:6px 12px;color:#5a6b69'>{escape(k)}</td>"
                    f"<td style='padding:6px 12px'><b>{escape(v)}</b></td></tr>" for k, v in filas)
    html = (f"<div style='font-family:Arial,sans-serif;max-width:560px'><h2 style='color:#0f3d3e'>Tu valoración en {BRAND}</h2>"
            f"<p>{escape(d.get('direccion') or '')}<br><small>Ref. catastral {escape(rc)}</small></p>"
            f"<table style='border-collapse:collapse'>{tabla}</table>"
            f"<p style='font-size:12px;color:#5a6b69'>Valoración automática orientativa a {date.today():%d/%m/%Y}. "
            f"No es una tasación oficial (Orden ECO/805/2003). <a href='{SITE_URL}/metodologia/'>Cómo calculamos</a>.</p></div>")
    req = urllib.request.Request(
        "https://api.resend.com/emails", method="POST",
        data=json.dumps({"from": RESEND_FROM, "to": [email], "subject": f"Tu valoración en {BRAND}",
                         "html": html}).encode(),
        headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20):
            return True
    except Exception:
        return False


@app.post("/api/lead")
async def api_lead(request: Request):
    if not EMAIL_ACTIVO:
        return JSONResponse({"error": "El envío por email aún no está disponible."}, 404)
    if _limitado("lead:" + _ip(request), 5):
        return JSONResponse({"error": "Demasiadas peticiones."}, 429)
    try:
        b = await request.json()
    except Exception:
        return JSONResponse({"error": "Petición no válida."}, 400)
    email = str(b.get("email", "")).strip()[:200]
    if not _EMAIL_RE.match(email):
        return JSONResponse({"error": "Revisa el email."}, 422)
    if not b.get("ok"):
        return JSONResponse({"error": "Necesitamos tu consentimiento para enviarte el informe."}, 422)
    rc = normalizar_rc(str(b.get("rc", "")))[:20]
    if not validar_rc(rc)[0]:
        return JSONResponse({"error": "Valora primero un inmueble."}, 422)
    try:
        data = valorar_inmueble(rc)
    except AvmError:
        return JSONResponse({"error": "No hemos podido preparar el informe ahora mismo."}, 503)
    enviado = _enviar_informe(email, rc, para_publico(data))
    with _db_lock:
        _CON.execute("INSERT INTO leads(ts,email,rc,perfil,motivo,consentimiento,enviado) VALUES(?,?,?,?,?,1,?)", (
            datetime.now(timezone.utc).isoformat(), email, rc,
            str(b.get("perfil", ""))[:30], str(b.get("motivo", ""))[:30], int(enviado)))
        _CON.commit()
    if not enviado:
        return JSONResponse({"error": "No hemos podido enviar el email. Inténtalo más tarde."}, 502)
    return {"ok": True}


# ── Buscador de RC por dirección ────────────────────────────────────────────
def _callejero(fn):
    try:
        return JSONResponse(fn(), headers={"Cache-Control": "public, max-age=3600"})
    except CallejeroError:
        return JSONResponse({"error": "No hemos podido consultar el Catastro. Inténtalo en un momento."}, 503)


@app.get("/api/catastro/municipios")
def api_municipios(request: Request, prov: str = "", q: str = ""):
    if _limitado("cj:" + _ip(request), 300):
        return JSONResponse({"error": "Demasiadas búsquedas seguidas. Prueba en un rato."}, 429)
    if prov not in NOMBRES_PROV or len(norm(q)) < 2:
        return JSONResponse({"error": "Elige provincia y escribe al menos 2 letras."}, 422)
    return _callejero(lambda: {"municipios": CALLEJERO.municipios(prov, q)})


@app.get("/api/catastro/calles")
def api_calles(request: Request, prov: str = "", mun: str = "", q: str = ""):
    if _limitado("cj:" + _ip(request), 300):
        return JSONResponse({"error": "Demasiadas búsquedas seguidas. Prueba en un rato."}, 429)
    if prov not in NOMBRES_PROV or not mun or len(norm(q)) < 3:
        return JSONResponse({"error": "Escribe al menos 3 letras de la calle."}, 422)
    return _callejero(lambda: {"calles": CALLEJERO.calles(prov, norm(mun), q)})


@app.get("/api/catastro/inmuebles")
def api_inmuebles(request: Request, prov: str = "", mun: str = "", tv: str = "", calle: str = "", num: str = ""):
    if _limitado("cj:" + _ip(request), 300):
        return JSONResponse({"error": "Demasiadas búsquedas seguidas. Prueba en un rato."}, 429)
    if prov not in NOMBRES_PROV or not mun or not calle or not re.fullmatch(r"\d{1,5}", num.strip()) \
            or not re.fullmatch(r"[A-Z]{1,3}", tv.strip()):
        return JSONResponse({"error": "Completa municipio, calle y número."}, 422)
    return _callejero(lambda: CALLEJERO.inmuebles(prov, norm(mun), tv.strip(), norm(calle), num.strip()))


# ── Precio de la vivienda por zona ──────────────────────────────────────────
@app.get("/precio-vivienda/{resto:path}", response_class=HTMLResponse)
def precio_vivienda(resto: str = ""):
    partes = [x for x in resto.split("/") if x]
    r = ZONAS.resolver(partes)
    if not r:
        return no_encontrada()
    path, tipo, code = r
    if partes and not resto.endswith("/"):
        return RedirectResponse(path, 301)
    return HTMLResponse(render_zona(path, tipo, code), headers={"Cache-Control": "public, max-age=3600"})


@app.get("/calculadoras/", response_class=HTMLResponse)
def calcs_indice():
    return HTMLResponse(CALC_CACHE[None], headers={"Cache-Control": "public, max-age=3600"})


@app.get("/calculadoras/{slug}/", response_class=HTMLResponse)
def calc(slug: str):
    if slug not in calculadoras.CALCS:
        return no_encontrada()
    return HTMLResponse(CALC_CACHE[slug], headers={"Cache-Control": "public, max-age=3600"})


@app.get("/calculadoras/{slug}")
def calc_sin_barra(slug: str):
    return RedirectResponse(f"/calculadoras/{slug}/", 301) if slug in calculadoras.CALCS else no_encontrada()


@app.get("/precio-vivienda")
def precio_vivienda_sin_barra():
    return RedirectResponse("/precio-vivienda/", 301)


# ── Páginas secundarias ─────────────────────────────────────────────────────
@app.get("/{slug}/", response_class=HTMLResponse)
def secundaria(slug: str):
    if slug not in SECUNDARIAS:
        return no_encontrada()
    return HTMLResponse(SECUNDARIAS[slug], headers={"Cache-Control": "public, max-age=600"})


@app.get("/privacidad.html")
def privacidad_antigua():
    return RedirectResponse("/privacidad/", 301)


# ── SEO / GEO técnico ────────────────────────────────────────────────────────
ROBOTS = f"""User-agent: *
Allow: /
Disallow: /api/

# Buscadores con IA (GEO): permitidos explícitamente
User-agent: OAI-SearchBot
Allow: /
User-agent: ChatGPT-User
Allow: /
User-agent: GPTBot
Allow: /
User-agent: PerplexityBot
Allow: /
User-agent: Perplexity-User
Allow: /
User-agent: ClaudeBot
Allow: /
User-agent: Claude-SearchBot
Allow: /
User-agent: Claude-User
Allow: /
User-agent: Google-Extended
Allow: /
User-agent: Bingbot
Allow: /
User-agent: Applebot-Extended
Allow: /

Sitemap: {SITE_URL}/sitemap.xml
"""

SITEMAP_PATHS = (["/"] + [f"/{s}/" for s in contenido.PAGINAS if s not in ("privacidad", "aviso-legal")]
                 + ["/calculadoras/"] + [f"/calculadoras/{k}/" for k in calculadoras.CALCS])


@app.get("/robots.txt", response_class=PlainTextResponse)
def robots():
    return ROBOTS


def _urlset(paths: list[str], lastmod: str) -> Response:
    urls = "".join(f"<url><loc>{escape(SITE_URL + p)}</loc><lastmod>{lastmod}</lastmod></url>" for p in paths)
    return Response('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                    f'{urls}</urlset>', media_type="application/xml")


@app.get("/sitemap.xml")
def sitemap():
    ZONAS._cargar()
    mods = {"paginas": LAST_MOD, "zonas": ZONAS.fecha.isoformat()}
    items = "".join(f"<sitemap><loc>{SITE_URL}/sitemap-{k}.xml</loc><lastmod>{v}</lastmod></sitemap>" for k, v in mods.items())
    return Response('<?xml version="1.0" encoding="UTF-8"?><sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                    f'{items}</sitemapindex>', media_type="application/xml")


@app.get("/sitemap-paginas.xml")
def sitemap_paginas():
    return _urlset(SITEMAP_PATHS, LAST_MOD)


@app.get("/sitemap-zonas.xml")
def sitemap_zonas():
    return _urlset(ZONAS.urls_indexables(), ZONAS.fecha.isoformat())


@app.get("/llms.txt", response_class=PlainTextResponse)
def llms():
    faq = "\n".join(f"- {q} {a}" for q, a in FAQ)
    return f"""# {BRAND}

> Valorador gratuito de inmuebles en España con solo la referencia catastral (20 caracteres).
> Valora viviendas, casas, garajes y trasteros. Muestra valor de mercado con rango, €/m²,
> media de la zona y precio de cierre estimado. No es una tasación oficial ECO/805/2003.

## Uso
- Web: {SITE_URL}/?rc=REFERENCIA_CATASTRAL (prellena el valorador)
- Metodología: {SITE_URL}/metodologia/

## Preguntas frecuentes
{faq}
"""


ESTATICOS = {"logo.svg": "image/svg+xml", "favicon.svg": "image/svg+xml", "og.png": "image/png",
             "buscador.js": "application/javascript", "sw.js": "application/javascript", "calc.js": "application/javascript",
             "manifest.webmanifest": "application/manifest+json",
             "icono-192.png": "image/png", "icono-512.png": "image/png"}


@app.get("/{nombre}")
def estatico(nombre: str):
    if nombre in ESTATICOS:
        return FileResponse(RAIZ / "static" / nombre, media_type=ESTATICOS[nombre],
                            headers={"Cache-Control": "public, max-age=86400"})
    if nombre in SECUNDARIAS:
        return RedirectResponse(f"/{nombre}/", 301)
    return no_encontrada()


def no_encontrada():
    return HTMLResponse(
        f'<!doctype html><html lang="es"><meta charset="utf-8"><meta name="robots" content="noindex">'
        f'<meta name="viewport" content="width=device-width,initial-scale=1"><title>Página no encontrada | {escape(BRAND)}</title>'
        f'<body style="font-family:system-ui;max-width:560px;margin:15vh auto;padding:0 20px">'
        f'<h1>Esta página no existe</h1><p><a href="/">Valora tu inmueble con la referencia catastral →</a></p>',
        status_code=404)


@app.get("/{path:path}", response_class=HTMLResponse)
def not_found(path: str):
    return no_encontrada()
