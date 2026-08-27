// Waitlist de Idealisto — servidor mínimo (Bun + bun:sqlite, sin dependencias).
// Nginx proxya /api/ → este puerto. La BD vive en ~/idealisto/data/waitlist.sqlite.
import { Database } from "bun:sqlite";
import { mkdirSync } from "node:fs";

const PORT = Number(process.env.PORT || 3201);
const DATA_DIR = new URL("../data/", import.meta.url).pathname;
mkdirSync(DATA_DIR, { recursive: true });

const db = new Database(`${DATA_DIR}waitlist.sqlite`);
db.run(`CREATE TABLE IF NOT EXISTS waitlist (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT NOT NULL UNIQUE,
  role TEXT NOT NULL DEFAULT 'invertir',
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  user_agent TEXT,
  ip TEXT
)`);

const insert = db.prepare(
  `INSERT INTO waitlist (email, role, user_agent, ip) VALUES (?, ?, ?, ?)
   ON CONFLICT(email) DO UPDATE SET role = excluded.role`
);

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

Bun.serve({
  port: PORT,
  async fetch(req) {
    const url = new URL(req.url);

    if (url.pathname === "/health") {
      return Response.json({ ok: true });
    }

    if (url.pathname === "/api/waitlist" && req.method === "POST") {
      let body: any;
      try {
        body = await req.json();
      } catch {
        return Response.json({ ok: false }, { status: 400 });
      }
      // Honeypot: los bots rellenan el campo oculto "web"
      if (body.web) return Response.json({ ok: true });

      const email = String(body.email || "").trim().toLowerCase();
      const role = body.role === "publicar" ? "publicar" : "invertir";
      if (!EMAIL_RE.test(email) || email.length > 254) {
        return Response.json({ ok: false, error: "email" }, { status: 400 });
      }

      const ua = (req.headers.get("user-agent") || "").slice(0, 300);
      const ip = req.headers.get("x-real-ip") || req.headers.get("x-forwarded-for") || "";
      insert.run(email, role, ua, ip.slice(0, 100));
      console.log(`[waitlist] ${role} ${email}`);
      return Response.json({ ok: true });
    }

    return new Response("Not found", { status: 404 });
  },
});

console.log(`Idealisto waitlist server en :${PORT}`);
