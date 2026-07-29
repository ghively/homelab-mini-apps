// ─── Alert Triage Console ──────────────────────────────────────────────

async function renderAlerts(content) {
  const data = await api('/api/alerts/active');
  const total = data.total;

  let html = pageHead('Alerts', 'Triage & silences', [
    { label: 'Firing', value: total, dot: total > 0 ? 'red pulse' : 'green' },
  ]);

  if (total === 0) {
    html += empty('✅', 'All clear — no active alerts', 'ok');
  }

  const alertItem = (a, sinceIso) => {
    const critical = a.severity === 'critical';
    return `
      <div class="alert-item ${critical ? 'critical' : ''}">
        <div class="info">
          <div class="title">${a.name}</div>
          <div class="subtitle">${a.summary || a.description || ''}</div>
          <div class="subtitle" style="margin-top:3px">${a.instance} · since ${timeAgo(sinceIso)}</div>
        </div>
        <span class="badge ${critical ? 'danger' : 'warning'}">${a.severity}</span>
      </div>
    `;
  };

  if (data.alertmanager.length > 0) {
    html += '<div class="section"><div class="section-title">Alertmanager</div>';
    html += data.alertmanager.map(a => alertItem(a, a.starts_at)).join('');
    html += '</div>';
  }

  if (data.prometheus_firing.length > 0) {
    html += '<div class="section"><div class="section-title">Prometheus (firing)</div>';
    html += data.prometheus_firing.map(a => alertItem(a, a.active_at)).join('');
    html += '</div>';
  }

  html += `<button class="btn secondary" onclick="viewSilenceForm()">Create Silence</button>`;
  html += `<button class="btn secondary" onclick="viewSilences()">View Active Silences</button>`;

  content.innerHTML = html;
}

async function viewSilenceForm() {
  const content = document.getElementById('content');
  historyStack.push(content.innerHTML);
  tg.BackButton.show();

  content.innerHTML = `
    <div class="detail-back" onclick="popView()">‹ Back</div>
    <div class="card">
      <div class="card-header">Create Silence</div>
      <div class="section-desc" style="padding:0">Suppress alerts matching a label</div>
      <input id="silence-matcher-name" class="search-bar" placeholder="Label name (e.g. alertname)" value="alertname">
      <input id="silence-matcher-value" class="search-bar" placeholder="Label value (e.g. HighCPU)">
      <input id="silence-duration" class="search-bar" type="number" placeholder="Duration (minutes)" value="60">
      <input id="silence-comment" class="search-bar" placeholder="Comment">
      <button class="btn" onclick="createSilence()">Create Silence</button>
    </div>
  `;
}

async function createSilence() {
  const matcherName = document.getElementById('silence-matcher-name').value;
  const matcherValue = document.getElementById('silence-matcher-value').value;
  const duration = parseInt(document.getElementById('silence-duration').value);
  const comment = document.getElementById('silence-comment').value;

  try {
    await api('/api/alerts/silence', {
      method: 'POST',
      body: JSON.stringify({
        matcher_name: matcherName,
        matcher_value: matcherValue,
        duration_minutes: duration,
        comment,
      }),
    });
    toast('Silence created');
    popView();
    await renderAlerts(document.getElementById('content'));
  } catch (err) {
    toast(`Failed: ${err.message}`);
  }
}

async function viewSilences() {
  const content = document.getElementById('content');
  historyStack.push(content.innerHTML);
  tg.BackButton.show();
  content.innerHTML = skeleton(3);

  try {
    const data = await api('/api/alerts/silences');
    let html = `<div class="detail-back" onclick="popView()">‹ Back</div>`;
    html += '<div class="card"><div class="card-header">Active Silences</div>';

    if (data.silences.length === 0) {
      html += '<p style="color:var(--hint);font-size:13px">No active silences</p>';
    } else {
      for (const s of data.silences) {
        html += `
          <div class="list-item">
            <div class="info">
              <div class="title">${s.comment || 'Silenced'}</div>
              <div class="subtitle">By ${s.createdBy} · until ${new Date(s.endsAt).toLocaleString()}</div>
              <div class="subtitle mono-val" style="font-size:11px">${s.matchers.map(m => `${m.name}=${m.value}`).join(', ')}</div>
            </div>
          </div>
        `;
      }
    }
    html += '</div>';
    content.innerHTML = html;
  } catch (err) {
    content.innerHTML = errorCard(err.message);
  }
}
