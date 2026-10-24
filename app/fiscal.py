"""Datos fiscales 2026 de las calculadoras (ITP, Sucesiones y Donaciones, plusvalía municipal).

Fuentes (revisadas el 24-10-2026):
  - Ministerio de Hacienda, «Tributación Autonómica. Medidas 2026», caps. I y IV (actualizado 23-09-2026).
  - BOE consolidado: TRLITPAJD (RDLeg 1/1993, art. 10 y 11), Ley 29/1987 (arts. 20-22), TRLRHL (arts. 104-108).
  - Coeficientes de plusvalía: RDL 8/2023 art. 24 (vigentes hasta el 30-11-2026) y RDL 29/2026 art. 10
    (desde el 01-12-2026; PENDIENTE de convalidación: revisar a mediados de noviembre de 2026).
  - REAF-CGE «Panorama de la Fiscalidad Autonómica y Foral 2026» para contrastar.
País Vasco y Navarra (forales) quedan fuera: datos no confirmados.
REVISAR cada año (enero) y cuando cambie una ley autonómica.
"""

ACTUALIZADO = "2026-10-24"

CCAA = [
    ("AN", "Andalucía"), ("AR", "Aragón"), ("AS", "Asturias"), ("IB", "Illes Balears"), ("CN", "Canarias"),
    ("CB", "Cantabria"), ("CL", "Castilla y León"), ("CM", "Castilla-La Mancha"), ("CT", "Cataluña"),
    ("VC", "Comunitat Valenciana"), ("EX", "Extremadura"), ("GA", "Galicia"), ("MD", "Madrid"),
    ("MC", "Región de Murcia"), ("RI", "La Rioja"), ("CE", "Ceuta"), ("ML", "Melilla"),
]


def T(*filas):
    """Tramos progresivos: T((0, 400000, 8), (400000, None, 10)) → [{desde, hasta, tipo}]."""
    return [{"desde": d, "hasta": h, "tipo": t} for d, h, t in filas]


def U(*filas):
    """Tipo único según el valor total: U((300000, 8), (500000, 9), (None, 10))."""
    return [{"hasta": h, "tipo": t} for h, t in filas]


