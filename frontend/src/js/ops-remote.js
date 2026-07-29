// ─── Quick Ops Remote ──────────────────────────────────────────────────

async function renderOpsRemote(content) {
  const data = await api('/api/ops-remote/hosts');

  let html = pageHead('Remote', 'Tap a host to see available actions', [
    { label: 'Hosts', value: data.hosts.length },
  ]);

  // Host selector
  html += '<div class="host-grid">';
  for (const host of data.hosts) {
    html += `
      <div class="host-card" data-host="${host.name}">
        <div class="name">${host.name}</div>
        <div class="ip">${host.role}</div>
        <div class="metric" style="margin-top:8px">${host.actions.length} actions</div>
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
  content.innerHTML = skeleton(3);

  try {
    const data = await api(`/api/ops-remote/actions/${host}`);

    let html = `<div class="detail-back" onclick="popView()">‹ Back</div>`;
    html += pageHead(host, `${data.actions.length} actions available`);
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
    html += '<div id="ops-output" style="margin-top:12px"></div>';

    content.innerHTML = html;

    content.querySelectorAll('[data-action]').forEach(el => {
      el.addEventListener('click', () => executeOpsAction(el.dataset.host, el.dataset.action));
    });
  } catch (err) {
    content.innerHTML = errorCard(err.message);
  }
}

async function executeOpsAction(host, actionId) {
  const output = document.getElementById('ops-output');
  output.innerHTML = `<div class="card"><div class="card-header">Executing: ${actionId}</div><div class="output-log">Running...</div></div>`;

  try {
    const result = await api(`/api/ops-remote/execute/${host}/${actionId}`, { method: 'POST' });
    const log = output.querySelector('.output-log');

    if (result.success) {
      log.textContent = result.stdout || '(no output)';
      log.classList.remove('err');
      tg.HapticFeedback.notificationOccurred('success');
    } else {
      log.textContent = `EXIT CODE: ${result.exit_code}\n\nSTDERR:\n${result.stderr || ''}\n\nSTDOUT:\n${result.stdout || ''}`;
      log.classList.add('err');
      tg.HapticFeedback.notificationOccurred('error');
    }
  } catch (err) {
    output.innerHTML = errorCard(err.message);
  }
}
