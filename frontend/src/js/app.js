// ─── Telegram WebApp init ───────────────────────────────────────────────
// The production app runs inside Telegram, but the public URL should fail
// clearly rather than throwing before the shell can render when opened in a
// normal browser or a crawler.
const tg = window.Telegram?.WebApp || {
  initData: '',
  ready() {},
  expand() {},
  setHeaderColor() {},
  setBackgroundColor() {},
  MainButton: { hide() {}, showProgress() {}, hideProgress() {} },
  BackButton: { hide() {}, show() {}, onClick() {} },
  HapticFeedback: { notificationOccurred() {}, selectionChanged() {}, impactOccurred() {} },
};
tg.ready();
tg.expand();
tg.setHeaderColor('bg_color');
tg.setBackgroundColor('bg_color');

// ─── Config ────────────────────────────────────────────────────────────
const API = ''; // Same origin
const initData = tg.initData;

// ─── Icons (24px stroke glyphs) ────────────────────────────────────────
const ICONS = {
  swarm: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="5" r="2.2"/><circle cx="5" cy="18" r="2.2"/><circle cx="19" cy="18" r="2.2"/><path d="M10.9 6.9 6 15.9M13.1 6.9 18 15.9M7.3 18h9.4"/></svg>',
  pipeline: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="6" cy="5" r="2.3"/><circle cx="6" cy="19" r="2.3"/><circle cx="18" cy="12" r="2.3"/><path d="M6 7.3v9.4M6 9.5c0 3.4 4.4 2.5 9.5 2.5"/></svg>',
  fleet: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="7" rx="2"/><rect x="4" y="13" width="16" height="7" rx="2"/><path d="M7.5 7.5h.01M7.5 16.5h.01"/></svg>',
  kanban: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3.5" y="4" width="4.6" height="16" rx="1.5"/><rect x="9.7" y="4" width="4.6" height="11" rx="1.5"/><rect x="15.9" y="4" width="4.6" height="7" rx="1.5"/></svg>',
  alerts: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M18 10a6 6 0 1 0-12 0c0 5-2 6-2 6h16s-2-1-2-6"/><path d="M10.3 20a2 2 0 0 0 3.4 0"/></svg>',
  'ops-remote': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M13 3 5 13.5h6L11 21l8-10.5h-6z"/></svg>',
  '1password': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="4"/><path d="m11 11 9 9M17.5 20.5l2-2M14.5 17.5l2-2"/></svg>',
  smarthome: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="m4 11 8-7 8 7"/><path d="M6 9.5V20h12V9.5"/></svg>',
  cost: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 20h16"/><path d="M6.5 20v-6.5M11.5 20V4.5M16.5 20V10"/></svg>',
  wiki: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 6c-1.5-1.3-3.5-2-6-2v14c2.5 0 4.5.7 6 2 1.5-1.3 3.5-2 6-2V4c-2.5 0-4.5.7-6 2z"/><path d="M12 6v14"/></svg>',
  back: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 5-7 7 7 7"/></svg>',
  refresh: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 11a8 8 0 1 0-2.5 5.8"/><path d="M20 5.5V11h-5.5"/></svg>',
};

// ─── App registry ──────────────────────────────────────────────────────
const apps = [
  { id: 'swarm',      name: 'Swarm',     desc: 'Source envelope health', color: '#3fc7c2', render: () => renderSwarm(contentEl()) },
  { id: 'pipeline',   name: 'Pipeline',  desc: 'MRs & CI approvals',     color: '#5b8def', render: () => renderPipeline(contentEl()) },
  { id: 'fleet',      name: 'Fleet',     desc: 'Host health & metrics',  color: '#7f7bf0', render: () => renderFleet(contentEl()) },
  { id: 'kanban',     name: 'Kanban',    desc: 'Ops board & issues',     color: '#ff9f3f', render: () => renderKanban(contentEl()) },
  { id: 'alerts',     name: 'Alerts',    desc: 'Triage & silences',      color: '#ff5d55', render: () => renderAlerts(contentEl()) },
  { id: 'ops-remote', name: 'Remote',    desc: 'One-tap host actions',   color: '#ffcf3f', render: () => renderOpsRemote(contentEl()) },
  { id: '1password',  name: '1Password', desc: 'Vault browser',          color: '#b07ce8', render: () => render1Password(contentEl()) },
  { id: 'smarthome',  name: 'Home',      desc: 'Lights & devices',       color: '#34d178', render: () => renderSmarthome(contentEl()) },
  { id: 'cost',       name: 'Cost',      desc: 'Usage & quotas',         color: '#f06292', render: () => renderCost(contentEl()) },
  { id: 'wiki',       name: 'Wiki',      desc: 'Docs & knowledge',       color: '#4fb8e8', render: () => renderWiki(contentEl()) },
];