ITP = {
    "AN": {"general": 7, "reducidos": [
        {"id": "an6", "nombre": "Vivienda habitual hasta 150.000 €", "tipo": 6, "requisitos": "Valor de la vivienda ≤ 150.000 €."},
        {"id": "an35", "nombre": "Menor de 35 años", "tipo": 3.5, "requisitos": "Menor de 35 años, vivienda habitual de valor ≤ 150.000 €."},
        {"id": "anfn", "nombre": "Familia numerosa o discapacidad", "tipo": 3.5, "requisitos": "Familia numerosa o discapacidad, vivienda habitual de valor ≤ 250.000 €."}]},
    "AR": {"tramos": T((0, 400000, 8), (400000, 450000, 8.5), (450000, 500000, 9), (500000, 750000, 9.5), (750000, None, 10)),
           "reducidos": [
        {"id": "arjov", "nombre": "Bonificación 12,5 % (menor de 35, discapacidad ≥ 65 %…)", "factor": 0.875,
         "requisitos": "Menor de 35 años, discapacidad ≥ 65 % o víctima de violencia de género; vivienda habitual de valor ≤ 100.000 €."},
        {"id": "arfn", "nombre": "Familia numerosa (bonificación 50 %)", "factor": 0.5,
         "requisitos": "Familia numerosa con renta ≤ 35.000 € (+ 6.000 € por hijo adicional). 60 % en núcleos rurales en riesgo de despoblación."}]},
    "AS": {"unico": U((300000, 8), (500000, 9), (None, 10)), "reducidos": [
        {"id": "asjov", "nombre": "Joven ≤ 35, familia numerosa o monoparental, zona rural…", "unico": U((150000, 4), (None, 6)),
         "requisitos": "Vivienda habitual. 4 % si el valor es ≤ 150.000 € y 6 % si es mayor."}],
           "nota": "Los grandes tenedores tributan al 20 %."},
    "IB": {"tramos": T((0, 400000, 8), (400000, 600000, 9), (600000, 1000000, 10), (1000000, 2000000, 12), (2000000, None, 13)),
           "reducidos": [
        {"id": "ibvh", "nombre": "Vivienda habitual", "tramos": T((0, 270151.20, 4), (270151.20, None, 8)),
         "requisitos": "Vivienda habitual de valor ≤ 331.859,70 € (Mallorca y Menorca) o ≤ 378.211,68 € (Ibiza y Formentera)."},
        {"id": "ibjov", "nombre": "Primera vivienda de menor de 36 o con discapacidad", "tramos": T((0, 270151.20, 2), (270151.20, None, 8)),
         "requisitos": "Primera vivienda habitual de menor de 36 años o con mínimo por discapacidad; mismos límites de valor."}]},
    "CN": {"general": 6.5, "reducidos": [
        {"id": "cn5", "nombre": "Vivienda habitual hasta 200.000 €", "tipo": 5,
         "requisitos": "Vivienda habitual con base ≤ 200.000 € y sin otra vivienda (bonificación adicional del 20 % si tienes ≤ 40 años y renta ≤ 46.455 €)."},
        {"id": "cnfn", "nombre": "Familia numerosa", "tipo": 1, "requisitos": "Familia numerosa, vivienda habitual."},
        {"id": "cndis", "nombre": "Discapacidad ≥ 65 % o familia monoparental", "tipo": 1, "requisitos": "Renta ≤ 46.455 € más incrementos."}]},
    "CB": {"general": 9, "reducidos": [
        {"id": "cbvh", "nombre": "Vivienda habitual", "tramos": T((0, 300000, 7), (300000, None, 9)), "requisitos": "Vivienda habitual."},
        {"id": "cb4", "nombre": "Menor de 40, familia numerosa, monoparental, VPP o municipio en riesgo de despoblación", "tipo": 4,
         "requisitos": "Vivienda habitual; también discapacidad del 33 al 65 %."},
        {"id": "cb3", "nombre": "Discapacidad ≥ 65 %", "tipo": 3, "requisitos": "Vivienda habitual."}]},
    "CL": {"tramos": T((0, 250000, 8), (250000, None, 10)), "reducidos": [
        {"id": "cl4", "nombre": "Familia numerosa, discapacidad ≥ 65 %, menores de 36 o VPP", "tipo": 4,
         "requisitos": "Vivienda habitual; renta ≤ 31.500 € (37.800 € familia numerosa)."},
        {"id": "clrural", "nombre": "Menor de 36 en municipio pequeño", "tipo": 0.01,
         "requisitos": "Vivienda habitual de valor < 150.000 € en municipio pequeño."}]},
    "CM": {"general": 9, "reducidos": [
        {"id": "cm6", "nombre": "Primera vivienda habitual con hipoteca", "tipo": 6, "requisitos": "Valor ≤ 240.000 € y préstamo hipotecario > 50 % del precio."},
        {"id": "cm5", "nombre": "Familia numerosa, monoparental o discapacidad ≥ 65 %", "tipo": 5, "requisitos": "Vivienda habitual de valor ≤ 240.000 €."},
        {"id": "cm3", "nombre": "Menor de 36 años", "tipo": 3, "requisitos": "Vivienda habitual de valor ≤ 240.000 € (desde el 31-03-2026)."}]},
    "CT": {"tramos": T((0, 600000, 10), (600000, 900000, 11), (900000, 1500000, 12), (1500000, None, 13)), "reducidos": [
        {"id": "ctjov", "nombre": "Joven ≤ 35 años", "tipo": 5, "requisitos": "Vivienda habitual; renta ≤ 36.000 €."},
        {"id": "ctfn", "nombre": "Familia numerosa o monoparental", "tipo": 5, "requisitos": "Vivienda habitual; renta ≤ 36.000 €."},
        {"id": "ctdis", "nombre": "Discapacidad", "tipo": 5, "requisitos": "Vivienda habitual; renta ≤ 36.000 €."}],
           "nota": "VPO al 7 %; grandes tenedores al 20 %."},
    "VC": {"unico": U((1000000, 9), (None, 11)), "reducidos": [
        {"id": "vcjov", "nombre": "Primera vivienda habitual de menor de 35", "unico": U((180000, 6), (None, 8)),
         "requisitos": "Renta ≤ 30.000 € individual o ≤ 47.000 € conjunta."},
        {"id": "vcfn", "nombre": "Familia numerosa o monoparental", "unico": U((180000, 3), (None, 4)), "requisitos": "Vivienda habitual."},
        {"id": "vcdis", "nombre": "Discapacidad ≥ 65 %", "unico": U((180000, 3), (None, 4)), "requisitos": "Vivienda habitual."}],
           "nota": "Tipo general del 9 % desde el 1 de junio de 2026 (antes, 10 %)."},
    "EX": {"tramos": T((0, 360000, 8), (360000, 600000, 10), (600000, None, 11)), "reducidos": [
        {"id": "ex7", "nombre": "Vivienda habitual", "tipo": 7, "requisitos": "Vivienda ≤ 200.000 € y renta ≤ 30.000 € individual o ≤ 55.000 € conjunta."},
        {"id": "ex4", "nombre": "Menor de 36, familia numerosa o discapacidad ≥ 65 %", "tipo": 4, "requisitos": "Mismos límites de valor y renta."},
        {"id": "exrural", "nombre": "Municipio de menos de 3.000 habitantes", "tipo": 4, "requisitos": "Vivienda habitual."}]},
    "GA": {"general": 8, "reducidos": [
        {"id": "ga7", "nombre": "Vivienda habitual", "tipo": 7, "requisitos": "Patrimonio ≤ 240.000 € + 30.000 € por miembro adicional."},
        {"id": "ga3", "nombre": "Menor de 36 años", "tipo": 3, "requisitos": "Mismo límite de patrimonio."},
        {"id": "gafn", "nombre": "Familia numerosa o discapacidad ≥ 65 %", "tipo": 3, "requisitos": "Familia numerosa: precio y patrimonio ≤ 400.000 € + 50.000 €."}]},
    "MD": {"general": 6, "reducidos": [
        {"id": "mdvh", "nombre": "Vivienda habitual hasta 250.000 € (bonificación 10 %)", "tipo": 5.4, "requisitos": "Valor ≤ 250.000 €."},
        {"id": "mdfn", "nombre": "Familia numerosa", "tipo": 4, "requisitos": "Vivienda habitual."},
        {"id": "mdrural", "nombre": "Menor de 35 en municipio < 2.500 hab.", "tipo": 0, "requisitos": "Bonificación del 100 %, vivienda ≤ 250.000 €."}]},
    "MC": {"general": 7.75, "reducidos": [
        {"id": "mc40", "nombre": "Menor de 40 años", "tipo": 3, "requisitos": "Base imponible general < 40.000 € y del ahorro ≤ 1.800 €."},
        {"id": "mcfn", "nombre": "Primera vivienda de familia numerosa", "tipo": 3, "requisitos": "Renta < 44.000 € + 6.000 € por hijo."},
        {"id": "mcdis", "nombre": "Discapacidad ≥ 65 %", "tipo": 3, "requisitos": "Vivienda habitual."}]},
    "RI": {"general": 7, "reducidos": [
        {"id": "ri40", "nombre": "Primera vivienda de menor de 40", "tipo": 4, "requisitos": "3 % en los municipios del anexo I."},
        {"id": "rifn", "nombre": "Familia numerosa", "tipo": 5, "requisitos": "3 % con requisitos adicionales."},
        {"id": "ridis", "nombre": "Discapacidad ≥ 33 %", "tipo": 5, "requisitos": "Vivienda habitual."}]},
    "CE": {"general": 3, "reducidos": [], "nota": "Tipo estatal del 6 % con bonificación del 50 %."},
    "ML": {"general": 3, "reducidos": [], "nota": "Tipo estatal del 6 % con bonificación del 50 %."},
}

