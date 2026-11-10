// Umumiy yordamchilar: barcha sahifalar shu fayldan foydalanadi
const esc = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

// "George_W_Bush" -> "George W Bush"
const pretty = name => String(name).replace(/_/g, ' ');

const initials = name => {
  const parts = pretty(name).trim().split(/\s+/);
  return ((parts[0]?.[0] || '') + (parts.length > 1 ? parts[parts.length - 1][0] : '')).toUpperCase() || '?';
};

// Har bir ism uchun doim bir xil rang (0–359)
const hue = name => [...String(name)].reduce((h, c) => (h * 31 + c.charCodeAt(0)) % 360, 7);

const avatar = (name, unknown = false) =>
  unknown
    ? '<span class="avatar unknown" aria-hidden="true">?</span>'
    : `<span class="avatar" style="--h:${hue(name)}" aria-hidden="true">${esc(initials(name))}</span>`;

// LBPH masofasi: kichik = ishonchli. Chegaraga nisbatan uch daraja.
function matchQuality(distance, threshold) {
  if (distance == null) return { label: '—', cls: '' };
  if (distance < threshold * 0.6) return { label: 'Strong', cls: 'ok' };
  if (distance < threshold) return { label: 'Fair', cls: 'warn' };
  return { label: 'No match', cls: 'no' };
}

const ICONS = {
  check: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>',
  alert: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 8v4M12 16h.01"/></svg>',
};

function toast(message, kind = 'ok', ms = 4000) {
  let box = document.querySelector('.toasts');
  if (!box) {
    box = document.createElement('div');
    box.className = 'toasts';
    box.setAttribute('aria-live', 'polite');
    document.body.appendChild(box);
  }
  const el = document.createElement('div');
  el.className = `toast ${kind}`;
  el.innerHTML = `<span class="toast-icon">${kind === 'ok' ? ICONS.check : ICONS.alert}</span><span>${esc(message)}</span>`;
  box.appendChild(el);
  setTimeout(() => { el.classList.add('leaving'); setTimeout(() => el.remove(), 200); }, ms);
}
