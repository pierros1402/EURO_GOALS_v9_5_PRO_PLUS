// ========================================================
// EURO_GOALS v9.5.0 PRO+ – UI Animations (Framer-like)
// ========================================================

function animateOnScroll() {
  const fadeSections = document.querySelectorAll('.fade-section');
  fadeSections.forEach((section) => {
    const rect = section.getBoundingClientRect();
    if (rect.top < window.innerHeight - 100) {
      section.classList.add('fade-in');
    }
  });
}

window.addEventListener('scroll', animateOnScroll);
window.addEventListener('load', () => {
  animateOnScroll();
  // Subtle staggered entrance
  document.querySelectorAll('.fade-section').forEach((section, i) => {
    setTimeout(() => section.classList.add('slide-up'), i * 150);
  });
});
