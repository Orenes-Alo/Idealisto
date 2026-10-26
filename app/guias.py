"""Guías por evento vital (plan SEO/GEO/AEO, 25-10-2026): heredar, divorciarse,
vender, alquilar o pujar en una subasta son los momentos en que alguien busca
«cuánto vale mi casa». Cada guía responde primero (respuesta rápida), explica
qué valor importa en ese momento y enlaza al tasador y a la calculadora que toca.

Mismo formato que contenido.PAGINAS; la clave lleva el prefijo «guias/» y
«padre» añade el nivel intermedio de la miga de pan. Nada de cifras inventadas:
los importes y tipos concretos viven en las calculadoras (app/fiscal.py).
"""

PADRE = ("Guías", "/guias/")
ACT = "2026-10-25"

GUIAS: dict[str, dict] = {}

GUIAS["guias/cuanto-vale-casa-heredada"] = {
    "actualizado": ACT, "padre": PADRE,
    "title": "Cuánto vale la casa que he heredado | Idealisto",
    "desc": ("Qué valor usa Hacienda en una herencia, en qué se diferencia del valor de mercado, qué impuestos "
             "hay que pagar y en qué plazos. Valora gratis el inmueble con su referencia catastral."),
    "miga": "Casa heredada",
    "h1": "¿Cuánto vale la casa que he heredado?",
    "respuesta": ("En una herencia hay dos cifras distintas: el <strong>valor de referencia del Catastro</strong>, que "
                  "es el mínimo que Hacienda usa como base del Impuesto sobre Sucesiones, y el <strong>valor de "
                  "mercado</strong>, que es lo que obtendrías si vendieras. Conviene conocer las dos antes de aceptar "
                  "la herencia y de decidir si vender, alquilar o quedarse la vivienda."),
    "html": """
<h2>¿Qué valor declara Hacienda en una herencia?</h2>
<p>Desde 2022, la base del Impuesto sobre Sucesiones de un inmueble es su <a href="/valor-de-referencia/">valor de referencia</a> del Catastro, salvo que declares un valor mayor. Si el inmueble no tiene valor de referencia, se toma el mayor entre el valor declarado y el valor de mercado. El valor de referencia se consulta en la Sede Electrónica del Catastro con la referencia catastral.</p>

<h2>¿Y cuánto vale de verdad en el mercado?</h2>
<p>El valor de mercado puede estar por encima o por debajo del de referencia. Con la <a href="/referencia-catastral/">referencia catastral</a> puedes ver en Idealisto un valor de mercado estimado con su rango, el precio por metro cuadrado de la zona y el precio de cierre esperado. Si el valor de mercado es muy inferior al de referencia, se puede discutir con una tasación pericial.</p>
__BUSCADOR__

<h2>¿Qué impuestos se pagan al heredar una vivienda?</h2>
<ul>
  <li><strong>Impuesto sobre Sucesiones</strong>: lo paga cada heredero según su parentesco y su comunidad autónoma. Muchas comunidades bonifican casi por completo a hijos y cónyuges. Calcúlalo en la <a href="/calculadoras/sucesiones-donaciones/">calculadora de Sucesiones y Donaciones</a>.</li>
  <li><strong>Plusvalía municipal</strong>: grava el aumento de valor del suelo desde que lo adquirió el fallecido. No se paga si no hubo ganancia. Calcúlala en la <a href="/calculadoras/plusvalia-municipal/">calculadora de plusvalía</a>.</li>
  <li><strong>Gastos de notaría y Registro</strong> por la escritura de aceptación y la inscripción a nombre de los herederos.</li>
</ul>

<h2>¿En qué plazo hay que hacerlo?</h2>
<p>El Impuesto sobre Sucesiones y la plusvalía municipal se presentan, con carácter general, en los <strong>seis meses</strong> siguientes al fallecimiento, y ambos admiten pedir una prórroga dentro de ese plazo. Pasado el plazo hay recargos.</p>

<h2>¿Y si hay varios herederos?</h2>
<p>La vivienda queda en proindiviso hasta que se reparte. Para adjudicarla a uno de ellos y compensar a los demás, o para venderla, todos necesitan una cifra de partida razonable: el valor de mercado con su rango es un buen punto de partida para negociar.</p>

<h2>Qué hacer después</h2>
<ul>
  <li>Si vas a vender: mira <a href="/guias/cuanto-pedir-al-vender-mi-casa/">cuánto pedir al vender tu casa</a>.</li>
  <li>Si vas a alquilar: mira <a href="/guias/cuanto-cobrar-de-alquiler/">cuánto cobrar de alquiler</a> y la <a href="/calculadoras/rentabilidad-alquiler/">calculadora de rentabilidad</a>.</li>
</ul>
""",
    "faq": [
        ("¿El valor de referencia es lo que vale mi casa?",
         "No necesariamente. Es un valor administrativo que fija el Catastro a partir de las compraventas de la zona y sirve de mínimo fiscal. El valor de mercado puede ser mayor o menor."),
        ("¿Puedo declarar un valor menor que el de referencia?",
         "No en la autoliquidación. Si crees que el valor de referencia supera el de mercado, puedes declarar el de referencia y pedir después la rectificación aportando una prueba, como una tasación."),
        ("¿Tengo que pagar plusvalía si heredo de mis padres?",
         "Sí, la plusvalía municipal se devenga en las herencias, salvo que no haya habido aumento de valor del suelo. Algunos ayuntamientos bonifican las transmisiones a hijos y cónyuges."),
    ],
}

