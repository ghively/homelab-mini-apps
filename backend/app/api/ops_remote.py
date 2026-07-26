"""Quick Ops Remote — execute predefined safe actions on fleet hosts."""

import asyncio
import httpx
import subprocess
from fastapi import APIRouter, Depends, HTTPException
from ..core.auth_secure import get_authenticated_user
from ..core.config import FLEET_HOSTS

router = APIRouter()

# Predefined safe actions per host
ACTIONS = {
    "gh-ai": {
        "restart_container:stalwart": {
            "cmd": "docker restart stalwart",
            "desc": "Restart Stalwart mail server",
        },
        "restart_container:searxng": {
            "cmd": "docker restart searxng",
            "desc": "Restart SearXNG",
        },
        "restart_container:open-webui": {
            "cmd": "docker restart open-webui",
            "desc": "Restart Open WebUI",
        },
        "logs:stalwart": {
            "cmd": "docker logs --tail 20 stalwart",
            "desc": "Stalwart recent logs",
        },
        "logs:searxng": {
            "cmd": "docker logs --tail 20 searxng",
            "desc": "SearXNG recent logs",
        },
        "docker_ps": {
            "cmd": "docker ps --format 'table {{.Names}}\\t{{.Status}}\\t{{.Ports}}'",
            "desc": "List running containers",
        },
        "disk_usage": {"cmd": "df -h / | tail -1", "desc": "Disk usage"},
        "memory": {"cmd": "free -h", "desc": "Memory info"},
    },
    "gh-arm": {
        "restart_container:monitoring-grafana": {
            "cmd": "docker restart monitoring-grafana",
            "desc": "Restart Grafana",
        },
        "restart_container:monitoring-prometheus": {
            "cmd": "docker restart monitoring-prometheus",
            "desc": "Restart Prometheus",
        },
        "logs:monitoring-grafana": {
            "cmd": "docker logs --tail 20 monitoring-grafana",
            "desc": "Grafana recent logs",
        },
        "logs:monitoring-prometheus": {
            "cmd": "docker logs --tail 20 monitoring-prometheus",
            "desc": "Prometheus recent logs",
        },
        "docker_ps": {
            "cmd": "docker ps --format 'table {{.Names}}\\t{{.Status}}\\t{{.Ports}}'",
            "desc": "List running containers",
        },
        "disk_usage": {"cmd": "df -h / | tail -1", "desc": "Disk usage"},
        "memory": {"cmd": "free -h", "desc": "Memory info"},
    },
    "gh-git": {
        "gitlab_status": {
            "cmd": "sudo gitlab-ctl status",
            "desc": "GitLab service status",
        },
        "disk_usage": {"cmd": "df -h / | tail -1", "desc": "Disk usage"},
        "memory": {"cmd": "free -h", "desc": "Memory info"},
    },
    "gh-media": {
        "docker_ps": {
            "cmd": "docker ps --format 'table {{.Names}}\\t{{.Status}}\\t{{.Ports}}'",
            "desc": "List running containers",
        },
        "disk_usage": {"cmd": "df -h / | tail -1", "desc": "Disk usage"},
        "memory": {"cmd": "free -h", "desc": "Memory info"},
        "restart_container:homeassistant": {
            "cmd": "docker restart homeassistant",
            "desc": "Restart Home Assistant",
        },
    },
    "gh-nvidia": {
        "gpu_info": {
            "cmd": "nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free,utilization.gpu --format=csv",
            "desc": "GPU status",
        },
        "docker_ps": {
            "cmd": "docker ps --format 'table {{.Names}}\\t{{.Status}}\\t{{.Ports}}'",
            "desc": "List running containers",
        },
        "disk_usage": {"cmd": "df -h / | tail -1", "desc": "Disk usage"},
        "memory": {"cmd": "free -h", "desc": "Memory info"},
    },
}


@router.get("/hosts")
async def list_hosts(user = Depends(get_authenticated_user)):
    """List all hosts with their available actions."""
    result = []
    for host, info in FLEET_HOSTS.items():
        result.append(
            {
                "name": host,
                "ip": info["ip"],
                "role": info.get("role", ""),
                "actions": list(ACTIONS.get(host, {}).keys()),
            }
        )
    return {"hosts": result}


@router.get("/actions/{host}")
async def list_actions(host: str, user = Depends(get_authenticated_user)):
    """List available actions for a host."""
    if host not in ACTIONS:
        raise HTTPException(404, f"Host {host} not found or no actions defined")
    return {
        "host": host,
        "actions": [{"id": k, "desc": v["desc"]} for k, v in ACTIONS[host].items()],
    }


@router.post("/execute/{host}/{action_id}")
async def execute_action(
    host: str, action_id: str, user = Depends(get_authenticated_user)
):
    """Execute a predefined action on a host."""
    if host not in ACTIONS or action_id not in ACTIONS[host]:
        raise HTTPException(404, "Host or action not found")

    action = ACTIONS[host][action_id]
    cmd = action["cmd"]

    # Determine if local or remote
    host_info = FLEET_HOSTS.get(host, {})
    target_ip = host_info.get("ts") or host_info.get("ip", "")
    is_local = target_ip in ("localhost", "100.92.162.32")

    try:
        if is_local:
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
        else:
            # SSH to remote host
            ssh_cmd = [
                "ssh",
                "-o",
                "ConnectTimeout=5",
                "-o",
                "StrictHostKeyChecking=no",
                f"ghively@{target_ip}",
                cmd,
            ]
            proc = await asyncio.create_subprocess_exec(
                *ssh_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)

        return {
            "success": proc.returncode == 0,
            "exit_code": proc.returncode,
            "stdout": stdout.decode()[:5000],
            "stderr": stderr.decode()[:2000],
            "command": cmd,
            "host": host,
            "action": action_id,
        }
    except asyncio.TimeoutError:
        return {"success": False, "error": "Command timed out (30s)", "command": cmd}
    except Exception as e:
        return {"success": False, "error": str(e), "command": cmd}
