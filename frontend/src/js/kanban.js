// ─── Jira OPS Kanban Board ─────────────────────────────────────────────

async function renderKanban(content) {
  content.innerHTML = loading('Loading board...');
  try {
    const data = await api('/api/kanban/jira/board');
    const cols = Object.entries(data.columns);

    if (cols.length === 0) {
      content.innerHTML = empty('📋', 'No issues found');
      return;
    }

    let html = '<div class="kanban-board">';
    for (const [status, issues] of cols) {
      html += `<div class="kanban-col">
        <div class="kanban-col-header">${status} (${issues.length})</div>`;
      for (const issue of issues) {
        const priColors = {'Highest':'danger','High':'warning','Medium':'info','Low':'info','Lowest':'info'};
        const priClass = priColors[issue.priority] || 'info';
        const labels = issue.labels.map(l => `<span class="badge info" style="margin-right:4px">${l}</span>`).join('');
        html += `<div class="kanban-card" data-key="${issue.key}">
          <div class="key">${issue.key}</div>
          <div class="summary">${issue.summary}</div>
          <div class="meta">
            <span class="badge ${priClass}">${issue.priority}</span>
            ${labels}
            <br><span style="font-size:11px">${issue.assignee} · ${timeAgo(issue.updated)}</span>
          </div>
        </div>`;
      }
      html += '</div>';
    }
    html += '</div>';

    content.innerHTML = html;

    content.querySelectorAll('[data-key]').forEach(el => {
      el.addEventListener('click', () => viewIssueDetail(el.dataset.key));
    });
  } catch (err) {
    content.innerHTML = `<div class="card"><p style="color:var(--destructive)">${err.message}</p>
      <p style="font-size:13px;color:var(--hint);margin-top:8px">Make sure JIRA_API_TOKEN and JIRA_EMAIL are set.</p></div>`;
  }
}

async function viewIssueDetail(key) {
  const content = document.getElementById('content');
  historyStack.push(content.innerHTML);
  tg.BackButton.show();
  content.innerHTML = loading('Loading issue...');

  try {
    const [transitions, boardData] = await Promise.all([
      api(`/api/kanban/jira/transitions/${key}`),
      api('/api/kanban/jira/board'),
    ]);

    // Find the issue in the board data
    let issue = null;
    for (const issues of Object.values(boardData.columns)) {
      issue = issues.find(i => i.key === key);
      if (issue) break;
    }

    let html = `<div class="detail-back" onclick="popView()">← Back</div>`;
    html += `<div class="card">
      <div style="font-size:12px;color:var(--accent);font-weight:600">${issue.key}</div>
      <div style="font-size:16px;font-weight:600;margin-top:4px">${issue.summary}</div>
      <div style="font-size:13px;color:var(--hint);margin-top:8px">
        ${issue.assignee} · ${issue.priority} · Updated ${timeAgo(issue.updated)}
      </div>
    </div>`;

    // Transitions
    if (transitions.transitions.length > 0) {
      html += '<div class="card"><div class="card-header">Move to</div>';
      for (const t of transitions.transitions) {
        html += `<button class="btn secondary" onclick="transitionIssue('${key}','${t.id}','${t.to}')" style="margin-top:4px">${t.to}</button>`;
      }
      html += '</div>';
    }

    // Comment
    html += `<div class="card">
      <div class="card-header">Add Comment</div>
      <textarea id="comment-text" class="search-bar" style="min-height:60px;margin-bottom:8px" placeholder="Type a comment..."></textarea>
      <button class="btn" onclick="addComment('${key}')">Add Comment</button>
    </div>`;

    content.innerHTML = html;
  } catch (err) {
    content.innerHTML = `<div class="card"><p style="color:var(--destructive)">${err.message}</p></div>`;
  }
}

async function transitionIssue(key, transitionId, toName) {
  try {
    await api(`/api/kanban/jira/transition/${key}`, {
      method: 'POST',
      body: JSON.stringify({ transition_id: transitionId }),
    });
    toast(`${key} → ${toName}`);
    await renderKanban(document.getElementById('content'));
  } catch (err) {
    toast(`Transition failed: ${err.message}`);
  }
}

async function addComment(key) {
  const text = document.getElementById('comment-text').value.trim();
  if (!text) return;
  try {
    await api(`/api/kanban/jira/comment/${key}`, {
      method: 'POST',
      body: JSON.stringify({ text }),
    });
    toast('Comment added');
    document.getElementById('comment-text').value = '';
  } catch (err) {
    toast(`Comment failed: ${err.message}`);
  }
}