GUIAS["guias/valor-vivienda-divorcio"] = {
    "actualizado": ACT, "padre": PADRE,
    "title": "Valorar la vivienda en un divorcio | Idealisto",
    "desc": ("Cómo se fija el valor de la casa en un divorcio o una separación para adjudicarla a uno de los dos "
             "o venderla, y qué impuestos afectan. Valoración gratuita con la referencia catastral."),
    "miga": "Divorcio",
    "h1": "¿Cuánto vale nuestra casa si nos divorciamos?",
    "respuesta": ("Para repartir la vivienda en un divorcio hace falta un valor de mercado que ambos acepten: con él se "
                  "calcula cuánto debe compensar quien se la queda al otro, descontando la hipoteca pendiente. Un "
                  "valor objetivo con rango, basado en inmuebles comparables, evita discusiones y sirve de base para "
                  "negociar o para una tasación posterior."),
    "html": """
<h2>¿Cómo se reparte la vivienda?</h2>
<p>Las opciones habituales son tres: que uno de los dos se la quede y compense al otro, venderla y repartir el dinero, o mantenerla en común (por ejemplo, mientras los hijos viven en ella). En las dos primeras, la cifra clave es el <strong>valor de mercado</strong> del inmueble.</p>

<h2>¿Cómo se calcula la compensación?</h2>
<ol>
  <li>Partid del valor de mercado de la vivienda.</li>
  <li>Restad la deuda hipotecaria pendiente.</li>
  <li>El resultado es el valor neto; a cada uno le corresponde su parte (la mitad, si era al 50 %).</li>
</ol>
<p>Quien se queda la casa suele asumir también la hipoteca, lo que necesita el acuerdo del banco.</p>
__BUSCADOR__

<h2>¿Qué impuestos afectan?</h2>
<ul>
  <li>La adjudicación de la vivienda a uno de los cónyuges al liquidar la sociedad de gananciales, o al extinguir el condominio, en general <strong>no tributa por Transmisiones Patrimoniales</strong>, aunque puede tributar por Actos Jurídicos Documentados según el caso y la comunidad autónoma.</li>
  <li>La <strong>plusvalía municipal</strong> no se devenga en las adjudicaciones entre cónyuges derivadas del divorcio.</li>
  <li>Si la vendéis a un tercero, cada uno tributa en el IRPF por su ganancia y se paga la plusvalía municipal. Consulta con tu asesor el caso concreto.</li>
</ul>

<h2>¿Basta con una valoración automática?</h2>
<p>Para negociar entre las partes, una valoración por comparables con su rango es un buen punto de partida. Si el reparto acaba en el juzgado o el banco tiene que aprobar el cambio de titular, normalmente se pedirá una tasación oficial.</p>
<p>Si os interesa saber a cuánto alquilaríais la vivienda mientras tanto, mira <a href="/guias/cuanto-cobrar-de-alquiler/">cuánto cobrar de alquiler</a>.</p>
""",
    "faq": [
        ("¿Qué valor se usa: el catastral, el de referencia o el de mercado?",
         "Para repartir entre vosotros, el de mercado. El valor catastral y el de referencia son valores fiscales y no reflejan lo que obtendríais al vender."),
        ("¿Y si no nos ponemos de acuerdo en el valor?",
         "Se puede encargar una tasación a una sociedad de tasación o, en un procedimiento judicial, una pericial. Una valoración por comparables ayuda a acotar la cifra antes."),
    ],
}

