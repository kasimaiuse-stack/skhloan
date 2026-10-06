/* SKH Loan Approval - frontend logic */
'use strict';

const API_URL = 'http://127.0.0.1:8000/predict';

const MSG = {
  network: 'Unable to connect to the prediction server. Please make sure the FastAPI backend is running.',
  api: 'Something went wrong while analyzing your application. Please try again.',
  invalid: 'Please correct the highlighted fields and try again.'
};

const $ = (id) => document.getElementById(id);

/* ---------- Icons ---------- */
const refreshIcons = () => window.lucide && window.lucide.createIcons();
document.addEventListener('DOMContentLoaded', () => { refreshIcons(); initNav(); initReveal(); initForm(); });

/* ---------- Navbar: blur on scroll + mobile menu ---------- */
function initNav() {
  const nav = $('navbar'), btn = $('menuBtn'), menu = $('mobileMenu');
  const onScroll = () => nav.classList.toggle('scrolled', window.scrollY > 20);
  onScroll();
  window.addEventListener('scroll', onScroll, { passive: true });

  const setMenu = (open) => {
    menu.classList.toggle('open', open);
    nav.classList.toggle('menu-open', open);
    btn.setAttribute('aria-expanded', String(open));
    btn.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
    menu.setAttribute('aria-hidden', String(!open));
    btn.innerHTML = `<i data-lucide="${open ? 'x' : 'menu'}" class="w-6 h-6"></i>`;
    refreshIcons();
  };
  btn.addEventListener('click', () => setMenu(!menu.classList.contains('open')));
  menu.querySelectorAll('a').forEach((a) => a.addEventListener('click', () => setMenu(false)));
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') setMenu(false); });
  window.addEventListener('resize', () => { if (window.innerWidth >= 768) setMenu(false); });
}

/* ---------- Fade-in on scroll ---------- */
function initReveal() {
  const items = document.querySelectorAll('.reveal');
  if (!('IntersectionObserver' in window)) { items.forEach((el) => el.classList.add('visible')); return; }
  const io = new IntersectionObserver((entries) => {
    entries.forEach((en) => { if (en.isIntersecting) { en.target.classList.add('visible'); io.unobserve(en.target); } });
  }, { threshold: 0.12 });
  items.forEach((el) => io.observe(el));
}

/* ---------- Form validation rules ---------- */
// type: 'int' | 'float' | 'select'. Names match the FastAPI CreditRisk model exactly.
const FIELDS = [
  { name: 'person_age', type: 'int', min: 18, max: 100, label: 'Age' },
  { name: 'person_income', type: 'int', min: 0, label: 'Income' },
  { name: 'person_emp_length', type: 'float', min: 0, max: 60, label: 'Employment length' },
  { name: 'loan_amnt', type: 'int', min: 1, label: 'Loan amount' },
  { name: 'loan_int_rate', type: 'float', min: 0, max: 100, label: 'Interest rate' },
  { name: 'loan_percent_income', type: 'float', min: 0, max: 1, label: 'Loan percent income' },
  { name: 'cb_person_cred_hist_length', type: 'int', min: 0, label: 'Credit history length' },
  { name: 'person_home_ownership', type: 'select', label: 'Home ownership' },
  { name: 'loan_grade', type: 'select', label: 'Loan grade' },
  { name: 'cb_person_default_on_file', type: 'select', label: 'Previous default' },
  { name: 'loan_intent', type: 'select', label: 'Loan intent' }
];

function setFieldError(name, message) {
  const input = $(name), ctl = input.closest('.ctl'), field = input.closest('.field');
  field.querySelector('.field-msg')?.remove();
  ctl.classList.toggle('invalid', Boolean(message));
  input.setAttribute('aria-invalid', message ? 'true' : 'false');
  if (message) {
    const p = document.createElement('p');
    p.className = 'field-msg';
    p.id = `${name}_err`;
    p.textContent = message;
    field.appendChild(p);
    input.setAttribute('aria-describedby', p.id);
  } else input.removeAttribute('aria-describedby');
}

/** Validates the form; returns the payload object or null. */
function buildPayload() {
  const payload = {};
  let firstBad = null;
  FIELDS.forEach((f) => {
    const raw = $(f.name).value.trim();
    let msg = '';
    if (raw === '') msg = f.type === 'select' ? 'Please choose an option.' : 'This field is required.';
    else if (f.type !== 'select') {
      const n = Number(raw);
      if (!Number.isFinite(n)) msg = 'Enter a valid number.';
      else if (f.type === 'int' && !Number.isInteger(n)) msg = 'Use a whole number.';
      else if (f.min !== undefined && n < f.min) msg = `Must be at least ${f.min}.`;
      else if (f.max !== undefined && n > f.max) msg = `Must be ${f.max} or less.`;
      else payload[f.name] = n;
    } else payload[f.name] = raw;
    setFieldError(f.name, msg);
    if (msg && !firstBad) firstBad = f.name;
  });
  if (firstBad) { $(firstBad).focus(); return null; }
  return payload;
}

/* ---------- UI helpers ---------- */
function showFormError(text) {
  const box = $('formError');
  box.textContent = text || '';
  box.classList.toggle('hidden', !text);
}

function setLoading(on) {
  const btn = $('submitBtn');
  btn.disabled = on;
  btn.setAttribute('aria-busy', String(on));
  $('spinner').classList.toggle('hidden', !on);
  $('btnText').textContent = on ? 'Analyzing...' : 'Analyze Credit Risk';
}

function showResult(status) {
  const card = $('result'), low = status === 0;
  card.classList.remove('hidden', 'show', 'low', 'high');
  card.classList.add(low ? 'low' : 'high');
  $('resultTitle').textContent = low ? 'Low Credit Risk' : 'Higher Credit Risk';
  $('resultText').textContent = low
    ? 'Your application shows a lower estimated credit risk based on the information provided.'
    : 'Our model estimates a higher credit risk based on the information provided.';
  $('resultIcon').innerHTML = `<i data-lucide="${low ? 'check' : 'alert-triangle'}" class="w-14 h-14" stroke-width="2.5"></i>`;
  refreshIcons();

  const ring = $('ring');
  ring.style.transition = 'none';
  ring.style.strokeDashoffset = '264';
  void card.offsetWidth; // restart animations
  card.classList.add('show');
  ring.style.transition = '';
  requestAnimationFrame(() => { ring.style.strokeDashoffset = '0'; });
  card.scrollIntoView({ behavior: 'smooth', block: 'center' });
  card.focus({ preventScroll: true });
}

/* ---------- Submit to FastAPI ---------- */
function initForm() {
  const form = $('loanForm');
  FIELDS.forEach((f) => $(f.name).addEventListener('input', () => setFieldError(f.name, '')));

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    showFormError('');
    $('result').classList.add('hidden');

    const payload = buildPayload();
    if (!payload) { showFormError(MSG.invalid); return; }

    setLoading(true);
    try {
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (!res.ok) throw new Error('api');
      const data = await res.json();
      if (data.loan_status !== 0 && data.loan_status !== 1) throw new Error('api');
      showResult(data.loan_status);
    } catch (err) {
      // Network failures surface as TypeError from fetch; everything else is an API problem.
      showFormError(err instanceof TypeError ? MSG.network : MSG.api);
      $('formError').scrollIntoView({ behavior: 'smooth', block: 'center' });
    } finally {
      setLoading(false);
    }
  });
}
