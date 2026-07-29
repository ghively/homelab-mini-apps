// ─── Cost / Quota Monitor ──────────────────────────────────────────────

async function renderCost(content) {
  content.innerHTML = skeleton(4);
  try {
    const [overview, models, oci] = await Promise.all([
      api('/api/cost/overview'),
      api('/api/cost/models'),
      api('/api/cost/oci'),
    ]);

    let html = pageHead('Cost', 'Usage, quotas & free-tier limits', [
      { label: 'Containers', value: overview.container_count },
    ]);

    // OCI free tier status
    const arm = oci['gh-arm'];
    html += '<div class="section"><div class="section-title">OCI Free Tier (gh-arm)</div>';
    html += `<div class="gauge-row">
      ${gauge('Disk', arm.disk_pct)}
      ${gauge('CPU', arm.cpu_pct)}
      ${gauge('Memory', arm.mem_pct)}
    </div>`;
    html += `<div class="section-desc">${arm.compute_limit}</div>`;
    html += '</div>';

    // Network
    html += '<div class="section"><div class="section-title">Network (all hosts)</div>';
    html += `<div class="stat-grid">
      <div class="stat-tile">
        <div class="stat-label">Download</div>
        <div class="stat-value">${overview.network.rx_mbps} <small>Mbps</small></div>
      </div>
      <div class="stat-tile">
        <div class="stat-label">Upload</div>
        <div class="stat-value">${overview.network.tx_mbps} <small>Mbps</small></div>
      </div>
    </div>`;
    html += '</div>';

    // Host resource usage
    html += '<div class="section"><div class="section-title">Host CPU / Memory</div>';
    html += '<div class="card">';
    for (const h of overview.host_cpu) {
      const ip = h.instance.split(':')[0];
      const memEntry = overview.host_mem.find(m => m.instance === h.instance);
      const memPct = memEntry ? Math.round(parseFloat(memEntry.value)) : 0;
      const cpuPct = Math.round(h.cpu_pct);
      html += `
        <div class="list-item">
          <div class="info">
            <div class="title mono-val" style="font-size:13px">${ip}</div>
            <div class="subtitle">CPU <span class="mono-val" style="color:${pctColor(cpuPct)}">${cpuPct}%</span> · MEM <span class="mono-val" style="color:${pctColor(memPct)}">${memPct}%</span></div>
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
        html += `<div class="list-item"><div class="info"><div class="title">${c.name}</div></div><div class="mono-val" style="color:var(--hint)">${c.memory_mb} MB</div></div>`;
      }
      html += '</div></div>';
    }

    content.innerHTML = html;
  } catch (err) {
    content.innerHTML = errorCard(err.message);
  }
}
