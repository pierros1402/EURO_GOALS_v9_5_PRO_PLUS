function animateOnScroll() {
  document.querySelectorAll('.fade-section').forEach((el) => {
    const rect = el.getBoundingClientRect();
    if (rect.top < window.innerHeight - 80) el.classList.add('fade-in');
  });
}

window.addEventListener('scroll', animateOnScroll);
window.addEventListener('load', () => {
  animateOnScroll();
  document.querySelectorAll('.fade-section').forEach((section, i) => {
    setTimeout(() => section.classList.add('slide-up'), i * 150);
  });
});
