document.addEventListener('DOMContentLoaded', () => {
  const toolbar = document.getElementById('quick-toolbar');

  toolbar.querySelector('[data-action="refresh"]').addEventListener('click', () => location.reload());
  toolbar.querySelector('[data-action="scrollTop"]').addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));

  const sections = {
    toggleSmartMoney: document.getElementById('smartmoney-panel'),
    toggleGoalMatrix: document.getElementById('goal-matrix-panel'),
    toggleAlerts: document.getElementById('alert-center')
  };

  toolbar.querySelectorAll('[data-action]').forEach(btn => {
    const action = btn.getAttribute('data-action');
    if (action.startsWith('toggle')) {
      btn.addEventListener('click', () => {
        const panel = sections[action];
        if (panel) {
          panel.classList.toggle('hidden');
          btn.classList.toggle('opacity-50');
        }
      });
    }
  });

  window.addEventListener('scroll', () => {
    toolbar.style.opacity = window.scrollY > 200 ? '0.7' : '1';
  });
});
