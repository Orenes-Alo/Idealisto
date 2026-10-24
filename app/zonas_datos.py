"""Genera data/zonas.json: datos propios de precio por provincia y municipio.

Fuentes (BD de Orenes, rol de solo lectura idealisto_ro):
  external_listings          anuncios de venta de portales (últimos 365 días)
  ineatlas_municipios        nombres y códigos INE (para normalizar municipios)
  mivau_valor_tasado_mun     valor tasado medio MIVAU (municipios > 25.000 hab.)
  oficial_cien_compraventas  compraventas notariales por provincia
  serpavi_renta              alquiler de referencia SERPAVI por municipio

Uso (en el servidor, semanal por systemd timer):
  .venv/bin/python -m app.zonas_datos            # escribe data/zonas.json
"""
from __future__ import annotations

import html
import json
import math
import os
import re
import sys
import time
import unicodedata
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "data" / "zonas.json"
# Sin serie mensual ni tiempo en mercado: el seguimiento de anuncios empezó en mayo de 2026 y esas
# métricas aún reflejan el ciclo de rastreo, no el mercado. Añadirlas cuando haya un año de histórico.

PROVINCIAS = {
    "01": "Álava", "02": "Albacete", "03": "Alicante", "04": "Almería", "05": "Ávila", "06": "Badajoz",
    "07": "Illes Balears", "08": "Barcelona", "09": "Burgos", "10": "Cáceres", "11": "Cádiz", "12": "Castellón",
    "13": "Ciudad Real", "14": "Córdoba", "15": "A Coruña", "16": "Cuenca", "17": "Girona", "18": "Granada",
    "19": "Guadalajara", "20": "Gipuzkoa", "21": "Huelva", "22": "Huesca", "23": "Jaén", "24": "León",
    "25": "Lleida", "26": "La Rioja", "27": "Lugo", "28": "Madrid", "29": "Málaga", "30": "Murcia",
    "31": "Navarra", "32": "Ourense", "33": "Asturias", "34": "Palencia", "35": "Las Palmas", "36": "Pontevedra",
    "37": "Salamanca", "38": "Santa Cruz de Tenerife", "39": "Cantabria", "40": "Segovia", "41": "Sevilla",
    "42": "Soria", "43": "Tarragona", "44": "Teruel", "45": "Toledo", "46": "Valencia", "47": "Valladolid",
    "48": "Bizkaia", "49": "Zamora", "50": "Zaragoza", "51": "Ceuta", "52": "Melilla",
}

UNIPROVINCIALES = {"28": "madrid", "30": "murcia", "33": "asturias", "39": "cantabria", "26": "rioja",
                   "07": "balears", "31": "navarra", "51": "ceuta", "52": "melilla"}

MIN_PAGINA = 10      # anuncios de vivienda para generar la página de municipio
MIN_INDEX = 50       # para indexarla (regla del plan SEO)


def slug(s: str) -> str:
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def clave(s: str) -> str:
    s = html.unescape(s or "")
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"\(.*?\)", " ", s)
    return re.sub(r"[^a-z0-9ñ]+", " ", s).strip()


def variantes(nombre: str) -> set[str]:
    """«Alicante/Alacant», «Coruña, A», «Palmas de Gran Canaria, Las» → todas sus formas."""
    out = set()
    partes = re.split(r"\s*/\s*|\s+-\s+", nombre)
    for p in partes + [nombre]:
        p = p.strip()
        m = re.match(r"^(.*),\s*(el|la|los|las|l'|o|a|os|as|es|sa|ses|s')$", p, re.I)
        if m:
            p2 = f"{m.group(2)} {m.group(1)}"
            out.add(clave(p2))
            out.add(clave(m.group(1)))
        out.add(clave(p))
    return {v for v in out if v}


def articulo_delante(n: str) -> str:
    m = re.match(r"^(.*),\s*(el|la|los|las|l'|o|a|os|as|es|sa|ses|s')$", n.strip(), re.I)
    if not m:
        return n.strip()
    art = m.group(2)
    art = art[0].upper() + art[1:].lower()
    return f"{art}{'' if art.endswith(chr(39)) else ' '}{m.group(1)}"


