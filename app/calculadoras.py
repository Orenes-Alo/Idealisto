"""Calculadoras: /calculadoras/ y /calculadoras/{itp,sucesiones-donaciones,plusvalia-municipal,rentabilidad-alquiler}/.

El cálculo va en static/calc.js; los datos fiscales salen de app/fiscal.py (una sola fuente).
"""
from __future__ import annotations

from . import fiscal

OPC_CCAA = "".join(f'<option value="{c}">{n}</option>' for c, n in fiscal.CCAA)


def num(name, label, ph="", step="1000", ayuda="", valor=""):
    return (f'<label>{label}<input type="number" name="{name}" inputmode="decimal" min="0" step="{step}" '
            f'placeholder="{ph}" value="{valor}">' + (f'<small>{ayuda}</small>' if ayuda else "") + "</label>")


def select(name, label, opciones, ayuda=""):
    return f'<label>{label}<select name="{name}">{opciones}</select>' + (f'<small>{ayuda}</small>' if ayuda else "") + "</label>"


def form(calc, campos):
    return (f'<form class="calc" data-calc="{calc}" novalidate><div class="calc-grid">{campos}</div>'
            '<div class="calc-out" aria-live="polite"></div></form>')


CALCS = {}

CALCS["itp"] = {
    "title": "Calcular ITP 2026 por comunidad autónoma (vivienda usada)",
    "desc": "Calcula el Impuesto de Transmisiones Patrimoniales de tu compra en 2026 con el tipo de tu comunidad, los tipos reducidos y el valor de referencia del Catastro.",
    "h1": "Calculadora de ITP 2026: cuánto pagas al comprar una vivienda usada",
    "nombre": "Calculadora de ITP",
    "respuesta": ("Al comprar una vivienda usada pagas el Impuesto de Transmisiones Patrimoniales (ITP): entre el 6 % y el 13 % "
                  "según la comunidad autónoma y el precio, con tipos reducidos para jóvenes, familias numerosas o vivienda "
                  "habitual. Se calcula sobre el mayor entre el precio escriturado y el valor de referencia del Catastro."),
    "form": form("itp",
                 select("ccaa", "Comunidad autónoma", OPC_CCAA)
                 + num("precio", "Precio de compra (€)", "200000")
                 + num("referencia", "Valor de referencia del Catastro (€)", "opcional",
                       ayuda='Si es mayor que el precio, se tributa por él. <a href="/valor-de-referencia/">Cómo consultarlo</a>.')
                 + select("reducido", "Tipo aplicable", '<option value="">Tipo general</option>')),
    "html": """
<h2>¿Cómo se calcula el ITP?</h2>
<p>La base imponible es el <strong>mayor</strong> entre el precio que firmas en la escritura y el <a href="/valor-de-referencia/">valor de referencia</a> que fija el Catastro para ese inmueble (art. 10 del Texto Refundido del ITP, en la redacción de la Ley 11/2021). Sobre esa base se aplica el tipo de tu comunidad autónoma, que puede ser:</p>
<ul>
  <li><strong>Único</strong>: un porcentaje sobre todo el valor (por ejemplo, el 7 % en Andalucía o el 6 % en Madrid).</li>
  <li><strong>Progresivo por tramos</strong>: cada parte del valor tributa a su tipo (Cataluña, Aragón, Illes Balears, Extremadura, Castilla y León).</li>
  <li><strong>Según el valor total</strong>: un solo tipo que depende del precio (Asturias y la Comunitat Valenciana).</li>
</ul>
<p>El ITP se paga en los 30 días hábiles siguientes a la escritura, con el modelo 600 de tu comunidad.</p>
<h2>¿Qué tipo de ITP se paga en cada comunidad en 2026?</h2>
__TABLA_ITP__
<p class="hint">Fuente: Ministerio de Hacienda, «Tributación Autonómica. Medidas 2026» (actualizado el 23-09-2026). País Vasco y Navarra tienen régimen foral y no se incluyen.</p>
""",
    "faq": [
        ("¿El ITP se paga sobre el precio o sobre el valor de referencia?",
         "Sobre el mayor de los dos. Si el valor de referencia del Catastro supera el precio escriturado, tributas por el valor de referencia."),
        ("¿Quién paga el ITP, el comprador o el vendedor?", "El comprador."),
        ("¿La vivienda nueva paga ITP?",
         "No. La primera entrega de una vivienda nueva paga IVA (10 %) y el Impuesto de Actos Jurídicos Documentados, no ITP."),
    ],
}

