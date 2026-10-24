"""Páginas secundarias de idealisto.es: pilares SEO, metodología y textos legales.

Cada página: title, desc, miga (breadcrumb), h1, respuesta (bloque de respuesta
directa, HTML), html (cuerpo) y opcionalmente faq [(q, a)] y howto (nombre, pasos).
"""
RAZON_TXT = "Orenes & Asociados Abogados-Consultoría Legal, S.L.P."
RAZON = "Orenes &amp; Asociados Abogados-Consultoría Legal, S.L.P."
NIF = "B05560313"
DOM = "Avenida de la Libertad 5, 1.º A, 30009 Murcia (España)"
EMAIL = "alonso.orenes@onmi.es"
FECHA_LEGAL = "24 de octubre de 2026"
SEDE = "https://www.sedecatastro.gob.es/"
SEDE_BUSQUEDA = "https://www1.sedecatastro.gob.es/CYCBienInmueble/OVCBusqueda.aspx"
MAIL = f'<a href="mailto:{EMAIL}">{EMAIL}</a>'

PAGINAS: dict[str, dict] = {}

# ─── Pilar: referencia catastral ────────────────────────────────────────────
PAGINAS["referencia-catastral"] = {
    "actualizado": "2026-10-24",
    "title": "Referencia catastral: qué es y cómo encontrarla (2026)",
    "desc": ("Busca tu referencia catastral por dirección, mira dónde está en el recibo del IBI y qué significan "
             "sus 20 caracteres. Y valora tu inmueble gratis."),
    "miga": "Referencia catastral",
    "h1": "Referencia catastral: qué es, dónde encontrarla y para qué sirve",
    "respuesta": ("La referencia catastral es el código de 20 caracteres que identifica cada inmueble en el "
                  "Catastro. La encuentras en el recibo del IBI, en la escritura o en la nota simple, y "
                  f"también puedes buscarla gratis por dirección en la <a href=\"{SEDE_BUSQUEDA}\" rel=\"noopener\">Sede Electrónica del Catastro</a>. "
                  "Con ella puedes saber cuánto vale el inmueble en Idealisto."),
    "html": f"""
<h2>Buscar tu referencia catastral por dirección</h2>
<p>Elige provincia, municipio, calle y número. Verás todos los inmuebles del portal con su referencia catastral, planta, puerta, uso y superficie, y podrás valorar el tuyo con un clic.</p>
<div class="caja-buscador">__BUSCADOR__</div>
<p class="hint">Datos de la Dirección General del Catastro. País Vasco y Navarra tienen catastros forales y no aparecen en este buscador.</p>

<h2>¿Qué es la referencia catastral?</h2>
<p>Es el identificador oficial y obligatorio de cada bien inmueble en España. La asigna la Dirección General del Catastro y es única: no hay dos inmuebles con la misma. Cada piso, local, plaza de garaje o trastero con entidad propia tiene la suya, aunque compartan edificio.</p>
<p>Fuera del País Vasco y Navarra, que tienen catastros forales con su propio formato, todas las referencias siguen la misma estructura de 20 caracteres.</p>

<h2>¿Dónde encuentro mi referencia catastral?</h2>
<ul>
  <li><strong>Recibo del IBI</strong>: es el sitio más rápido. Aparece en el propio recibo o en la carta de domiciliación.</li>
  <li><strong>Escritura de compraventa</strong>: figura en la descripción de la finca.</li>
  <li><strong>Nota simple del Registro de la Propiedad</strong>: suele aparecer junto a la descripción registral.</li>
  <li><strong>Sede Electrónica del Catastro</strong>: puedes <a href="{SEDE_BUSQUEDA}" rel="noopener">buscarla por dirección</a> (provincia, municipio, calle y número) o señalando el inmueble en el mapa, sin identificarte. Si el edificio tiene varios inmuebles, verás la lista y eliges el tuyo por planta y puerta.</li>
</ul>

<h2>¿Qué significan los 20 caracteres?</h2>
<div class="scroll"><table>
  <thead><tr><th>Posiciones</th><th>Qué identifican</th><th>Ejemplo (9872023VH5797S0001WX)</th></tr></thead>
  <tbody>
    <tr><td>1–7</td><td>La finca o parcela</td><td>9872023</td></tr>
    <tr><td>8–14</td><td>La hoja del plano catastral donde está la parcela</td><td>VH5797S</td></tr>
    <tr><td>15–18</td><td>El inmueble concreto dentro de la parcela (número de cargo)</td><td>0001</td></tr>
    <tr><td>19–20</td><td>Dos caracteres de control para detectar errores al copiarla</td><td>WX</td></tr>
  </tbody>
</table></div>
<p>Los <strong>14 primeros</strong> identifican la parcela (el edificio o el solar entero). Por eso, si solo tienes 14 caracteres, tienes la referencia de la finca, no la de tu vivienda: te faltan los 6 que distinguen tu piso del resto.</p>
<p>En suelo <strong>rústico</strong> los 14 primeros caracteres siguen otra lógica: código de provincia y municipio, sector, polígono y parcela. Los 6 últimos funcionan igual.</p>
<p>Los dos caracteres de control salen de un cálculo sobre los anteriores. Por eso Idealisto detecta al instante si te has equivocado al copiar una letra.</p>

<h2>¿Para qué sirve la referencia catastral?</h2>
<ul>
  <li>Declarar el inmueble en la Renta (imputación de rentas o alquileres).</li>
  <li>Pagar el IBI y la plusvalía municipal.</li>
  <li>Compraventas, herencias y donaciones: la escritura y la autoliquidación de impuestos la incluyen.</li>
  <li>Contratar suministros, pedir una nota simple o un certificado catastral.</li>
  <li><strong>Saber cuánto vale el inmueble</strong>: con la referencia, Idealisto obtiene superficie, uso, año y ubicación exacta, y lo compara con lo que está en venta alrededor. <a href="/">Pruébalo gratis</a>.</li>
</ul>
""",
    "faq": [
        ("¿La referencia catastral es pública?",
         "La referencia y los datos físicos del inmueble (superficie, uso, año) son de consulta libre en la "
         "Sede del Catastro. Los datos protegidos, como el titular o el valor catastral, solo los puede "
         "consultar el propio titular o quien tenga un interés legítimo."),
        ("¿Qué hago si solo tengo 14 caracteres?",
         "Esa es la referencia de la parcela. Búscala en la Sede del Catastro y elige tu inmueble en la "
         "lista para obtener los 20 caracteres completos."),
        ("¿La plaza de garaje tiene referencia propia?",
         "Depende. Si se compró como finca independiente, tiene su propia referencia. Si va vinculada a la "
         "vivienda, comparte referencia con ella y aparece como una construcción más del inmueble."),
        ("¿Cambia la referencia catastral al vender?",
         "No. La referencia identifica el inmueble, no al propietario, y se mantiene aunque cambie de manos. "
         "Solo cambia si el inmueble se divide, se agrupa o se segrega."),
    ],
    "howto": ("Cómo encontrar tu referencia catastral por dirección", [
        ("Entra en la Sede del Catastro", "Abre la consulta de datos catastrales sin identificarte."),
        ("Busca por dirección", "Elige provincia, municipio, calle y número."),
        ("Elige tu inmueble", "Si hay varios, selecciona tu planta y puerta y copia los 20 caracteres."),
    ]),
}

