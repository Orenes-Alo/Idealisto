# DESIGN.md — Dirección de arte "Expediente Reservado"

> Este archivo es la fuente de verdad visual del proyecto. Toda decisión de color,
> tipografía, espaciado o movimiento se deriva de aquí. Si algo no está en este
> documento, no se inventa: se pregunta.
>
> Uso con Claude Code: mantener en la raíz del repo y referenciarlo desde `CLAUDE.md`
> con la línea `Lee y aplica DESIGN.md antes de escribir o modificar cualquier UI.`

---

## 1. El sujeto

**Producto:** portal español de oportunidades inmobiliarias **fuera de mercado**.

**Dos audiencias, dos trabajos distintos:**

| | Inversor | Aportador |
|---|---|---|
| Quién es | Inversor particular o semiprofesional que ya compra inmuebles y está harto de competir en Idealista | Particular, agente, gestor de patrimonio o abogado que tiene un activo que no quiere publicar en abierto |
| Qué paga | Cuota mensual para acceder a los datos completos | Nada. Publicar es gratis |
| Qué necesita ver | Que hay inventario real, ahora, y suficiente para justificar la cuota | Que hay compradores solventes esperando y que nadie le va a saltar |
| Qué teme | Pagar por un catálogo vacío o por refritos de portales | Perder el control del activo o la comisión |

**Trabajo único de la home:** llevar a cada visitante a su puerta en menos de un scroll y demostrar, con inventario velado real, que el otro lado existe.

**El mundo del que sale la estética:** el expediente administrativo español. Papel manila, sello de caucho, registro de entrada, folio numerado, nota simple, referencia catastral, impreso con casillas, tachadura de documento reservado. No el mundo de "portal inmobiliario", que es el que hay que evitar.

---

## 2. Tesis de la dirección

**Cada oportunidad es un expediente reservado.** El visitante ve la carátula, el número de registro, la provincia y las cifras esenciales. Los datos que valen dinero están **literalmente censurados con una barra de tinta**. Suscribirse no es "desbloquear contenido": es que se levante la reserva del expediente.

La tachadura no es decoración. Es la mecánica del negocio hecha lenguaje visual, y es lo único audaz de la página. Todo lo demás es disciplinado y silencioso.

**Nota de calibración.** Esta dirección vive cerca de dos defaults conocidos de diseño generado por IA: el fondo crema con serif de alto contraste y acento terracota, y el layout tipo periódico con reglas finas y radio 0. Nos separamos de ellos así, y estas separaciones no son negociables:

- El papel es **manila amarillento sucio** (`#E8E0CE`), no crema pastel. Nunca `#F4F1EA` ni vecinos.
- El acento rojo es **rojo de cuño** (`#B23A2E`), saturado y oscuro. Nunca terracota cálido tipo `#D97757`.
- La estructura no es de periódico sino de **impreso administrativo**: campos etiquetados, casillas, líneas de puntos guía, anotaciones en el margen. Columnas de texto corrido tipo broadsheet: prohibidas.
- La serif de display es **Zodiak**, con personalidad propia, no una Didone genérica.

---

## 3. Tokens

### 3.1 Color

| Token | Hex | Uso |
|---|---|---|
| `paper` | `#E8E0CE` | Fondo global. Manila. |
| `paper-shade` | `#DBD2BC` | Paneles, filas alternas, zonas hundidas. |
| `ink` | `#17150F` | Texto principal. También la barra de tachadura. |
| `ink-soft` | `#5A544A` | Texto secundario, metadatos. |
| `archive` | `#8A8272` | Deshabilitado, bordes, líneas de guía. |
| `stamp` | `#B23A2E` | Sellos, estados críticos, un solo CTA por vista. |
| `seal` | `#2F4034` | Verde botella. Verificado, aprobado, confirmación. |

Reglas:

- Un único acento activo por vista. Si el `stamp` está en el CTA, no aparece en ningún otro sitio de esa pantalla.
- Prohibido cualquier gradiente de color. La única variación de fondo permitida es el grano.
- Estados de foco: contorno `ink` de 2px con offset 2px. Nunca un halo difuso.

### 3.2 Textura

Grano SVG sobre el fondo global, opacidad entre `0.06` y `0.10`, `mix-blend-mode: multiply`. Sin grano el manila parece un color plano de Tailwind y se cae toda la dirección.

```css
/* utilidad .paper-grain aplicada al <body> mediante ::after */
body::after {
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 1;
  opacity: 0.08;
  mix-blend-mode: multiply;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
}
```

### 3.3 Tipografía

