"""Cuentas de Idealisto: registro (nombre, email, teléfono), acceso por enlace y sesiones.

Sin contraseñas: el registro y cada inicio de sesión envían un enlace de un
solo uso (24 h). La primera vez que se usa el enlace de verificación, el
usuario pasa a lead de InversionNPL (POST /internal/idealisto/lead) y entra en
su cadena de emails (base legal: interés legítimo, mismo titular; baja en
cada email). Los emails salen por el backend de Orenes (remitente
inversionnpl.com, decisión del usuario 25-10-2026).
"""
from __future__ import annotations

import hashlib
import re
import secrets
import sqlite3
import threading
import time
import uuid
from datetime import datetime, timezone
from html import escape

from . import orenes

SITE = "https://idealisto.es"
COOKIE = "idealisto_sesion"
SESION_DIAS = 365
ENLACE_HORAS = 24
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$")


def _h(t: str) -> str:
    return hashlib.sha256(t.encode()).hexdigest()


def ahora() -> float:
    return time.time()


def normalizar_telefono(raw: str) -> str | None:
    t = re.sub(r"[\s\-\.\(\)]", "", raw or "")
    if t.startswith("00"):
        t = "+" + t[2:]
    if re.fullmatch(r"[6789]\d{8}", t):
        return "+34" + t
    if re.fullmatch(r"\+\d{8,15}", t):
        return t
    return None


class Cuentas:
    def __init__(self, con: sqlite3.Connection, lock: threading.Lock):
        self.con, self.lock = con, lock
        with lock:
            con.executescript("""
            CREATE TABLE IF NOT EXISTS usuario(
              id TEXT PRIMARY KEY, email TEXT NOT NULL UNIQUE, nombre TEXT, telefono TEXT,
              creado REAL NOT NULL, verificado REAL, ultimo_acceso REAL, lead_enviado REAL);
            CREATE TABLE IF NOT EXISTS enlace(
              hash TEXT PRIMARY KEY, usuario_id TEXT NOT NULL, destino TEXT, expira REAL NOT NULL, usado REAL);
            CREATE TABLE IF NOT EXISTS sesion(
              hash TEXT PRIMARY KEY, usuario_id TEXT NOT NULL, creada REAL NOT NULL, expira REAL NOT NULL);
            """)
            con.commit()

    # ── consultas ──────────────────────────────────────────────────────────
    def por_email(self, email: str):
        with self.lock:
            return self.con.execute("SELECT id, email, nombre, telefono, verificado, lead_enviado FROM usuario WHERE email=?",
                                    (email.lower(),)).fetchone()

    def por_sesion(self, token: str | None):
        if not token:
            return None
        with self.lock:
            fila = self.con.execute(
                """SELECT u.id, u.email, u.nombre, u.telefono FROM sesion s JOIN usuario u ON u.id = s.usuario_id
                    WHERE s.hash=? AND s.expira > ? AND u.verificado IS NOT NULL""", (_h(token), ahora())).fetchone()
        return dict(zip(("id", "email", "nombre", "telefono"), fila)) if fila else None

    # ── registro y acceso ──────────────────────────────────────────────────
    def registrar(self, nombre: str, email: str, telefono: str, destino: str) -> str:
        """Crea (o actualiza si aún no estaba verificado) y envía el enlace. Devuelve 'verificacion' o 'acceso'."""
        email = email.strip().lower()
        u = self.por_email(email)
        with self.lock:
            if not u:
                uid = str(uuid.uuid4())
                self.con.execute("INSERT INTO usuario(id,email,nombre,telefono,creado) VALUES(?,?,?,?,?)",
                                 (uid, email, nombre, telefono, ahora()))
            else:
                uid = u[0]
                if not u[4]:  # sin verificar: se puede corregir nombre y teléfono
                    self.con.execute("UPDATE usuario SET nombre=?, telefono=? WHERE id=?", (nombre, telefono, uid))
            self.con.commit()
        tipo = "acceso" if (u and u[4]) else "verificacion"
        self._enviar_enlace(uid, email, nombre or (u[2] if u else ""), destino, tipo)
        return tipo

    def pedir_acceso(self, email: str, destino: str) -> bool:
        u = self.por_email(email)
        if not u:
            return False
        self._enviar_enlace(u[0], u[1], u[2] or "", destino, "acceso" if u[4] else "verificacion")
        return True

    def _enviar_enlace(self, uid: str, email: str, nombre: str, destino: str, tipo: str):
        token = secrets.token_urlsafe(32)
        with self.lock:
            self.con.execute("INSERT INTO enlace(hash,usuario_id,destino,expira) VALUES(?,?,?,?)",
                             (_h(token), uid, destino, ahora() + ENLACE_HORAS * 3600))
            self.con.commit()
        url = f"{SITE}/acceso?t={token}"
        if tipo == "verificacion":
            asunto = "Confirma tu email y mira la valoración"
            cuerpo = ("Confirma tu email para ver la valoración de tu inmueble. El enlace caduca en 24 horas y solo se puede usar una vez.")
            boton = "Confirmar y ver la valoración"
        else:
            asunto = "Tu enlace para entrar en Idealisto"
            cuerpo = "Pulsa el botón para entrar en Idealisto. El enlace caduca en 24 horas y solo se puede usar una vez."
            boton = "Entrar en Idealisto"
        orenes.llamar("POST", "/internal/idealisto/enviar", {
            "tipo": tipo, "to": email, "subject": asunto, "html": email_html(nombre, cuerpo, boton, url)}, timeout=20)

    def consumir_enlace(self, token: str):
        """Valida el enlace, marca verificado y crea sesión. Devuelve (sesion_token, destino, usuario, primera_vez) o None."""
        with self.lock:
            fila = self.con.execute("SELECT usuario_id, destino, expira, usado FROM enlace WHERE hash=?", (_h(token),)).fetchone()
            if not fila or fila[3] or fila[2] < ahora():
                return None
            uid, destino = fila[0], fila[1]
            self.con.execute("UPDATE enlace SET usado=? WHERE hash=?", (ahora(), _h(token)))
            u = self.con.execute("SELECT email, nombre, telefono, verificado FROM usuario WHERE id=?", (uid,)).fetchone()
            primera = u[3] is None
            self.con.execute("UPDATE usuario SET verificado=COALESCE(verificado, ?), ultimo_acceso=? WHERE id=?",
                             (ahora(), ahora(), uid))
            sesion = secrets.token_urlsafe(32)
            self.con.execute("INSERT INTO sesion(hash,usuario_id,creada,expira) VALUES(?,?,?,?)",
                             (_h(sesion), uid, ahora(), ahora() + SESION_DIAS * 86400))
            self.con.commit()
        return sesion, destino, {"id": uid, "email": u[0], "nombre": u[1], "telefono": u[2]}, primera

    def cerrar_sesion(self, token: str | None):
        if token:
            with self.lock:
                self.con.execute("DELETE FROM sesion WHERE hash=?", (_h(token),))
                self.con.commit()

    def enviar_lead(self, usuario: dict):
        """Alta del lead en InversionNPL (una vez). Best-effort: si falla, se reintenta en el siguiente acceso."""
        with self.lock:
            hecho = self.con.execute("SELECT lead_enviado FROM usuario WHERE id=?", (usuario["id"],)).fetchone()
        if hecho and hecho[0]:
            return
        try:
            orenes.llamar("POST", "/internal/idealisto/lead", {
                "email": usuario["email"], "nombre": usuario["nombre"], "telefono": usuario["telefono"],
                "idealisto_id": usuario["id"]}, timeout=20)
            with self.lock:
                self.con.execute("UPDATE usuario SET lead_enviado=? WHERE id=?", (ahora(), usuario["id"]))
                self.con.commit()
        except orenes.OrenesError as e:
            print("[idealisto] lead a Orenes falló:", e)


