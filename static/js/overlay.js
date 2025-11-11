(function(){
  const root = document.getElementById('eg-overlay');
  if(!root) return;

  const btnToggle = document.getElementById('btnToggleOverlay');
  const btnClose = document.getElementById('ovClose');
  const btnCompact = document.getElementById('ovCompact');
  const heatmapCanvas = document.getElementById('ovHeatmap');
  const ctx = heatmapCanvas.getContext('2d');
  const elInsights = document.getElementById('ovInsights');
  const elOdds = document.getElementById('ovOdds');
  const elSignals = document.getElementById('ovSignals');

  let state = { enabled: true, opacity: .94, compact: true, hotkey: 'KeyO' };

  async function init(){
    try { state = await fetch('/overlay/state').then(r=>r.json()); } catch {}
    root.style.opacity = state.opacity;
    root.classList.toggle('hidden', !state.enabled);
  }

  function toggle(){
    fetch('/overlay/toggle', {method:'POST'}).then(r=>r.json()).then(s=>{
      state = s;
      root.classList.toggle('hidden', !state.enabled);
    }).catch(()=>{ root.classList.toggle('hidden'); });
  }

  function drawHeatmap(cells){
    const n = cells.length;
    const w = heatmapCanvas.width, h = heatmapCanvas.height;
    const cw = Math.floor(w/n), ch = Math.floor(h/n);
    for(let y=0;y<n;y++){
      for(let x=0;x<n;x++){
        const v = cells[y][x];
        const shade = Math.floor(255 - v*200);
        ctx.fillStyle = `rgb(${shade},${Math.max(40,shade)},255)`;
        ctx.fillRect(x*cw, y*ch, cw, ch);
      }
    }
  }

  function renderInsights(ins){
    elInsights.innerHTML = `
      <div>xG Home: <b>${ins.xg_home??'-'}</b></div>
      <div>xG Away: <b>${ins.xg_away??'-'}</b></div>
      <div>Likely Goals: <b>${ins.likely_goals??'-'}</b></div>`;
  }

  function renderOdds(od){
    elOdds.innerHTML = '';
    Object.entries(od||{}).forEach(([k,v])=>{
      const kEl = document.createElement('div');
      const vEl = document.createElement('div');
      kEl.textContent = k; vEl.textContent = v;
      elOdds.appendChild(kEl); elOdds.appendChild(vEl);
    });
  }

  function renderSignals(sig){
    elSignals.innerHTML = '';
    (sig||[]).forEach(s=>{
      const div = document.createElement('div');
      div.className = 'item';
      div.textContent = `${s.type} – ${s.market} ${s.dir} (${s.delta})`;
      elSignals.appendChild(div);
    });
  }

  function showWithPayload(p){
    if(!state.enabled) root.classList.remove('hidden');
    drawHeatmap(p.goal_matrix?.heatmap?.cells||[[0]]);
    renderInsights(p.goal_matrix?.insights||{});
    renderOdds(p.smartmoney?.odds||{});
    renderSignals(p.smartmoney?.signals||[]);
  }

  window.egOverlay = { showWithPayload };

  window.addEventListener('keydown', (e)=>{
    if(e.code === (state.hotkey||'KeyO')){
      e.preventDefault(); toggle();
    }
  });

  btnToggle?.addEventListener('click', toggle);
  btnClose?.addEventListener('click', toggle);
  btnCompact?.addEventListener('click', ()=> root.classList.toggle('compact'));
  init();
})();