| Rol | Familia | Fuente | Uso |
|---|---|---|---|
| Display | **Zodiak** | Fontshare | Titulares. Solo pesos 300 y 700, nunca intermedios. |
| Cuerpo | **Supreme** | Fontshare | Párrafos, botones, navegación. |
| Datos | **JetBrains Mono** | Google Fonts | Cifras, referencias, etiquetas de campo, sellos. |

```html
<link href="https://api.fontshare.com/v2/css?f[]=zodiak@300,700&f[]=supreme@400,500&display=swap" rel="stylesheet">
```

Reglas tipográficas, todas obligatorias:

- **Todas las cifras van en JetBrains Mono con `font-variant-numeric: tabular-nums`.** Precios, yields, superficies, referencias catastrales, contadores. Es lo que da el aire de documento y no de folleto.
- Las etiquetas de campo van en mono, `text-transform: uppercase`, `letter-spacing: 0.12em`, tamaño 11–12px, color `ink-soft`. Son etiquetas de impreso, no eyebrows decorativos.
- Saltos de escala de 3x como mínimo entre display y cuerpo. Un H1 de 96px sobre un cuerpo de 17px, no un 32px tímido.
- Zodiak nunca por debajo de 24px: a tamaño pequeño pierde carácter y gana ilegibilidad.
- Cuerpo con `max-width: 68ch` y `line-height: 1.6`.
- Sentence case en toda la interfaz. Mayúsculas solo en etiquetas de campo y sellos.

### 3.4 Espaciado y forma

- Retícula de 12 columnas con canal de 24px. **Asimetría obligatoria:** la división por defecto es 8/4 o 7/5, nunca 6/6 ni contenido centrado.
- Margen izquierdo ancho reservado para anotaciones marginales (número de folio, referencia, fecha de registro), como en un expediente real.
- Ritmo vertical: secciones separadas por `clamp(80px, 10vw, 160px)`. Dentro de una sección, escala 8/16/24/40/64.
- `--radius: 0` en todo. Sin excepciones. Las esquinas redondeadas son el primer síntoma de plantilla.
- Separadores: línea de 1px `archive`. Para zonas de formulario, línea de puntos (`border-bottom: 1px dotted`).
- Sombras: **ninguna**. La profundidad se consigue con `paper-shade` y con líneas.

### 3.5 Bloque `@theme` para Tailwind v4

```css
@import "tailwindcss";

@theme {
  --color-paper:        #E8E0CE;
  --color-paper-shade:  #DBD2BC;
  --color-ink:          #17150F;
  --color-ink-soft:     #5A544A;
  --color-archive:      #8A8272;
  --color-stamp:        #B23A2E;
  --color-seal:         #2F4034;

  --font-display: "Zodiak", Georgia, serif;
  --font-body:    "Supreme", system-ui, sans-serif;
  --font-data:    "JetBrains Mono", ui-monospace, monospace;

  --text-folio:    0.6875rem;  /* 11px — etiquetas de campo */
  --text-note:     0.8125rem;  /* 13px — anotaciones marginales */
  --text-body:     1.0625rem;  /* 17px */
  --text-lead:     1.375rem;   /* 22px */
  --text-title:    2.5rem;     /* 40px */
  --text-display:  clamp(3rem, 8vw, 6rem);

  --radius-none: 0;
  --tracking-label: 0.12em;

  --ease-reveal: cubic-bezier(0.22, 1, 0.36, 1);
  --duration-reveal: 420ms;
}
```

---

## 4. La firma: la tachadura

El elemento por el que se recuerda el sitio. Especificación completa.

### 4.1 Qué se ve y qué no

**Siempre visible, sin pagar:** referencia del expediente, provincia y comarca, tipología, superficie, rango de precio (en horquilla, no cifra exacta), yield estimado, estado de verificación, fecha de alta, número de inversores que ya lo han abierto.

**Siempre tachado hasta suscribirse:** dirección exacta, referencia catastral, precio de cierre, identidad y contacto del aportador, documentación adjunta, fotografías interiores.

Nunca se oculta el catálogo entero tras un registro. El inventario velado **es** el argumento de venta.

### 4.2 Comportamiento visual

```
Estado velado          Dirección  ███████████████████
Al pasar el cursor     Dirección  ███████████████████  ← la barra se levanta 2px, aparece cursor de candado
Al desbloquear         Dirección  Calle ██████ , 4º    ← la barra se retira de izquierda a derecha
                       Dirección  Calle Mayor 12, 4º
```

- La barra es un rectángulo sólido `ink`, alto igual a la altura de línea, con un ligero desbordamiento horizontal irregular (±3px) para que parezca aplicada a mano y no un `div` perfecto.
- Animación de retirada: `transform: scaleX()` con origen izquierdo, `var(--duration-reveal)` y `var(--ease-reveal)`. Escalonada por campos con 60ms de retardo entre ellos.
- Nunca usar `filter: blur()` sobre el texto. Da aspecto de paywall barato y además queda borroso, no censurado.

