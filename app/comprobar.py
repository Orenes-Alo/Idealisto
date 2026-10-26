"""«¿Está bien de precio?» para compradores (2026-10-26).

Compara el precio que piden por un inmueble concreto (por su referencia catastral) con la valoración
del motor de Orenes: valor_min / valor_max son el p25 y el p75 de €/m² de los testigos × superficie.
Mismas reglas que /precio-vivienda/comprobar de inversionnpl.com. Además contrasta los m² del anuncio
con los del Catastro y estima el ITP de la comunidad. Lógica pura, sin red: testeable.
"""
from __future__ import annotations

from . import fiscal
from .callejero import PROVINCIAS, norm

# Muy por debajo del tramo bajo: un 15 % bajo el p25 o un 40 % bajo la mediana, lo que quede más abajo.
VEREDICTOS = ("sospechoso", "gran_precio", "justo", "caro")


def umbral_sospechoso(valor_min: float, valor_central: float) -> float:
    return min(valor_min * 0.85, valor_central * 0.6)


def veredicto(precio: float, valor_min: float, valor_central: float, valor_max: float) -> str:
    if precio < umbral_sospechoso(valor_min, valor_central):
        return "sospechoso"
    if precio < valor_min:
        return "gran_precio"
    if precio <= valor_max:
        return "justo"
    return "caro"


def contraste_m2(m2_anuncio: float | None, m2_catastro: float | None) -> dict | None:
    """Los anuncios suelen dar la superficie construida con zonas comunes, hasta un ~15 % más que la del
    Catastro sin comunes. Más de un 20 % por encima (o un 15 % por debajo) merece una pregunta."""
    if not m2_anuncio or not m2_catastro or m2_anuncio <= 0 or m2_catastro <= 0:
        return None
    dif = (m2_anuncio - m2_catastro) / m2_catastro
    return {"anuncio": round(m2_anuncio), "catastro": round(m2_catastro), "dif_pct": round(dif * 100),
            "aviso": dif > 0.20 or dif < -0.15}


# ── ITP por comunidad (tipo general de fiscal.ITP; los reducidos dependen del comprador) ──
_CCAA_POR_PROV = {
    "04": "AN", "11": "AN", "14": "AN", "18": "AN", "21": "AN", "23": "AN", "29": "AN", "41": "AN",
    "22": "AR", "44": "AR", "50": "AR", "33": "AS", "07": "IB", "35": "CN", "38": "CN", "39": "CB",
    "05": "CL", "09": "CL", "24": "CL", "34": "CL", "37": "CL", "40": "CL", "42": "CL", "47": "CL", "49": "CL",
    "02": "CM", "13": "CM", "16": "CM", "19": "CM", "45": "CM", "08": "CT", "17": "CT", "25": "CT", "43": "CT",
    "03": "VC", "12": "VC", "46": "VC", "06": "EX", "10": "EX", "15": "GA", "27": "GA", "32": "GA", "36": "GA",
    "28": "MD", "30": "MC", "26": "RI", "51": "CE", "52": "ML",
}
_COD_POR_NOMBRE = {n: c for c, n in PROVINCIAS} | {
    "ALICANTE": "03", "CASTELLON": "12", "CASTELLON DE LA PLANA": "12", "SANTA CRUZ DE TENERIFE": "38",
    "BALEARES": "07", "ILLES BALEARS": "07", "CORUÑA": "15", "LA CORUÑA": "15", "GERONA": "17",
    "LERIDA": "25", "ORENSE": "32", "LOGROÑO": "26", "RIOJA": "26", "PALMAS": "35"}
_NOMBRE_CCAA = dict(fiscal.CCAA)


def ccaa_de_provincia(provincia: str | None) -> str | None:
    p = norm(provincia or "")
    cod = _COD_POR_NOMBRE.get(p) or _COD_POR_NOMBRE.get(p.split("/")[0].strip())
    return _CCAA_POR_PROV.get(cod or "")


def itp_general(ccaa: str, base: float) -> tuple[float, float] | None:
    """(cuota, tipo medio %) con el tipo general de la comunidad, o None si no hay dato."""
    d = fiscal.ITP.get(ccaa)
    if not d or base <= 0:
        return None
    if d.get("general") is not None:
        cuota = base * d["general"] / 100
    elif d.get("tramos"):
        cuota = sum((min(base, t["hasta"] if t["hasta"] is not None else base) - t["desde"]) * t["tipo"] / 100
                    for t in d["tramos"] if base > t["desde"])
    elif d.get("unico"):
        tipo = next(t["tipo"] for t in d["unico"] if t["hasta"] is None or base <= t["hasta"])
        cuota = base * tipo / 100
    else:
        return None
    return cuota, cuota / base * 100


def comprobar(data: dict, precio: float, m2_anuncio: float | None = None) -> dict:
    """data = respuesta del motor (/internal/avm/rc). Devuelve el resultado completo; el endpoint
    decide qué cifras enseña sin cuenta."""
    vmin, vc, vmax = float(data["valor_min"]), float(data["valor_central"]), float(data["valor_max"])
    v = veredicto(precio, vmin, vc, vmax)
    ccaa = ccaa_de_provincia(data.get("provincia"))
    itp = itp_general(ccaa, precio) if ccaa else None
    return {
        "veredicto": v,
        "diferencia_pct": round((precio - vc) / vc * 100) if vc else 0,
        "precio": round(precio),
        "valor_central": round(vc), "valor_min": round(vmin), "valor_max": round(vmax),
        "umbral": round(umbral_sospechoso(vmin, vc)),
        "cierre_estimado": data.get("cierre_estimado"),
        "m2": contraste_m2(m2_anuncio, data.get("superficie_m2")),
        "itp": {"cuota": round(itp[0]), "tipo": round(itp[1], 2), "ccaa": _NOMBRE_CCAA.get(ccaa, ccaa)} if itp else None,
    }
