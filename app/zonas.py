"""Páginas programáticas de precio por zona: /precio-vivienda/[provincia/[municipio/]].

Lee data/zonas.json (lo genera app.zonas_datos cada semana) y se recarga solo
cuando cambia el fichero. Reglas del plan SEO: el municipio se indexa solo con
≥ min_index anuncios de vivienda; por debajo, página noindex enlazada desde
la provincia. Cada página lleva datos propios (no texto de relleno).
"""
from __future__ import annotations

import json
from datetime import date, datetime
from html import escape
from pathlib import Path

from .callejero import PROVINCIAS as PROV_CATASTRO

CATASTRO_POR_CODIGO = {c: n for c, n in PROV_CATASTRO}


def eur(n) -> str:
    return "—" if n is None else f"{n:,.0f} €".replace(",", ".")


def num(n) -> str:
    return "—" if n is None else f"{n:,.0f}".replace(",", ".")


def dec(x, nd=1) -> str:
    return f"{x:.{nd}f}".replace(".", ",")


def m2(n) -> str:
    return "—" if n is None else f"{num(n)} €/m²"


def pct(a, b) -> int | None:
    return round(100 * (a / b - 1)) if a and b else None


def cmp_txt(p: int | None, mas: str = "más caro", menos: str = "más barato") -> str:
    if p is None:
        return ""
    if abs(p) < 3:
        return "en línea con"
    return f"un {abs(p)} % {mas if p > 0 else menos} que"


