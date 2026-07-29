// ─── Fleet Health Dashboard ────────────────────────────────────────────

async function renderFleet(content) {
  const data = await api('/api/fleet/overview');

  let html = pageHead('Fleet', 'Host health across the lab', [
    { label: 'Up', value: data.hosts_up, dot: 'green' },
    { label: 'Down', value: data.hosts_down, dot: data.hosts_down > 0 ? 'red' : 'gray' },
    { label: 'Total', value: data.total_hosts },
  ]);

  if (data.hosts.length === 0) {
    html += empty('🖥️', 'No hosts reporting');
    content.innerHTML = html;
    return;
  }

  html += '<div class="host-grid">';
  for (const host of data.hosts) {
    const up = host.up;
    const cpu = host.cpu || 0;
    const mem = host.mem || 0;
    const disk = host.disk || 0;
    const worst = Math.max(cpu, mem, disk);
    let dotClass = 'green';
    if (!up) dotClass = 'red pulse';
    else if (worst >= 90) dotClass = 'red';
    else if (worst >= 75) dotClass = 'yellow';

    html += `
      <div class="host-card ${up ? '' : 'down'}" data-ip="${host.ip}">
        <div style="display:flex;justify-content:space-between;align-items:start;gap:6px;">
          <div style="min-width:0">
            <div class="name">${host.name || host.ip}</div>
            <div class="ip">${host.ip}</div>
          </div>
          <span class="status-dot ${dotClass}" style="margin-top:5px"></span>
        </div>
        ${up ? `
          <div class="mini-meters">
            ${miniMeter('CPU', cpu)}
            ${miniMeter('MEM', mem)}
            ${miniMeter('DSK', disk)}
          </div>
        ` : '<div class="metric" style="color:var(--status-critical);margin-top:10px;font-weight:700;">OFFLINE</div>'}
      </div>
    `;
  }
  html += '</div>';

  content.innerHTML = html;

  content.querySelectorAll('[data-ip]').forEach(el => {
    el.addEventListener('click', () => viewHostDetail(el.dataset.ip));
  });
}

async function viewHostDetail(ip) {
  const content = document.getElementById('content');
  historyStack.push(content.innerHTML);
  tg.BackButton.show();
  content.innerHTML = skeleton(4);

  try {
    const data = await api(`/api/fleet/host/${encodeURIComponent(ip)}`);
    const uptime = formatUptime(data.uptime_seconds);

    let html = `<div class="detail-back" onclick="popView()">‹ Back</div>`;
    html += pageHead(data.name || data.ip, `<span class="mono-val">${data.ip}</span> · up ${uptime}`);

    html += `<div class="gauge-row">
      ${gauge('CPU', data.cpu_pct)}
      ${gauge('Memory', data.mem_pct)}
      ${gauge('Disk', data.disk_pct)}
    </div>`;

    html += `<div class="card"><div class="card-header">Details</div>`;
    html += `<div class="list-item"><div class="info"><div class="title">Load (1m)</div></div><div class="mono-val">${data.load1.toFixed(2)}</div></div>`;
    html += `<div class="list-item"><div class="info"><div class="title">Uptime</div></div><div class="mono-val">${uptime}</div></div>`;
    html += `<div class="list-item"><div class="info"><div class="title">Network RX</div></div><div class="mono-val">${formatBytes(data.net_rx_bps)}/s</div></div>`;
    html += `<div class="list-item"><div class="info"><div class="title">Network TX</div></div><div class="mono-val">${formatBytes(data.net_tx_bps)}/s</div></div>`;
    html += `<div class="list-item"><div class="info"><div class="title">Containers</div></div><div class="mono-val">${data.container_count}</div></div>`;
    html += `</div>`;

    content.innerHTML = html;
  } catch (err) {
    content.innerHTML = errorCard(err.message);
  }
}

function formatUptime(seconds) {
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  if (days > 0) return `${days}d ${hours}h`;
  const mins = Math.floor((seconds % 3600) / 60);
  return `${hours}h ${mins}m`;
}

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes.toFixed(0)}B`;
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)}KB`;
  if (bytes < 1073741824) return `${(bytes / 1048576).toFixed(1)}MB`;
  return `${(bytes / 1073741824).toFixed(1)}GB`;
}