# ─── Pilar: valor de referencia ─────────────────────────────────────────────
PAGINAS["valor-de-referencia"] = {
    "actualizado": "2026-10-24",
    "title": "Valor de referencia del Catastro 2026: guía y comparación",
    "desc": ("Qué es el valor de referencia del Catastro, en qué impuestos se usa (ITP, Sucesiones y "
             "Donaciones), en qué se diferencia del valor de mercado y qué hacer si es demasiado alto."),
    "miga": "Valor de referencia",
    "h1": "Valor de referencia del Catastro: qué es y qué hacer si es demasiado alto",
    "respuesta": ("El valor de referencia es el valor que el Catastro asigna cada año a cada inmueble a partir de "
                  "los precios escriturados ante notario. Desde 2022 es la base mínima del ITP y del Impuesto de "
                  "Sucesiones y Donaciones: si declaras un precio inferior, tributas por el valor de referencia. "
                  "Compáralo con el valor de mercado de tu inmueble en Idealisto."),
    "html": """
<h2>¿Qué es el valor de referencia?</h2>
<p>Lo introdujo la Ley 11/2021 de medidas de prevención y lucha contra el fraude fiscal, con efectos desde el 1 de enero de 2022. La Dirección General del Catastro lo calcula cada año para cada inmueble a partir de las compraventas reales comunicadas por los notarios, agrupadas por zonas y tipologías, y le aplica un factor de minoración para no superar el valor de mercado.</p>
<p>Los valores de cada año se publican en otoño del año anterior: los de 2026 se publicaron en octubre de 2025.</p>

<h2>¿En qué impuestos se usa?</h2>
<ul>
  <li><strong>ITP (Transmisiones Patrimoniales Onerosas)</strong>: en la compra de vivienda usada, la base imponible es el mayor entre el precio escriturado y el valor de referencia.</li>
  <li><strong>Impuesto de Sucesiones y Donaciones</strong>: en herencias y donaciones, la base es el mayor entre el valor declarado y el de referencia.</li>
  <li><strong>Impuesto sobre el Patrimonio</strong>: es uno de los valores que entran en juego para los inmuebles adquiridos desde 2022.</li>
</ul>
<p>No se usa para el IBI ni para la plusvalía municipal, que siguen calculándose con el valor catastral.</p>

<h2>Valor de referencia, valor de mercado y valor catastral</h2>
<div class="scroll"><table>
  <thead><tr><th></th><th>Quién lo fija</th><th>Para qué sirve</th></tr></thead>
  <tbody>
    <tr><td><strong>Valor de mercado</strong></td><td>El mercado: lo que pagaría hoy un comprador.</td><td>Vender, comprar, repartir una herencia, negociar.</td></tr>
    <tr><td><strong>Valor de referencia</strong></td><td>El Catastro, cada año, a partir de escrituras.</td><td>Base mínima del ITP y de Sucesiones y Donaciones.</td></tr>
    <tr><td><strong>Valor catastral</strong></td><td>El Catastro, en las ponencias de valores municipales.</td><td>IBI, imputación de rentas en el IRPF, plusvalía municipal.</td></tr>
  </tbody>
</table></div>

<h2>¿Cómo consulto mi valor de referencia?</h2>
<p>Se consulta en la <a href="https://www.sedecatastro.gob.es/" rel="noopener">Sede Electrónica del Catastro</a>, en el apartado de valor de referencia, con la referencia catastral y la fecha de la operación. Para obtener un certificado necesitas identificarte con Cl@ve, certificado digital o DNI electrónico.</p>

<h2>¿Qué hago si el valor de referencia es más alto que el de mercado?</h2>
<p>Ocurre, sobre todo en inmuebles en mal estado, con cargas o con características que una valoración por zonas no capta. El valor de referencia no se recurre por separado; se impugna a la vez que el impuesto:</p>
<ol>
  <li>Si ya has presentado la autoliquidación, pide su <strong>rectificación</strong> alegando que el valor de referencia supera el de mercado.</li>
  <li>Si Hacienda te ha girado una liquidación, recúrrela (reposición o reclamación económico-administrativa).</li>
  <li>Aporta pruebas del valor real: una tasación, comparables, el estado del inmueble. La Administración pedirá un informe preceptivo y vinculante al Catastro.</li>
</ol>
<p>Una valoración de Idealisto te sirve para detectar el problema y decidir si merece la pena. Para impugnar, lo habitual es aportar una tasación pericial y contar con un asesor fiscal o un abogado.</p>
""",
    "faq": [
        ("¿El valor de referencia puede ser superior al de mercado?",
         "No debería, porque el Catastro aplica un factor de minoración, pero ocurre en inmuebles cuyo estado "
         "o características no reflejan la media de su zona. En ese caso puedes impugnarlo junto con el impuesto."),
        ("¿El valor de referencia afecta al IBI?",
         "No. El IBI y la plusvalía municipal se calculan con el valor catastral, que es otro distinto."),
        ("¿Todos los inmuebles tienen valor de referencia?",
         "No. Hay inmuebles sin valor de referencia asignado, por ejemplo algunos de características "
         "singulares. En ese caso la base imponible es el valor declarado, que Hacienda puede comprobar."),
        ("¿Cada cuánto cambia el valor de referencia?",
         "Se actualiza cada año. El Catastro publica en otoño los valores que se aplicarán el año siguiente."),
    ],
}

