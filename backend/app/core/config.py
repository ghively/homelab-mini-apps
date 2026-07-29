"""Configuration — loaded from environment variables."""

import os

# Telegram
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
ALLOWED_USER_IDS = [
    int(x)
    for x in os.environ.get("MINIAPPS_ALLOWED_USERS", "8971338885").split(",")
    if x.strip()
]

# Service URLs
PROMETHEUS_URL = os.environ.get("PROMETHEUS_URL", "http://100.65.126.126:9090")
GRAFANA_URL = os.environ.get("GRAFANA_URL", "http://100.65.126.126:3002")
GRAFANA_API_KEY = os.environ.get("GRAFANA_API_KEY", "")
HASS_URL = os.environ.get("HASS_URL", "http://localhost:18123")
HASS_TOKEN = os.environ.get("HASS_TOKEN", "")
GITLAB_URL = os.environ.get("GITLAB_API_URL", "https://git.hively.dev/api/v4")
GITLAB_TOKEN = os.environ.get("GITLAB_TOKEN", "")
HOMELAB_ANSIBLE_PROJECT_ID = os.environ.get("HOMELAB_ANSIBLE_PROJECT_ID", "113")

# Jira
JIRA_URL = os.environ.get("JIRA_URL", "https://hivelylabs.atlassian.net")
JIRA_EMAIL = os.environ.get("JIRA_EMAIL", "genehively@gmail.com")
JIRA_API_TOKEN = os.environ.get("JIRA_API_TOKEN", "")

# Vikunja
VIKUNJA_URL = os.environ.get("VIKUNJA_URL", "http://100.65.126.126:3456/api/v1")
VIKUNJA_TOKEN = os.environ.get("VIKUNJA_TOKEN", "")

# Media (Jellyfin on gh-media)
JELLYFIN_URL = os.environ.get("JELLYFIN_URL", "http://100.116.139.100:8096")
JELLYFIN_API_KEY = os.environ.get("JELLYFIN_API_KEY", "")

# Outline
OUTLINE_URL = os.environ.get("OUTLINE_URL", "https://doc.hively.dev/api")
OUTLINE_TOKEN = os.environ.get("OUTLINE_TOKEN", "")

# Wiki
WIKI_ROOT = os.environ.get("WIKI_ROOT", "/wiki")

# Session DB
SESSION_DB = os.environ.get("SESSION_DB", "/data/sessions.db")

# Fleet hosts (Tailscale IPs where available)
FLEET_HOSTS = {
    "gh-ai": {
        "ip": "localhost",
        "ts": "100.92.162.32",
        "role": "Hermes + Mail + Search",
    },
    "gh-arm": {
        "ip": "100.65.126.126",
        "ts": "100.65.126.126",
        "role": "Monitoring + SIEM",
    },
    "gh-git": {"ip": "100.116.221.84", "ts": "100.116.221.84", "allowed_commands": []},
    "gh-mac": {
        "ip": "192.168.0.167",
        "ts": "100.97.166.81",
        "role": "AI Workload / ML",
    },
    "gh-media": {
        "ip": "192.168.0.165",
        "ts": "100.116.139.100",
        "role": "Media + HA + IoT",
    },
    "gh-storage": {"ip": "192.168.0.196", "ts": None, "role": "Synology NAS"},
    "gh-nvidia": {"ip": "100.88.26.95", "ts": "100.88.26.95", "role": "AI Compute"},
}
