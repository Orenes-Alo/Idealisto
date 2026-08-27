# Idealisto

Lee y aplica DESIGN.md antes de escribir o modificar cualquier UI.

## Repo

- Marketplace de oportunidades inmobiliarias fuera de mercado. Todo salvo NPL/REO (eso es inversionnpl.com).
- Fase 0: landing de preventa estática (`public/`) + waitlist API (`server/index.ts`, Bun + bun:sqlite, puerto 3201).
- Deploy: `git pull` en `~/idealisto` del VPS 207.180.235.200. Waitlist: `./run_waitlist.sh` (screen `idealisto-waitlist`).
- nginx vivo gestionado por certbot: editar in-place en sites-available, nunca copiar el conf del repo encima.