# ─── Landing núcleo: tasación por referencia catastral ──────────────────────
PAGINAS["tasacion-referencia-catastral"] = {
    "actualizado": "2026-10-24",
    "title": "Tasación por referencia catastral gratis y sin email",
    "desc": ("Valora gratis un piso, casa, garaje o trastero con solo su referencia catastral: valor de "
             "mercado con rango, €/m², media de la zona y precio de cierre. Sin formularios ni email."),
    "miga": "Tasación por referencia catastral",
    "h1": "Tasación por referencia catastral: gratis, en segundos y sin formularios",
    "respuesta": ("Para valorar un inmueble con su referencia catastral, pega los 20 caracteres en Idealisto. "
                  "Obtenemos del Catastro su superficie, uso, año y ubicación, lo comparamos con los inmuebles "
                  "similares en venta a su alrededor y te damos su valor de mercado con un rango, sin pedirte "
                  "nada más."),
    "html": """
<h2>¿Se puede tasar un piso solo con la referencia catastral?</h2>
<p>Los valoradores habituales te piden metros, habitaciones, baños, estado, planta y tu email antes de enseñarte nada. Casi todo eso ya está en el Catastro: con la referencia sabemos la superficie construida y su desglose (vivienda, garaje, trastero, zonas comunes), el uso, el año de construcción, la planta y la ubicación exacta de la parcela.</p>

<h2>¿Qué obtienes?</h2>
<ul>
  <li><strong>Valor de mercado estimado</strong> con un rango mínimo y máximo.</li>
  <li><strong>Precio por m²</strong> del inmueble y <strong>media de la zona</strong>.</li>
  <li><strong>Precio de cierre estimado</strong>: lo que se suele firmar tras negociar, que no es lo mismo que el precio de anuncio.</li>
  <li><strong>Nivel de confianza</strong>: alto, medio o bajo según cuántos comparables hay y cómo de parecidos son.</li>
  <li>Un <strong>informe en PDF</strong> que puedes descargar al momento.</li>
</ul>

<h2>¿Es una tasación oficial?</h2>
<p>Una tasación oficial (Orden ECO/805/2003) la firma un técnico de una sociedad de tasación homologada por el Banco de España, tras visitar el inmueble, y es la que exige el banco para una hipoteca. La de Idealisto es una valoración automática orientativa: sirve para saber en qué rango te mueves antes de vender, comprar, heredar, repartir o pujar en una subasta, sin pagar ni visitar nada.</p>

<h2>¿Cuándo es especialmente útil?</h2>
<ul>
  <li><strong>Herencias y donaciones</strong>: para comparar el valor de mercado con el <a href="/valor-de-referencia/">valor de referencia</a> que usa Hacienda.</li>
  <li><strong>Divorcios y repartos</strong>: una cifra neutral de partida.</li>
  <li><strong>Antes de poner precio</strong> a tu piso, o de hacer una oferta por uno.</li>
  <li><strong>Subastas del BOE y activos de banco</strong>: el edicto trae la referencia catastral; en segundos sabes el descuento real sobre mercado.</li>
</ul>
""",
    "faq": [
        ("¿Es gratis?", "Sí. La valoración es gratuita y no te pedimos ningún dato personal para verla."),
        ("¿Qué fiabilidad tiene?",
         "Depende de cuántos inmuebles comparables haya cerca. Por eso mostramos un rango y un nivel de "
         "confianza en cada valoración. En zonas con poca oferta, preferimos no dar cifra a dar una mala."),
        ("¿Valoráis locales, naves y suelos?",
         "De momento la herramienta pública valora viviendas, casas, garajes y trasteros. Para locales, naves "
         "y suelos, escríbenos y lo estudiamos caso a caso."),
    ],
}