### 4.3 Requisito de seguridad, no negociable

**El dato tachado no puede existir en el DOM.** El servidor devuelve el campo censurado o no lo devuelve. Cualquier implementación que pinte el valor real y lo tape con CSS regala el producto a quien abra el inspector, y con él todo el modelo de negocio.

En accesibilidad, el campo velado se anuncia como `Dirección: reservada. Requiere suscripción.` mediante `aria-label`, y el elemento visual lleva `aria-hidden="true"`.

---

## 5. Componentes

### 5.1 Carátula de expediente (tarjeta)

Tres estados. Sin sombra, sin radio, sin borde completo: solo regla superior de 1px y fondo `paper-shade` al hover.

```
┌ EXP-2026-0412 ─────────────────── [ VERIFICADO ] ┐   ← mono 11px + sello
│                                                   │
│  Nave industrial                                  │   ← Zodiak 300, 40px
│  Alcantarilla · Murcia                            │   ← Supreme, ink-soft
│                                                   │
│  SUPERFICIE   1.240 m²                            │   ← etiquetas mono / cifras mono
│  HORQUILLA    380.000 – 420.000 €                 │
│  YIELD EST.   8,4 %                               │
│  DIRECCIÓN    ████████████████                    │   ← tachadura
│                                                   │
│  Alta 14.08.2026 · 23 inversores lo han abierto   │   ← note 13px, ink-soft
└───────────────────────────────────────────────────┘
```

- El número de expediente es el ancla visual, arriba a la izquierda, siempre en mono.
- El yield es la única cifra que puede ir en `stamp` cuando supera un umbral configurable. Un color, un motivo.
- En móvil, la tarjeta pasa a una sola columna manteniendo la estructura de campos etiquetados. No se convierten en párrafos.

### 5.2 Sellos de estado

Rectángulo con borde de 2px, texto mono en mayúsculas con tracking amplio, rotación entre −4° y +4° (aleatoria pero estable por expediente, derivada del id), opacidad 0.85 para simular tinta absorbida.

| Sello | Color | Significado |
|---|---|---|
| `VERIFICADO` | `seal` | Titularidad y datos comprobados |
| `EN EXCLUSIVA` | `stamp` | Solo aquí |
| `RESERVADO` | `ink` | Con oferta aceptada, aún visible |
| `RETIRADO` | `archive` | Cerrado. Se mantiene visible tachado por completo, como prueba de actividad |

Los expedientes retirados **no se borran**. Un archivo con historial es la prueba social más honesta que tienes.

### 5.3 Índice de expedientes (vista tabla)

La vista por defecto para el inversor suscrito. Densidad alta, filas de 44px, alternancia `paper` / `paper-shade`, cabecera fija con etiquetas mono. Ordenable por yield, alta y provincia. Es la vista que hace sentir que hay volumen.

### 5.4 Apertura de expediente (formulario del aportador)

El momento de marca del lado vendedor. Se diseña como un impreso, no como un formulario web.

- Campos sin caja: solo etiqueta mono en mayúsculas y línea inferior de puntos. El texto que escribe el usuario aparece en Supreme sobre esa línea.
- Numeración de apartados romana en el margen izquierdo (I, II, III), porque aquí el orden **sí** es información: identificación del activo, condiciones, documentación.
- Al enviar: animación de sello de caucho cayendo sobre el impreso con el número de registro asignado. Es la única animación llamativa de todo el sitio y se gasta aquí a propósito.
- Confirmación: "Expediente EXP-2026-0413 abierto." Nunca "¡Gracias por tu envío!".

### 5.5 Muro de suscripción

No es un modal que interrumpe. Es una **diligencia al pie del expediente**: bloque a ancho completo sobre `paper-shade`, con la lista de lo que se levanta al suscribirse redactada como campos, el precio en mono a tamaño de display, y un único botón `stamp`.

Copy del botón: `Levantar la reserva`. Coherente en toda la aplicación: el mismo verbo en el botón, en el toast y en el correo.

### 5.6 Estados vacíos y errores

- Índice sin resultados: "Ningún expediente coincide con estos criterios. Amplía la provincia o el rango de precio." Con dos botones que hagan justo eso.
- Error de pago: explica qué ha pasado y qué hacer. Sin disculpas, sin tono personal.

---

## 6. Arquitectura de páginas

```
/                    Home con doble puerta
/inversores          Argumento de compra + índice velado + precio
/publicar            Argumento del aportador + impreso de apertura
/expedientes         Índice completo (velado o abierto según sesión)
/expedientes/[ref]   Expediente individual
```

