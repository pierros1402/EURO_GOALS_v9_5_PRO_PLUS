(function(){
  const $ = (q,el=document)=>el.querySelector(q);
  const $$ = (q,el=document)=>Array.from(el.querySelectorAll(q));

  const btnDJ = $('#btnDowJones');
  const dd = $('#djDropdown');
  const settings = $('#eg-settings');
  const btnSettings = $('#btnSettings');

  const inlineHost = $('#dj-inline');
  const grid = $('#dj-grid');
  const chips = $('#dj-chips');
  const statusEl = $('#dj-status');
  const footer = $('#dj-footer');

  let timer = null;
  const DEFAULT_AUTO = (parseInt((window.djRefreshSeconds||10),10)||10) * 1000;

  function getMode(){
    return localStorage.getItem('dj_mode') || 'inline';
  }
  function setMode(m){
    localStorage.setItem('dj_mode', m);
    updateUIForMode();
  }

  function pos(el, anchor){
    const r = anchor.getBoundingClientRect();
    el.style.position='absolute';
    el.style.left = r.left + 'px';
    el.style.top = (r.bottom + 4 + window.scrollY) + 'px';
  }

  function toggleDropdown(){
    dd.classList.toggle('hidden');
    if(!dd.classList.contains('hidden')) pos(dd, btnDJ);
  }

  function toggleSettings(){
    settings.classList.toggle('hidden');
  }

  function updateUIForMode(){
    const m = getMode();
    // highlight selections
    $$("[data-dj]").forEach(b=>{
      if (b.dataset.dj===m) b.classList.add('active'); else b.classList.remove('active');
    });
    // show/hide inline panel
    inlineHost?.classList.toggle('hidden', m!=='inline');
    if (m==='inline') startAuto(); else stopAuto();
    if (m==='full') window.open('/dowjones','_blank');
  }

  async function fetchLive(){
    try{
      statusEl && (statusEl.textContent='refreshing…');
      const r = await fetch('/api/dowjones/live');
      const j = await r.json();
      render(j);
      statusEl && (statusEl.innerHTML = `<span class="ok">ok</span> · tick ${j.tick} · ts ${j.ts}`);
    }catch(e){ statusEl && (statusEl.textContent='error'); }
  }

  function render(data){
    // chips
    chips && (chips.innerHTML='');
    if (data.mock){ const m = document.createElement('div'); m.className='chip'; m.textContent='Mock Mode'; chips?.appendChild(m); }

    // grid
    if(!grid) return;
    grid.innerHTML='';
    (data.rows||[]).forEach(row=>{
      const card = document.createElement('div');
      card.className='dj-card';
      card.innerHTML = `
        <div class="dj-row">
          <div>
            <div class="dj-id"># ${row.fixture_id}</div>
            <div class="dj-dom">Dominant: ${row.dominant ?? '-'}</div>
          </div>
          <div class="dj-score">${Number(row.score||0).toFixed(4)}</div>
        </div>
        <div class="dj-mk">${Object.entries(row.markets||{}).map(([k,v])=>`<span>${k}: ${Number(v).toFixed(4)}</span>`).join('')}</div>`;
      grid.appendChild(card);
    });
    footer && (footer.textContent = `Items ${data.rows?.length||0}`);
  }

  function startAuto(){ stopAuto(); timer = setInterval(fetchLive, DEFAULT_AUTO); fetchLive(); }
  function stopAuto(){ if(timer){ clearInterval(timer); timer=null; } }

  // Events
  btnDJ && btnDJ.addEventListener('click', toggleDropdown);
  btnSettings && btnSettings.addEventListener('click', toggleSettings);
  dd && dd.addEventListener('click', e=>{
    const b = e.target.closest('.eg-dd-item');
    if(!b) return; setMode(b.dataset.dj); dd.classList.add('hidden');
  });
  $$('#eg-settings [data-dj]').forEach(b=> b.addEventListener('click', ()=> setMode(b.dataset.dj)));

  // theme toggles (light/dark/auto)
  $$('#eg-settings .eg-theme').forEach(b=> b.addEventListener('click', ()=>{
    const t = b.dataset.theme; localStorage.setItem('eg_theme', t); applyTheme();
    $$('#eg-settings .eg-theme').forEach(x=>x.classList.toggle('active', x===b));
  }));
  function applyTheme(){
    const t = localStorage.getItem('eg_theme')||'auto';
    document.documentElement.dataset.theme=t;
  }

  // init
  window.addEventListener('click', (e)=>{
    if (!dd?.contains(e.target) && e.target!==btnDJ) dd?.classList.add('hidden');
  });
  applyTheme();
  updateUIForMode();
})();
________________________________________