def elegir_nombre(nombre_ine: str, en_anuncios: dict[str, int]) -> str:
    """Nombre para el título y la URL. En los bilingües («Alacant/Alicante») gana la forma que más
    usan los anuncios, que es la que se busca; si no, la primera del INE."""
    partes = [p.strip() for p in nombre_ine.split("/") if p.strip()]
    if len(partes) > 1 and en_anuncios:
        votos = defaultdict(int)
        for raw, n in en_anuncios.items():
            primero = clave(re.split(r"\s*/\s*", html.unescape(raw))[0])
            for p in partes:
                if clave(articulo_delante(p)) == primero or clave(p) == primero:
                    votos[p] += n
        if votos:
            return articulo_delante(max(votos, key=votos.get))
    return articulo_delante(partes[0] if partes else nombre_ine)


CLASE_SQL = r"""
CASE
  WHEN e.tipo IN ('piso','casa','local','garaje','nave','terreno','trastero') THEN e.tipo
  WHEN coalesce(e.tipo,'') = '' THEN CASE
    WHEN e.title ~* '(garaje|aparcamiento|parking)' THEN 'garaje'
    WHEN e.title ~* 'trastero' THEN 'trastero'
    WHEN e.title ~* '(local comercial|oficina|\(local)' THEN 'local'
    WHEN e.title ~* '\mnave' THEN 'nave'
    WHEN e.title ~* '(terreno|solar|parcela)' THEN 'terreno'
    WHEN e.title ~* '(chalet|casa|adosad|pareado|unifamiliar|villa|bungal|cortijo|mas[ií]a|caser[ií]o)' THEN 'casa'
    WHEN e.title ~* '(piso|apartamento|(&#xc1;|á|a)tico|d(&#xfa;|ú|u)plex|estudio|loft|planta baja)' THEN 'piso'
  END
END"""


def base_cte(grupo: str) -> str:
    """CTE de anuncios de venta deduplicados (mismo precio y superficie en el mismo municipio = mismo inmueble
    en varios portales). `grupo` es la columna de agrupación: m.code (municipio) o m.prov (provincia)."""
    return f"""
WITH m AS (SELECT * FROM unnest(%(provs)s::text[], %(muns)s::text[], %(codes)s::text[]) AS t(prov, mun, code)),
l AS (
  SELECT DISTINCT ON ({grupo}, clase, round(e.price), round(coalesce(e.area_m2, 0)))
         {grupo} AS g, clase, e.price::float8 AS p, e.area_m2::float8 AS a, e.first_seen_at, e.delisted_at,
         e.first_price::float8 AS fp, e.lat, e.lon
    FROM external_listings e
    JOIN m ON m.prov = e.province_code AND m.mun = e.municipality
    CROSS JOIN LATERAL (SELECT {CLASE_SQL} AS clase) c
   WHERE e.operation = 'venta' AND e.scraped_at >= now() - interval '365 days' AND e.price > 0
   ORDER BY {grupo}, clase, round(e.price), round(coalesce(e.area_m2, 0)), e.scraped_at DESC
),
v AS (SELECT * FROM l WHERE clase IN ('piso','casa') AND a BETWEEN 25 AND 1500
        AND p BETWEEN 15000 AND 30000000 AND p / a BETWEEN 150 AND 25000)
"""


Q_VIVIENDA = """
SELECT g, count(*) n,
       percentile_cont(ARRAY[.25,.5,.75]) WITHIN GROUP (ORDER BY p / a) q,
       percentile_cont(.5) WITHIN GROUP (ORDER BY p) precio,
       percentile_cont(.5) WITHIN GROUP (ORDER BY a) sup,
       count(*) FILTER (WHERE clase = 'piso') n_piso,
       percentile_cont(.5) WITHIN GROUP (ORDER BY p / a) FILTER (WHERE clase = 'piso') m_piso,
       count(*) FILTER (WHERE clase = 'casa') n_casa,
       percentile_cont(.5) WITHIN GROUP (ORDER BY p / a) FILTER (WHERE clase = 'casa') m_casa,
       avg(lat) FILTER (WHERE lat BETWEEN 27 AND 44.5) lat, avg(lon) FILTER (WHERE lon BETWEEN -18.5 AND 4.5) lon
  FROM v GROUP BY g
"""

