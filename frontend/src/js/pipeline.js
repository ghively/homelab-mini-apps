// ─── Pipeline Approval Gate ────────────────────────────────────────────

async function renderPipeline(content) {
  const data = await api('/api/pipeline/status');

  let html = pageHead('Pipeline', 'Merge requests & CI', [
    { label: 'Open MRs', value: data.merge_requests.length },
    { label: 'Pipelines', value: data.pipelines.length },
  ]);

  html += '<div class="section"><div class="section-title">Merge Requests</div>';
  if (data.merge_requests.length === 0) {
    html += empty('✅', 'No open merge requests', 'ok');
  } else {
    for (const mr of data.merge_requests) {
      const pstatus = pipelineBadge(mr.pipeline_status);
      html += `
        <div class="card" data-mr="${mr.iid}" style="margin-bottom:8px">
          <div style="display:flex;justify-content:space-between;align-items:start;gap:8px;">
            <div style="flex:1;min-width:0">
              <div class="mono-val" style="font-size:12px;color:var(--accent);font-weight:700">!${mr.iid}</div>
              <div style="font-weight:600;margin-top:2px">${mr.title}</div>
              <div style="font-size:12px;color:var(--hint);margin-top:4px">
                ${mr.source_branch} · ${mr.changes_count} files · ${mr.author}
              </div>
            </div>
            <div style="flex-shrink:0">${pstatus}</div>
          </div>
        </div>
      `;
    }
  }
  html += '</div>';

  // Recent pipelines
  html += '<div class="section"><div class="section-title">Recent Pipelines</div>';
  if (data.pipelines.length === 0) {
    html += '<div class="section-desc">No recent pipelines</div>';
  } else {
    html += '<div class="card">';
    for (const p of data.pipelines) {
      const badge = pipelineBadge(p.status);
      html += `
        <div class="list-item">
          <div class="info">
            <div class="title mono-val" style="font-size:13px">${p.ref}</div>
            <div class="subtitle mono-val" style="font-size:11px">${p.sha} · ${timeAgo(p.created_at)}</div>
          </div>
          <div>${badge}</div>
        </div>
      `;
    }
    html += '</div>';
  }
  html += '</div>';

  content.innerHTML = html;

  // Bind MR clicks
  content.querySelectorAll('[data-mr]').forEach(el => {
    el.addEventListener('click', () => viewMRDetail(parseInt(el.dataset.mr)));
  });
}

function pipelineBadge(status) {
  const map = {
    'success': '<span class="badge success">passed</span>',
    'failed': '<span class="badge danger">failed</span>',
    'running': '<span class="badge warning">running</span>',
    'pending': '<span class="badge warning">pending</span>',
    'canceled': '<span class="badge info">canceled</span>',
    'manual': '<span class="badge info">manual</span>',
    'none': '<span class="badge unknown plain">no pipeline</span>',
    'unknown': '<span class="badge unknown">unknown</span>',
  };
  return map[status] || `<span class="badge info">${status}</span>`;
}

async function viewMRDetail(iid) {
  const content = document.getElementById('content');
  historyStack.push(content.innerHTML);
  tg.BackButton.show();
  content.innerHTML = skeleton(4);

  const data = await api(`/api/pipeline/mr/${iid}/diff`);
  let html = `<div class="detail-back" onclick="popView()">‹ Back</div>`;
  html += `<div class="card">
    <div class="mono-val" style="font-size:12px;color:var(--accent);font-weight:700">!${data.iid}</div>
    <div style="font-size:16px;font-weight:700;margin-top:4px">${data.title}</div>
    <div style="font-size:13px;color:var(--hint);margin-top:8px">${data.description || 'No description'}</div>
  </div>`;

  // Changes
  for (const ch of data.changes) {
    const path = ch.new_file ? ch.new_path : ch.old_path;
    const marker = ch.new_file
      ? '<span class="badge success plain">A</span>'
      : ch.deleted_file
        ? '<span class="badge danger plain">D</span>'
        : '<span class="badge info plain">M</span>';
    html += `<div class="diff-file">
      <div class="diff-file-header">${marker} ${path}</div>
      <div class="diff-content">${formatDiff(ch.diff)}</div>
    </div>`;
  }

  // Merge button
  html += `<button class="btn" onclick="mergeMR(${iid})" style="margin-top:12px">Merge MR !${iid}</button>`;
  html += `<button class="btn secondary" onclick="window.open('${data.web_url || '#'}', '_blank')">Open in GitLab</button>`;

  content.innerHTML = html;
}

function formatDiff(diff) {
  if (!diff) return '';
  return diff.split('\n').map(line => {
    if (line.startsWith('+++') || line.startsWith('---')) return '';
    if (line.startsWith('@@')) return `<span class="diff-ctx">${line}</span>`;
    if (line.startsWith('+')) return `<span class="diff-add">${line}</span>`;
    if (line.startsWith('-')) return `<span class="diff-del">${line}</span>`;
    return `<span class="diff-ctx">${line}</span>`;
  }).filter(l => l !== '').join('\n');
}

async function mergeMR(iid) {
  tg.MainButton.showProgress();
  try {
    await api(`/api/pipeline/mr/${iid}/merge`, { method: 'POST' });
    toast(`MR !${iid} merged successfully`);
    await renderPipeline(document.getElementById('content'));
  } catch (err) {
    toast(`Merge failed: ${err.message}`);
  }
  tg.MainButton.hideProgress();
}
