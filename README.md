# Homelab Mini Apps

A secure Telegram Mini Apps platform for managing homelab infrastructure from your phone. Built with a **fail-closed source-envelope architecture** — when a data source is unreachable, the app never renders stale or fake data as healthy.

## Architecture

```
┌─────────────────────────────────────────────┐
│  Telegram WebApp (Frontend)                 │
│  HTML/CSS/JS + Observatory design system    │
│  ↕ Authorization: tma <initData>            │
├─────────────────────────────────────────────┤
│  FastAPI Backend (Python 3.12)              │
│  ├─ Secure Auth (HMAC + replay protection)  │
│  ├─ SourceEnvelope[T] contract              │
│  ├─ Swarm Monitor (GitLab + Prometheus)     │
│  ├─ Pipeline / MR approval gate             │
│  ├─ Fleet status (Prometheus node_exporter) │
│  ├─ Alert triage (Alertmanager + Prometheus)│
│  ├─ Kanban board (Hermes native Kanban)     │
│  ├─ Remote ops (SSH command execution)      │
│  ├─ 1Password vault browser                 │
│  ├─ Smart home (Home Assistant)             │
│  ├─ Cost tracking                           │
│  └─ Wiki browser                            │
├─────────────────────────────────────────────┤
│  Docker Container (Python 3.12-slim)        │
│  Caddy reverse proxy (TLS, HTTPS)           │
└─────────────────────────────────────────────┘
```

### Source Envelope Contract

Every data source returns a `SourceEnvelope[T]` — a normalized wrapper that carries:

- **Provenance**: where the data came from, when it was fetched
- **Status**: `ok` / `stale` / `unavailable` / `error`
- **Freshness**: milliseconds since fetch
- **Data**: the typed payload (or null on failure)

**Fail-closed rule**: When a source is unreachable, the envelope status is `unavailable` and data is null. The frontend renders this as "unknown" — never as "healthy." This prevents silent failures from presenting a false sense of security.

### Security Model

- **HMAC authentication**: Telegram's `initData` string is verified against the bot token using HMAC-SHA256. No plaintext token comparison.
- **Replay protection**: Requests with stale `auth_date` (older than 5 minutes) are rejected.
- **Allowlist**: Only configured Telegram user IDs can access the API.
- **Redaction layer**: A pattern-based redactor strips secrets (tokens, API keys, passwords) from all responses and logs.
- **CORS locked**: Only Telegram webview origins are allowed.
- **No secret mounts**: The container does not mount SSH keys or 1Password config. Secrets are passed as environment variables only.

## Apps

| App | Icon | Description |
|-----|------|-------------|
| **Swarm Monitor** | 🌀 | GitLab pipeline status + Prometheus fleet health in fail-closed envelopes |
| **Pipeline** | 🔧 | GitLab CI pipeline status, MR review, merge/retry approval gate |
| **Fleet** | 🖥️ | Host health from Prometheus node_exporter (CPU, memory, disk) |
| **Kanban** | 📋 | Hermes native Kanban task board |
| **Alerts** | 🚨 | Active alerts from Alertmanager + Prometheus, silence management |
| **Remote** | ⚡ | Execute predefined SSH commands on fleet hosts |
| **1Password** | 🔑 | Browse vault items (metadata only, no secrets displayed) |
| **Home** | 🏠 | Home Assistant entity control |
| **Cost** | 📊 | Cloud spending tracker |
| **Wiki** | 📚 | Browse homelab documentation wiki |

## Design System

The **Observatory** design system provides:

- **Semantic status tokens**: `--status-healthy`, `--status-attention`, `--status-degraded`, `--status-critical`, `--status-unknown`, `--status-verified`, `--status-unverified`
- **Telegram-native foundations**: All colors derive from `tg-theme-*` CSS variables, so the app automatically matches the user's Telegram theme; surfaces and borders are derived with `color-mix` so light and dark themes both work from one palette
- **Home-screen launcher**: A tile grid of all mini apps with inline SVG glyphs and per-app accent colors, plus a sticky glass top bar with back/refresh inside each app
- **Component library**: cards, stat chips, badges with status dots, skeleton loaders, ring gauges, toggle switches, segmented controls, alert cards with severity accents, diff viewer, and terminal output — all vanilla CSS, no build step
- **Safe-area support**: `env(safe-area-inset-*)` handling for iPhone notch/home indicator
- **System font stack**: No external font dependencies — uses the device's native UI font
- **Reduced-motion support**: All animation collapses under `prefers-reduced-motion`

### TypeScript Design System Package

Located in `frontend/packages/design-system/`, the TypeScript package provides:

- Token definitions (`tokens/semantic.ts`, `tokens/telegram-themes.ts`)
- Theme provider (`theme/provider.ts`)
- Web components (theme-aware, safe-area, focus-trap, unsupported-client detection)
- Client detection (`client/detector.ts`)
- Accessibility provider (`accessibility/provider.ts`)

## Project Structure

