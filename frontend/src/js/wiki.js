// ─── Wiki / Knowledge Reader ───────────────────────────────────────────

let _wikiSource = 'local'; // 'local' or 'outline'

async function renderWiki(content) {
  content.innerHTML = `
    ${pageHead('Wiki', 'Docs & knowledge base')}
    <div class="segmented">
      <button class="seg ${_wikiSource === 'local' ? 'active' : ''}" id="wiki-local-btn" onclick="switchWikiSource('local')">Local Wiki</button>
      <button class="seg ${_wikiSource === 'outline' ? 'active' : ''}" id="wiki-outline-btn" onclick="switchWikiSource('outline')">Outline</button>
    </div>
    <input id="wiki-search" class="search-bar" placeholder="Search wiki..." oninput="debounceWikiSearch()">
    <div id="wiki-content">${skeleton(3, 60)}</div>
  `;
  await loadWikiContent();
}

function switchWikiSource(source) {
  _wikiSource = source;
  document.getElementById('wiki-local-btn').classList.toggle('active', source === 'local');
  document.getElementById('wiki-outline-btn').classList.toggle('active', source === 'outline');
  tg.HapticFeedback.selectionChanged?.();
  loadWikiContent();
}

let _wikiSearchTimer;
function debounceWikiSearch() {
  clearTimeout(_wikiSearchTimer);
  _wikiSearchTimer = setTimeout(loadWikiContent, 400);
}

async function loadWikiContent() {
  const container = document.getElementById('wiki-content');
  if (!container) return;
  const search = document.getElementById('wiki-search')?.value || '';
  container.innerHTML = skeleton(3, 60);

  try {
    if (search) {
      // Search mode
      const results = await api(`/api/wiki/local/search?q=${encodeURIComponent(search)}`);
      let html = `<div class="section-desc">${results.matches.length} results</div>`;
      html += '<div class="card">';
      for (const m of results.matches) {
        html += `
          <div class="list-item" data-path="${m.full_path}" data-name="${m.path}">
            <div class="info">
              <div class="title">📄 ${m.path}</div>
            </div>
          </div>
        `;
      }
      html += '</div>';
      container.innerHTML = html;
      container.querySelectorAll('[data-path]').forEach(el => {
        el.addEventListener('click', () => readLocalFile(el.dataset.path, el.dataset.name));
      });
    } else if (_wikiSource === 'local') {
      const data = await api('/api/wiki/local/collections');
      let html = `<div class="section-desc">${data.entity_count} entities · ${data.collections.length} collections</div>`;
      html += '<div class="card">';
      for (const c of data.collections) {
        if (c.type === 'file') {
          html += `<div class="list-item" data-collection="${c.name}"><div class="info"><div class="title">📄 ${c.name}</div></div></div>`;
        } else {
          html += `<div class="list-item" data-collection="${c.name}"><div class="info"><div class="title">📁 ${c.name}</div><div class="subtitle">${c.doc_count} docs</div></div></div>`;
        }
      }
      html += '</div>';
      container.innerHTML = html;

      container.querySelectorAll('[data-collection]').forEach(el => {
        el.addEventListener('click', () => browseCollection(el.dataset.collection));
      });
    } else {
      // Outline
      const data = await api('/api/wiki/outline/collections');
      if (data.collections && data.collections.length > 0) {
        let html = '<div class="card">';
        for (const c of data.collections) {
          html += `<div class="list-item" data-outline-collection="${c.id}"><div class="info"><div class="title">📁 ${c.name}</div><div class="subtitle">${c.description || ''}</div></div></div>`;
        }
        html += '</div>';
        container.innerHTML = html;

        container.querySelectorAll('[data-outline-collection]').forEach(el => {
          el.addEventListener('click', () => browseOutlineCollection(el.dataset.outlineCollection));
        });
      } else {
        container.innerHTML = `<div class="card"><p style="color:var(--hint);font-size:13px">${data.note || 'No collections found'}</p></div>`;
      }
    }
  } catch (err) {
    container.innerHTML = errorCard(err.message);
  }
}

