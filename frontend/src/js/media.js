// ─── Media — latest movies & TV, cast to Home Assistant players ────────

const _posterCache = new Map(); // item id → blob object URL

async function renderMedia(content) {
  content.innerHTML = skeleton(3, 190);
  try {
    const data = await api('/api/media/latest');

    let html = pageHead('Media', 'Recently added on Jellyfin', [
      { label: 'Movies', value: data.movies.length },
      { label: 'Shows', value: data.shows.length },
    ]);

    if (data.movies.length === 0 && data.shows.length === 0) {
      html += empty('🎬', 'Nothing new in the library');
      content.innerHTML = html;
      return;
    }

    html += mediaShelf('Latest Movies', data.movies);
    html += mediaShelf('Latest Shows', data.shows);

    content.innerHTML = html;
    bindMediaCards(content);
    hydratePosters(content);
  } catch (err) {
    content.innerHTML = errorCard(err.message, 'JELLYFIN_URL and JELLYFIN_API_KEY must be set.');
  }
}

function mediaShelf(title, items) {
  if (items.length === 0) return '';
  return `
    <div class="section">
      <div class="section-title">${title}</div>
      <div class="media-shelf">
        ${items.map(m => {
          const posterId = m.poster_id || m.id;
          const sub = m.type === 'Episode'
            ? `S${m.season ?? '?'} · E${m.episode ?? '?'}`
            : (m.year || '');
          return `
            <div class="media-card" data-media='${JSON.stringify(m).replace(/'/g, '&#39;')}'>
              <div class="media-poster ${m.has_poster ? '' : 'no-art'}" data-poster="${posterId}">
                <span class="media-poster-fallback">🎬</span>
                ${m.rating ? `<span class="media-rating">★ ${m.rating.toFixed(1)}</span>` : ''}
              </div>
              <div class="media-name">${m.series || m.name}</div>
              <div class="media-sub">${sub}</div>
            </div>`;
        }).join('')}
      </div>
    </div>`;
}

function bindMediaCards(root) {
  root.querySelectorAll('[data-media]').forEach(el => {
    el.addEventListener('click', () => {
      tg.HapticFeedback.selectionChanged?.();
      viewMediaDetail(JSON.parse(el.dataset.media));
    });
  });
}

// Posters need the auth header, so <img src> won't do — fetch each as a blob.
async function hydratePosters(root) {
  for (const el of root.querySelectorAll('[data-poster]:not(.no-art)')) {
    const id = el.dataset.poster;
    try {
      if (!_posterCache.has(id)) {
        const res = await fetch(`/api/media/poster/${id}`, {
          headers: { 'Authorization': `tma ${initData}` },
        });
        if (!res.ok) throw new Error('no poster');
        _posterCache.set(id, URL.createObjectURL(await res.blob()));
      }
      el.style.backgroundImage = `url(${_posterCache.get(id)})`;
      el.classList.add('loaded');
    } catch {
      el.classList.add('no-art');
    }
  }
}

async function viewMediaDetail(m) {
  const content = document.getElementById('content');
  historyStack.push(content.innerHTML);
  tg.BackButton.show();

  const posterId = m.poster_id || m.id;
  const facts = [
    m.year,
    m.runtime_min ? `${m.runtime_min} min` : null,
    m.official_rating,
    m.rating ? `★ ${m.rating.toFixed(1)}` : null,
  ].filter(Boolean).join(' · ');

  content.innerHTML = `
    <div class="detail-back" onclick="popView()">‹ Back</div>
    <div class="media-hero">
      <div class="media-poster large ${m.has_poster ? '' : 'no-art'}" data-poster="${posterId}">
        <span class="media-poster-fallback">🎬</span>
      </div>
      <div class="media-hero-info">
        <div class="media-hero-title">${m.series || m.name}</div>
        ${m.series ? `<div class="media-hero-ep">S${m.season ?? '?'} · E${m.episode ?? '?'} — ${m.name}</div>` : ''}
        <div class="media-hero-facts">${facts}</div>
      </div>
    </div>
    ${m.overview ? `<div class="card"><div class="card-header">Overview</div><div class="media-overview">${m.overview}</div></div>` : ''}
    <div class="card">
      <div class="card-header">Play On</div>
      <div id="media-players">${skeleton(2, 48)}</div>
    </div>
  `;
  hydratePosters(content);
  loadMediaPlayers(m);
}

async function loadMediaPlayers(m) {
  const box = document.getElementById('media-players');
  try {
    const data = await api('/api/media/players');
    if (!box) return;
    if (data.players.length === 0) {
      box.innerHTML = '<p style="color:var(--hint);font-size:13px">No media players found in Home Assistant</p>';
      return;
    }
    box.innerHTML = data.players.map(p => {
      const offline = p.state === 'unavailable' || p.state === 'unknown';
      const sub = offline ? 'unavailable'
        : p.now_playing ? `playing: ${p.now_playing}`
        : p.state;
      return `
        <div class="list-item">
          <div class="info">
            <div class="title">${playerGlyph(p)} ${p.name}</div>
            <div class="subtitle">${sub}</div>
          </div>
          ${offline
            ? '<span class="badge unknown">offline</span>'
            : `<button class="action" data-cast="${p.entity_id}">▶ Play</button>`}
        </div>`;
    }).join('');

    box.querySelectorAll('[data-cast]').forEach(btn => {
      btn.addEventListener('click', () => castMedia(btn, m, btn.dataset.cast));
    });
  } catch (err) {
    if (box) box.innerHTML = errorCard(err.message);
  }
}

function playerGlyph(p) {
  const n = (p.name + ' ' + p.entity_id).toLowerCase();
  if (n.includes('tv') || n.includes('shield') || n.includes('roku')) return '📺';
  if (n.includes('cast') || n.includes('chromecast')) return '📡';
  if (n.includes('speaker') || n.includes('sonos') || n.includes('audio')) return '🔊';
  return '▶️';
}

async function castMedia(btn, m, entityId) {
  const original = btn.textContent;
  btn.textContent = 'Casting…';
  btn.disabled = true;
  try {
    await api('/api/media/play', {
      method: 'POST',
      body: JSON.stringify({ entity_id: entityId, item_id: m.id }),
    });
    btn.textContent = '✓ Playing';
    toast(`Playing “${m.series || m.name}”`);
    tg.HapticFeedback.notificationOccurred('success');
    setTimeout(() => { btn.textContent = original; btn.disabled = false; }, 2500);
  } catch (err) {
    btn.textContent = original;
    btn.disabled = false;
    toast(`Cast failed: ${err.message}`);
    tg.HapticFeedback.notificationOccurred('error');
  }
}
