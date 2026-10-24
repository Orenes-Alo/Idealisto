# Idealisto

Tasador gratuito de inmuebles por referencia catastral en idealisto.es (desde 24-10-2026; antes era una landing de preventa de marketplace, retirada).

## Repo

- `app/idealisto.py`: FastAPI (puerto 3201). Home-herramienta, `/api/valorar`, `/api/lead`, páginas secundarias, robots/sitemap/llms.
- `app/contenido.py`: pilares SEO, metodología y textos legales (titular: Orenes & Asociados). `app/home.html` + `app/estilo.css`: la home.
- La valoración NO se calcula aquí: `POST /internal/avm/rc` del backend de Orenes (mismo VPS, puertos 3001/3002 blue/green) con `Authorization: Bearer $IDEALISTO_AVM_TOKEN`. Es el mismo precio justo que Testigos de venta; no crear un motor paralelo.
- Nunca mostrar cifras inventadas: sin AVM, error 503. Si no hay comparables, se dice.
- La RC consultada no se guarda en claro (hash). Leads solo si hay email activo (RESEND_API_KEY + RESEND_FROM).
- Tests: `python -m unittest discover -s tests` desde la raíz.

## Servidor

- `~/idealisto` en 207.180.235.200; deploy = `git pull` + `sudo systemctl restart idealisto`.
- venv en `~/idealisto/.venv` (`pip install -r requirements.txt`); secretos en `~/idealisto/.env` (no versionado).
- Servicio systemd `idealisto` (`deploy/idealisto.service`), arranca solo tras reinicio.
- nginx vivo gestionado por certbot (`sites-available/idealisto.es`): editar in-place, nunca copiar encima. `location /` hace proxy a 127.0.0.1:3201.
- `data/waitlist.sqlite` es la lista de espera antigua (1 inscrito); no se usa ni se borra.