async function browseCollection(name) {
  const content = document.getElementById('content');
  historyStack.push(content.innerHTML);
  tg.BackButton.show();
  content.innerHTML = skeleton(3, 60);

  try {
    const data = await api(`/api/wiki/local/docs/${name}`);
    let html = `<div class="detail-back" onclick="popView()">‹ Back</div>`;
    html += pageHead(name, `${data.docs.length} docs`);
    html += '<div class="card">';

    for (const doc of data.docs) {
      html += `
        <div class="list-item" data-doc-path="${doc.path}">
          <div class="info">
            <div class="title">📄 ${doc.name}</div>
            <div class="subtitle">${doc.size} bytes</div>
          </div>
        </div>
      `;
    }
    html += '</div>';

    content.innerHTML = html;
    content.querySelectorAll('[data-doc-path]').forEach(el => {
      el.addEventListener('click', () => readCollectionDoc(name, el.dataset.docPath));
    });
  } catch (err) {
    content.innerHTML = errorCard(err.message);
  }
}

async function readCollectionDoc(collection, docPath) {
  const content = document.getElementById('content');
  historyStack.push(content.innerHTML);
  tg.BackButton.show();
  content.innerHTML = skeleton(2, 140);

  try {
    const data = await api(`/api/wiki/local/read?collection=${encodeURIComponent(collection)}&doc=${encodeURIComponent(docPath)}`);
    content.innerHTML = `
      <div class="detail-back" onclick="popView()">‹ Back</div>
      <div class="card wiki-doc">${escapeHtml(data.content)}</div>
    `;
  } catch (err) {
    content.innerHTML = errorCard(err.message);
  }
}

async function readLocalFile(fullPath, displayName) {
  // This is used for search results that point to files outside the wiki/wiki structure
  const content = document.getElementById('content');
  historyStack.push(content.innerHTML);
  tg.BackButton.show();
  content.innerHTML = skeleton(2, 140);

  try {
    const res = await fetch(`/api/wiki/local/read?collection=${encodeURIComponent(displayName)}`);
    const data = await res.json();
    content.innerHTML = `
      <div class="detail-back" onclick="popView()">‹ Back</div>
      <div class="card wiki-doc">${escapeHtml(data.content || 'Unable to read file')}</div>
    `;
  } catch (err) {
    content.innerHTML = errorCard(err.message);
  }
}

async function browseOutlineCollection(collectionId) {
  const content = document.getElementById('content');
  historyStack.push(content.innerHTML);
  tg.BackButton.show();
  content.innerHTML = skeleton(3, 60);

  try {
    const data = await api(`/api/wiki/outline/docs/${collectionId}`);
    let html = `<div class="detail-back" onclick="popView()">‹ Back</div>`;
    html += '<div class="card">';
    for (const d of data.docs) {
      html += `<div class="list-item" data-outline-doc="${d.id}"><div class="info"><div class="title">📄 ${d.title}</div><div class="subtitle">${timeAgo(d.updated)}</div></div></div>`;
    }
    html += '</div>';
    content.innerHTML = html;

    content.querySelectorAll('[data-outline-doc]').forEach(el => {
      el.addEventListener('click', () => readOutlineDoc(el.dataset.outlineDoc));
    });
  } catch (err) {
    content.innerHTML = errorCard(err.message);
  }
}

async function readOutlineDoc(docId) {
  const content = document.getElementById('content');
  historyStack.push(content.innerHTML);
  tg.BackButton.show();
  content.innerHTML = skeleton(2, 140);

  try {
    const data = await api(`/api/wiki/outline/read/${docId}`);
    content.innerHTML = `
      <div class="detail-back" onclick="popView()">‹ Back</div>
      <div class="card" style="font-size:14px;line-height:1.6;white-space:pre-wrap;">${escapeHtml(data.text)}</div>
    `;
  } catch (err) {
    content.innerHTML = errorCard(err.message);
  }
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