# ─── Metodología ────────────────────────────────────────────────────────────
PAGINAS["metodologia"] = {
    "actualizado": "2026-10-24",
    "title": "Metodología de valoración | Idealisto",
    "desc": ("Fuentes, método de comparación, homogeneización, rango y nivel de confianza de las "
             "valoraciones automáticas de Idealisto."),
    "miga": "Metodología",
    "h1": "Cómo calculamos el valor de tu inmueble",
    "respuesta": ("Idealisto valora por comparación: toma los datos del inmueble del Catastro y los compara con "
                  "inmuebles similares en venta a su alrededor, homogeneizados por superficie, planta y "
                  "antigüedad. La cifra es la mediana de esos comparables y el rango, su dispersión central."),
    "html": """
<h2>1. Datos del inmueble: el Catastro</h2>
<p>Con la referencia catastral consultamos a la Dirección General del Catastro el uso, la superficie construida y su desglose por construcciones (vivienda, garaje, trastero, elementos comunes), la planta, el año de construcción y las coordenadas oficiales de la parcela. Así sabemos, por ejemplo, si una vivienda es un piso o una casa unifamiliar, o si su superficie incluye un garaje.</p>

<h2>2. Comparables: inmuebles en venta alrededor</h2>
<p>Buscamos inmuebles del mismo tipo anunciados a la venta en un radio que empieza siendo pequeño y se amplía solo hasta reunir un número mínimo de comparables, como exige la normativa de tasación para el método de comparación. La base de comparables se actualiza de forma continua y conserva el histórico de cada anuncio.</p>

<h2>3. Homogeneización</h2>
<p>Ningún comparable es idéntico al tuyo. Ajustamos el precio por m² de cada uno por las diferencias de superficie, planta y antigüedad respecto a tu inmueble. En zonas donde conviven edificios muy antiguos y obra nueva, las viviendas antiguas se comparan con su propio segmento.</p>

<h2>4. Cifra, rango y anejos</h2>
<ul>
  <li><strong>Valor central</strong>: la mediana del precio por m² de los comparables, tras descartar los atípicos (regla del rango intercuartílico), multiplicada por la superficie de tu inmueble.</li>
  <li><strong>Rango</strong>: los percentiles 25 y 75 de esos comparables. La mitad de los inmuebles parecidos de tu zona se anuncian dentro de ese rango.</li>
  <li><strong>Anejos</strong>: si la vivienda incluye garaje, trastero u otras construcciones, no los valoramos al precio del salón, sino aparte y con coeficientes propios.</li>
  <li><strong>Garajes y trasteros</strong> con referencia propia se valoran con comparables de su tipo o, si no hay suficientes, en proporción al precio de la vivienda de la zona.</li>
</ul>

<h2>5. Precio de cierre</h2>
<p>Los anuncios reflejan precios de oferta; lo que se firma ante notario suele ser algo menor. Estimamos el precio de cierre aplicando el descuento medio entre oferta y escritura calibrado para tu municipio o provincia con estadística oficial de compraventas.</p>

<h2>6. Nivel de confianza</h2>
<ul>
  <li><strong>Alta</strong>: muchos comparables, cercanos y homogéneos.</li>
  <li><strong>Media</strong>: muestra suficiente pero más dispersa o más lejana.</li>
  <li><strong>Baja</strong>: pocos comparables, o una mediana que se aleja mucho del precio oficial escriturado de la provincia. Tómala como orientación gruesa.</li>
</ul>
<p>Si no hay comparables suficientes, no damos cifra.</p>

<h2>Límites</h2>
<ul>
  <li>No vemos el interior: reformas, estado de conservación, vistas o luz no están en el Catastro. Una vivienda reformada puede valer más que el rango, y una a reformar, menos.</li>
  <li>País Vasco y Navarra tienen catastros forales; de momento la herramienta pública valora inmuebles del Catastro estatal.</li>
  <li>Locales, naves y suelos necesitan otros métodos (rentas, coste de reposición, residual) y no están en la herramienta pública.</li>
  <li>No es una tasación oficial (Orden ECO/805/2003) y no sirve para una hipoteca.</li>
</ul>

<h2>Fuentes</h2>
<ul>
  <li>Datos catastrales: Dirección General del Catastro (Sede Electrónica y servicios web).</li>
  <li>Comparables: anuncios de venta de portales inmobiliarios, con su histórico.</li>
  <li>Precios escriturados y descuento de cierre: estadística oficial de compraventas notariales y registrales.</li>
</ul>
<p>Datos tratados por la sociedad titular de Idealisto, que mantiene la misma base de comparables que usa en su actividad profesional de valoración de activos inmobiliarios.</p>
""",
}

