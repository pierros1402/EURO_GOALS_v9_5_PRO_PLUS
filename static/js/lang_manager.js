/* ============================================================
   AI MATCHLAB — LANGUAGE MANAGER (EN / GR)
   ============================================================ */

const LANG_KEY = "aimatchlab_lang";

const i18n = {
  en: {
    "subtitle.dashboard": "Real-time AI-powered match monitoring & insight panels",
    "subtitle.lab": "AI-Driven Sports Analytics Lab",

    "status.live_chain": "Live data chain online",

    "panel.system": "System Status",
    "panel.fixtures": "Fixtures Overview",

    "footer.responsible": "Responsible Gambling",
    "footer.privacy": "Privacy Policy",
    "footer.cookies": "Cookies Policy",
    "footer.terms": "Terms & Conditions",

    "loading": "Loading..."
  },

  gr: {
    "subtitle.dashboard": "Παρακολούθηση αγώνων σε πραγματικό χρόνο με AI",
    "subtitle.lab": "Εργαστήριο Αναλύσεων με Τεχνητή Νοημοσύνη",

    "status.live_chain": "Live data chain ενεργή",

    "panel.system": "Κατάσταση Συστήματος",
    "panel.fixtures": "Πρόγραμμα Αγώνων",

    "footer.responsible": "Υπεύθυνο Παιχνίδι",
    "footer.privacy": "Πολιτική Απορρήτου",
    "footer.cookies": "Πολιτική Cookies",
    "footer.terms": "Όροι & Προϋποθέσεις",

    "loading": "Φόρτωση..."
  }
};

/* ============================================================
   LOAD LANGUAGE
   ============================================================ */

function getSavedLang() {
  const lang = localStorage.getItem(LANG_KEY);
  return lang === "gr" ? "gr" : "en";
}

function saveLang(lang) {
  localStorage.setItem(LANG_KEY, lang);
}

/* ============================================================
   APPLY LANGUAGE TO PAGE
   ============================================================ */

function applyLang(lang) {
  const dict = i18n[lang] || i18n.en;

  document.querySelectorAll("[data-i18n]").forEach(el => {
    const key = el.getAttribute("data-i18n");
    if (dict[key]) el.textContent = dict[key];
  });

  // Update active buttons
  document.querySelectorAll(".lang-btn").forEach(btn => {
    if (btn.dataset.lang === lang) {
      btn.classList.add("active");
    } else {
      btn.classList.remove("active");
    }
  });
}

/* ============================================================
   INIT LANGUAGE SWITCHING
   ============================================================ */

function initLangSwitch() {
  const currentLang = getSavedLang();
  applyLang(currentLang);

  const switchEl = document.getElementById("lang-switch");
  if (!switchEl) return;

  switchEl.querySelectorAll("button").forEach(btn => {
    btn.addEventListener("click", () => {
      const lang = btn.dataset.lang;
      saveLang(lang);
      applyLang(lang);
    });
  });
}

/* INIT */
document.addEventListener("DOMContentLoaded", initLangSwitch);
