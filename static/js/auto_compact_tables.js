(function () {
  const MOBILE_MAX = 640;
  let applied = false;

  function isMobile() { return window.innerWidth <= MOBILE_MAX; }

  function compactAll() {
    document.querySelectorAll('table[data-compact="true"]').forEach(table => {
      compactTable(table, isMobile());
    });
  }

  function getColumnsMeta(table) {
    const ths = Array.from(table.querySelectorAll('thead th'));
    return ths.map((th, idx) => ({
      index: idx,
      key: th.getAttribute('data-key') || `col${idx}`,
      label: th.textContent.trim(),
      priority: parseInt(th.getAttribute('data-priority') || '999', 10)
    }));
  }

  function compactTable(table, enable) {
    if (!enable) {
      if (applied) {
        // no-op; desktop reload restores original markup
      }
      return;
    }
    if (table.classList.contains('is-compact')) return;

    const meta = getColumnsMeta(table);
    if (!meta.length) return;

    const sorted = [...meta].sort((a, b) => a.priority - b.priority);
    const primaryCols = sorted.slice(0, 2);
    const secondaryCols = meta.filter(m => !primaryCols.find(p => p.index === m.index));

    const rows = Array.from(table.querySelectorAll('tbody tr'));
    rows.forEach(tr => {
      if (tr.dataset.compacted === '1') return;

      const tds = Array.from(tr.children);
      const data = {};
      meta.forEach((m, i) => data[m.key] = (tds[i] && tds[i].textContent.trim()) || '');

      const container = document.createElement('div');
      container.className = 'compact-row';

      const primaryText = primaryCols.map(m => data[m.key]).filter(Boolean).join(' • ');
      const primaryDiv = document.createElement('div');
      primaryDiv.className = 'compact-primary';
      primaryDiv.textContent = primaryText || '—';

      const toggleBtn = document.createElement('button');
      toggleBtn.type = 'button';
      toggleBtn.className = 'compact-toggle';
      toggleBtn.setAttribute('aria-expanded', 'false');
      toggleBtn.textContent = '▸';

      const details = document.createElement('div');
      details.className = 'row-details';
      const grid = document.createElement('div');
      grid.className = 'details-grid';

      secondaryCols.forEach(col => {
        const label = document.createElement('div');
        label.className = 'detail-label';
        label.textContent = col.label;

        const val = document.createElement('div');
        val.className = 'detail-value';
        val.textContent = data[col.key] || '—';

        grid.appendChild(label); grid.appendChild(val);
      });

      details.appendChild(grid);

      toggleBtn.addEventListener('click', () => {
        const expanded = details.classList.toggle('expanded');
        toggleBtn.setAttribute('aria-expanded', expanded ? 'true' : 'false');
        toggleBtn.textContent = expanded ? '▾' : '▸';
      });

      container.appendChild(primaryDiv);
      container.appendChild(toggleBtn);

      const td = document.createElement('td');
      td.colSpan = meta.length;
      td.appendChild(container);
      td.appendChild(details);

      tr.innerHTML = '';
      tr.appendChild(td);
      tr.dataset.compacted = '1';
    });

    table.classList.add('is-compact', 'compact-table');
    applied = true;
  }

  window.addEventListener('load', compactAll);
  window.addEventListener('resize', () => {
    const wantMobile = isMobile();
    const hasCompact = document.querySelector('table[data-compact="true"].is-compact') !== null;
    if (wantMobile && !hasCompact) {
      compactAll();
    } else if (!wantMobile && hasCompact) {
      window.location.reload();
    }
  });
})();
