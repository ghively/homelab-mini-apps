// ─── Smart Home Control ────────────────────────────────────────────────

async function renderSmarthome(content) {
  content.innerHTML = skeleton(4);
  try {
    const data = await api('/api/smarthome/states');
    const domains = Object.keys(data.entities).sort();
    const totalEntities = domains.reduce((n, d) => n + data.entities[d].length, 0);

    let html = pageHead('Home', 'Home Assistant control', [
      { label: 'Entities', value: totalEntities },
      { label: 'Domains', value: domains.length },
    ]);

    // Quick scene buttons
    html += '<div class="section"><div class="section-title">Quick Actions</div>';
    html += '<div class="action-grid">';
    html += `<div class="action-btn" onclick="callService('light','turn_off',{})"><div class="icon">💡</div><div class="label">All Lights Off</div></div>`;
    html += `<div class="action-btn" onclick="callService('light','turn_on',{})"><div class="icon">🔆</div><div class="label">All Lights On</div></div>`;
    html += '</div></div>';

    for (const domain of domains) {
      const entities = data.entities[domain];
      if (entities.length === 0) continue;

      html += `<div class="section"><div class="section-title" style="text-transform:capitalize">${domain} <span style="color:var(--hint);font-weight:500;font-size:13px">${entities.length}</span></div>`;
      html += '<div class="card">';

      for (const e of entities) {
        const isOn = e.state === 'on';
        const canToggle = ['light', 'switch', 'input_boolean'].includes(domain);

        let stateBadge = '';
        if (!canToggle) {
          if (isOn) stateBadge = '<span class="badge success">ON</span>';
          else if (e.state === 'off') stateBadge = '<span class="badge unknown plain">OFF</span>';
          else stateBadge = `<span class="badge info plain">${e.state}</span>`;
        }

        html += `
          <div class="list-item" data-entity="${e.entity_id}">
            <div class="info">
              <div class="title">${e.friendly_name}</div>
              <div class="subtitle mono-val" style="font-size:11px">${e.entity_id}</div>
            </div>
            ${stateBadge}
            ${canToggle ? `<button class="switch ${isOn ? 'on' : ''}" aria-label="Toggle ${e.friendly_name}" onclick="toggleEntity('${e.entity_id}', ${isOn})"></button>` : ''}
          </div>
        `;
      }
      html += '</div></div>';
    }

    content.innerHTML = html;
  } catch (err) {
    content.innerHTML = errorCard(err.message, 'HASS_URL and HASS_TOKEN must be set.');
  }
}

async function toggleEntity(entityId, isOn) {
  const domain = entityId.split('.')[0];
  const service = isOn ? 'turn_off' : 'turn_on';
  // Flip the switch immediately for feedback, then reload real state
  const sw = document.querySelector(`[data-entity="${entityId}"] .switch`);
  if (sw) sw.classList.toggle('on');
  await callService(domain, service, { entity_id: entityId });
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
