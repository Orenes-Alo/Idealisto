"""Informe completo de pago (4,70 € + IVA): el Word del motor de Testigos de Orenes.

Flujo: el usuario (con sesión) pide el informe de una valoración suya →
Checkout de Stripe creado por Orenes (cuenta de InversionNPL, mismo titular) →
vuelta a /informe/ok → Idealisto verifica el pago contra Orenes (sin webhook) →
genera el Word en segundo plano (Orenes tarda 30-90 s: Catastro, IGN, OSM, IA)
→ se guarda en data/informes/ y se envía el aviso con el enlace de descarga.
"""
from __future__ import annotations

import sqlite3
import threading
import time
from pathlib import Path

from . import orenes
from .cuentas import SITE, email_html

PRECIO_BASE = 4.70
PRECIO_TOTAL = 5.69  # 4,70 € + 21 % IVA (redondeo de Stripe a céntimos: 569)


class Informes:
    def __init__(self, con: sqlite3.Connection, lock: threading.Lock, carpeta: Path):
        self.con, self.lock, self.carpeta = con, lock, carpeta
        carpeta.mkdir(parents=True, exist_ok=True)
        with lock:
            con.executescript("""
            CREATE TABLE IF NOT EXISTS valoracion_usuario(
              id INTEGER PRIMARY KEY, usuario_id TEXT NOT NULL, rc TEXT NOT NULL, datos TEXT NOT NULL, creada REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS compra(
              id INTEGER PRIMARY KEY, usuario_id TEXT NOT NULL, valoracion_id INTEGER NOT NULL, rc TEXT NOT NULL,
              stripe_session TEXT UNIQUE, estado TEXT NOT NULL DEFAULT 'pendiente', creada REAL NOT NULL,
              pagada REAL, lista REAL, error TEXT, intentos INTEGER NOT NULL DEFAULT 0);
            """)
            con.commit()
        with lock:
            cols = {r[1] for r in con.execute("PRAGMA table_info(compra)")}
            if "generando_desde" not in cols:
                con.execute("ALTER TABLE compra ADD COLUMN generando_desde REAL")
                con.commit()

    # ── valoraciones del usuario ───────────────────────────────────────────
    def guardar_valoracion(self, usuario_id: str, rc: str, datos_json: str) -> int:
        with self.lock:
            cur = self.con.execute("INSERT INTO valoracion_usuario(usuario_id, rc, datos, creada) VALUES(?,?,?,?)",
                                   (usuario_id, rc, datos_json, time.time()))
            self.con.commit()
            return cur.lastrowid

    def valoracion(self, vid: int, usuario_id: str):
        with self.lock:
            return self.con.execute("SELECT id, rc, datos, creada FROM valoracion_usuario WHERE id=? AND usuario_id=?",
                                    (vid, usuario_id)).fetchone()

    # ── compra ─────────────────────────────────────────────────────────────
    def iniciar(self, usuario: dict, vid: int) -> str:
        v = self.valoracion(vid, usuario["id"])
        if not v:
            raise ValueError("valoracion")
        with self.lock:
            cur = self.con.execute("INSERT INTO compra(usuario_id, valoracion_id, rc, creada) VALUES(?,?,?,?)",
                                   (usuario["id"], vid, v[1], time.time()))
            self.con.commit()
            cid = cur.lastrowid
        r = orenes.llamar("POST", "/internal/idealisto/checkout", {
            "email": usuario["email"], "rc": v[1], "ref": f"compra-{cid}",
            "success_url": f"{SITE}/informe/ok?c={cid}&session_id={{CHECKOUT_SESSION_ID}}",
            "cancel_url": f"{SITE}/mis-informes/?cancelado={cid}"}, timeout=30)
        with self.lock:
            self.con.execute("UPDATE compra SET stripe_session=? WHERE id=?", (r["id"], cid))
            self.con.commit()
        return r["url"]

    def compra(self, cid: int, usuario_id: str):
        with self.lock:
            f = self.con.execute("""SELECT c.id, c.rc, c.estado, c.stripe_session, c.creada, c.pagada, c.lista, c.error,
                                           v.datos FROM compra c JOIN valoracion_usuario v ON v.id = c.valoracion_id
                                     WHERE c.id=? AND c.usuario_id=?""", (cid, usuario_id)).fetchone()
        return dict(zip(("id", "rc", "estado", "session", "creada", "pagada", "lista", "error", "datos"), f)) if f else None

    def compras(self, usuario_id: str):
        with self.lock:
            filas = self.con.execute("""SELECT c.id, c.rc, c.estado, c.creada, c.lista, v.datos FROM compra c
                                          JOIN valoracion_usuario v ON v.id = c.valoracion_id
                                         WHERE c.usuario_id=? AND c.estado != 'pendiente' ORDER BY c.creada DESC""",
                                     (usuario_id,)).fetchall()
        return [dict(zip(("id", "rc", "estado", "creada", "lista", "datos"), f)) for f in filas]

    def verificar_pago(self, cid: int, usuario: dict) -> dict | None:
        """Si Stripe confirma el pago, marca pagada y lanza la generación. Idempotente."""
        c = self.compra(cid, usuario["id"])
        if not c:
            return None
        if c["estado"] == "pendiente" and c["session"]:
            s = orenes.llamar("GET", f"/internal/idealisto/checkout/{c['session']}", timeout=20)
            if s.get("pagado") and s.get("ref") == f"compra-{cid}":
                with self.lock:
                    self.con.execute("UPDATE compra SET estado='pagada', pagada=? WHERE id=? AND estado='pendiente'",
                                     (time.time(), cid))
                    self.con.commit()
                threading.Thread(target=self._actividad, args=(usuario["email"],), daemon=True).start()
                c = self.compra(cid, usuario["id"])
        if c["estado"] in ("pagada", "error", "generando") and self._reclamar(cid):
            threading.Thread(target=self._generar, args=(cid, usuario), daemon=True).start()
        return self.compra(cid, usuario["id"])

    def _reclamar(self, cid: int) -> bool:
        """Paso atómico a 'generando' (hay 2 workers de uvicorn): pagada, error con < 3 intentos,
        o 'generando' colgado más de 6 minutos."""
        with self.lock:
            cur = self.con.execute(
                """UPDATE compra SET estado='generando', intentos=intentos+1, error=NULL, lista=NULL,
                          pagada=COALESCE(pagada, ?), creada=creada
                    WHERE id=? AND (estado='pagada' OR (estado='error' AND intentos < 3)
                          OR (estado='generando' AND COALESCE(lista, 0) = 0 AND ? - COALESCE(generando_desde, 0) > 360))""",
                (time.time(), cid, time.time()))
            if cur.rowcount:
                self.con.execute("UPDATE compra SET generando_desde=? WHERE id=?", (time.time(), cid))
            self.con.commit()
            return cur.rowcount == 1

    def _actividad(self, email: str):
        try:
            orenes.llamar("POST", "/internal/idealisto/actividad", {"email": email, "tipo": "informe"}, timeout=10)
        except orenes.OrenesError:
            pass

    def ruta(self, cid: int) -> Path:
        return self.carpeta / f"informe-{cid}.docx"

    def _generar(self, cid: int, usuario: dict):
        try:
            with self.lock:
                fila = self.con.execute("SELECT rc FROM compra WHERE id=?", (cid,)).fetchone()
            buf = orenes.llamar("POST", "/internal/idealisto/informe", {"rc": fila[0]}, timeout=240, crudo=True)
            if not buf.startswith(b"PK"):
                raise RuntimeError("respuesta no es un .docx")
            tmp = self.ruta(cid).with_suffix(".tmp")
            tmp.write_bytes(buf)
            tmp.replace(self.ruta(cid))
            with self.lock:
                self.con.execute("UPDATE compra SET estado='listo', lista=? WHERE id=?", (time.time(), cid))
                self.con.commit()
            try:
                orenes.llamar("POST", "/internal/idealisto/enviar", {
                    "tipo": "informe", "to": usuario["email"], "subject": "Tu informe de valoración está listo",
                    "html": email_html(usuario.get("nombre") or "",
                                       f"Tu informe completo de la referencia catastral {fila[0]} ya está listo. "
                                       f"Importe: 4,70 € + 21 % IVA = 5,69 €. Puedes descargarlo cuando quieras desde «Mis informes».",
                                       "Descargar el informe", f"{SITE}/mis-informes/",
                                       '<p style="margin:0 0 12px;color:#5a6b69;font-size:13px">Si necesitas factura, responde a este email con tus datos fiscales.</p>')},
                    timeout=20)
            except orenes.OrenesError as e:
                print("[idealisto] aviso de informe listo falló:", e)
        except Exception as e:  # noqa: BLE001 — se reintenta desde /informe/ok o /mis-informes (hasta 3 intentos)
            with self.lock:
                self.con.execute("UPDATE compra SET estado='error', error=? WHERE id=?", (str(e)[:300], cid))
                self.con.commit()
            print(f"[idealisto] informe {cid} falló:", e)