# ─── Legal ──────────────────────────────────────────────────────────────────
PAGINAS["aviso-legal"] = {
    "title": "Aviso legal | Idealisto",
    "desc": f"Aviso legal de idealisto.es: titular ({RAZON_TXT}, NIF {NIF}), condiciones de uso y responsabilidad.",
    "miga": "Aviso legal",
    "h1": "Aviso legal",
    "sin_cta": True,
    "html": f"""
<p><em>Última actualización: {FECHA_LEGAL}</em></p>
<h2>Titular</h2>
<p>En cumplimiento del artículo 10 de la Ley 34/2002, de servicios de la sociedad de la información y de comercio electrónico:</p>
<ul>
  <li>Titular: {RAZON}</li>
  <li>NIF: {NIF}</li>
  <li>Domicilio: {DOM}</li>
  <li>Email: {MAIL}</li>
  <li>Datos registrales: sociedad inscrita en el Registro Mercantil de Murcia.</li>
</ul>
<h2>Objeto</h2>
<p>idealisto.es ofrece una herramienta gratuita de valoración automática de inmuebles a partir de su referencia catastral, junto con contenidos informativos sobre el Catastro y la fiscalidad inmobiliaria.</p>
<h2>Naturaleza de las valoraciones</h2>
<p>Las valoraciones son estimaciones automáticas y orientativas, calculadas con datos públicos del Catastro y con inmuebles comparables en venta. No constituyen una tasación oficial conforme a la Orden ECO/805/2003, no tienen validez para fines hipotecarios, judiciales ni fiscales y no sustituyen el asesoramiento de un profesional. El titular no garantiza su exactitud y no responde de las decisiones que el usuario tome basándose en ellas.</p>
<p>Los contenidos informativos sobre impuestos y procedimientos son generales y pueden no ajustarse a tu caso concreto o a la normativa de tu comunidad autónoma.</p>
<h2>Uso del servicio</h2>
<p>Queda prohibido el uso automatizado de la herramienta (consultas masivas, extracción de datos o reventa de resultados) sin autorización previa por escrito. El servicio aplica límites de uso por motivos técnicos.</p>
<h2>Propiedad intelectual</h2>
<p>Los textos, el diseño, el código y los modelos de valoración son del titular o se usan con licencia. Los datos catastrales proceden de la Dirección General del Catastro.</p>
<h2>Ley aplicable</h2>
<p>Este aviso se rige por la legislación española. Si eres consumidor, puedes acudir a los Juzgados y Tribunales de tu domicilio.</p>
""",
}