# ── Sucesiones y Donaciones ────────────────────────────────────────────────
TARIFA_ISD = [  # art. 21.2 Ley 29/1987: base liquidable desde, cuota íntegra, tipo sobre el resto
    (0.00, 0.00, 7.65), (7993.46, 611.50, 8.50), (15980.91, 1290.43, 9.35), (23968.36, 2037.26, 10.20),
    (31955.81, 2851.98, 11.05), (39943.26, 3734.59, 11.90), (47930.72, 4685.10, 12.75), (55918.17, 5703.50, 13.60),
    (63905.62, 6789.79, 14.45), (71893.07, 7943.98, 15.30), (79880.52, 9166.06, 16.15), (119757.67, 15606.22, 18.70),
    (159634.83, 23063.25, 21.25), (239389.13, 40011.04, 25.50), (398777.54, 80655.08, 29.75), (797555.08, 199291.40, 34.00),
]
COEFICIENTES_ISD = {  # art. 22.2: por patrimonio preexistente (4 tramos)
    "I_II": [1.0, 1.05, 1.10, 1.20], "III": [1.5882, 1.6676, 1.7471, 1.9059], "IV": [2.0, 2.1, 2.2, 2.4],
}
PATRIMONIO_TRAMOS = ["Hasta 402.678 €", "De 402.678 a 2.007.380 €", "De 2.007.380 a 4.020.771 €", "Más de 4.020.771 €"]