GUIAS["guias/cuanto-pedir-al-vender-mi-casa"] = {
    "actualizado": ACT, "padre": PADRE,
    "title": "Cuánto pedir al vender mi casa | Idealisto",
    "desc": ("Cómo fijar el precio de venta de tu vivienda: valor de mercado, margen de negociación, precio de "
             "cierre y gastos e impuestos de la venta. Valora gratis con la referencia catastral."),
    "miga": "Vender",
    "h1": "¿Cuánto debería pedir al vender mi casa?",
    "respuesta": ("Pide un precio dentro del rango de los inmuebles comparables de tu zona, no por encima. Ten en cuenta "
                  "que lo que se firma ante notario suele ser algo menor que el precio anunciado: Idealisto te da el "
                  "valor de mercado, el rango y el precio de cierre estimado para tu municipio."),
    "html": """
<h2>¿Cómo se fija un buen precio de salida?</h2>
<ul>
  <li><strong>Mira los comparables</strong>: viviendas del mismo tipo, superficie y antigüedad a la venta cerca de la tuya.</li>
  <li><strong>Sitúate dentro del rango</strong>: un precio muy por encima alarga la venta y acaba en rebajas; los compradores comparan.</li>
  <li><strong>Ajusta por lo que no sale en el Catastro</strong>: reforma, luz, vistas o una planta alta con ascensor suben el valor; necesitar reforma lo baja.</li>
</ul>
__BUSCADOR__

<h2>¿Por qué el precio final suele ser menor?</h2>
<p>Los portales muestran precios de oferta. Entre el precio anunciado y el escriturado hay un margen de negociación que varía por zona y momento del mercado. Por eso Idealisto calcula un <strong>precio de cierre</strong> calibrado con estadística oficial de compraventas de tu municipio o provincia. Compara además con el <a href="/precio-vivienda/">precio de la vivienda en tu municipio</a>.</p>

<h2>¿Qué gastos e impuestos tiene vender?</h2>
<ul>
  <li><strong>IRPF</strong>: tributa la ganancia (precio de venta menos el de compra y los gastos). Hay exenciones, por ejemplo al reinvertir en vivienda habitual o para mayores de 65 años que venden la suya.</li>
  <li><strong>Plusvalía municipal</strong>: la paga quien vende, salvo pacto; calcúlala en la <a href="/calculadoras/plusvalia-municipal/">calculadora de plusvalía</a>.</li>
  <li>Cancelación registral de la hipoteca, certificado energético y, si la usas, la comisión de la agencia.</li>
</ul>
<p>El comprador paga el ITP o el IVA; puedes estimarlo en la <a href="/calculadoras/itp/">calculadora de ITP</a> para saber cuánto tendrá que desembolsar en total.</p>
""",
    "faq": [
        ("¿Pongo un precio alto para tener margen de negociación?",
         "Con prudencia. Un precio fuera del rango de la zona recibe menos visitas y acaba en rebajas sucesivas, que también restan credibilidad. Es mejor un precio dentro del rango con algo de margen."),
        ("¿Cada cuánto debo revisar el precio?",
         "Si en unas semanas no hay visitas ni ofertas, el precio está por encima de lo que el mercado paga en tu zona. Vuelve a comparar con los inmuebles parecidos que siguen a la venta."),
    ],
}