PAGINAS["privacidad"] = {
    "title": "Política de privacidad | Idealisto",
    "desc": "Cómo trata Idealisto tus datos: valoración sin datos personales, email solo si pides el informe, sin cesión a inmobiliarias.",
    "miga": "Privacidad",
    "h1": "Política de privacidad",
    "sin_cta": True,
    "html": f"""
<p><em>Última actualización: {FECHA_LEGAL}</em></p>
<h2>Responsable del tratamiento</h2>
<p>{RAZON}, NIF {NIF}, {DOM}. Contacto: {MAIL}.</p>
<h2>Valorar sin datos personales</h2>
<p>Para valorar un inmueble solo necesitas su referencia catastral. No te pedimos nombre, email ni teléfono. La referencia catastral no se guarda en claro: registramos únicamente un resumen técnico irreversible (hash), el tipo de inmueble, la provincia y la cifra obtenida, con fines estadísticos y de mejora del servicio.</p>
<p>Por seguridad, y para aplicar los límites de uso, tratamos tu dirección IP de forma transitoria (en memoria, durante como máximo una hora) y en los registros técnicos del servidor.</p>
<h2>Si nos pides el informe por email</h2>
<ul>
  <li><strong>Datos</strong>: email, la referencia catastral del inmueble valorado y, si los indicas, tu perfil y el motivo de la consulta.</li>
  <li><strong>Finalidad</strong>: enviarte el informe que has pedido.</li>
  <li><strong>Base jurídica</strong>: tu consentimiento (art. 6.1.a RGPD), que puedes retirar en cualquier momento.</li>
  <li><strong>Conservación</strong>: hasta que retires el consentimiento y, como máximo, 24 meses.</li>
  <li><strong>Destinatarios</strong>: no cedemos tus datos a inmobiliarias ni a terceros. Los encargados técnicos (alojamiento del servidor y envío de email) solo los tratan por cuenta nuestra.</li>
</ul>
<h2>Analítica</h2>
<p>Si activamos analítica web, será con IP anonimizada y la indicaremos aquí junto con el aviso de cookies correspondiente.</p>
<h2>Tus derechos</h2>
<p>Puedes ejercer los derechos de acceso, rectificación, supresión, oposición, limitación y portabilidad escribiendo a {MAIL}. Si consideras que no hemos atendido bien tu solicitud, puedes reclamar ante la Agencia Española de Protección de Datos (<a href="https://www.aepd.es" rel="noopener">www.aepd.es</a>).</p>
""",
}