def B(bonif, nota="", hasta=None, resto=0):
    """Bonificación sobre la cuota para grupos I y II (y `resto` para III/IV). `hasta`: si la base liquidable
    lo supera, la calculadora no da cifra (régimen propio por encima del límite)."""
    return {"bonif_I_II": bonif, "bonif_resto": resto, "nota": nota, "hasta": hasta}


ISD = {
    "AN": {"sucesion": dict(B(99, "Reducción autonómica de 1.000.000 € y bonificación del 99 % para cónyuge, hijos y padres."),
                            reduccion_I_II=1000000),
           "donacion": B(99, "Bonificación del 99 % en documento público.")},
    "AR": {"sucesion": {"propio": "Reducción del 100 % hasta 500.000 € (sumando todas las reducciones; 3 M€ para hijos menores).",
                        "exento_hasta": 500000, "nota": "Por encima de 500.000 € se tributa por el exceso con reglas propias."},
           "donacion": B(99, "Reducción del 100 % hasta 100.000 €; bonificación del 99 % para el grupo II si la base (5 años) ≤ 500.000 €.",
                         hasta=500000)},
    "AS": {"sucesion": {"propio": "Reducción de 300.000 € y escala propia agravada (del 21,25 % al 36,5 %). Asturias es de las comunidades donde más se paga de padres a hijos."},
           "donacion": {"propio": "Escala propia del 2 % al 36,5 % (2 % hasta 150.000 €) en documento público y con patrimonio del donatario ≤ 402.678 €."}},
    "IB": {"sucesion": B(100, "Bonificación del 100 %."), "donacion": B(100, "Bonificación del 100 %.")},
    "CN": {"sucesion": B(99.9, "Bonificación del 99,9 %."), "donacion": B(99.9, "Bonificación del 99,9 %.")},
    "CB": {"sucesion": B(100, "Bonificación del 100 %."), "donacion": B(100, "Bonificación del 100 %.")},
    "CL": {"sucesion": B(99, "Bonificación del 99 %."), "donacion": B(99, "Bonificación del 99 % en documento público y con origen de fondos justificado.")},
    "CM": {"sucesion": {"bonif_tramos": [[175000, 100], [225000, 95], [275000, 90], [300000, 85], [None, 80]],
                        "nota": "Bonificación según la base liquidable: del 100 % (menos de 175.000 €) al 80 % (300.000 € o más)."},
           "donacion": {"bonif_tramos": [[120000, 95], [240000, 90], [None, 85]],
                        "nota": "Bonificación según la base liquidable: 95 %, 90 % u 85 %."}},
    "CT": {"sucesion": {"propio": "Reducción de 100.000 € para cónyuge e hijos, bonificación por tramos (del 99 % al 20 % para hijos) y tarifa propia del 7 % al 32 %."},
           "donacion": {"tarifa": T((0, 200000, 5), (200000, 600000, 7), (600000, None, 9)),
                        "nota": "Tarifa propia para grupos I y II en escritura pública: 5 %, 7 % y 9 %."}},
    "VC": {"sucesion": B(99, "Bonificación del 99 % para grupos I y II."),
           "donacion": B(99, "Bonificación del 99 % (grupo II si la base de 5 años ≤ 500.000 €).", hasta=500000)},
    "EX": {"sucesion": B(99, "Bonificación del 99 %."),
           "donacion": B(99, "Bonificación del 99 % hasta 300.000 € de base liquidable; 50 % sobre el exceso hasta 600.000 €.", hasta=300000)},
    "GA": {"sucesion": {"propio": "Reducción de 1.000.000 € para grupos I y II, tarifa propia del 5 % al 18 % y deducción del 99 % para el grupo I.",
                        "exento_hasta": 1000000},
           "donacion": {"tarifa": T((0, 200000, 5), (200000, 600000, 7), (600000, None, 9)),
                        "nota": "Tarifa propia para grupos I y II en escritura pública: 5 %, 7 % y 9 %."}},
    "MD": {"sucesion": B(99, "Bonificación del 99 % (50 % para el grupo III).", resto=0),
           "donacion": B(99, "Bonificación del 99 %; exentas las donaciones de hasta 1.000 €.")},
    "MC": {"sucesion": B(99, "Deducción del 99 %."), "donacion": B(99, "Deducción del 99 % en documento público y con fondos justificados.")},
    "RI": {"sucesion": B(99, "Deducción del 99 %."), "donacion": B(99, "Deducción del 99 %.")},
    "CE": {"sucesion": B(99, "Bonificación del 99 % si el fallecido residía en Ceuta al menos 5 años."), "donacion": B(50, "Bonificación del 50 %.")},
    "ML": {"sucesion": B(99, "Bonificación del 99 % si el fallecido residía en Melilla al menos 5 años."), "donacion": B(50, "Bonificación del 50 %.")},
}
ISD["MD"]["sucesion"]["bonif_III"] = 50

