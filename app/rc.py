"""Referencia catastral: normalización y validación (formato + dígitos de control)."""
from __future__ import annotations

import re

_RC_ALPHABET = "ABCDEFGHIJKLMNÑOPQRSTUVWXYZ0123456789"
_RC_CHECK = "MQWERTYUIOPASDFGHJKLBZX"
_RC_WEIGHTS = (13, 15, 12, 5, 4, 17, 9, 21, 3, 7, 1)


def normalizar_rc(raw: str) -> str:
    return re.sub(r"[\s\-\.\/]", "", (raw or "")).upper()


def _rc_digit(chunk: str) -> str:
    total = sum(
        w * (int(c) if c.isdigit() else _RC_ALPHABET.find(c) + 1)
        for w, c in zip(_RC_WEIGHTS, chunk)
    )
    return _RC_CHECK[total % 23]


def digitos_control(rc18: str) -> str:
    return _rc_digit(rc18[0:7] + rc18[14:18]) + _rc_digit(rc18[7:14] + rc18[14:18])


def validar_rc(rc: str) -> tuple[bool, str]:
    """Devuelve (ok, mensaje). rc ya normalizada."""
    if not rc:
        return False, "Introduce la referencia catastral."
    if len(rc) == 14 and re.fullmatch(r"[0-9A-Z]{14}", rc):
        return False, ("Esa es la referencia de la finca (14 caracteres). Necesitamos los 20 "
                       "caracteres del inmueble concreto: los encontrarás en el recibo del IBI.")
    if not re.fullmatch(r"[0-9A-ZÑ]{20}", rc):
        return False, "La referencia catastral tiene 20 caracteres (letras y números)."
    if rc[18:20] != digitos_control(rc[:18]):
        return False, ("Los dos últimos caracteres no cuadran con el resto. "
                       "Revisa que no falte o sobre ninguna letra.")
    return True, ""
