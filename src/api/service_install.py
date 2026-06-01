"""Install Beak Flow as a user-level OS service (systemd / launchd / Task Scheduler)."""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

from src.api.server_config import load_config, resolve_log_path, save_config
from src.api.static_paths import package_static_dir, resolve_static_dir

SERVICE_NAME_LINUX = "beak-flow"
SERVICE_LABEL_MACOS = "com.beak.flow"
TASK_NAME_WINDOWS = "BeakFlow"


def beak_flow_executable() -> str:
    exe = shutil.which("beak-flow")
    if exe:
        return exe
    raise RuntimeError(
        "beak-flow not found on PATH. Install with `pip install -e .` and restart your shell."
    )


def warn_if_ui_missing() -> None:
    if resolve_static_dir() is None:
        print(
            "Warning: UI not built. Run `beak-flow build-ui` before using the web interface.",
            file=sys.stderr,
        )


def render_systemd_unit(
    exec_path: str,
    host: str,
    port: int,
    log_path: Path,
) -> str:
    return f"""[Unit]
Description=Beak Flow planning gateway
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart={exec_path} run --host {host} --port {port}
Restart=on-failure
RestartSec=5
StandardOutput=append:{log_path}
StandardError=append:{log_path}

[Install]
WantedBy=default.target
"""


def render_launchd_plist(
    exec_path: str,
    host: str,
    port: int,
    log_path: Path,
) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>{SERVICE_LABEL_MACOS}</string>
  <key>ProgramArguments</key>
  <array>
    <string>{exec_path}</string>
    <string>run</string>
    <string>--host</string>
    <string>{host}</string>
    <string>--port</string>
    <string>{port}</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>StandardOutPath</key>
  <string>{log_path}</string>
  <key>StandardErrorPath</key>
  <string>{log_path}</string>
</dict>
</plist>
"""


def _run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=check, capture_output=True, text=True)


def install_service(host: Optional[str] = None, port: Optional[int] = None) -> None:
    warn_if_ui_missing()
    cfg = load_config()
    h = host or str(cfg["host"])
    p = port if port is not None else int(cfg["port"])
    log_path = resolve_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    save_config(h, p, str(log_path))

    exe = beak_flow_executable()
    system = platform.system()

    if system == "Linux":
        _install_linux(exe, h, p, log_path)
    elif system == "Darwin":
        _install_macos(exe, h, p, log_path)
    elif system == "Windows":
        _install_windows(exe, h, p)
    else:
        raise RuntimeError(f"Unsupported platform for service install: {system}")

    print(f"Beak Flow service installed. Open http://{h}:{p}/")
    if system == "Linux":
        print("Tip: run `loginctl enable-linger $USER` to keep the service running after logout.")


def _install_linux(exe: str, host: str, port: int, log_path: Path) -> None:
    unit_dir = Path.home() / ".config" / "systemd" / "user"
    unit_dir.mkdir(parents=True, exist_ok=True)
    unit_path = unit_dir / f"{SERVICE_NAME_LINUX}.service"
    unit_path.write_text(render_systemd_unit(exe, host, port, log_path), encoding="utf-8")
    _run(["systemctl", "--user", "daemon-reload"])
    _run(["systemctl", "--user", "enable", f"{SERVICE_NAME_LINUX}.service"])
    _run(["systemctl", "--user", "start", f"{SERVICE_NAME_LINUX}.service"])


def _install_macos(exe: str, host: str, port: int, log_path: Path) -> None:
    agents = Path.home() / "Library" / "LaunchAgents"
    agents.mkdir(parents=True, exist_ok=True)
    plist_path = agents / f"{SERVICE_LABEL_MACOS}.plist"
    plist_path.write_text(render_launchd_plist(exe, host, port, log_path), encoding="utf-8")
    uid = os.getuid()
    _run(["launchctl", "bootout", f"gui/{uid}", str(plist_path)], check=False)
    _run(["launchctl", "bootstrap", f"gui/{uid}", str(plist_path)])


def _install_windows(exe: str, host: str, port: int) -> None:
    tr = f'"{exe}" run --host {host} --port {port}'
    _run(
        [
            "schtasks",
            "/Create",
            "/TN",
            TASK_NAME_WINDOWS,
            "/TR",
            tr,
            "/SC",
            "ONLOGON",
            "/RL",
            "LIMITED",
            "/F",
        ]
    )


def uninstall_service() -> None:
    system = platform.system()
    if system == "Linux":
        _run(["systemctl", "--user", "stop", f"{SERVICE_NAME_LINUX}.service"], check=False)
        _run(["systemctl", "--user", "disable", f"{SERVICE_NAME_LINUX}.service"], check=False)
        unit_path = Path.home() / ".config" / "systemd" / "user" / f"{SERVICE_NAME_LINUX}.service"
        if unit_path.is_file():
            unit_path.unlink()
        _run(["systemctl", "--user", "daemon-reload"], check=False)
    elif system == "Darwin":
        plist_path = Path.home() / "Library" / "LaunchAgents" / f"{SERVICE_LABEL_MACOS}.plist"
        uid = os.getuid()
        _run(["launchctl", "bootout", f"gui/{uid}", str(plist_path)], check=False)
        if plist_path.is_file():
            plist_path.unlink()
    elif system == "Windows":
        _run(["schtasks", "/Delete", "/TN", TASK_NAME_WINDOWS, "/F"], check=False)
    else:
        raise RuntimeError(f"Unsupported platform: {system}")
    print("Beak Flow service removed.")


def service_status() -> str:
    system = platform.system()
    if system == "Linux":
        r = _run(["systemctl", "--user", "is-active", f"{SERVICE_NAME_LINUX}.service"], check=False)
        active = r.stdout.strip() if r.returncode == 0 else r.stdout.strip() or "inactive"
        enabled_r = _run(
            ["systemctl", "--user", "is-enabled", f"{SERVICE_NAME_LINUX}.service"],
            check=False,
        )
        enabled = enabled_r.stdout.strip() if enabled_r.returncode == 0 else "disabled"
        unit = Path.home() / ".config" / "systemd" / "user" / f"{SERVICE_NAME_LINUX}.service"
        installed = unit.is_file()
        return f"installed={installed} active={active} enabled={enabled}"
    if system == "Darwin":
        plist_path = Path.home() / "Library" / "LaunchAgents" / f"{SERVICE_LABEL_MACOS}.plist"
        installed = plist_path.is_file()
        r = _run(["launchctl", "list"], check=False)
        running = SERVICE_LABEL_MACOS in (r.stdout or "")
        return f"installed={installed} running={running}"
    if system == "Windows":
        r = _run(["schtasks", "/Query", "/TN", TASK_NAME_WINDOWS], check=False)
        exists = r.returncode == 0
        return f"installed={exists}"
    return f"unsupported platform: {system}"


def static_index_hint() -> str:
    return str(package_static_dir() / "index.html")