Q_OTROS = """
SELECT g, clase, count(*) n,
       percentile_cont(.5) WITHIN GROUP (ORDER BY p) precio,
       percentile_cont(.5) WITHIN GROUP (ORDER BY p / nullif(a, 0)) eur_m2
  FROM l
 WHERE (clase = 'garaje' AND p BETWEEN 2000 AND 300000)
    OR (clase = 'trastero' AND p BETWEEN 1000 AND 150000)
    OR (clase = 'local' AND a BETWEEN 15 AND 3000 AND p / a BETWEEN 50 AND 20000)
    OR (clase = 'nave' AND a BETWEEN 80 AND 50000 AND p / a BETWEEN 20 AND 5000)
    OR (clase = 'terreno' AND a >= 50 AND p / a BETWEEN 1 AND 3000)
 GROUP BY g, clase HAVING count(*) >= 8
"""


def r(x, nd=0):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return None
    return round(float(x), nd) if nd else int(round(float(x)))


def dist_km(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))


def generar(dsn: str) -> dict:
    import psycopg

    t0 = time.time()
    con = psycopg.connect(dsn, autocommit=True)
    cur = con.cursor()

    # 1) Municipios INE y casación de los nombres de los anuncios.
    cur.execute("SELECT mun_code, mun_name, prov_code FROM ineatlas_municipios")
    ine = {code: (name, prov) for code, name, prov in cur.fetchall()}
    por_clave: dict[tuple[str, str], str] = {}
    for code, (name, prov) in ine.items():
        for v in variantes(name):
            por_clave.setdefault((prov, v), code)
    cur.execute("""SELECT province_code, municipality, count(*) FROM external_listings
                    WHERE scraped_at >= now() - interval '365 days' AND operation = 'venta'
                      AND province_code IS NOT NULL AND municipality IS NOT NULL GROUP BY 1, 2""")
    provs, muns, codes = [], [], []
    nombres_anuncio: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    total = casados = 0
    for prov, mun, n in cur.fetchall():
        total += n
        code = None
        for v in variantes(mun):
            code = por_clave.get((prov, v))
            if code:
                break
        if code:
            casados += n
            provs.append(prov); muns.append(mun); codes.append(code)
            nombres_anuncio[code][mun] += n
    print(f"casación de municipios: {casados}/{total} anuncios ({casados / max(total, 1):.1%})", file=sys.stderr)
    params = {"provs": provs, "muns": muns, "codes": codes}

    def consulta(grupo: str, q: str):
        cur.execute(base_cte(grupo) + q, params)
        return cur.fetchall()

    def bloque_vivienda(fila) -> dict:
        g, n, q, precio, sup, n_piso, m_piso, n_casa, m_casa, lat, lon = fila
        return {
            "n": n, "p25": r(q[0]), "med": r(q[1]), "p75": r(q[2]), "precio_med": r(precio, -3) if precio else None,
            "sup_med": r(sup),
            "piso": {"n": n_piso, "med": r(m_piso)} if n_piso and n_piso >= 10 else None,
            "casa": {"n": n_casa, "med": r(m_casa)} if n_casa and n_casa >= 10 else None,
            "lat": r(lat, 4), "lon": r(lon, 4),
        }

    datos = {}
    for nivel, grupo in (("mun", "m.code"), ("prov", "m.prov")):
        viv = {f[0]: bloque_vivienda(f) for f in consulta(grupo, Q_VIVIENDA)}
        for g, clase, n, precio, eur_m2 in consulta(grupo, Q_OTROS):
            if g in viv:
                viv[g].setdefault("otros", {})[clase] = {"n": n, "precio_med": r(precio, -2), "eur_m2": r(eur_m2)}
        datos[nivel] = viv
        print(f"{nivel}: {len(viv)} con vivienda ({time.time() - t0:.0f}s)", file=sys.stderr)

    # 2) Oficiales.
    cur.execute("""SELECT DISTINCT ON (mun_code) mun_code, fecha, eur_m2_total, n_tasaciones
                     FROM mivau_valor_tasado_mun WHERE eur_m2_total IS NOT NULL ORDER BY mun_code, fecha DESC""")
    mivau = {c: {"fecha": f.isoformat(), "eur_m2": r(e), "n": n} for c, f, e, n in cur.fetchall()}
    cur.execute("""SELECT DISTINCT ON (codigo) codigo, anio, renta_m2_med FROM serpavi_renta
                    WHERE nivel = 'municipio' AND tipologia = 'VC' AND renta_m2_med IS NOT NULL
                    ORDER BY codigo, anio DESC""")
    serpavi = {c: {"anio": a, "eur_m2_mes": r(v, 2)} for c, a, v in cur.fetchall()}
    cur.execute("""SELECT region_code, fecha, n_compraventas, importe_medio_eur FROM oficial_cien_compraventas
                    WHERE nivel = 'provincia' AND region_code IS NOT NULL AND fecha >= now() - interval '30 months'
                    ORDER BY region_code, fecha""")
    cien = defaultdict(list)
    for code, f, n, imp in cur.fetchall():
        cien[code].append((f, n, imp))
    # Comunidades uniprovinciales: el dato viene a nivel CCAA («Murcia, Región de»…).
    cur.execute("""SELECT region, fecha, n_compraventas, importe_medio_eur FROM oficial_cien_compraventas
                    WHERE nivel = 'ccaa' AND fecha >= now() - interval '30 months' ORDER BY region, fecha""")
    filas_ccaa = cur.fetchall()
    for code, clave_prov in UNIPROVINCIALES.items():
        if code in cien:
            continue
        for region, f, n, imp in filas_ccaa:
            if clave_prov in clave(region):
                cien[code].append((f, n, imp))

    # 3) Ensamblado.
    municipios = {}
    for code, d in datos["mun"].items():
        if d["n"] < MIN_PAGINA or code not in ine:
            continue
        nombre_ine, prov = ine[code]
        d.update({"nombre": elegir_nombre(nombre_ine, nombres_anuncio.get(code, {})), "nombre_ine": nombre_ine, "prov": prov,
                  "indexable": d["n"] >= MIN_INDEX, "mivau": mivau.get(code), "serpavi": serpavi.get(code)})
        if d["serpavi"] and d.get("piso") and d["piso"]["med"]:
            d["rentab_bruta"] = r(100 * 12 * d["serpavi"]["eur_m2_mes"] / d["piso"]["med"], 1)
        municipios[code] = d
    # slugs únicos por provincia
    vistos = defaultdict(set)
    for code in sorted(municipios, key=lambda c: -municipios[c]["n"]):
        d = municipios[code]
        s = slug(d["nombre"])
        if s in vistos[d["prov"]]:
            s = f"{s}-{code}"
        vistos[d["prov"]].add(s)
        d["slug"] = s
    # vecinos: los 6 más cercanos con página
    con_coords = [(c, (d["lat"], d["lon"])) for c, d in municipios.items() if d["lat"] and d["lon"]]
    for c, pto in con_coords:
        cerca = sorted(((dist_km(pto, p2), c2) for c2, p2 in con_coords if c2 != c))[:6]
        municipios[c]["vecinos"] = [c2 for km, c2 in cerca if km < 60]

    provincias = {}
    for code, nombre in PROVINCIAS.items():
        d = datos["prov"].get(code)
        if not d:
            continue
        serie = cien.get(code, [])
        ult4 = serie[-4:]
        d.update({"nombre": nombre, "slug": slug(nombre),
                  "municipios": sorted((c for c, m in municipios.items() if m["prov"] == code),
                                       key=lambda c: -municipios[c]["n"])})
        if len(ult4) == 4:
            d["cien"] = {"hasta": ult4[-1][0].isoformat(), "compraventas_12m": sum(x[1] or 0 for x in ult4),
                         "importe_medio": r(ult4[-1][2], -2) if ult4[-1][2] else None}
            if len(serie) >= 8 and serie[-8][1]:
                prev = sum(x[1] or 0 for x in serie[-8:-4])
                d["cien"]["var_compraventas"] = r(100 * (d["cien"]["compraventas_12m"] / prev - 1), 1) if prev else None
        provincias[code] = d

    return {"generado": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "min_index": MIN_INDEX,
            "casacion": round(casados / max(total, 1), 4), "provincias": provincias, "municipios": municipios}


def main():
    dsn = os.environ.get("IDEALISTO_DB")
    if not dsn:
        sys.exit("Falta IDEALISTO_DB")
    datos = generar(dsn)
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    tmp = SALIDA.with_suffix(".tmp")
    tmp.write_text(json.dumps(datos, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    tmp.replace(SALIDA)
    idx = sum(1 for m in datos["municipios"].values() if m["indexable"])
    print(f"{len(datos['provincias'])} provincias, {len(datos['municipios'])} municipios ({idx} indexables) → {SALIDA}")


if __name__ == "__main__":
    main()
