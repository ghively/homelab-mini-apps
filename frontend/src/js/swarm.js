// Swarm Monitor — read-only GitLab + Prometheus source envelopes
async function renderSwarm(content) {
  const data = await api('/api/swarm/');

  let html = `
    <div class="card">
      <div class="card-header">Swarm Monitor — Source Overview</div>
      <div style="display:flex;gap:12px;align-items:center;">
        <span class="badge ${data.summary.healthy_sources === data.summary.total_sources ? 'success' : 'warning'}">
          ${data.summary.healthy_sources}/${data.summary.total_sources} healthy
        </span>
      </div>
    </div>
  `;

  for (const source of data.sources) {
    const statusClass = source.status === 'ok' ? 'success'
      : source.status === 'stale' ? 'warning'
      : source.status === 'unavailable' ? 'unknown'
      : 'danger';

    const statusLabel = source.status.toUpperCase();

    let sourceData = '';
    if (source.data) {
      if (source.source.includes('gitlab')) {
        const lp = source.data.latest_pipeline || {};
        sourceData = `
          <div>Latest pipeline: <span class="badge ${lp.status === 'success' ? 'success' : lp.status === 'failed' ? 'danger' : 'warning'}">${lp.status || 'unknown'}</span></div>
          <div>Ref: ${lp.ref || '—'} · SHA: ${lp.sha || '—'}</div>
        `;
      } else if (source.source.includes('prometheus')) {
        sourceData = `
          <div>Hosts up: ${source.data.hosts_up}/${source.data.hosts_total}</div>
          ${source.data.hosts ? source.data.hosts.map(h =>
            `<div style="margin-left:12px;">${h.status === 'up' ? '✅' : '❌'} ${h.instance}</div>`
          ).join('') : ''}
        `;
      }
    } else {
      sourceData = `<div style="color:var(--hint);">${source.error || 'No data available'}</div>`;
    }

    html += `
      <div class="source-card">
        <div class="source-header">
          <span class="source-title">${source.source}</span>
          <span class="badge ${statusClass}">${statusLabel}</span>
        </div>
        <div class="source-data">${sourceData}</div>
        <div class="provenance">
          <span class="source-name">${source.provenance.kind}</span>
          <span class="freshness">${source.freshness_ms ? Math.round(source.freshness_ms / 1000) + 's old' : 'unknown'}</span>
        </div>
      </div>
    `;
  }

  content.innerHTML = html;
}
