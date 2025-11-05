// =======================================================
// EURO_GOALS v9.5.3 PRO+ – Inline Filters + Pinned Column
// - Attaches filters to tables with given form controls
// - Keeps first column sticky (desktop); disabled by compact mode
// =======================================================

(function () {
  function pinFirstColumn(table) {
    // Add sticky-col to first TH and first TD of each row (desktop only)
    if (window.innerWidth <= 640) return; // mobile disables pin
    const theadFirst = table.querySelector('thead th:first-child');
    if (theadFirst) theadFirst.classList.add('sticky-col');

    table.querySelectorAll('tbody tr').forEach(tr => {
      const td = tr.querySelector('td:first-child');
      if (td) td.classList.add('sticky-col');
    });
  }

  function unpinFirstColumn(table) {
    table.querySelectorAll('.sticky-col').forEach(el => el.classList.remove('sticky-col'));
  }

  function attachFilters(cfg) {
    const { form, table, map } = cfg;
    if (!form || !table) return;

    const tbody = table.querySelector('tbody');
    if (!tbody) return;

    // Helper: get row data by column indices
    const getRow = (tr) => Array.from(tr.children).map(td => (td.textContent || '').trim());

    function apply() {
      const values = Object.fromEntries(new FormData(form).entries());

      const search = (values.search || '').toLowerCase();
      const pred = (values.prediction || '').toLowerCase();
      const minMove = parseFloat(values.minMove || '0');
      const alertOnly = values.alertOnly === 'on';
      const minConf = parseFloat(values.minConf || '0');

      let visible = 0;
      tbody.querySelectorAll('tr').forEach(tr => {
        const tds = Array.from(tr.children);
        if (!tds.length) return;

        // If compact mode replaced row with single cell (auto-compact), filter inside that single cell
        const rowText = tr.textContent.toLowerCase();

        // base conditions per table
        let ok = true;

        if (map.matchIdx !== undefined) {
          ok = ok && rowText.includes(search);
        }

        if (map.movementIdx !== undefined && !isNaN(minMove) && minMove > 0) {
          const mvTxt = (tds[map.movementIdx]?.textContent || '0').replace(/[^\d\.\-]/g,'');
          const mv = parseFloat(mvTxt || '0');
          ok = ok && mv >= minMove;
        }

        if (map.alertIdx !== undefined && alertOnly) {
          const av = (tds[map.alertIdx]?.textContent || '').toLowerCase();
          ok = ok && (av.includes('alert') || av.includes('⚠') || av.includes('🔔'));
        }

        if (map.predIdx !== undefined && pred) {
          const pv = (tds[map.predIdx]?.textContent || '').toLowerCase();
          ok = ok && pv.includes(pred);
        }

        if (map.confIdx !== undefined && !isNaN(minConf) && minConf > 0) {
          const cvTxt = (tds[map.confIdx]?.textContent || '0').replace(/[^\d\.]/g,'');
          const cv = parseFloat(cvTxt || '0');
          ok = ok && cv >= minConf;
        }

        tr.style.display = ok ? '' : 'none';
        if (ok) visible += 1;
      });

      // Update count badge if exists
      const badge = form.querySelector('[data-count]');
      if (badge) badge.textContent = visible.toString();
    }

    form.addEventListener('input', apply);
    form.addEventListener('change', apply);

    // Initial pin + filter
    pinFirstColumn(table);
    apply();

    // Re-pin on dynamic updates (e.g., data refresh via system_summary.js)
    const obs = new MutationObserver(() => {
      unpinFirstColumn(table);
      pinFirstColumn(table);
      apply();
    });
    obs.observe(tbody, { childList: true, subtree: true });

    // On resize, if crossing breakpoint, re-evaluate pinning
    window.addEventListener('resize', () => {
      unpinFirstColumn(table);
      pinFirstColumn(table);
    });
  }

  window.addEventListener('DOMContentLoaded', () => {
    // SMARTMONEY
    attachFilters({
      form: document.getElementById('filters-sm'),
      table: document.getElementById('smartmoney-table-el'),
      map: { matchIdx: 0, lineIdx: 1, movementIdx: 2, alertIdx: 3 }
    });

    // GOALMATRIX
    attachFilters({
      form: document.getElementById('filters-gm'),
      table: document.getElementById('goalmatrix-table-el'),
      map: { matchIdx: 0, ouIdx: 1, predIdx: 2, confIdx: 3 }
    });
  });
})();
