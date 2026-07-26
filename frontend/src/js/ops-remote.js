// ─── Quick Ops Remote ──────────────────────────────────────────────────

async function renderOpsRemote(content) {
  const data = await api('/api/ops-remote/hosts');

  let html = '<div class="section"><div class="section-title">Quick Ops Remote</div>';
  html += '<div class="section-desc">Tap a host to see available actions</div></div>';

  // Host selector
  html += '<div class="host-grid">';
  for (const host of data.hosts) {
    html += `
      <div class="host-card" data-host="${host.name}">
        <div class="name">${host.name}</div>
        <div class="ip">${host.role}</div>
        <div class="metric" style="margin-top:4px">${host.actions.length} actions</div>
      </div>
    `;
  }
  html += '</div>';

  content.innerHTML = html;

  content.querySelectorAll('[data-host]').forEach(el => {
    el.addEventListener('click', () => viewHostActions(el.dataset.host));
  });
}

async function viewHostActions(host) {
  const content = document.getElementById('content');
  historyStack.push(content.innerHTML);
  tg.BackButton.show();
  content.innerHTML = loading(`Loading ${host} actions...`);

  try {
    const data = await api(`/api/ops-remote/actions/${host}`);

    let html = `<div class="detail-back" onclick="popView()">← Back</div>`;
    html += `<div class="section-title">${host}</div>`;
    html += '<div class="action-grid">';

    for (const action of data.actions) {
      const icon = action.id.startsWith('restart') ? '🔄' :
                   action.id.startsWith('logs') ? '📜' :
                   action.id === 'docker_ps' ? '🐳' :
                   action.id === 'disk_usage' ? '💾' :
                   action.id === 'memory' ? '🧠' :
                   action.id === 'gpu_info' ? '🎮' :
                   action.id === 'gitlab_status' ? '🦊' : '⚡';
      html += `
        <div class="action-btn" data-action="${action.id}" data-host="${host}">
          <div class="icon">${icon}</div>
          <div class="label">${action.desc}</div>
        </div>
      `;
    }
    html += '</div>';

    // Output area
    html += '<div id="ops-output"></div>';

    content.innerHTML = html;

    content.querySelectorAll('[data-action]').forEach(el => {
      el.addEventListener('click', () => executeOpsAction(el.dataset.host, el.dataset.action));
    });
  } catch (err) {
    content.innerHTML = `<div class="card"><p style="color:var(--destructive)">${err.message}</p></div>`;
  }
}

async function executeOpsAction(host, actionId) {
  const output = document.getElementById('ops-output');
  output.innerHTML = `<div class="card"><div class="card-header">Executing: ${actionId}</div><div class="output-log">Running...</div></div>`;

  try {
    const result = await api(`/api/ops-remote/execute/${host}/${actionId}`, { method: 'POST' });
    const log = output.querySelector('.output-log');

    if (result.success) {
      log.innerHTML = `${result.stdout || '(no output)'}`;
      log.style.color = '#0f0';
      tg.HapticFeedback.notificationOccurred('success');
    } else {
      log.innerHTML = `EXIT CODE: ${result.exit_code}\n\nSTDERR:\n${result.stderr || ''}\n\nSTDOUT:\n${result.stdout || ''}`;
      log.style.color = '#f00';
      tg.HapticFeedback.notificationOccurred('error');
    }
  } catch (err) {
    output.innerHTML = `<div class="card"><p style="color:var(--destructive)">${err.message}</p></div>`;
  }
}