CALCS["sucesiones-donaciones"] = {
    "title": "Calculadora de Sucesiones y Donaciones 2026 por comunidad",
    "desc": "Estima cuánto pagas por heredar o recibir en donación un inmueble en 2026 según tu comunidad autónoma y tu parentesco, con el valor de referencia del Catastro.",
    "h1": "Calculadora del Impuesto de Sucesiones y Donaciones 2026",
    "nombre": "Calculadora de Sucesiones y Donaciones",
    "respuesta": ("Lo que pagas por heredar o recibir en donación un inmueble depende sobre todo de tu comunidad autónoma y del "
                  "parentesco: en la mayoría, hijos, cónyuges y padres tienen bonificaciones del 99 % o más, mientras que en "
                  "Asturias, Cataluña o Aragón (por encima de 500.000 €) se paga bastante más. El inmueble se valora como mínimo "
                  "por su valor de referencia del Catastro."),
    "form": form("sucesiones",
                 select("modo", "Operación", '<option value="sucesion">Herencia</option><option value="donacion">Donación</option>')
                 + select("ccaa", "Comunidad autónoma", OPC_CCAA,
                          "En herencias, la del último domicilio del fallecido; en donaciones de inmuebles, donde está el inmueble.")
                 + select("grupo", "Parentesco", '<option value="II">Hijo de 21 o más, cónyuge, padre o madre (grupo II)</option>'
                          '<option value="I">Hijo o nieto menor de 21 (grupo I)</option>'
                          '<option value="III">Hermano, sobrino, tío o familiar político (grupo III)</option>'
                          '<option value="IV">Primo o sin parentesco (grupo IV)</option>')
                 + '<div class="campo-edad" hidden>' + num("edad", "Edad del heredero", "15", "1") + "</div>"
                 + num("valor", "Valor del inmueble (€)", "250000",
                       ayuda='Valor de mercado. <a href="/#valorar">Calcúlalo con la referencia catastral</a>.')
                 + num("referencia", "Valor de referencia del Catastro (€)", "opcional")
                 + select("patrimonio", "Patrimonio previo del heredero", "".join(
                     f'<option value="{i}">{t}</option>' for i, t in enumerate(fiscal.PATRIMONIO_TRAMOS)))
                 + '<label class="campo-vivienda chk-calc"><input type="checkbox" name="vivienda"> Era la vivienda habitual del fallecido '
                   '<small>Reducción del 95 % (límite 122.606 € por heredero; hay que conservarla 10 años).</small></label>'),
    "html": """
<h2>¿Cómo se calcula el Impuesto de Sucesiones?</h2>
<ol>
  <li><strong>Valor del inmueble</strong>: el mayor entre el valor declarado y el valor de referencia del Catastro.</li>
  <li><strong>Reducciones</strong>: por parentesco (15.956,87 € para hijos, cónyuge y padres en la normativa estatal, que muchas comunidades mejoran) y, en herencias, del 95 % por la vivienda habitual del fallecido.</li>
  <li><strong>Tarifa</strong>: la estatal (del 7,65 % al 34 %) o la propia de la comunidad, multiplicada por un coeficiente según el parentesco y el patrimonio previo.</li>
  <li><strong>Bonificación autonómica</strong>: en la mayoría de comunidades, del 99 % o el 100 % para cónyuge, hijos y padres.</li>
</ol>
<p>El plazo para presentarlo es de 6 meses desde el fallecimiento (prorrogable otros 6) en herencias y de 30 días hábiles en donaciones.</p>
<h2>¿Dónde se paga más por heredar de padres a hijos en 2026?</h2>
__TABLA_ISD__
<p class="hint">Fuente: Ministerio de Hacienda, «Tributación Autonómica. Medidas 2026», y Ley 29/1987. Resumen orientativo: cada comunidad añade requisitos (documento público, residencia, mantenimiento) y reducciones propias.</p>
""",
    "faq": [
        ("¿Se paga Sucesiones por heredar la casa de los padres?",
         "Depende de la comunidad. En la mayoría, la bonificación del 99 % o más deja el impuesto en una cantidad pequeña; en Asturias, Cataluña o en herencias grandes en Aragón, la factura puede ser relevante."),
        ("¿Qué valor se declara al heredar un piso?",
         "Como mínimo, el valor de referencia del Catastro. Si el valor de mercado es mayor, se debe declarar el de mercado."),
        ("¿Es mejor heredar o recibir en donación?",
         "Depende de la comunidad: en algunas la donación tiene las mismas ventajas que la herencia y en otras no. Además, quien dona puede tributar en su IRPF por la ganancia y pagar la plusvalía municipal."),
    ],
}

