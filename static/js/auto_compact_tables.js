// =======================================================
// EURO_GOALS v9.5.2 PRO+ – Auto-Compact Tables (mobile)
// - Works for any <table data-compact="true"> with <th data-key="...">
// - Keeps columns with lowest data-priority as "primary", collapses the rest
// - Builds expandable detail blocks per row on small screens
// =======================================================

(function () {
  const MOBILE_MAX = 640; // match CSS
  let applied = false;

  function isMobile() {
    return window.innerWidth <= MOBILE_MAX;
  }

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
    // Reset if disabling or going desktop
    if (!enable) {
      if (applied) {
        restoreRows(table);
        table.classList.remove('is-compact', 'compact-table');
      }
      return;
    }

    // Already compacted? ensure structure exists
    if (table.classList.contains('is-compact')) return;

    const meta = getColumnsMeta(table);
    if (!meta.length) return;

    // Decide primary columns (lowest priorities, keep 1 or 2)
    const sorted = [...meta].sort((a, b) => a.priority - b.priority);
    const primaryCols = sorted.slice(0, 2); // keep 2 main fields on mobile
    const secondaryCols = meta.filter(m => !primaryCols.find(p => p.index === m.index));

    // Transform each row
    const rows = Array.from(table.querySelectorAll('tbody tr'));
    rows.forEach((tr, ri) => {
      if (tr.dataset.compacted === '1') return;

      const tds = Array.from(tr.children);
      const data = {};
      meta.forEach((m, i) => {
        data[m.key] = (tds[i] && tds[i].textContent.trim()) || '';
      });

      // Build compact container
      const container = document.createElement('div');
      container.className = 'compact-row';

      // Primary text (joined)
      const primaryText = primaryCols
        .map(m => data[m.key])
        .filter(Boolean)
        .join(' • ');
      const primaryDiv = document.createElement('div');
      primaryDiv.className = 'compact-primary';
      primaryDiv.textContent = primaryText || '—';

      // Toggle
      const toggleBtn = document.createElement('button');
      toggleBtn.type = 'button';
      toggleBtn.className = 'compact-toggle';
      toggleBtn.setAttribute('aria-expanded', 'false');
      toggleBtn.setAttribute('aria-label', 'Show details');
      toggleBtn.textContent = '▸';

      // Details block
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

        grid.appendChild(label);
        grid.appendChild(val);
      });

      details.appendChild(grid);

      // Wire up toggle
      toggleBtn.addEventListener('click', () => {
        const expanded = details.classList.toggle('expanded');
        toggleBtn.setAttribute('aria-expanded', expanded ? 'true' : 'false');
        toggleBtn.textContent = expanded ? '▾' : '▸';
      });

      container.appendChild(primaryDiv);
      container.appendChild(toggleBtn);

      // Replace row cells with single cell holding the compact structure
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

  function restoreRows(table) {
    // Only possible if original HTML still around (we compact in-place).
    // Since we replaced row content, we cannot reconstruct original cells
    // without re-rendering from server. Easiest approach:
    // - When disabling compact (desktop), just reload the page.
    // Because data presentation desktop-first is the original template anyway.
    if (applied) {
      // Soft fallback: do nothing here; desktop reload will happen naturally on resize.
    }
  }

  // Initial run
  window.addEventListener('load', compactAll);
  window.addEventListener('resize', () => {
    // On crossing breakpoint, reload to restore original table structure.
    const wantMobile = isMobile();
    const hasCompact = document.querySelector('table[data-compact="true"].is-compact') !== null;
    if (wantMobile && !hasCompact) {
      compactAll();
    } else if (!wantMobile && hasCompact) {
      // Clean restore by reload to get original markup from server templates
      // (keeps logic simple & robust)
      window.location.reload();
    }
  });
})();
