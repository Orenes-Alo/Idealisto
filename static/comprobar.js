// «¿Está bien de precio?» (/comprobar-precio/): RC + precio → semáforo. Sin cuenta se ve el veredicto;
// con cuenta, también el rango, la mediana y el precio de cierre.
(function () {
  const $ = s => document.querySelector(s);
  const f = $('#fc'), rc = $('#rc'), precio = $('#precio'), m2 = $('#m2'), go = $('#go'), e = $('#e'), ld = $('#ld'), res = $('#res');
  const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const eur = n => n == null ? '—' : Math.round(n).toLocaleString('es-ES', { useGrouping: true }) + ' €';
  const r1000 = n => Math.round(n / 1000) * 1000;
  const SEM = {
    sospechoso: ['Demasiado barato: revisa antes de seguir', 'mal'],
    gran_precio: ['Gran precio', 'bien'],
    justo: ['Precio justo', 'justo'],
    caro: ['Caro', 'caro'],
  };
  const CONSEJO = {
    sospechoso: 'Un precio así casi siempre tiene explicación: ocupación, nuda propiedad, cargas, un estado muy malo o unos metros que no cuadran. Puede ser una oportunidad, pero no pagues ninguna señal sin revisar antes la lista de abajo.',
    gran_precio: 'Está en el tramo bajo de la zona: piden menos que por 3 de cada 4 inmuebles comparables. Merece la pena moverse rápido, pero comprueba antes el estado y la nota simple: a veces lo barato tiene motivo.',
    justo: 'Está dentro de lo que se pide normalmente por inmuebles como este. Aun así hay margen: los precios de anuncio suelen cerrarse algo por debajo.',
    caro: 'Piden más que por 3 de cada 4 inmuebles comparables. Puede estar justificado (reforma reciente, vistas, garaje o trastero incluidos, planta alta con ascensor); si no, negocia con la valoración en la mano.',
  };

  // Prefill por URL: ?rc=…&precio=…&m2=… (mini formularios de las páginas de zona); con RC y precio, comprueba solo
  const q = new URLSearchParams(location.search);
  if (q.get('rc')) rc.value = q.get('rc');
  if (q.get('precio')) precio.value = q.get('precio');
  if (q.get('m2')) m2.value = q.get('m2');
  if (q.get('rc') && q.get('precio')) setTimeout(() => f.requestSubmit(), 50);
  else if (q.get('rc')) precio.focus();

  function pinta(d) {
    const [tit, cls] = SEM[d.veredicto];
    const dif = d.diferencia_pct === 0 ? 'en la valoración de mercado'
      : `un <strong>${Math.abs(d.diferencia_pct)} % ${d.diferencia_pct > 0 ? 'por encima' : 'por debajo'}</strong> de su valoración de mercado`;
    const ficha = [d.ficha.uso, d.ficha.superficie_m2 ? d.ficha.superficie_m2 + ' m² en el Catastro' : '', d.ficha.anio_construccion ? 'de ' + d.ficha.anio_construccion : ''].filter(Boolean).join(' · ');
    let cifras = '';
    if (d.valor_central != null) {
      cifras = `<div class="kv">
        <div><small>Valoración de mercado</small><strong>${eur(r1000(d.valor_central))}</strong></div>
        <div><small>Rango habitual</small><strong>${eur(r1000(d.valor_min))} – ${eur(r1000(d.valor_max))}</strong></div>
        <div><small>Por debajo, sospechoso</small><strong>${eur(r1000(d.umbral))}</strong></div>
        <div><small>Precio de cierre estimado</small><strong>${d.cierre_estimado ? eur(r1000(d.cierre_estimado)) : '—'}</strong></div>
      </div>`;
    } else {
      cifras = `<div class="cta-registro"><strong>¿Quieres ver las cifras?</strong> Con tu cuenta gratuita ves la valoración de mercado, el rango habitual y el precio al que se suele cerrar la venta, para negociar con datos.
        <a class="btn small" href="/?rc=${encodeURIComponent(d.rc)}#valorar">Ver la valoración completa</a></div>`;
    }
    let metros = '';
    if (d.m2) {
      metros = d.m2.aviso
        ? `<p class="aviso"><strong>Ojo con los metros:</strong> el anuncio dice ${d.m2.anuncio} m² y el Catastro ${d.m2.catastro} m² (${d.m2.dif_pct > 0 ? '+' : ''}${d.m2.dif_pct} %). Lo normal es hasta un 10–15 % más por las zonas comunes; una diferencia así merece una pregunta al vendedor.</p>`
        : `<p class="hint">Metros: el anuncio dice ${d.m2.anuncio} m² y el Catastro ${d.m2.catastro} m² (${d.m2.dif_pct > 0 ? '+' : ''}${d.m2.dif_pct} %), una diferencia normal por las zonas comunes.</p>`;
    }
    const itp = d.itp ? `<p class="hint">ITP estimado en ${esc(d.itp.ccaa)}: <strong>${eur(d.itp.cuota)}</strong> (tipo general, ${String(d.itp.tipo).replace('.', ',')} %), sobre el precio o sobre el valor de referencia si es mayor. Con reducciones por edad o familia puede ser menos: <a href="/calculadoras/itp/">calcúlalo</a>.</p>` : '';
    const aviso = d.confianza === 'baja' ? '<p class="hint">Hay pocos comparables cerca: tómalo como orientación.</p>' : '';
    res.innerHTML = `<div class="semaforo s-${cls}" id="resultado">
      <div class="sem-tit">${tit}</div>
      <p>${esc(d.ficha.direccion || 'El inmueble')}${ficha ? ' <small>(' + esc(ficha) + ')</small>' : ''}: por ${eur(d.precio)} está ${dif}.</p>
      ${cifras}
      <p>${CONSEJO[d.veredicto]}</p>${metros}${itp}${aviso}
    </div>`;
    res.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  f.addEventListener('submit', async ev => {
    ev.preventDefault(); e.textContent = '';
    if (!rc.value.trim()) { e.textContent = 'Introduce la referencia catastral o búscala por dirección.'; return; }
    if (!(Number(precio.value) >= 3000)) { e.textContent = 'Introduce el precio que te piden, en euros.'; precio.focus(); return; }
    go.disabled = true; go.textContent = 'Comprobando…'; ld.style.display = 'block'; res.innerHTML = '';
    try {
      const r = await fetch('/api/comprobar', { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rc: rc.value, precio: Number(precio.value), m2: m2.value ? Number(m2.value) : null }) });
      const d = await r.json().catch(() => ({}));
      if (!r.ok) { e.textContent = d.error || 'No hemos podido comprobarlo. Inténtalo en un momento.'; return; }
      pinta(d);
      if (window.gtag) gtag('event', 'comprobar_ok', { veredicto: d.veredicto, registrado: d.valor_central != null });
    } catch (_) { e.textContent = 'No hemos podido comprobarlo. Inténtalo en un momento.'; }
    finally { go.disabled = false; go.textContent = 'Comprobar precio'; ld.style.display = 'none'; }
  });
})();
