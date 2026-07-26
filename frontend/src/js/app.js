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
  MainButton: { hide() {} },
  BackButton: { hide() {}, show() {}, onClick() {} },
  HapticFeedback: { notificationOccurred() {} },
};
tg.ready();
tg.expand();
tg.setHeaderColor('secondary_bg_color');
tg.setBackgroundColor('bg_color');

// ─── Config ────────────────────────────────────────────────────────────
const API = ''; // Same origin
const initData = tg.initData;

// ─── App state ─────────────────────────────────────────────────────────
const apps = [
  { id: 'swarm',      name: 'Swarm',    icon: '🌀', render: renderSwarm },
  { id: 'pipeline',   name: 'Pipeline', icon: '🔧', render: renderPipeline },
  { id: 'fleet',      name: 'Fleet',    icon: '🖥️', render: renderFleet },
  { id: 'kanban',     name: 'Kanban',   icon: '📋', render: renderKanban },
  { id: 'alerts',     name: 'Alerts',   icon: '🚨', render: renderAlerts },
  { id: 'ops-remote', name: 'Remote',   icon: '⚡', render: renderOpsRemote },
  { id: '1password',  name: '1Password',icon: '🔑', render: render1Password },
  { id: 'smarthome',  name: 'Home',     icon: '🏠', render: renderSmarthome },
  { id: 'cost',       name: 'Cost',     icon: '📊', render: renderCost },
  { id: 'wiki',       name: 'Wiki',     icon: '📚', render: renderWiki },
];

let currentApp = null;
let historyStack = [];

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

function empty(icon, msg) {
  return `<div class="empty"><div class="icon">${icon}</div><div>${msg}</div></div>`;
}

function statusDot(up, warnThreshold = false) {
  if (up === true) return '<span class="status-dot green"></span>';
  if (up === false) return '<span class="status-dot red"></span>';
  if (warnThreshold) return '<span class="status-dot yellow"></span>';
  return '<span class="status-dot gray"></span>';
}

function pctColor(pct) {
  if (pct >= 90) return '#ff453a';
  if (pct >= 75) return '#ffd60a';
  return '#30d158';
}

function progress(pct, color) {
  return `<div class="progress-bar"><div class="fill" style="width:${pct}%;background:${color || pctColor(pct)}"></div></div>`;
}

function timeAgo(iso) {
  const diff = Date.now() - new Date(iso).getTime();
  const min = Math.floor(diff / 60000);
  if (min < 60) return `${min}m ago`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr}h ago`;
  return `${Math.floor(hr / 24)}d ago`;
}

// ─── Navigation ────────────────────────────────────────────────────────
function renderNav() {
  const nav = document.getElementById('nav');
  nav.innerHTML = apps.map(a => `
    <div class="nav-tab ${a.id === currentApp ? 'active' : ''}" data-app="${a.id}">
      <span class="icon">${a.icon}</span>
      <span class="label">${a.name}</span>
    </div>
  `).join('');

  nav.querySelectorAll('.nav-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      historyStack = [];
      switchApp(tab.dataset.app);
    });
  });
}

function switchApp(appId) {
  currentApp = appId;
  historyStack = [];
  renderNav();
  const app = apps.find(a => a.id === appId);
  const content = document.getElementById('content');
  content.innerHTML = loading();
  tg.MainButton.hide();
  tg.BackButton.hide();

  app.render(content).catch(err => {
    content.innerHTML = `<div class="card"><p style="color:var(--destructive)">Error: ${err.message}</p></div>`;
  });
}

// Navigate to detail view (pushes current state)
function pushView(renderFn) {
  const content = document.getElementById('content');
  historyStack.push(content.innerHTML);
  tg.BackButton.show();
  content.innerHTML = loading();
  renderFn(content).catch(err => {
    content.innerHTML = `<div class="card"><p style="color:var(--destructive)">Error: ${err.message}</p></div>`;
  });
}

function popView() {
  if (historyStack.length > 0) {
    document.getElementById('content').innerHTML = historyStack.pop();
    if (historyStack.length === 0) tg.BackButton.hide();
  }
}

tg.BackButton.onClick(popView);

// ─── Init ──────────────────────────────────────────────────────────────
async function init() {
  try {
    // Verify auth
    const me = await api('/api/me');
    console.log('Authenticated as:', me);
    currentApp = 'swarm'; // Default to Swarm Monitor
    renderNav();
    switchApp('swarm');
  } catch (err) {
    document.getElementById('content').innerHTML =
      `<div class="card"><p style="color:var(--destructive)">Authentication failed: ${err.message}</p></div>`;
  }
}

// Fix: pushView had wrong variable name
// (removed duplicate function)