let currentApp = null;   // null = home launcher
let historyStack = [];

function contentEl() { return document.getElementById('content'); }

// ─── Helpers ───────────────────────────────────────────────────────────
async function api(path, opts = {}) {
  const headers = { 'Authorization': `tma ${initData}`, ...opts.headers };
  if (opts.body) headers['Content-Type'] = 'application/json';
  const res = await fetch(path, { ...opts, headers });
  if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`);
  return res.json();
}

function h(html) {
  const div = document.createElement('div');
  div.innerHTML = html.trim();
  return div.firstChild;
}

function toast(msg) {
  const el = h(`<div class="toast">${msg}</div>`);
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 2500);
  tg.HapticFeedback.notificationOccurred('success');
}

function loading(msg = 'Loading...') {
  return `<div class="loading-screen"><div class="spinner"></div><p>${msg}</p></div>`;
}

// Skeleton placeholder: n shimmering card-shaped blocks
function skeleton(n = 3, height = 76) {
  return Array.from({ length: n }, () =>
    `<div class="skeleton" style="height:${height}px"></div>`).join('');
}

function empty(icon, msg) {
  return `<div class="empty"><div class="icon">${icon}</div><div>${msg}</div></div>`;
}

function errorCard(msg, hint = '') {
  return `<div class="error-card">
    <div class="error-title">Something went wrong</div>
    <div class="error-detail">${msg}</div>
    ${hint ? `<div class="error-detail" style="margin-top:6px">${hint}</div>` : ''}
  </div>`;
}

// Page header with optional stat chips: chips = [{label, value, color?}]
function pageHead(title, sub = '', chips = []) {
  const chipHtml = chips.length
    ? `<div class="chips">${chips.map(c =>
        `<span class="chip">${c.dot ? `<span class="status-dot ${c.dot}"></span>` : ''}${c.label} <b${c.color ? ` style="color:${c.color}"` : ''}>${c.value}</b></span>`
      ).join('')}</div>`
    : '';
  return `<div class="page-head">
    <div class="page-title">${title}</div>
    ${sub ? `<div class="page-sub">${sub}</div>` : ''}
    ${chipHtml}
  </div>`;
}

function statusDot(up, warnThreshold = false) {
  if (up === true) return '<span class="status-dot green"></span>';
  if (up === false) return '<span class="status-dot red"></span>';
  if (warnThreshold) return '<span class="status-dot yellow"></span>';
  return '<span class="status-dot gray"></span>';
}

function pctColor(pct) {
  if (pct >= 90) return 'var(--status-critical)';
  if (pct >= 75) return 'var(--status-attention)';
  return 'var(--status-healthy)';
}

function progress(pct, color) {
  return `<div class="progress-bar"><div class="fill" style="width:${pct}%;background:${color || pctColor(pct)}"></div></div>`;
}

function gauge(label, pct) {
  const val = Math.round(pct);
  return `<div class="gauge-card">
    <div class="gauge" style="--pct:${Math.min(100, Math.max(0, val))};--gauge-color:${pctColor(val)}">
      <span class="gauge-val">${val}%</span>
    </div>
    <div class="gauge-label">${label}</div>
  </div>`;
}

function timeAgo(iso) {
  const diff = Date.now() - new Date(iso).getTime();
  const min = Math.floor(diff / 60000);
  if (min < 60) return `${min}m ago`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr}h ago`;
  return `${Math.floor(hr / 24)}d ago`;
}