CALCS["plusvalia-municipal"] = {
    "title": "Calcular la plusvalía municipal 2026 (método objetivo y real)",
    "desc": "Calcula la plusvalía municipal (IIVTNU) de la venta de tu vivienda con los coeficientes máximos vigentes y compara el método objetivo con el real.",
    "h1": "Calculadora de plusvalía municipal 2026",
    "nombre": "Calculadora de plusvalía municipal",
    "respuesta": ("La plusvalía municipal se paga al vender, heredar o donar un inmueble urbano. Se calcula multiplicando el valor "
                  "catastral del suelo por un coeficiente según los años de tenencia, o por la ganancia real si es menor, y aplicando "
                  "el tipo del ayuntamiento (máximo 30 %). Si vendes con pérdidas, no se paga."),
    "form": form("plusvalia",
                 num("vc_suelo", "Valor catastral del suelo (€)", "40000", "100", "Aparece en el recibo del IBI.")
                 + num("vc_total", "Valor catastral total (€)", "90000", "100", "Para el método real.")
                 + num("anios", "Años de tenencia", "8", "0.1", "Desde que lo compraste o heredaste.")
                 + num("tipo", "Tipo del ayuntamiento (%)", "30", "0.1", "Máximo 30 %. Consulta la ordenanza fiscal.")
                 + num("compra", "Precio de compra (€)", "opcional")
                 + num("venta", "Precio de venta (€)", "opcional")
                 + '<label>Fecha de la venta<input type="date" name="fecha"></label>'),
    "html": """
<h2>¿Cómo se calcula la plusvalía municipal?</h2>
<p>Desde el Real Decreto-ley 26/2021 hay dos métodos y pagas por el que dé <strong>menos</strong>:</p>
<ul>
  <li><strong>Objetivo</strong>: valor catastral del suelo × coeficiente por años de tenencia (los máximos los fija el Estado; tu ayuntamiento puede bajarlos).</li>
  <li><strong>Real</strong>: diferencia entre el precio de venta y el de compra, en la proporción que representa el suelo en el valor catastral.</li>
</ul>
<p>Si no hay ganancia (vendes por menos de lo que compraste), no se paga. Al resultado se aplica el tipo del ayuntamiento, como máximo el 30 %.</p>
<h2>Coeficientes máximos en 2026</h2>
__TABLA_PLUSVALIA__
<p class="hint">Hasta el 30-11-2026 rigen los coeficientes del RDL 8/2023; desde el 01-12-2026, los del RDL 29/2026, pendiente de convalidación en el Congreso. La calculadora aplica la tabla según la fecha de la venta. Fuente: BOE (art. 107 TRLRHL).</p>
""",
    "faq": [
        ("¿Quién paga la plusvalía municipal?", "En una venta, el vendedor. En una herencia o donación, quien recibe el inmueble."),
        ("¿Se paga plusvalía si vendo con pérdidas?",
         "No. Si el precio de venta es menor o igual que el de compra no hay incremento de valor y la operación no está sujeta (art. 104.5 TRLRHL)."),
        ("¿Dónde veo el valor catastral del suelo?", "En el recibo del IBI o en la Sede Electrónica del Catastro, con tu identificación."),
    ],
}