**Home, orden de bloques:**

1. **Hero.** Titular en Zodiak sobre el hecho central, y debajo, inmediatamente, **tres carátulas de expediente reales ya veladas**. Nada de ilustración, mockup ni foto de stock. El inventario es el hero.
2. **Bifurcación explícita.** Dos paneles asimétricos (7/5): "Busco oportunidades" y "Tengo una oportunidad". A partir de aquí cada uno va a su recorrido.
3. **Archivo en cifras.** Expedientes abiertos este mes, provincias activas, inversores verificados, tiempo medio hasta primera oferta. Todo en mono, tamaño grande, con la fecha de actualización al lado. Si un dato aún no existe, se omite: no se inventa.
4. **Cómo se levanta la reserva.** Demostración interactiva de la tachadura sobre un expediente de ejemplo. Es la explicación del producto y la firma visual a la vez.
5. **Garantía de no-bypass** para el aportador, con jerarquía propia. Es el bloque que decide su registro.
6. **Precio**, en una sola tarjeta, sin comparativa de tres planes.

---

## 7. Movimiento

Presupuesto total de animación del sitio, y no se amplía:

1. **Carga de la home:** las carátulas aparecen escalonadas, 80ms entre ellas, desplazamiento vertical de 12px y opacidad. Una sola vez.
2. **Retirada de tachadura:** al desbloquear, según sección 4.2.
3. **Sello de registro:** al enviar el impreso de apertura.
4. **Hover:** fondo `paper-shade` y desplazamiento de 2px. Nada más.

`prefers-reduced-motion: reduce` elimina 1, 3 y 4, y convierte 2 en un cambio de estado instantáneo. Sin parallax, sin scroll suave, sin contadores que suben solos, sin elementos que aparecen a cada scroll.

---

## 8. Vocabulario

La consistencia léxica es parte de la identidad. Glosario cerrado:

| Se dice | No se dice |
|---|---|
| Expediente | Anuncio, listing, propiedad |
| Abrir un expediente | Publicar, subir, dar de alta |
| Levantar la reserva | Desbloquear, hacerse premium, upgrade |
| Aportador | Vendedor, partner, colaborador |
| Índice | Buscador, catálogo, feed |
| Retirado | Vendido, cerrado, caducado |

Registro: sobrio, preciso, con una pizca de formalidad administrativa. Frases cortas. Cifras antes que adjetivos. Nunca signos de exclamación. Nunca "revoluciona", "descubre el poder de", "la plataforma líder".

---

## 9. Suelo de calidad

- Responsive real desde 360px. La estructura de campos etiquetados se mantiene en móvil.
- Foco de teclado visible en todos los interactivos, con el contorno definido en 3.1.
- Contraste mínimo AA: `ink` sobre `paper` cumple de sobra; `archive` solo para texto de 13px o mayor y nunca para información esencial.
- Zodiak y Supreme con `font-display: swap` y precarga de los dos pesos usados.
- El dato reservado nunca viaja al cliente (sección 4.3).

---

## 10. Prohibiciones específicas

Además de lo anterior:

- Emojis en cualquier parte de la interfaz. Ni como iconos, ni en el copy, ni en los correos.
- Iconos de casita, llave, gráfico ascendente o maletín.
- Fotografía de stock: gente estrechándose la mano, skylines, manos sobre planos, salones de catálogo.
- El bloque "cómo funciona" con tres círculos numerados. Si necesitas explicar el flujo, hazlo con el expediente de ejemplo del punto 4 de la home.
- Tres tarjetas de beneficios idénticas alineadas.
- Testimonios sin nombre, cargo y operación verificables.
- Gráficas decorativas que no representen datos reales del archivo.
- Modo oscuro. Esta dirección es papel; no tiene versión nocturna.
- Cualquier redondeo, sombra difusa o gradiente.

---

## 11. Prompt de arranque para Claude Code

```
Lee DESIGN.md completo antes de escribir nada.

Construye la home siguiendo la dirección "Expediente Reservado" exactamente como está
especificada: tokens de la sección 3, firma de la sección 4, componentes de la 5 y
orden de bloques de la 6.

Restricciones que verificaré: radio 0 en todo, cero sombras, cero gradientes, todas las
cifras en mono tabular, ningún layout centrado simétrico, ningún emoji, grano aplicado
al fondo.

Usa contenido real de ejemplo del mercado español (Murcia, Alicante, Valencia): naves,
locales, suelo, vivienda. Nada de lorem ipsum ni de nombres inventados en inglés.

Al terminar, arranca el servidor, toma una captura con Playwright MCP y critícala contra
la sección 10 antes de enseñármela. Dime qué has cambiado tras esa crítica.
```
