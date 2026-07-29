// ─── 1Password Vault Browser ───────────────────────────────────────────

async function render1Password(content) {
  content.innerHTML = `
    ${pageHead('1Password', 'Read-only vault browser')}
    <input id="1p-search" class="search-bar" placeholder="Search vault items..." oninput="debounceSearch1P()">
    <div id="1p-items">${skeleton(3, 60)}</div>
  `;
  await load1PItems();
}

let _1pSearchTimer;
function debounceSearch1P() {
  clearTimeout(_1pSearchTimer);
  _1pSearchTimer = setTimeout(load1PItems, 300);
}

async function load1PItems() {
  const search = document.getElementById('1p-search')?.value || '';
  const container = document.getElementById('1p-items');
  if (!container) return;
  container.innerHTML = skeleton(3, 60);

  try {
    const data = await api(`/api/1password/items${search ? '?query=' + encodeURIComponent(search) : ''}`);
    let html = `<div class="section-desc">${data.total} items</div>`;

    if (data.items.length === 0) {
      html += empty('🔑', 'No items found');
    } else {
      html += '<div class="card">';
      for (const item of data.items) {
        const icon = item.category === 'LOGIN' ? '👤' :
                     item.category === 'PASSWORD' ? '🔒' :
                     item.category === 'API_CREDENTIAL' ? '🔌' :
                     item.category === 'SSH_KEY' ? '🔐' :
                     item.category === 'DOCUMENT' ? '📄' : '📦';
        html += `
          <div class="list-item" data-item="${item.id}">
            <div class="info">
              <div class="title">${icon} ${item.title}</div>
              <div class="subtitle">${item.category} · ${item.vault}</div>
            </div>
          </div>
        `;
      }
      html += '</div>';
    }
    container.innerHTML = html;

    container.querySelectorAll('[data-item]').forEach(el => {
      el.addEventListener('click', () => view1PItem(el.dataset.item));
    });
  } catch (err) {
    container.innerHTML = errorCard(err.message);
  }
}

async function view1PItem(itemId) {
  const content = document.getElementById('content');
  historyStack.push(content.innerHTML);
  tg.BackButton.show();
  content.innerHTML = skeleton(3);

  try {
    const data = await api(`/api/1password/items/${itemId}`);
    let html = `<div class="detail-back" onclick="popView()">‹ Back</div>`;
    html += pageHead(data.title, data.category);

    if (data.fields.length > 0) {
      html += '<div class="card"><div class="card-header">Fields</div>';
      for (const f of data.fields) {
        if (!f.label && !f.value) continue;
        const isSecret = f.type === 'CONCEALED' || f.purpose === 'PASSWORD';
        const maskedValue = isSecret ? '••••••••' : (f.value || '');
        html += `
          <div class="list-item">
            <div class="info">
              <div class="title">${f.label || f.id}</div>
              <div class="subtitle mono-val" style="font-size:12px" id="field-${f.id}">${maskedValue}</div>
            </div>
            ${isSecret && f.value ? `<button class="action" onclick="revealField('${f.id}', '${btoa(f.value)}')">Show</button>` : ''}
            ${!isSecret && f.value ? `<button class="action" onclick="copyText('${btoa(f.value)}')">Copy</button>` : ''}
          </div>
        `;
      }
      html += '</div>';
    }

    if (data.urls && data.urls.length > 0) {
      html += '<div class="card"><div class="card-header">URLs</div>';
      for (const u of data.urls) {
        html += `<div class="list-item"><div class="info"><div class="subtitle">${u.href}</div></div></div>`;
      }
      html += '</div>';
    }

    if (data.notes) {
      html += `<div class="card"><div class="card-header">Notes</div><div style="font-size:13px;white-space:pre-wrap">${data.notes}</div></div>`;
    }

    content.innerHTML = html;
  } catch (err) {
    content.innerHTML = errorCard(err.message);
  }
}

function revealField(id, encoded) {
  const el = document.getElementById(`field-${id}`);
  el.textContent = atob(encoded);
  tg.HapticFeedback.selectionChanged();
}

function copyText(encoded) {
  const text = atob(encoded);
  navigator.clipboard.writeText(text).then(() => {
    toast('Copied to clipboard');
  });
}