CALCS["rentabilidad-alquiler"] = {
    "title": "Calculadora de rentabilidad de alquiler: bruta y neta",
    "desc": "Calcula la rentabilidad bruta y neta de comprar un piso para alquilar, con gastos de compra, reforma, comunidad, IBI, seguro y periodos vacíos.",
    "h1": "Calculadora de rentabilidad de un piso en alquiler",
    "nombre": "Calculadora de rentabilidad de alquiler",
    "respuesta": ("La rentabilidad bruta es el alquiler de un año dividido entre el precio de compra. La neta resta los gastos "
                  "(comunidad, IBI, seguro, mantenimiento y meses sin inquilino) y divide entre la inversión total, incluidos "
                  "impuestos y reforma. En España, una rentabilidad bruta del 5 % al 7 % es habitual fuera de las grandes capitales."),
    "form": form("rentabilidad",
                 num("precio", "Precio de compra (€)", "180000")
                 + num("gastos_pct", "Impuestos y gastos de compra (%)", "10", "0.5", "ITP, notaría, registro y gestoría.", "10")
                 + num("reforma", "Reforma y mobiliario (€)", "0", "500")
                 + num("alquiler", "Alquiler mensual (€)", "850", "10",
                       'Orientación: el <a href="/precio-vivienda/">alquiler de referencia de tu municipio</a>.')
                 + num("comunidad", "Comunidad al mes (€)", "60", "5")
                 + num("ibi", "IBI al año (€)", "350", "10")
                 + num("seguro", "Seguro al año (€)", "200", "10")
                 + num("mantenimiento", "Mantenimiento (% del alquiler)", "5", "0.5", "", "5")
                 + num("vacio", "Tiempo vacío (% del año)", "5", "1", "", "5")),
    "html": """
<h2>Rentabilidad bruta y neta: diferencias</h2>
<ul>
  <li><strong>Bruta</strong> = alquiler anual / precio de compra. Sirve para comparar zonas rápidamente.</li>
  <li><strong>Neta</strong> = (alquiler anual − gastos) / inversión total. Es la que mide lo que realmente ganas antes de impuestos.</li>
</ul>
<p>Para saber si el precio de compra es razonable, <a href="/#valorar">valora el piso con su referencia catastral</a> y consulta el <a href="/precio-vivienda/">precio por zona</a>, que incluye el alquiler de referencia oficial y la rentabilidad bruta estimada de cada municipio.</p>
""",
    "faq": [
        ("¿Qué es una buena rentabilidad para un piso en alquiler?",
         "Depende de la zona y del riesgo: en grandes capitales caras es habitual una rentabilidad bruta del 3 % al 5 %, y en ciudades medianas, del 5 % al 7 %."),
        ("¿Los gastos de compra cuentan en la rentabilidad?",
         "En la neta, sí: el ITP, la notaría, el registro y la reforma forman parte de lo que inviertes."),
    ],
}


def _pct(x) -> str:
    return f"{x:g} %".replace(".", ",")


def _eur(x) -> str:
    return f"{int(x):,} €".replace(",", ".")


def tabla_itp() -> str:
    def desc(c):
        if c.get("tramos"):
            return " · ".join(_pct(t["tipo"]) + (f' hasta {_eur(t["hasta"])}' if t["hasta"] else " en el resto")
                              for t in c["tramos"])
        if c.get("unico"):
            return " · ".join(_pct(u["tipo"]) + (f' si vale ≤ {_eur(u["hasta"])}' if u["hasta"] else " si vale más")
                              for u in c["unico"])
        return _pct(c["general"])
    filas = "".join(
        f'<tr><td>{n}</td><td>{desc(fiscal.ITP[k])}</td>'
        f'<td>{"; ".join(r["nombre"] for r in fiscal.ITP[k]["reducidos"]) or "—"}</td></tr>'
        for k, n in fiscal.CCAA)
    return ('<div class="scroll"><table><thead><tr><th>Comunidad</th><th>Tipo general</th><th>Tipos reducidos principales</th></tr></thead>'
            f'<tbody>{filas}</tbody></table></div>')


def tabla_isd() -> str:
    def txt(v):
        return v.get("propio") or v.get("nota") or ""
    filas = "".join(f'<tr><td>{n}</td><td>{txt(fiscal.ISD[k]["sucesion"])}</td><td>{txt(fiscal.ISD[k]["donacion"])}</td></tr>'
                    for k, n in fiscal.CCAA)
    return ('<div class="scroll"><table><thead><tr><th>Comunidad</th><th>Herencias (hijos, cónyuge, padres)</th>'
            f'<th>Donaciones (hijos, cónyuge, padres)</th></tr></thead><tbody>{filas}</tbody></table></div>')


def tabla_plusvalia() -> str:
    a, b = fiscal.COEF_RDL_8_2023, fiscal.COEF_RDL_29_2026
    filas = "".join(f'<tr><td>{"Menos de 1" if i == 0 else ("20 o más" if i == 20 else i)}</td><td>{a[i]:.2f}</td><td>{b[i]:.2f}</td></tr>'.replace(".", ",")
                    for i in range(21))
    return ('<div class="scroll"><table><thead><tr><th>Años</th><th>Hasta 30-11-2026</th><th>Desde 01-12-2026</th></tr></thead>'
            f'<tbody>{filas}</tbody></table></div>')


TABLAS = {"__TABLA_ITP__": tabla_itp, "__TABLA_ISD__": tabla_isd, "__TABLA_PLUSVALIA__": tabla_plusvalia}
