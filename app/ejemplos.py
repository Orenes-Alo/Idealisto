"""Genera data/ejemplos.json: valoraciones reales para la landing, ANONIMIZADAS.

Solo se guardan municipio, provincia, uso, superficie, año y las cifras del motor;
nunca la dirección ni la referencia catastral.

Uso (en el servidor):  .venv/bin/python -m app.ejemplos RC1 RC2 RC3 ...
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

from . import orenes
from .idealisto import MESES, _uso

SALIDA = Path(__file__).resolve().parent.parent / "data" / "ejemplos.json"
CAMPOS = ("valor_central", "valor_min", "valor_max", "eur_m2", "cierre_estimado", "testigos", "confianza",
          "superficie_m2", "anio_construccion")


def main(rcs: list[str]):
    ejemplos = []
    for rc in rcs:
        try:
            d = orenes.llamar("POST", "/internal/avm/rc", {"rc": rc}, timeout=60)
        except orenes.OrenesError as e:
            print("sin valoración:", rc[:7] + "…", e.status)
            continue
        if d.get("tipo_amplio") in ("local", "nave"):
            continue
        ej = {k: d.get(k) for k in CAMPOS}
        ej.update({"uso": _uso(d.get("uso")), "municipio": (d.get("municipio") or "").split("/")[0].strip().title(),
                   "provincia": (d.get("provincia") or "").split("/")[0].strip().title()})
        ejemplos.append(ej)
        print("ok:", ej["municipio"], ej["uso"], ej["valor_central"])
    hoy = date.today()
    SALIDA.write_text(json.dumps({"fecha": hoy.isoformat(), "fecha_txt": f"{hoy.day} de {MESES[hoy.month - 1]} de {hoy.year}",
                                  "ejemplos": ejemplos}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(len(ejemplos), "ejemplos →", SALIDA)


if __name__ == "__main__":
    main(sys.argv[1:])