// ─── Top bar ───────────────────────────────────────────────────────────
function renderTopbar() {
  const bar = document.getElementById('topbar');
  const app = apps.find(a => a.id === currentApp);

  if (!app) {
    bar.innerHTML = `
      <div class="topbar-title">
        <div>
          <div class="t">Homelab</div>
          <div class="s"><span class="status-dot green" id="conn-dot"></span><span id="conn-label">Connected</span></div>
        </div>
      </div>`;
    return;
  }

  bar.innerHTML = `
    <button class="topbar-btn" id="topbar-back" aria-label="Back">${ICONS.back}</button>
    <div class="topbar-title" style="--tile:${app.color}">
      <span class="app-glyph">${ICONS[app.id]}</span>
      <div class="t">${app.name}</div>
    </div>
    <button class="topbar-btn" id="topbar-refresh" aria-label="Refresh">${ICONS.refresh}</button>`;

  document.getElementById('topbar-back').addEventListener('click', () => {
    historyStack.length ? popView() : goHome();
  });
  document.getElementById('topbar-refresh').addEventListener('click', async (e) => {
    const btn = e.currentTarget;
    btn.classList.add('spinning');
    tg.HapticFeedback.impactOccurred?.('light');
    historyStack = [];
    tg.BackButton.hide();
    try { await runApp(app); } finally { btn.classList.remove('spinning'); }
  });
}

// ─── Home launcher ─────────────────────────────────────────────────────
function renderHome() {
  currentApp = null;
  historyStack = [];
  renderTopbar();
  tg.MainButton.hide();
  tg.BackButton.hide();

  contentEl().innerHTML = `
    <div class="home-hero">
      <div class="greeting">Control Center</div>
      <div class="tagline">${apps.length} apps · fail-closed sources</div>
    </div>
    <div class="app-grid">
      ${apps.map(a => `
        <button class="app-tile" data-app="${a.id}" style="--tile:${a.color}">
          <span class="app-tile-icon">${ICONS[a.id]}</span>
          <span class="app-tile-name">${a.name}</span>
          <span class="app-tile-desc">${a.desc}</span>
        </button>`).join('')}
    </div>`;

  contentEl().querySelectorAll('[data-app]').forEach(tile => {
    tile.addEventListener('click', () => {
      tg.HapticFeedback.selectionChanged?.();
      switchApp(tile.dataset.app);
    });
  });
}

function goHome() {
  renderHome();
}

// ─── App navigation ────────────────────────────────────────────────────
async function runApp(app) {
  const content = contentEl();
  content.innerHTML = skeleton(4);
  try {
    await app.render();
  } catch (err) {
    content.innerHTML = errorCard(err.message);
  }
}

function switchApp(appId) {
  currentApp = appId;
  historyStack = [];
  renderTopbar();
  tg.MainButton.hide();
  tg.BackButton.show();
  runApp(apps.find(a => a.id === appId));
}

// Navigate to detail view (pushes current state)
function pushView(renderFn) {
  const content = contentEl();
  historyStack.push(content.innerHTML);
  tg.BackButton.show();
  content.innerHTML = skeleton(3);
  renderFn(content).catch(err => {
    content.innerHTML = errorCard(err.message);
  });
}

function popView() {
  if (historyStack.length > 0) {
    contentEl().innerHTML = historyStack.pop();
  } else if (currentApp) {
    goHome();
  }
}

// Telegram back button: pop a detail view, or return to the launcher
tg.BackButton.onClick(() => {
  historyStack.length ? popView() : goHome();
});

// ─── Init ──────────────────────────────────────────────────────────────
async function init() {
  renderHome();
  try {
    const me = await api('/api/me');
    console.log('Authenticated as:', me);
  } catch (err) {
    const dot = document.getElementById('conn-dot');
    const label = document.getElementById('conn-label');
    if (dot) dot.className = 'status-dot red';
    if (label) label.textContent = 'Auth failed';
    contentEl().innerHTML = errorCard(
      `Authentication failed: ${err.message}`,
      'Open this app from the Telegram bot — direct browser access is not authorized.'
    );
  }
}
