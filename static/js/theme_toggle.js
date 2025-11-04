// ========================================================
// EURO_GOALS v9.5.0 PRO+ – Theme Toggle (Light/Dark/Auto)
// - Persists to localStorage ("eg_theme")
// - Respects prefers-color-scheme when 'auto'
// ========================================================

const THEME_KEY = 'eg_theme'; // 'light' | 'dark' | 'auto'

function applyTheme(theme) {
  const html = document.documentElement;
  html.setAttribute('data-theme', theme);
  updateIcon(theme);
}

function updateIcon(theme) {
  const icon = document.getElementById('theme-icon');
  if (!icon) return;

  const effective = getEffectiveTheme(theme);
  // Icon indicates the *other* mode available to switch to quickly
  icon.textContent = effective === 'dark' ? '🌞' : '🌙';
}

function getEffectiveTheme(theme) {
  if (theme === 'auto') {
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
      ? 'dark'
      : 'light';
  }
  return theme;
}

function loadTheme() {
  const saved = localStorage.getItem(THEME_KEY) || 'auto';
  applyTheme(saved);
}

function nextTheme(current) {
  // Cycle: auto -> dark -> light -> auto
  if (current === 'auto') return 'dark';
  if (current === 'dark') return 'light';
  return 'auto';
}

document.addEventListener('DOMContentLoaded', () => {
  loadTheme();

  const toggleBtn = document.getElementById('theme-toggle');
  if (!toggleBtn) return;

  toggleBtn.addEventListener('click', () => {
    const current = document.documentElement.getAttribute('data-theme') || 'auto';
    const next = nextTheme(current);
    localStorage.setItem(THEME_KEY, next);
    applyTheme(next);
  });

  // React to system scheme changes if on 'auto'
  if (window.matchMedia) {
    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    mq.addEventListener?.('change', () => {
      const saved = localStorage.getItem(THEME_KEY) || 'auto';
      if (saved === 'auto') applyTheme('auto');
    });
  }
});