def email_html(nombre: str, cuerpo: str, boton: str, url: str, extra: str = "") -> str:
    saludo = f"Hola {escape(nombre.split()[0])}," if nombre else "Hola,"
    return f"""<!doctype html><html lang="es"><body style="margin:0;background:#f7f4ee;font-family:Arial,Helvetica,sans-serif">
<table width="100%" cellpadding="0" cellspacing="0" role="presentation" style="background:#f7f4ee"><tr><td align="center" style="padding:28px 16px">
<table width="560" cellpadding="0" cellspacing="0" role="presentation" style="max-width:560px;width:100%;background:#fffdf9;border:1px solid #e4ddd0;border-radius:14px">
<tr><td style="padding:26px 28px 6px"><span style="display:inline-block;background:#0f3d3e;color:#f4c95d;font:700 18px Georgia,serif;width:34px;height:34px;line-height:34px;text-align:center;border-radius:8px">i</span>
<span style="font:700 20px Georgia,serif;color:#0f3d3e;vertical-align:middle;margin-left:8px">Idealisto</span></td></tr>
<tr><td style="padding:14px 28px 6px;color:#10201f;font-size:15px;line-height:1.6"><p style="margin:0 0 12px">{saludo}</p><p style="margin:0 0 12px">{escape(cuerpo)}</p>{extra}</td></tr>
<tr><td align="center" style="padding:10px 28px 24px"><a href="{escape(url)}" style="display:inline-block;background:#0f3d3e;color:#fff;text-decoration:none;font-weight:700;padding:14px 26px;border-radius:10px">{escape(boton)}</a></td></tr>
<tr><td style="padding:0 28px 22px;color:#5a6b69;font-size:12px;line-height:1.5">Si no has sido tú, ignora este email. Idealisto es un servicio de Orenes &amp; Asociados, titular también de InversionNPL.</td></tr>
</table></td></tr></table></body></html>"""