class Zonas:
    def __init__(self, path: Path):
        self.path = path
        self.mtime = None
        self.d: dict = {"provincias": {}, "municipios": {}}

    def _cargar(self):
        try:
            mt = self.path.stat().st_mtime
        except FileNotFoundError:
            return
        if mt != self.mtime:
            self.d = json.loads(self.path.read_text(encoding="utf-8"))
            self.mtime = mt
            self.prov_slug = {p["slug"]: c for c, p in self.d["provincias"].items()}
            self.mun_slug = {(m["prov"], m["slug"]): c for c, m in self.d["municipios"].items()}
            self.cache: dict = {}

    @property
    def fecha(self) -> date:
        return datetime.fromisoformat(self.d.get("generado", "2026-10-24T00:00:00+00:00")).date()

    def url_prov(self, code: str) -> str:
        return f"/precio-vivienda/{self.d['provincias'][code]['slug']}/"

    def url_mun(self, code: str) -> str:
        m = self.d["municipios"][code]
        return f"/precio-vivienda/{self.d['provincias'][m['prov']]['slug']}/{m['slug']}/"

    # ── rutas ───────────────────────────────────────────────────────────────
    def resolver(self, partes: list[str]):
        """Devuelve (path, tipo, código) o None."""
        self._cargar()
        if not partes:
            return ("/precio-vivienda/", "indice", None)
        pc = self.prov_slug.get(partes[0])
        if not pc:
            return None
        if len(partes) == 1:
            return (self.url_prov(pc), "prov", pc)
        mc = self.mun_slug.get((pc, partes[1]))
        if not mc or len(partes) > 2:
            return None
        return (self.url_mun(mc), "mun", mc)

    def urls_indexables(self) -> list[str]:
        self._cargar()
        out = ["/precio-vivienda/"] + [self.url_prov(c) for c in self.d["provincias"]]
        out += [self.url_mun(c) for c, m in self.d["municipios"].items() if m["indexable"]]
        return out

    # ── bloques comunes ─────────────────────────────────────────────────────
    def _fecha_txt(self) -> str:
        meses = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre",
                 "octubre", "noviembre", "diciembre")
        f = self.fecha
        return f"{f.day} de {meses[f.month - 1]} de {f.year}"

    @staticmethod
    def _kpis(items: list[tuple[str, str, str]]) -> str:
        return '<div class="kpis">' + "".join(
            f'<div class="kpi"><small>{escape(t)}</small><strong>{v}</strong>'
            + (f'<span>{s}</span>' if s else "") + "</div>" for t, v, s in items if v and v != "—") + "</div>"

    @staticmethod
    def _tabla_tipos(d: dict) -> str:
        filas = [("Viviendas (todas)", m2(d["med"]), num(d["n"]))]
        if d.get("piso"):
            filas.append(("Pisos", m2(d["piso"]["med"]), num(d["piso"]["n"])))
        if d.get("casa"):
            filas.append(("Casas y chalés", m2(d["casa"]["med"]), num(d["casa"]["n"])))
        o = d.get("otros") or {}
        if o.get("garaje"):
            filas.append(("Plazas de garaje", eur(o["garaje"]["precio_med"]) + " por plaza", num(o["garaje"]["n"])))
        if o.get("trastero"):
            filas.append(("Trasteros", eur(o["trastero"]["precio_med"]) + " por trastero", num(o["trastero"]["n"])))
        if o.get("local"):
            filas.append(("Locales comerciales", m2(o["local"]["eur_m2"]), num(o["local"]["n"])))
        if o.get("nave"):
            filas.append(("Naves industriales", m2(o["nave"]["eur_m2"]), num(o["nave"]["n"])))
        if o.get("terreno"):
            filas.append(("Suelo y parcelas", m2(o["terreno"]["eur_m2"]), num(o["terreno"]["n"])))
        return ('<div class="scroll"><table><thead><tr><th>Tipo de inmueble</th><th>Precio mediano en venta</th>'
                '<th>Anuncios analizados</th></tr></thead><tbody>'
                + "".join(f"<tr><td>{escape(a)}</td><td><strong>{b}</strong></td><td>{c}</td></tr>" for a, b, c in filas)
                + "</tbody></table></div>")

    @staticmethod
    def _valorador(prov_code: str, nombre_mun: str | None) -> str:
        prov_cat = CATASTRO_POR_CODIGO.get(prov_code, "")
        lugar = f" en {escape(nombre_mun)}" if nombre_mun else ""
        return (f'<h2>¿Cuánto vale tu inmueble{lugar}?</h2>'
                '<p>Pega su referencia catastral o búscala por dirección y verás su valor de mercado, gratis con tu cuenta.</p>'
                '<form class="mini-rc" action="/" method="get"><input name="rc" maxlength="30" autocomplete="off" '
                'placeholder="Referencia catastral" aria-label="Referencia catastral">'
                '<button class="btn" type="submit">Valorar gratis</button></form>'
                f'<details class="b-det"><summary>¿No la tienes? Búscala por dirección</summary>'
                f'__BUSCADOR__{escape(prov_cat)}|{escape(nombre_mun or "")}__</details>'
                f'<h2>¿Vas a comprar{lugar}? Comprueba si está bien de precio</h2>'
                '<p>Pega la referencia catastral del piso que te interesa y el precio que te piden: te decimos si es un gran '
                'precio, un precio justo, caro o sospechosamente barato. Gratis y sin registro.</p>'
                '<form class="mini-rc mini-comprar" action="/comprobar-precio/" method="get">'
                '<input name="rc" maxlength="30" autocomplete="off" placeholder="Referencia catastral" aria-label="Referencia catastral">'
                '<input name="precio" type="number" inputmode="numeric" min="3000" step="500" placeholder="Precio que te piden (€)" '
                'aria-label="Precio que te piden en euros" class="precio">'
                '<button class="btn" type="submit">Comprobar precio</button></form>'
                '<p class="hint">¿No tienes la referencia? Búscala con la dirección del anuncio en '
                '<a href="/comprobar-precio/">la herramienta</a>.</p>')

    def _ld(self, path: str, migas: list[tuple[str, str]], nombre_lugar: str, desc: str,
            geo: tuple | None, faq: list[tuple[str, str]], site: str) -> list:
        lugar = {"@type": "AdministrativeArea", "name": nombre_lugar, "containedInPlace": {"@type": "Country", "name": "España"}}
        if geo and geo[0] and geo[1]:
            lugar["geo"] = {"@type": "GeoCoordinates", "latitude": geo[0], "longitude": geo[1]}
        g = [
            {"@type": "WebPage", "@id": site + path, "url": site + path, "name": migas[-1][0], "inLanguage": "es-ES",
             "dateModified": self.fecha.isoformat(), "about": lugar, "isPartOf": {"@id": f"{site}/#web"}},
            {"@type": "Dataset", "name": f"Precio de la vivienda en {nombre_lugar}", "description": desc,
             "url": site + path, "dateModified": self.fecha.isoformat(), "spatialCoverage": lugar,
             "temporalCoverage": f"{date(self.fecha.year - 1, self.fecha.month, 1).isoformat()}/{self.fecha.isoformat()}",
             "variableMeasured": "Precio mediano por metro cuadrado de la vivienda en venta (€/m²)",
             "creator": {"@id": f"{site}/#org"}, "isAccessibleForFree": True},
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": i + 1, "name": n, "item": site + u} for i, (n, u) in enumerate(migas)]},
        ]
        if faq:
            g.append({"@type": "FAQPage", "mainEntity": [
                {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]})
        return g

    @staticmethod
    def _faq_html(faq) -> str:
        return ('<h2>Preguntas frecuentes</h2>' + "".join(
            f"<details><summary>{escape(q)}</summary><p>{escape(a)}</p></details>" for q, a in faq)) if faq else ""

    @staticmethod
    def _migas_html(migas) -> str:
        return '<p class="crumbs">' + " › ".join(
            f'<a href="{u}">{escape(n)}</a>' for n, u in migas[:-1]) + f" › {escape(migas[-1][0])}</p>"

    def _nota_metodo(self) -> str:
        return (f'<p class="hint">Fuente: análisis de Idealisto sobre anuncios de venta de portales inmobiliarios de los últimos 12 meses, '
                f'sin duplicados entre portales y sin valores atípicos; mediana del precio por m² construido. Son precios de oferta: '
                f'el precio de cierre suele ser algo menor. Valor tasado: Ministerio de Vivienda (estadística de valor tasado). '
                f'Alquiler: Sistema Estatal de Referencia del Precio del Alquiler (SERPAVI). Actualizado el {self._fecha_txt()}. '
                f'<a href="/metodologia/">Metodología</a>.</p>')

    # ── páginas ─────────────────────────────────────────────────────────────
    def pagina(self, tipo: str, code: str | None, site: str) -> dict:
        self._cargar()
        k = (tipo, code)
        if k not in self.cache:
            self.cache[k] = getattr(self, f"_p_{tipo}")(code, site)
        return self.cache[k]

    def _p_indice(self, _code, site) -> dict:
        P = self.d["provincias"]
        filas = "".join(
            f'<tr><td><a href="{self.url_prov(c)}">{escape(p["nombre"])}</a></td><td><strong>{m2(p["med"])}</strong></td>'
            f'<td>{m2((p.get("piso") or {}).get("med"))}</td><td>{m2((p.get("casa") or {}).get("med"))}</td><td>{num(p["n"])}</td></tr>'
            for c, p in sorted(P.items(), key=lambda x: x[1]["nombre"]))
        caras = sorted(P.values(), key=lambda p: -p["med"])
        resp = (f'La provincia más cara para comprar vivienda es {escape(caras[0]["nombre"])} ({m2(caras[0]["med"])}) y la más '
                f'barata, {escape(caras[-1]["nombre"])} ({m2(caras[-1]["med"])}), según la mediana de los anuncios de venta '
                f'que analiza Idealisto. Elige tu provincia para ver el precio de cada municipio.')
        migas = [("Inicio", "/"), ("Precio de la vivienda por zona", "/precio-vivienda/")]
        cuerpo = (f'<main class="wrap doc ancha">{self._migas_html(migas)}<h1>Precio de la vivienda en España por provincia y municipio</h1>'
                  f'<p class="fecha">Actualizado el {self._fecha_txt()}</p>'
                  f'<p class="answer"><strong>Respuesta rápida:</strong> {resp}</p>'
                  '<div class="scroll"><table><thead><tr><th>Provincia</th><th>Vivienda</th><th>Pisos</th><th>Casas</th>'
                  f'<th>Anuncios</th></tr></thead><tbody>{filas}</tbody></table></div>'
                  f'{self._nota_metodo()}{self._valorador("", None)}</main>')
        desc = "Precio medio de la vivienda en venta por provincia y municipio en España: €/m² de pisos, casas, garajes y locales, con datos propios actualizados cada semana."
        return {"title": "Precio de la vivienda por provincia y municipio (2026)", "desc": desc, "cuerpo": cuerpo,
                "graph": self._ld("/precio-vivienda/", migas, "España", desc, None, [], site), "noindex": False}

    def _p_prov(self, code, site) -> dict:
        p = self.d["provincias"][code]
        M = self.d["municipios"]
        nombre = p["nombre"]
        muns = p["municipios"]
        filas = "".join(
            f'<tr><td><a href="{self.url_mun(c)}">{escape(M[c]["nombre"])}</a></td><td><strong>{m2(M[c]["med"])}</strong></td>'
            f'<td>{m2((M[c].get("piso") or {}).get("med"))}</td><td>{m2((M[c].get("casa") or {}).get("med"))}</td>'
            f'<td>{num(M[c]["n"])}</td></tr>' for c in muns)
        con_datos = [M[c] for c in muns if M[c]["n"] >= 50]
        extremos = ""
        if len(con_datos) >= 3:
            caro = max(con_datos, key=lambda m: m["med"])
            barato = min(con_datos, key=lambda m: m["med"])
            extremos = (f' El municipio más caro con datos suficientes es {escape(caro["nombre"])} ({m2(caro["med"])}) y el más '
                        f'barato, {escape(barato["nombre"])} ({m2(barato["med"])}).')
        resp = (f'En la provincia de {escape(nombre)}, el precio mediano de la vivienda en venta es de {m2(p["med"])}, según '
                f'{num(p["n"])} anuncios analizados por Idealisto en los últimos 12 meses.{extremos}')
        cien = p.get("cien") or {}
        kpis = self._kpis([
            ("Vivienda en venta", m2(p["med"]), f'rango central {num(p["p25"])}–{num(p["p75"])} €/m²'),
            ("Pisos", m2((p.get("piso") or {}).get("med")), ""),
            ("Casas y chalés", m2((p.get("casa") or {}).get("med")), ""),
            ("Compraventas en 12 meses", num(cien.get("compraventas_12m")),
             (f'{"+" if (cien.get("var_compraventas") or 0) > 0 else ""}{cien["var_compraventas"]} % interanual · datos notariales'
              if cien.get("var_compraventas") is not None else "datos notariales")),
            ("Importe medio escriturado", eur(cien.get("importe_medio")), "último trimestre publicado"),
        ])
        migas = [("Inicio", "/"), ("Precio de la vivienda", "/precio-vivienda/"), (f"Provincia de {nombre}", self.url_prov(code))]
        faq = [(f"¿Cuánto cuesta el metro cuadrado en la provincia de {nombre}?",
                f"La mediana de los anuncios de vivienda en venta en la provincia de {nombre} es de {m2(p['med'])}. "
                f"La mitad de las viviendas se anuncian entre {num(p['p25'])} y {num(p['p75'])} €/m².")]
        if cien.get("compraventas_12m"):
            faq.append((f"¿Cuántas viviendas se venden en la provincia de {nombre}?",
                        f"Según los datos notariales publicados por el Ministerio de Vivienda, en los últimos cuatro trimestres "
                        f"disponibles se firmaron {num(cien['compraventas_12m'])} compraventas de vivienda libre en la provincia."))
        cuerpo = (f'<main class="wrap doc ancha">{self._migas_html(migas)}<h1>Precio de la vivienda en la provincia de {escape(nombre)}</h1>'
                  f'<p class="fecha">Actualizado el {self._fecha_txt()}</p>'
                  f'<p class="answer"><strong>Respuesta rápida:</strong> {resp}</p>{kpis}'
                  f'<h2>Precio por tipo de inmueble en la provincia de {escape(nombre)}</h2>{self._tabla_tipos(p)}'
                  f'<h2>Precio de la vivienda por municipio</h2>'
                  f'<div class="scroll"><table><thead><tr><th>Municipio</th><th>Vivienda</th><th>Pisos</th><th>Casas</th><th>Anuncios</th>'
                  f'</tr></thead><tbody>{filas}</tbody></table></div>'
                  f'{self._nota_metodo()}{self._valorador(code, None)}{self._faq_html(faq)}</main>')
        desc = (f"Precio de la vivienda en la provincia de {nombre}: {m2(p['med'])} de mediana, pisos, casas, garajes y "
                f"locales, y el precio de cada municipio. Datos propios actualizados cada semana.")[:158]
        return {"title": f"Precio vivienda provincia de {nombre} 2026: €/m²"[:60], "desc": desc, "cuerpo": cuerpo,
                "graph": self._ld(self.url_prov(code), migas, f"provincia de {nombre}", desc, None, faq, site),
                "noindex": False}

    def _p_mun(self, code, site) -> dict:
        m = self.d["municipios"][code]
        p = self.d["provincias"][m["prov"]]
        M = self.d["municipios"]
        nombre, prov = m["nombre"], p["nombre"]
        lugar = nombre if nombre == prov else f"{nombre} ({prov})"
        sup = m.get("sup_med") or 90
        ejemplo = round(m["med"] * sup, -3)
        resp = (f'En {escape(lugar)}, el precio mediano de la vivienda en venta es de {m2(m["med"])}, según {num(m["n"])} '
                f'anuncios analizados por Idealisto en los últimos 12 meses. La mitad de las viviendas se anuncian entre '
                f'{num(m["p25"])} y {num(m["p75"])} €/m²: una vivienda típica de {sup} m² ronda los {eur(ejemplo)}.')
        vs_prov = pct(m["med"], p["med"])
        mivau = m.get("mivau") or {}
        vs_tasado = pct(m["med"], mivau.get("eur_m2"))
        serp = m.get("serpavi") or {}
        kpis = self._kpis([
            ("Vivienda en venta", m2(m["med"]), f'{cmp_txt(vs_prov)} la provincia' if vs_prov is not None else ""),
            ("Rango central", f'{num(m["p25"])}–{num(m["p75"])} €/m²', "percentiles 25 y 75"),
            ("Precio mediano anunciado", eur(m.get("precio_med")), f"superficie mediana {sup} m²"),
            ("Valor tasado oficial", m2(mivau.get("eur_m2")),
             f'Ministerio de Vivienda, {mivau["fecha"][:4]}' if mivau else ""),
            ("Alquiler de referencia", f'{dec(serp["eur_m2_mes"], 2)} €/m² al mes' if serp else "—",
             f'SERPAVI {serp["anio"]}' if serp else ""),
            ("Rentabilidad bruta estimada", f'{dec(m["rentab_bruta"])} %' if m.get("rentab_bruta") else "—",
             "alquiler de referencia sobre precio de pisos"),
        ])
        oferta_vs = ""
        if vs_tasado is not None:
            oferta_vs = (f'<h2>¿Precio de anuncio o precio real en {escape(nombre)}?</h2><p>El valor tasado medio de la vivienda en '
                         f'{escape(nombre)}, según la estadística del Ministerio de Vivienda, es de {m2(mivau["eur_m2"])}. Los anuncios '
                         f'piden {"un " + str(abs(vs_tasado)) + " % más" if vs_tasado >= 3 else ("un " + str(abs(vs_tasado)) + " % menos" if vs_tasado <= -3 else "prácticamente lo mismo")}. '
                         'Esa diferencia es el margen habitual de negociación más la diferencia entre lo que se pide y lo que un tasador '
                         'certifica. Para saber cuánto vale una vivienda concreta, valórala con su referencia catastral.</p>')
        vecinos = [c for c in m.get("vecinos", []) if c in M]
        vec_html = ""
        if vecinos:
            vec_html = ('<h2>Precio de la vivienda en municipios cercanos</h2><div class="scroll"><table><thead><tr><th>Municipio</th>'
                        '<th>Vivienda</th><th>Diferencia</th></tr></thead><tbody>' + "".join(
                            f'<tr><td><a href="{self.url_mun(c)}">{escape(M[c]["nombre"])}</a></td><td>{m2(M[c]["med"])}</td>'
                            f'<td>{(("+" if (pct(M[c]["med"], m["med"]) or 0) > 0 else "") + str(pct(M[c]["med"], m["med"])) + " %") if pct(M[c]["med"], m["med"]) is not None else "—"}</td></tr>'
                            for c in vecinos) + "</tbody></table></div>")
        o = m.get("otros") or {}
        faq = [(f"¿Cuánto cuesta el metro cuadrado en {nombre}?",
                f"La mediana de los anuncios de vivienda en venta en {nombre} es de {m2(m['med'])}"
                + (f"; los pisos se anuncian a {m2(m['piso']['med'])}" if m.get("piso") else "")
                + (f" y las casas a {m2(m['casa']['med'])}" if m.get("casa") else "") + ".")]
        if vs_prov is not None:
            faq.append((f"¿Es caro comprar vivienda en {nombre}?",
                        f"La vivienda en {nombre} se anuncia {cmp_txt(vs_prov)} la media de la provincia de {prov} "
                        f"({m2(m['med'])} frente a {m2(p['med'])})."))
        if o.get("garaje"):
            faq.append((f"¿Cuánto cuesta una plaza de garaje en {nombre}?",
                        f"El precio mediano de las plazas de garaje en venta en {nombre} es de {eur(o['garaje']['precio_med'])}, "
                        f"según {num(o['garaje']['n'])} anuncios."))
        if m.get("rentab_bruta"):
            faq.append((f"¿Qué rentabilidad da alquilar un piso en {nombre}?",
                        f"Con el alquiler de referencia oficial ({dec(serp['eur_m2_mes'], 2)} €/m² al mes, SERPAVI {serp['anio']}) y el "
                        f"precio mediano de los pisos en venta, la rentabilidad bruta ronda el {dec(m['rentab_bruta'])} % anual, "
                        f"antes de gastos e impuestos."))
        migas = [("Inicio", "/"), ("Precio de la vivienda", "/precio-vivienda/"),
                 (f"Provincia de {prov}", self.url_prov(m["prov"])), (nombre, self.url_mun(code))]
        oficial = (f'<p class="hint">Nombre oficial: {escape(m["nombre_ine"])}.</p>'
                   if m["nombre_ine"].replace(" ", "") != nombre.replace(" ", "") else "")
        cuerpo = (f'<main class="wrap doc ancha">{self._migas_html(migas)}<h1>Precio de la vivienda en {escape(nombre)} (2026)</h1>'
                  f'<p class="fecha">Actualizado el {self._fecha_txt()}</p>'
                  f'<p class="answer"><strong>Respuesta rápida:</strong> {resp}</p>{kpis}'
                  f'<h2>Precio por tipo de inmueble en {escape(nombre)}</h2>{self._tabla_tipos(m)}{oferta_vs}'
                  f'{self._valorador(m["prov"], nombre)}{vec_html}'
                  f'<p>Ver el <a href="{self.url_prov(m["prov"])}">precio de la vivienda en la provincia de {escape(prov)}</a>.</p>'
                  f'{self._nota_metodo()}{oficial}{self._faq_html(faq)}</main>')
        desc = (f"Precio de la vivienda en {nombre}: {m2(m['med'])} de mediana"
                + (f", pisos a {m2(m['piso']['med'])}" if m.get("piso") else "")
                + ", garajes y locales. Valora tu inmueble con su referencia catastral.")[:158]
        return {"title": f"Precio vivienda en {nombre} 2026: €/m² y valoración"[:60], "desc": desc, "cuerpo": cuerpo,
                "graph": self._ld(self.url_mun(code), migas, lugar, desc, (m.get("lat"), m.get("lon")), faq, site),
                "noindex": not m["indexable"]}