# ── Plusvalía municipal ────────────────────────────────────────────────────
COEF_RDL_8_2023 = [0.15, 0.15, 0.14, 0.14, 0.16, 0.18, 0.19, 0.20, 0.19, 0.15, 0.12,
                   0.10, 0.09, 0.09, 0.09, 0.09, 0.10, 0.13, 0.17, 0.23, 0.40]
COEF_RDL_29_2026 = [0.17, 0.16, 0.16, 0.17, 0.17, 0.19, 0.21, 0.23, 0.24, 0.25, 0.22,
                    0.18, 0.14, 0.12, 0.11, 0.11, 0.11, 0.11, 0.13, 0.20, 0.30]
PLUSVALIA = {
    "tipo_max": 30,
    "tablas": [
        {"desde": "2000-01-01", "norma": "RDL 8/2023, art. 24", "coef": COEF_RDL_8_2023},
        {"desde": "2026-12-01", "norma": "RDL 29/2026, art. 10 (pendiente de convalidación)", "coef": COEF_RDL_29_2026},
    ],
}


def para_js() -> dict:
    isd_ccaa = {}
    for k, v in ISD.items():
        isd_ccaa[k] = v
    return {
        "itp": ITP,
        "isd": {"tarifa": [{"base": b, "cuota": c, "tipo": t} for b, c, t in TARIFA_ISD],
                "reducciones": {"I": 15956.87, "II": 15956.87, "III": 7993.46, "IV": 0},
                "reduccion_I_por_anio": 3990.72, "reduccion_I_max": 47858.59,
                "vivienda_habitual": {"pct": 95, "limite": 122606.47},
                "coeficientes": COEFICIENTES_ISD, "ccaa": isd_ccaa},
        "plusvalia": PLUSVALIA,
    }
