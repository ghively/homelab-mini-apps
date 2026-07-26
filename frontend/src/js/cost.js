// ─── Cost / Quota Monitor ──────────────────────────────────────────────

async function renderCost(content) {
  content.innerHTML = loading('Loading metrics...');
  try {
    const [overview, models, oci] = await Promise.all([
      api('/api/cost/overview'),
      api('/api/cost/models'),
      api('/api/cost/oci'),
    ]);

    let html = '';

    // OCI free tier status
    html += '<div class="section"><div class="section-title">OCI Free Tier (gh-arm)</div>';
    html += '<div class="card">';
    html += `<div class="list-item"><div class="info"><div class="title">Disk</div></div><div style="color:${pctColor(oci['gh-arm'].disk_pct)}">${oci['gh-arm'].disk_pct}%</div></div>`;
    html += `${progress(oci['gh-arm'].disk_pct)}`;
    html += `<div class="list-item"><div class="info"><div class="title">CPU</div></div><div style="color:${pctColor(oci['gh-arm'].cpu_pct)}">${oci['gh-arm'].cpu_pct}%</div></div>`;
    html += `${progress(oci['gh-arm'].cpu_pct)}`;
    html += `<div class="list-item"><div class="info"><div class="title">Memory</div></div><div style="color:${pctColor(oci['gh-arm'].mem_pct)}">${oci['gh-arm'].mem_pct}%</div></div>`;
    html += `${progress(oci['gh-arm'].mem_pct)}`;
    html += `<div class="subtitle" style="margin-top:8px">${oci['gh-arm'].compute_limit}</div>`;
    html += '</div></div>';

    // Network
    html += '<div class="section"><div class="section-title">Network (all hosts)</div>';
    html += '<div class="card">';
    html += `<div class="list-item"><div class="info"><div class="title">Download</div></div><div>${overview.network.rx_mbps} Mbps</div></div>`;
    html += `<div class="list-item"><div class="info"><div class="title">Upload</div></div><div>${overview.network.tx_mbps} Mbps</div></div>`;
    html += `<div class="subtitle" style="margin-top:8px">${overview.container_count} containers running across fleet</div>`;
    html += '</div></div>';

    // Host resource usage
    html += '<div class="section"><div class="section-title">Host CPU/Memory</div>';
    html += '<div class="card">';
    for (const h of overview.host_cpu) {
      const ip = h.instance.split(':')[0];
      const memEntry = overview.host_mem.find(m => m.instance === h.instance);
      const memPct = memEntry ? Math.round(parseFloat(memEntry.value)) : 0;
      const cpuPct = Math.round(h.cpu_pct);
      html += `
        <div class="list-item">
          <div class="info">
            <div class="title">${ip}</div>
            <div class="subtitle">CPU: <span style="color:${pctColor(cpuPct)}">${cpuPct}%</span> · MEM: <span style="color:${pctColor(memPct)}">${memPct}%</span></div>
          </div>
        </div>
      `;
    }
    html += '</div></div>';

    // Model usage
    if (models.usage && models.usage.length > 0) {
      html += '<div class="section"><div class="section-title">Model Usage (24h)</div>';
      html += '<div class="card">';
      for (const u of models.usage) {
        html += `
          <div class="list-item">
            <div class="info">
              <div class="title">${u.model}</div>
              <div class="subtitle">${u.provider} · ${u.requests} requests · ${(u.tokens / 1000).toFixed(1)}K tokens</div>
            </div>
          </div>
        `;
      }
      html += '</div></div>';
    }

    // Top containers by memory
    if (overview.containers.length > 0) {
      html += '<div class="section"><div class="section-title">Top Containers (memory)</div>';
      html += '<div class="card">';
      for (const c of overview.containers.slice(0, 10)) {
        html += `<div class="list-item"><div class="info"><div class="title">${c.name}</div><div class="subtitle">${c.memory_mb} MB</div></div></div>`;
      }
      html += '</div></div>';
    }

    content.innerHTML = html;
  } catch (err) {
    content.innerHTML = `<div class="card"><p style="color:var(--destructive)">${err.message}</p></div>`;
  }
}
