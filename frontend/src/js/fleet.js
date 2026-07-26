// ─── Fleet Health Dashboard ────────────────────────────────────────────

async function renderFleet(content) {
  const data = await api('/api/fleet/overview');
  let html = `<div class="section">
    <div class="section-title">Fleet Overview</div>
    <div class="section-desc">${data.hosts_up} up · ${data.hosts_down} down · ${data.total_hosts} total</div>
  </div>`;

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
    if (!up) dotClass = 'red';
    else if (worst >= 90) dotClass = 'red';
    else if (worst >= 75) dotClass = 'yellow';

    html += `
      <div class="host-card" data-ip="${host.ip}">
        <div style="display:flex;justify-content:space-between;align-items:start;">
          <div>
            <div class="name">${host.name || host.ip}</div>
            <div class="ip">${host.ip}</div>
          </div>
          <span class="status-dot ${dotClass}"></span>
        </div>
        ${up ? `
          <div class="metrics">
            <div class="metric">CPU <span style="color:${pctColor(cpu)}">${cpu}%</span></div>
            <div class="metric">MEM <span style="color:${pctColor(mem)}">${mem}%</span></div>
            <div class="metric">DSK <span style="color:${pctColor(disk)}">${disk}%</span></div>
          </div>
        ` : '<div class="metric" style="color:var(--destructive);margin-top:4px;">OFFLINE</div>'}
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
  content.innerHTML = loading('Probing host...');

  try {
    const data = await api(`/api/fleet/host/${encodeURIComponent(ip)}`);
    const uptime = formatUptime(data.uptime_seconds);

    let html = `<div class="detail-back" onclick="popView()">← Back</div>`;
    html += `<div class="card">
      <div style="font-size:18px;font-weight:600">${data.name || data.ip}</div>
      <div style="font-size:13px;color:var(--hint)">${data.ip}</div>
    </div>`;

    html += '<div class="card"><div class="card-header">CPU</div>';
    html += `<div style="display:flex;align-items:center;gap:8px;">`;
    html += `<span style="font-size:24px;font-weight:700;color:${pctColor(data.cpu_pct)}">${data.cpu_pct.toFixed(1)}%</span>`;
    html += `</div>${progress(data.cpu_pct)}</div>`;

    html += '<div class="card"><div class="card-header">Memory</div>';
    html += `<span style="font-size:24px;font-weight:700;color:${pctColor(data.mem_pct)}">${data.mem_pct.toFixed(1)}%</span>`;
    html += `${progress(data.mem_pct)}</div>`;

    html += '<div class="card"><div class="card-header">Disk</div>';
    html += `<span style="font-size:24px;font-weight:700;color:${pctColor(data.disk_pct)}">${data.disk_pct.toFixed(1)}%</span>`;
    html += `${progress(data.disk_pct)}</div>`;

    html += `<div class="card"><div class="card-header">Details</div>`;
    html += `<div class="list-item"><div class="info"><div class="title">Load (1m)</div></div><div>${data.load1.toFixed(2)}</div></div>`;
    html += `<div class="list-item"><div class="info"><div class="title">Uptime</div></div><div>${uptime}</div></div>`;
    html += `<div class="list-item"><div class="info"><div class="title">Network RX</div></div><div>${formatBytes(data.net_rx_bps)}/s</div></div>`;
    html += `<div class="list-item"><div class="info"><div class="title">Network TX</div></div><div>${formatBytes(data.net_tx_bps)}/s</div></div>`;
    html += `<div class="list-item"><div class="info"><div class="title">Containers</div></div><div>${data.container_count}</div></div>`;
    html += `</div>`;

    content.innerHTML = html;
  } catch (err) {
    content.innerHTML = `<div class="card"><p style="color:var(--destructive)">Error: ${err.message}</p></div>`;
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
