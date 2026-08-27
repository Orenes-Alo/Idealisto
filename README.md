# Idealisto

Marketplace de oportunidades de inversión inmobiliaria en España.

- El **publicador** (propietario legítimo o encargado acreditado) publica gratis, bajo protocolo de validación de titularidad.
- El **inversor** paga suscripción por ver, analizar y contactar.
- Cualquier tipología de bien inmueble **excepto NPL/REO** (ese mercado es de [inversionnpl.com](https://inversionnpl.com)).

## Estado

Fase 0 — dominio conectado, landing placeholder.

## Estructura

```
idealisto/
├── public/              # Landing estática servida por nginx
└── nginx/
    └── idealisto.es.conf  # Server block (pre-certbot; certbot añade SSL en el servidor)
```

## Servidor

- VPS: 207.180.235.200 (mismo que Orenes/nplinvest), usuario `orenes`
- Repo en servidor: `~/idealisto/`
- Deploy: `git pull` en el servidor (contenido estático)
