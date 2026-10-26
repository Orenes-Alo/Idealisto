// Buscador de referencia catastral por dirección (provincia → municipio → calle → número).
// Se monta sobre cualquier <div class="buscador" data-modo="home|enlace">.
(function () {
  const PROVS = JSON.parse(document.getElementById('provincias-json').textContent);
  const debounce = (fn, ms) => { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; };
  const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const get = async (url) => {
    const r = await fetch(url);
    const d = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(d.error || 'No hemos podido consultar el Catastro. Inténtalo en un momento.');
    return d;
  };
  const planta = p => ({ '00': 'Bajo', 'BJ': 'Bajo', 'SM': 'Semisótano', 'SS': 'Sótano', 'EN': 'Entreplanta', 'AT': 'Ático' }[p] || (/^B\d?$/.test(p) ? 'Bajo' : /^-?\d+$/.test(p) ? (parseInt(p, 10) < 0 ? 'Sótano ' + Math.abs(parseInt(p, 10)) : parseInt(p, 10) + 'º')  : p));

  document.querySelectorAll('.buscador').forEach(root => {
    const modo = root.dataset.modo || 'enlace';
    root.innerHTML = `
      <div class="b-grid">
        <label>Provincia<select class="b-prov"><option value="">Elige provincia</option>${PROVS.map(p => `<option>${esc(p[1])}</option>`).join('')}</select></label>
        <label>Municipio<input class="b-mun" autocomplete="off" placeholder="Escribe el municipio" disabled></label>
        <label class="b-ancha">Calle<input class="b-calle" autocomplete="off" placeholder="Nombre de la calle, sin «calle» ni «avenida»" disabled></label>
        <label>Número<input class="b-num" inputmode="numeric" placeholder="Nº" disabled></label>
      </div>
      <div class="b-sug" hidden></div>
      <button class="btn small b-go" type="button" disabled>Buscar inmuebles</button>
      <p class="err b-err" aria-live="polite"></p>
      <div class="b-res"></div>`;
    const $ = s => root.querySelector(s);
    const prov = $('.b-prov'), mun = $('.b-mun'), calle = $('.b-calle'), num = $('.b-num'), sug = $('.b-sug'), go = $('.b-go'), err = $('.b-err'), res = $('.b-res');
    let munOk = '', via = null;

    const sugerir = (items, pintar, elegir) => {
      if (!items.length) { sug.hidden = true; return; }
      sug.innerHTML = items.map((it, i) => `<button type="button" data-i="${i}">${pintar(it)}</button>`).join('');
      sug.hidden = false;
      sug.querySelectorAll('button').forEach(b => b.addEventListener('click', () => { elegir(items[+b.dataset.i]); sug.hidden = true; }));
    };
    const listo = () => { go.disabled = !(munOk && via && num.value.trim()); };

    prov.addEventListener('change', () => {
      munOk = ''; via = null; mun.value = ''; calle.value = ''; res.innerHTML = '';
      mun.disabled = !prov.value; calle.disabled = true; num.disabled = true; listo();
      if (prov.value) mun.focus();
    });
    mun.addEventListener('input', debounce(async () => {
      munOk = ''; via = null; calle.disabled = true; num.disabled = true; listo(); err.textContent = '';
      if (mun.value.trim().length < 2) { sug.hidden = true; return; }
      try {
        const d = await get(`/api/catastro/municipios?prov=${encodeURIComponent(prov.value)}&q=${encodeURIComponent(mun.value)}`);
        sugerir(d.municipios, m => esc(m), m => { mun.value = m; munOk = m; calle.disabled = false; calle.focus(); listo(); });
      } catch (e) { err.textContent = e.message; }
    }, 300));
    calle.addEventListener('input', debounce(async () => {
      via = null; num.disabled = true; listo(); err.textContent = '';
      if (calle.value.trim().length < 3) { sug.hidden = true; return; }
      try {
        const d = await get(`/api/catastro/calles?prov=${encodeURIComponent(prov.value)}&mun=${encodeURIComponent(munOk)}&q=${encodeURIComponent(calle.value)}`);
        if (!d.calles.length) { sug.hidden = true; err.textContent = 'No encontramos esa calle. Prueba con una sola palabra del nombre.'; return; }
        sugerir(d.calles, c => `<b>${esc(c.tv)}</b> ${esc(c.calle)}${c.nucleo ? ` <small>· ${esc(c.nucleo)}</small>` : ''}`,
          c => { via = c; calle.value = `${c.tv} ${c.calle}`; num.disabled = false; num.focus(); listo(); });
      } catch (e) { err.textContent = e.message; }
    }, 350));
    num.addEventListener('input', listo);

    // Páginas de zona: provincia y municipio ya puestos (al abrir el desplegable, para no mover la página al cargar).
    if (root.dataset.prov) {
      let hecho = false;
      const prefill = () => {
        if (hecho) return; hecho = true;
        prov.value = root.dataset.prov; prov.dispatchEvent(new Event('change'));
        if (root.dataset.mun) { mun.value = root.dataset.mun; mun.dispatchEvent(new Event('input')); }
      };
      const det = root.closest('details');
      if (det) det.addEventListener('toggle', () => { if (det.open) prefill(); }); else prefill();
    }
    num.addEventListener('keydown', e => { if (e.key === 'Enter' && !go.disabled) { e.preventDefault(); go.click(); } });

    go.addEventListener('click', async () => {
      err.textContent = ''; res.innerHTML = '<p class="hint">Consultando el Catastro…</p>'; go.disabled = true;
      try {
        const d = await get(`/api/catastro/inmuebles?prov=${encodeURIComponent(prov.value)}&mun=${encodeURIComponent(munOk)}&tv=${encodeURIComponent(via.tv)}&calle=${encodeURIComponent(via.calle)}&num=${encodeURIComponent(num.value.trim())}`);
        if (window.gtag) gtag('event', 'buscador_direccion', { encontrados: d.inmuebles.length });
        if (!d.inmuebles.length) {
          res.innerHTML = `<p class="hint">${esc(d.error || 'No hay inmuebles en ese número.')}${d.numeros.length ? ' Números con inmuebles en esa calle: ' + d.numeros.map(esc).join(', ') + '.' : ''}</p>`;
          return;
        }
        const filas = d.inmuebles.map(x => `<tr><td>${esc([x.escalera && x.escalera !== 'T' ? 'Esc. ' + x.escalera : '', x.planta ? planta(x.planta) : '', x.puerta && x.puerta !== 'OS' ? 'Pta. ' + x.puerta : ''].filter(Boolean).join(' · ') || 'Inmueble completo')}</td>
          <td>${esc(x.uso)}${x.superficie ? ' · ' + x.superficie + ' m²' : ''}</td><td class="mono">${esc(x.rc)}</td>
          <td><a class="btn small" href="/?rc=${esc(x.rc)}#valorar" data-rc="${esc(x.rc)}">Valorar</a></td></tr>`).join('');
        res.innerHTML = `<p class="hint">${d.inmuebles.length} inmueble${d.inmuebles.length > 1 ? 's' : ''} en este número. Elige el tuyo:</p>
          <div class="scroll"><table class="b-tabla"><thead><tr><th>Planta y puerta</th><th>Uso</th><th>Referencia catastral</th><th></th></tr></thead><tbody>${filas}</tbody></table></div>`;
        if (modo === 'comprobar') res.querySelectorAll('a[data-rc]').forEach(a => {
          a.textContent = 'Elegir';
          a.addEventListener('click', ev => {
            ev.preventDefault();
            document.getElementById('rc').value = a.dataset.rc;
            root.closest('details')?.removeAttribute('open');
            const p = document.getElementById('precio');
            if (p.value) document.getElementById('fc').requestSubmit(); else p.focus();
          });
        });
        if (modo === 'home') res.querySelectorAll('a[data-rc]').forEach(a => a.addEventListener('click', ev => {
          ev.preventDefault();
          const inp = document.getElementById('rc'); inp.value = a.dataset.rc; inp.dispatchEvent(new Event('input'));
          root.closest('details')?.removeAttribute('open');
          document.getElementById('f').requestSubmit();
        }));
      } catch (e) { res.innerHTML = ''; err.textContent = e.message; }
      finally { listo(); }
    });
  });
})();
