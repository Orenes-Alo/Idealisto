// Calculadoras de Idealisto. Cada <form class="calc" data-calc="..."> se recalcula al escribir.
// Los datos fiscales (tipos por CCAA, tarifas, coeficientes) llegan en <script id="fiscal-json">.
(function () {
  const F = JSON.parse(document.getElementById('fiscal-json')?.textContent || '{}');
  const eur = n => (n == null || !isFinite(n)) ? '—' : new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(n);
  const pct = (n, d = 2) => (n == null || !isFinite(n)) ? '—' : n.toLocaleString('es-ES', { maximumFractionDigits: d, minimumFractionDigits: d }) + ' %';
  // Inputs type="number": el navegador ya entrega el valor con punto decimal.
  const val = (f, k) => { const v = parseFloat(f.elements[k]?.value); return isFinite(v) ? v : 0; };
  const sel = (f, k) => f.elements[k]?.value || '';
  const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const filas = rows => '<table class="calc-tabla">' + rows.map(([a, b, fuerte]) =>
    `<tr${fuerte ? ' class="total"' : ''}><td>${a}</td><td>${b}</td></tr>`).join('') + '</table>';

  // Tramos progresivos [{desde, hasta|null, tipo}] → cuota.
  const porTramos = (base, tramos) => {
    let cuota = 0;
    for (const t of tramos) {
      if (base <= t.desde) break;
      const tope = t.hasta == null ? base : Math.min(base, t.hasta);
      cuota += (tope - t.desde) * t.tipo / 100;
    }
    return cuota;
  };
  // Tarifa del ISD en formato BOE: [{base, cuota, tipo}] = cuota íntegra hasta `base` + tipo sobre el resto.
  const porEscala = (base, escala) => {
    let fila = escala[0];
    for (const e of escala) if (base >= e.base) fila = e;
    return fila.cuota + (base - fila.base) * fila.tipo / 100;
  };
  // ITP: tipo general, tramos progresivos o tipo único según el valor total.
  const cuotaItp = (base, c) => c.tramos ? porTramos(base, c.tramos)
    : c.unico ? base * c.unico.find(u => u.hasta == null || base <= u.hasta).tipo / 100
    : base * (c.tipo ?? c.general) / 100;

  const CALCS = {
    rentabilidad(f) {
      const precio = val(f, 'precio'), alquiler = val(f, 'alquiler');
      if (!precio || !alquiler) return '<p class="hint">Introduce el precio de compra y el alquiler mensual.</p>';
      const inversion = precio * (1 + val(f, 'gastos_pct') / 100) + val(f, 'reforma');
      const ingresos = alquiler * 12 * (1 - val(f, 'vacio') / 100);
      const gastos = val(f, 'comunidad') * 12 + val(f, 'ibi') + val(f, 'seguro') + ingresos * val(f, 'mantenimiento') / 100;
      const neto = ingresos - gastos;
      return filas([
        ['Inversión total (precio + gastos de compra + reforma)', eur(inversion)],
        ['Ingresos anuales (descontado el vacío)', eur(ingresos)],
        ['Gastos anuales', eur(gastos)],
        ['Rentabilidad bruta (alquiler anual / precio)', pct(alquiler * 12 / precio * 100), true],
        ['Rentabilidad neta (beneficio / inversión total)', pct(neto / inversion * 100), true],
        ['Años para recuperar la inversión', neto > 0 ? (inversion / neto).toLocaleString('es-ES', { maximumFractionDigits: 1 }) : '—'],
      ]) + '<p class="hint">Antes del IRPF. El alquiler de vivienda habitual puede tener reducciones en la renta según el contrato y la zona.</p>';
    },

    itp(f) {
      const c = F.itp?.[sel(f, 'ccaa')]; const precio = val(f, 'precio'), ref = val(f, 'referencia');
      if (!c || !precio) return '<p class="hint">Elige comunidad e introduce el precio.</p>';
      const base = Math.max(precio, ref);
      const red = c.reducidos?.find(r => r.id === sel(f, 'reducido'));
      const general = cuotaItp(base, c);
      const cuota = !red ? general : red.factor != null ? general * red.factor : cuotaItp(base, red);
      return filas([
        ['Base imponible', eur(base) + (ref > precio ? ' <small>(valor de referencia, mayor que el precio)</small>' : '')],
        ['Tipo efectivo', pct(cuota / base * 100) + (red ? ' <small>(' + esc(red.nombre) + ')</small>' : '')],
        ['ITP a pagar', eur(cuota), true],
      ]) + (ref > precio ? `<p class="aviso">El valor de referencia supera el precio: tributas por ${eur(ref)}. Si crees que está por encima del valor de mercado, puedes <a href="/valor-de-referencia/">impugnarlo</a>.</p>` : '')
        + (red ? `<p class="hint">Requisitos básicos: ${esc(red.requisitos)} Hay más condiciones (plazos, renta, escritura): compruébalas antes de aplicar el tipo reducido.</p>` : '')
        + (c.nota ? `<p class="hint">${esc(c.nota)}</p>` : '');
    },

    sucesiones(f) {
      const d = F.isd; if (!d) return '';
      const modo = sel(f, 'modo'), grupo = sel(f, 'grupo');
      const c = d.ccaa?.[sel(f, 'ccaa')]?.[modo];
      const valor = Math.max(val(f, 'valor'), val(f, 'referencia'));
      if (!c || !valor) return '<p class="hint">Elige comunidad, parentesco e introduce el valor del inmueble.</p>';
      const g12 = grupo === 'I' || grupo === 'II';
      if (c.propio && g12) {
        if (c.exento_hasta && valor <= c.exento_hasta)
          return filas([['Valor del inmueble', eur(valor)], ['Impuesto estimado', eur(0), true]]) + `<p class="hint">${esc(c.propio)}</p>`;
        return `<p class="aviso"><strong>Esta comunidad tiene un régimen propio que no calculamos automáticamente.</strong> ${esc(c.propio)} ${esc(c.nota || '')}</p><p class="hint">Para una cifra fiable, consulta con un asesor fiscal.</p>`;
      }
      // Reducciones (solo sucesiones): parentesco + vivienda habitual del fallecido (95 %, con límite por heredero).
      let reduccion = 0, redVivienda = 0;
      if (modo === 'sucesion') {
        reduccion = d.reducciones[grupo] || 0;
        if (grupo === 'I') reduccion = Math.min(d.reduccion_I_max, d.reducciones.I + d.reduccion_I_por_anio * Math.max(0, 21 - val(f, 'edad')));
        if (g12 && c.reduccion_I_II) reduccion = Math.max(reduccion, c.reduccion_I_II);
        if (f.elements.vivienda?.checked && grupo !== 'IV') redVivienda = Math.min(valor * d.vivienda_habitual.pct / 100, d.vivienda_habitual.limite);
      }
      const base = Math.max(0, valor - reduccion - redVivienda);
      if (c.hasta && g12 && base > c.hasta) {
        return `<p class="aviso"><strong>Por encima de ${eur(c.hasta)} de base liquidable cambian las reglas en esta comunidad</strong> y no damos cifra automática. ${esc(c.nota || '')}</p>`;
      }
      const coef = d.coeficientes[g12 ? 'I_II' : grupo][parseInt(sel(f, 'patrimonio') || '0', 10)];
      let cuota, bonif = 0, etiqueta;
      if (c.tarifa && g12) { cuota = porTramos(base, c.tarifa); etiqueta = 'Cuota con la tarifa autonómica'; }
      else {
        cuota = porEscala(base, d.tarifa) * coef;
        etiqueta = 'Cuota (tarifa estatal × coeficiente ' + coef.toLocaleString('es-ES') + ')';
        if (g12) bonif = c.bonif_tramos ? c.bonif_tramos.find(t => t[0] == null || base < t[0])[1] : (c.bonif_I_II || 0);
        else if (grupo === 'III' && c.bonif_III) bonif = c.bonif_III;
        else bonif = c.bonif_resto || 0;
      }
      return filas([
        ['Valor computable (mayor de valor declarado y de referencia)', eur(valor)],
        ['Reducciones', modo === 'sucesion' ? '− ' + eur(reduccion + redVivienda) : 'no hay reducción por parentesco en donaciones'],
        ['Base liquidable', eur(base)],
        [etiqueta, eur(cuota)],
        ['Bonificación autonómica', bonif ? pct(bonif, bonif % 1 ? 1 : 0) : '—'],
        ['Impuesto estimado', eur(cuota * (1 - bonif / 100)), true],
      ]) + `<p class="hint">${esc(c.nota || '')} Estimación con las reglas generales; hay reducciones propias (vivienda habitual mejorada, discapacidad, empresa familiar) y requisitos formales (documento público, plazos) que pueden cambiar el resultado.</p>`;
    },

    plusvalia(f) {
      const d = F.plusvalia; if (!d) return '';
      const vcSuelo = val(f, 'vc_suelo'), vcTotal = val(f, 'vc_total'), anios = Math.max(0, val(f, 'anios'));
      const tipo = Math.min(d.tipo_max, val(f, 'tipo') || d.tipo_max);
      const compra = val(f, 'compra'), venta = val(f, 'venta');
      if (!vcSuelo) return '<p class="hint">Introduce el valor catastral del suelo (está en el recibo del IBI).</p>';
      if (compra && venta && venta <= compra)
        return filas([['Ganancia real', eur(venta - compra)], ['Plusvalía municipal', eur(0), true]]) + '<p class="aviso">Si vendes por menos de lo que compraste no hay incremento de valor y no se paga plusvalía municipal (art. 104.5 TRLRHL). Guarda las escrituras como prueba.</p>';
      const fecha = sel(f, 'fecha') || new Date().toISOString().slice(0, 10);
      const tabla = d.tablas.filter(t => t.desde <= fecha).pop();
      const a = Math.floor(anios);
      const coef = a < 1 ? tabla.coef[0] * Math.floor(anios * 12) / 12 : tabla.coef[Math.min(20, a)];
      const baseObj = vcSuelo * coef;
      const baseReal = (compra && venta) ? (venta - compra) * Math.min(1, vcSuelo / (vcTotal || vcSuelo)) : null;
      const base = baseReal != null ? Math.min(baseObj, baseReal) : baseObj;
      return filas([
        [`Método objetivo: suelo × coeficiente ${coef.toLocaleString('es-ES', { maximumFractionDigits: 4 })}`, eur(baseObj)],
        ['Método real: ganancia × peso del suelo en el valor catastral', baseReal != null ? eur(baseReal) : '<small>introduce compra, venta y valor catastral total</small>'],
        ['Base imponible (la menor)', eur(base)],
        ['Tipo municipal', pct(tipo, 1)],
        ['Plusvalía a pagar', eur(base * tipo / 100), true],
      ]) + `<p class="hint">Coeficientes máximos de ${esc(tabla.norma)}. Tu ayuntamiento puede aplicar coeficientes y tipos menores, reducir el valor del suelo hasta un 15 % y bonificar herencias de vivienda habitual: consulta su ordenanza.</p>`;
    },
  };

  document.querySelectorAll('form.calc').forEach(f => {
    const out = f.querySelector('.calc-out'); const fn = CALCS[f.dataset.calc];
    let usado = false;
    const pintar = () => {
      // ITP: los tipos reducidos dependen de la comunidad.
      if (f.dataset.calc === 'itp' && f.elements.reducido) {
        const c = F.itp?.[sel(f, 'ccaa')]; const s = f.elements.reducido;
        if (s.dataset.ccaa !== sel(f, 'ccaa')) {
          s.innerHTML = ['<option value="">Tipo general</option>'].concat((c?.reducidos || []).map(r =>
            `<option value="${esc(r.id)}">${esc(r.nombre)}</option>`)).join('');
          s.dataset.ccaa = sel(f, 'ccaa');
        }
      }
      const edad = f.querySelector('.campo-edad'); if (edad) edad.hidden = !(sel(f, 'grupo') === 'I' && sel(f, 'modo') === 'sucesion');
      const viv = f.querySelector('.campo-vivienda'); if (viv) viv.hidden = sel(f, 'modo') !== 'sucesion';
      out.innerHTML = fn(f);
    };
    const uso = () => { if (!usado && window.gtag) { usado = true; gtag('event', 'calculadora_uso', { tipo: f.dataset.calc }); } };
    f.addEventListener('input', () => { pintar(); uso(); });
    f.addEventListener('change', pintar);
    f.addEventListener('submit', e => { e.preventDefault(); pintar(); });
    pintar();
  });
})();