GUIAS["guias/cuanto-cobrar-de-alquiler"] = {
    "actualizado": ACT, "padre": PADRE,
    "title": "Cuánto cobrar de alquiler por mi piso | Idealisto",
    "desc": ("Cómo fijar la renta de alquiler: precios de la zona, índice oficial de referencia en zonas "
             "tensionadas y rentabilidad. Valora gratis la vivienda con su referencia catastral."),
    "miga": "Alquilar",
    "h1": "¿Cuánto puedo cobrar de alquiler por mi piso?",
    "respuesta": ("La renta la marca el mercado de tu zona, salvo en las zonas declaradas tensionadas, donde la Ley de "
                  "Vivienda limita la renta de los contratos nuevos con el índice oficial de referencia. El informe "
                  "completo de Idealisto incluye el alquiler de referencia del inmueble y su rentabilidad bruta."),
    "html": """
<h2>¿Cómo se calcula una renta razonable?</h2>
<ul>
  <li>Compara con pisos parecidos que se alquilan en tu zona: misma superficie, habitaciones, estado y si está amueblado.</li>
  <li>Consulta el <strong>Sistema Estatal de Referencia del Precio del Alquiler de Vivienda</strong> del Ministerio de Vivienda, que da un rango por inmueble a partir de su referencia catastral.</li>
  <li>Comprueba la rentabilidad con la <a href="/calculadoras/rentabilidad-alquiler/">calculadora de rentabilidad</a>: renta anual frente al valor de la vivienda y los gastos.</li>
</ul>
__BUSCADOR__

<h2>¿Y si mi piso está en una zona tensionada?</h2>
<p>En los municipios o zonas que la comunidad autónoma haya declarado tensionados conforme a la Ley 12/2023, la renta de un contrato nuevo no puede superar, en general, la del contrato anterior (actualizada), con algunas excepciones, y si el propietario es un gran tenedor se limita al índice de referencia. Consulta si tu municipio está declarado antes de fijar el precio.</p>

<h2>¿Qué valor tiene un piso alquilado si quiero venderlo?</h2>
<p>Un piso con inquilino se vende normalmente a inversores, que lo valoran por su rentabilidad; puede venderse por debajo del valor de un piso vacío. Si vas a vender, mira <a href="/guias/cuanto-pedir-al-vender-mi-casa/">cuánto pedir al vender tu casa</a>.</p>
""",
    "faq": [
        ("¿Qué rentabilidad es buena para un alquiler?",
         "Depende de la ciudad y del riesgo: en las capitales grandes la rentabilidad bruta suele ser menor que en ciudades medianas. Compara siempre la rentabilidad neta, después de gastos, impuestos y periodos sin inquilino."),
        ("¿Dónde veo si mi municipio es zona tensionada?",
         "En la web del Ministerio de Vivienda y en el boletín oficial de tu comunidad autónoma, que publican las declaraciones de zonas de mercado residencial tensionado."),
    ],
}