```
homelab-mini-apps/
├── Dockerfile                 # Container image (Python 3.12-slim + 1Password CLI)
├── docker-compose.yml         # Compose definition (no secret mounts)
├── backend/
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py            # FastAPI app, CORS, router wiring
│   │   ├── core/
│   │   │   ├── auth_secure.py # HMAC auth, replay protection, allowlist
│   │   │   ├── envelope.py    # SourceEnvelope[T] contract
│   │   │   ├── redaction.py   # Secret pattern redaction
│   │   │   ├── registry.py    # App registry
│   │   │   ├── audit.py       # Audit event logging
│   │   │   ├── health.py      # Health checks
│   │   │   ├── config.py      # Environment configuration
│   │   │   └── auth.py        # Legacy auth (deprecated, use auth_secure)
│   │   ├── api/
│   │   │   ├── swarm/         # Swarm Monitor router (GitLab + Prometheus)
│   │   │   ├── pipeline.py    # GitLab pipeline + MR management
│   │   │   ├── fleet.py       # Prometheus fleet metrics
│   │   │   ├── alerts.py      # Alertmanager alerts + silences
│   │   │   ├── kanban.py      # Hermes Kanban integration
│   │   │   ├── ops_remote.py  # Remote SSH commands
│   │   │   ├── onepassword.py # 1Password vault browser
│   │   │   ├── smarthome.py   # Home Assistant control
│   │   │   ├── cost.py        # Cost tracking
│   │   │   └── wiki.py        # Wiki browser
│   │   ├── services/
│   │   │   └── swarm_monitor.py  # Async GitLab + Prometheus adapter
│   │   └── adapters/
│   │       ├── gitlab.py      # GitLab API adapter
│   │       └── prometheus.py  # Prometheus API adapter
│   └── tests/
│       ├── test_auth.py
│       ├── test_envelope.py
│       ├── test_redaction.py
│       ├── test_health.py
│       └── test_swarm_monitor.py
└── frontend/
    ├── index.html
    ├── src/
    │   ├── css/app.css        # Observatory design tokens + component styles
    │   └── js/
    │       ├── app.js         # App shell, navigation, auth
    │       ├── swarm.js       # Swarm Monitor view
    │       ├── pipeline.js    # Pipeline view
    │       ├── fleet.js       # Fleet view
    │       ├── alerts.js      # Alerts view
    │       ├── kanban.js      # Kanban view
    │       ├── ops-remote.js  # Remote ops view
    │       ├── onepassword.js # 1Password view
    │       ├── smarthome.js   # Smart home view
    │       ├── cost.js        # Cost view
    │       └── wiki.js        # Wiki view
    └── packages/
        └── design-system/     # TypeScript design system package
            ├── src/
            │   ├── tokens/    # Semantic + Telegram theme tokens
            │   ├── theme/     # Theme provider
            │   ├── web-components/  # Custom elements
            │   ├── accessibility/
            │   ├── client/
            │   ├── safe-area/
            │   └── types/
            └── tests/
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | Yes | Telegram bot token (from @BotFather) |
| `MINIAPPS_ALLOWED_USERS` | Yes | Comma-separated Telegram user IDs allowed to access |
| `GITLAB_API_URL` | No | GitLab API base URL |
| `GITLAB_TOKEN` | No | GitLab access token (read_api scope minimum) |
| `HOMELAB_ANSIBLE_PROJECT_ID` | No | GitLab project ID for pipeline/MR features |
| `PROMETHEUS_URL` | No | Prometheus URL for fleet metrics |
| `GRAFANA_URL` | No | Grafana URL for dashboard links |
| `HASS_URL` | No | Home Assistant URL |
| `HASS_TOKEN` | No | Home Assistant long-lived token |
| `OP_SERVICE_ACCOUNT_TOKEN` | No | 1Password service account token |
| `OP_VAULT` | No | 1Password vault name |
| `OUTLINE_URL` | No | Outline wiki URL |
| `OUTLINE_TOKEN` | No | Outline API token |

## Local Development

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 9876

# Run tests
cd backend
python -m pytest tests/ -v
```

## Test Suite

108 tests covering:
- **Auth** (18 tests): HMAC verification, forged data rejection, stale auth rejection, replay protection
- **Envelope** (16 tests): SourceEnvelope creation, serialization, fail-closed behavior
- **Redaction** (20 tests): Secret pattern matching, JSON redaction, fixture leakage detection
- **Health** (12 tests): Auth config validation, dependency checks
- **Swarm Monitor** (10 tests): Adapter fail-closed contract, provenance, serialization

## Deployment

This app is deployed as a Docker container behind Caddy (TLS termination). The homelab uses Ansible for deployment via the `homelab-ansible` repo's `docker_stack` role.

For standalone deployment:

```bash
# Create .env with required variables
cat > .env << 'EOF'
TELEGRAM_BOT_TOKEN=your_bot_token
MINIAPPS_ALLOWED_USERS=your_telegram_user_id
EOF

# Build and run
docker compose up -d --build
```

## Bot Configuration

To set the Telegram menu button to open the app:

```bash
curl -sS "https://api.telegram.org/bot<TOKEN>/setChatMenuButton" \
  -H "Content-Type: application/json" \
  -d '{"menu_button": {"type": "web_app", "text": "Mini Apps", "web_app": {"url": "https://your-domain.com"}}}'
```

## License

Private — Homelab use only.
