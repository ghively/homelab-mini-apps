"""Configuration — loaded from environment variables.

No real infrastructure values (IPs, hostnames, domains, credentials, personal
identifiers) ship as defaults. Every default below is a placeholder; a real
deployment must supply real values via environment variables (e.g. a `.env`
file consumed by docker-compose, or your process manager of choice).
"""

import json
import os

# Telegram
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

# Owner identity — the single Telegram user ID with OWNER role. Set this via
# env var in any real deployment; the placeholder below matches no real account.
OWNER_USER_ID = int(os.environ.get("MINIAPPS_OWNER_USER_ID", "111111111"))

ALLOWED_USER_IDS = [
    int(x)
    for x in os.environ.get("MINIAPPS_ALLOWED_USERS", str(OWNER_USER_ID)).split(",")
    if x.strip()
]

# Public origin this app is served from (used for CORS allow-listing).
MINIAPPS_PUBLIC_ORIGIN = os.environ.get(
    "MINIAPPS_PUBLIC_ORIGIN", "https://miniapps.example.com"
)

# Service URLs
PROMETHEUS_URL = os.environ.get("PROMETHEUS_URL", "http://192.0.2.50:9090")
GRAFANA_URL = os.environ.get("GRAFANA_URL", "http://192.0.2.50:3002")
GRAFANA_API_KEY = os.environ.get("GRAFANA_API_KEY", "")
ALERTMANAGER_URL = os.environ.get("ALERTMANAGER_URL", "http://192.0.2.50:9093")
UPTIME_KUMA_URL = os.environ.get("UPTIME_KUMA_URL", "http://192.0.2.50:3001")
HASS_URL = os.environ.get("HASS_URL", "http://localhost:18123")
HASS_TOKEN = os.environ.get("HASS_TOKEN", "")
GITLAB_URL = os.environ.get("GITLAB_API_URL", "https://gitlab.example.com/api/v4")
GITLAB_TOKEN = os.environ.get("GITLAB_TOKEN", "")
HOMELAB_ANSIBLE_PROJECT_ID = os.environ.get("HOMELAB_ANSIBLE_PROJECT_ID", "113")

# Jira
JIRA_URL = os.environ.get("JIRA_URL", "https://your-org.atlassian.net")
JIRA_EMAIL = os.environ.get("JIRA_EMAIL", "you@example.com")
JIRA_API_TOKEN = os.environ.get("JIRA_API_TOKEN", "")

# Vikunja
VIKUNJA_URL = os.environ.get("VIKUNJA_URL", "http://192.0.2.50:3456/api/v1")
VIKUNJA_TOKEN = os.environ.get("VIKUNJA_TOKEN", "")

# 1Password
OP_SERVICE_ACCOUNT_TOKEN = os.environ.get("OP_SERVICE_ACCOUNT_TOKEN", "")
OP_VAULT = os.environ.get("OP_VAULT", "Personal")

# Outline
OUTLINE_URL = os.environ.get("OUTLINE_URL", "https://docs.example.com/api")
OUTLINE_TOKEN = os.environ.get("OUTLINE_TOKEN", "")

# Wiki
WIKI_ROOT = os.environ.get("WIKI_ROOT", "/wiki")

# Session DB
SESSION_DB = os.environ.get("SESSION_DB", "/data/sessions.db")

# SSH user for Quick Ops Remote command execution
FLEET_SSH_USER = os.environ.get("FLEET_SSH_USER", "deploy")

# Fleet hosts — configure via FLEET_HOSTS_JSON (a JSON object keyed by host
# name; each entry may set "ip", "ts" (Tailscale IP), and "role"). The
# placeholder default below uses documentation-range addresses (RFC 5737 /
# CGNAT) and generic role labels — no real network topology ships by default.
_DEFAULT_FLEET_HOSTS = {
    "app-server": {
        "ip": "localhost",
        "ts": "100.64.0.10",
        "role": "App / Mail / Search",
    },
    "monitor-server": {
        "ip": "192.0.2.11",
        "ts": "100.64.0.11",
        "role": "Monitoring / SIEM",
    },
    "git-server": {"ip": "192.0.2.12", "ts": "100.64.0.12", "allowed_commands": []},
    "workstation": {
        "ip": "192.0.2.13",
        "ts": "100.64.0.13",
        "role": "AI Workload / ML",
    },
    "media-server": {
        "ip": "192.0.2.14",
        "ts": "100.64.0.14",
        "role": "Media + Home Automation + IoT",
    },
    "storage-server": {"ip": "192.0.2.15", "ts": None, "role": "NAS"},
    "gpu-server": {"ip": "192.0.2.16", "ts": "100.64.0.16", "role": "AI Compute"},
}

try:
    FLEET_HOSTS = (
        json.loads(os.environ["FLEET_HOSTS_JSON"])
        if os.environ.get("FLEET_HOSTS_JSON")
        else _DEFAULT_FLEET_HOSTS
    )
except (json.JSONDecodeError, TypeError):
    FLEET_HOSTS = _DEFAULT_FLEET_HOSTS

# The host key in FLEET_HOSTS that this app itself runs on (commands for it
# are executed locally instead of over SSH).
FLEET_LOCAL_HOST = os.environ.get("FLEET_LOCAL_HOST", "app-server")