GUIAS["guias/valor-vivienda-subasta"] = {
    "actualizado": ACT, "padre": PADRE,
    "title": "Cuánto vale una vivienda en subasta | Idealisto",
    "desc": ("Valor de subasta, valor de mercado y cuánto pujar por una vivienda de una subasta judicial o del "
             "BOE. Calcula el valor de mercado con la referencia catastral del lote."),
    "miga": "Subastas",
    "h1": "¿Cuánto vale una vivienda que sale a subasta?",
    "respuesta": ("El «valor de subasta» que publica el BOE no es el valor de mercado: suele venir de la tasación de la "
                  "hipoteca, a veces de hace muchos años. Antes de pujar conviene calcular el valor de mercado actual "
                  "con la referencia catastral del lote y restarle las cargas, la situación de ocupación y los gastos."),
    "html": """
<h2>¿Qué cifras aparecen en el anuncio de la subasta?</h2>
<ul>
  <li><strong>Valor de subasta</strong>: el que fija el procedimiento, normalmente el de tasación de la escritura de hipoteca.</li>
  <li><strong>Depósito</strong>: lo que hay que consignar para pujar en una subasta judicial, por lo general el 5 % del valor de subasta.</li>
  <li><strong>Referencia catastral</strong>: con ella puedes valorar el inmueble aquí y consultar su ficha del Catastro.</li>
</ul>
__BUSCADOR__

<h2>¿Hay un precio mínimo para adjudicarse la vivienda?</h2>
<p>No hay un único precio mínimo. La Ley de Enjuiciamiento Civil establece qué ocurre según el porcentaje que alcance la mejor puja respecto al valor de subasta, y en algunos supuestos el ejecutante o el deudor pueden mejorarla. Por eso conviene leer el edicto completo y, si no lo dominas, asesorarte.</p>

<h2>¿Qué hay que restar al valor de mercado?</h2>
<ul>
  <li><strong>Cargas</strong> que no se cancelan con la subasta (las anteriores a la que se ejecuta): pide una nota simple.</li>
  <li><strong>Ocupación</strong>: si hay ocupantes, el plazo para tomar posesión y su coste.</li>
  <li><strong>Deudas</strong> con la comunidad de propietarios y el IBI pendiente, dentro de los límites legales.</li>
  <li><strong>Impuestos y gastos</strong> de la adjudicación: calcúlalos en la <a href="/calculadoras/itp/">calculadora de ITP</a>.</li>
  <li>El estado del interior, que normalmente no se puede visitar.</li>
</ul>

<h2>¿Dónde encontrar subastas analizadas?</h2>
<p>La plataforma <a href="https://inversionnpl.com/" rel="noopener">InversionNPL</a>, del mismo titular que Idealisto, analiza subastas del BOE y operaciones de deuda hipotecaria con su valor de mercado y su cobertura.</p>
""",
    "faq": [
        ("¿El valor de subasta es lo que vale la casa?",
         "No. Suele ser el valor de tasación de la hipoteca y puede estar muy alejado del valor de mercado actual, en ambos sentidos."),
        ("¿Puedo visitar la vivienda antes de pujar?",
         "En general no, salvo que el ocupante lo permita. Por eso se valora por comparables y se descuenta el riesgo de que el interior necesite reforma."),
    ],
}

GUIAS["guias"] = {
    "title": "Guías: cuánto vale tu casa al heredar, vender, alquilar… | Idealisto",
    "desc": ("Guías prácticas para saber cuánto vale una vivienda en cada momento: herencia, divorcio, venta, "
             "alquiler y subasta. Con valoración gratuita por referencia catastral."),
    "miga": "Guías",
    "h1": "Guías: cuánto vale tu casa según tu situación",
    "respuesta": "El valor que importa cambia según el momento: aquí tienes qué cifra mirar y qué impuestos y plazos aplican en cada caso.",
    "html": """
<ul class="guias">
  <li><a href="/guias/cuanto-vale-casa-heredada/"><strong>He heredado una casa</strong></a>: valor de referencia, valor de mercado, Sucesiones y plusvalía.</li>
  <li><a href="/guias/valor-vivienda-divorcio/"><strong>Nos divorciamos</strong></a>: cómo se valora y se reparte la vivienda.</li>
  <li><a href="/guias/cuanto-pedir-al-vender-mi-casa/"><strong>Quiero vender</strong></a>: precio de salida, precio de cierre y gastos de la venta.</li>
  <li><a href="/guias/cuanto-cobrar-de-alquiler/"><strong>Quiero alquilar</strong></a>: renta de la zona, zonas tensionadas y rentabilidad.</li>
  <li><a href="/guias/valor-vivienda-subasta/"><strong>Me interesa una subasta</strong></a>: valor de subasta frente a valor de mercado.</li>
  <li><a href="/comprobar-precio/"><strong>Voy a comprar</strong></a>: comprueba si el precio que te piden está bien, si los metros cuadran y cuánto ITP pagarás.</li>
</ul>
""",
}
