# Idealisto

Marketplace de oportunidades de inversión inmobiliaria en España.

- El **publicador** (propietario legítimo o encargado acreditado) publica gratis, bajo protocolo de validación de titularidad.
- El **inversor** paga suscripción por ver, analizar y contactar.
- Cualquier tipología de bien inmueble **excepto NPL/REO** (ese mercado es de [inversionnpl.com](https://inversionnpl.com)).

## Estado

Fase 0 — landing de preventa con lista de espera funcionando.

## Estructura

```
idealisto/
├── public/                # Landing estática servida por nginx (+ privacidad.html)
├── server/index.ts        # Waitlist API (Bun + bun:sqlite, puerto 3201, sin deps)
├── run_waitlist.sh        # Arranca el servidor en screen (se ejecuta EN el servidor)
├── data/                  # waitlist.sqlite (solo en servidor, no en git)
└── nginx/
    └── idealisto.es.conf  # REFERENCIA — el archivo vivo lo gestiona certbot; editar in-place
```

## Servidor

- VPS: 207.180.235.200 (mismo que Orenes/nplinvest), usuario `orenes`
- Repo en servidor: `~/idealisto/`
- Deploy estático: `git pull` en el servidor
- Waitlist: screen `idealisto-waitlist` → `./run_waitlist.sh` para (re)arrancar
- Consultar apuntados: `~/.bun/bin/bun -e "console.table(new (require('bun:sqlite').Database)('/home/orenes/idealisto/data/waitlist.sqlite').query('SELECT email,role,created_at FROM waitlist ORDER BY id DESC').all())"`
