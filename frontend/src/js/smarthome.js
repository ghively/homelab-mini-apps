// ─── Smart Home Control ────────────────────────────────────────────────

async function renderSmarthome(content) {
  content.innerHTML = loading('Loading entities...');
  try {
    const data = await api('/api/smarthome/states');
    const domains = Object.keys(data.entities).sort();
    let html = '';

    // Quick scene buttons
    html += '<div class="section"><div class="section-title">Quick Actions</div>';
    html += '<div class="action-grid">';
    html += `<div class="action-btn" onclick="callService('light','turn_off',{})"><div class="icon">💡</div><div class="label">All Lights Off</div></div>`;
    html += `<div class="action-btn" onclick="callService('light','turn_on',{})"><div class="icon">🔆</div><div class="label">All Lights On</div></div>`;
    html += '</div></div>';

    for (const domain of domains) {
      const entities = data.entities[domain];
      if (entities.length === 0) continue;

      html += `<div class="section"><div class="section-title">${domain} (${entities.length})</div>`;
      html += '<div class="card">';

      for (const e of entities) {
        const isOn = e.state === 'on';
        const canToggle = ['light', 'switch', 'input_boolean'].includes(domain);

        let stateBadge;
        if (isOn) stateBadge = '<span class="badge success">ON</span>';
        else if (e.state === 'off') stateBadge = '<span class="badge info">OFF</span>';
        else stateBadge = `<span class="badge info">${e.state}</span>`;

        html += `
          <div class="list-item" data-entity="${e.entity_id}">
            <div class="info">
              <div class="title">${e.friendly_name}</div>
              <div class="subtitle">${e.entity_id} · ${e.state}</div>
            </div>
            ${stateBadge}
            ${canToggle ? `<button class="action" onclick="toggleEntity('${e.entity_id}', ${isOn})">${isOn ? 'Off' : 'On'}</button>` : ''}
          </div>
        `;
      }
      html += '</div></div>';
    }

    content.innerHTML = html;
  } catch (err) {
    content.innerHTML = `<div class="card">
      <p style="color:var(--destructive)">${err.message}</p>
      <p style="font-size:13px;color:var(--hint);margin-top:8px">HASS_URL and HASS_TOKEN must be set.</p>
    </div>`;
  }
}

async function toggleEntity(entityId, isOn) {
  const domain = entityId.split('.')[0];
  const service = isOn ? 'turn_off' : 'turn_on';
  await callService(domain, service, { entity_id: entityId });
  // Reload
  await renderSmarthome(document.getElementById('content'));
}

async function callService(domain, service, serviceData) {
  try {
    await api(`/api/smarthome/call/${domain}/${service}`, {
      method: 'POST',
      body: JSON.stringify({ service_data: serviceData }),
    });
    toast(`${domain}.${service} called`);
  } catch (err) {
    toast(`Failed: ${err.message}`);
  }
}
