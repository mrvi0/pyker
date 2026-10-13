"""OS boot/login hooks (systemd user, LaunchAgent, Windows Startup)."""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

from pyker.colors import Colors


def find_pyker_executable() -> Optional[str]:
    """Resolve absolute path / command used to invoke pyker."""
    candidates = []

    which = shutil.which("pyker")
    if which:
        candidates.append(Path(which).resolve())

    argv0 = Path(sys.argv[0]).expanduser()
    if not argv0.is_absolute():
        argv0 = Path.cwd() / argv0
    if argv0.exists():
        candidates.append(argv0.resolve())

    home_bin = Path.home() / ".local" / "bin" / "pyker"
    if home_bin.exists():
        candidates.append(home_bin.resolve())

    for path in candidates:
        if path.exists() and os.access(path, os.X_OK):
            return str(path)

    # python -m pyker
    return f"{sys.executable} -m pyker"


def startup_unit_paths(home: Optional[Path] = None) -> dict:
    home = home or Path.home()
    return {
        "systemd_unit": home / ".config" / "systemd" / "user" / "pyker-resurrect.service",
        "launch_agent": home / "Library" / "LaunchAgents" / "com.pyker.resurrect.plist",
        "windows_cmd": (
            home
            / "AppData"
            / "Roaming"
            / "Microsoft"
            / "Windows"
            / "Start Menu"
            / "Programs"
            / "Startup"
            / "pyker-resurrect.cmd"
        ),
    }


def startup_is_installed(home: Optional[Path] = None) -> bool:
    paths = startup_unit_paths(home)
    system = platform.system()
    if system == "Linux":
        return paths["systemd_unit"].exists()
    if system == "Darwin":
        return paths["launch_agent"].exists()
    if system == "Windows":
        return paths["windows_cmd"].exists()
    return False


class StartupHooks:
    """Install/remove OS hooks that run `pyker resurrect` on login."""

    def __init__(self, home: Optional[Path] = None):
        self.home = Path(home) if home else Path.home()
        self.paths = startup_unit_paths(self.home)

    def is_installed(self) -> bool:
        return startup_is_installed(self.home)

    def install(self, boot_process_count: int = 0) -> bool:
        system = platform.system()
        if system == "Linux":
            return self._install_linux(boot_process_count)
        if system == "Darwin":
            return self._install_macos()
        if system == "Windows":
            return self._install_windows()
        print(f"{Colors.RED}[ERROR]{Colors.RESET} Unsupported platform: {system}")
        return False

    def uninstall(self) -> bool:
        system = platform.system()
        if system == "Linux":
            return self._uninstall_linux()
        if system == "Darwin":
            return self._uninstall_macos()
        if system == "Windows":
            return self._uninstall_windows()
        print(f"{Colors.RED}[ERROR]{Colors.RESET} Unsupported platform: {system}")
        return False

    def _install_linux(self, boot_process_count: int) -> bool:
        if not shutil.which("systemctl"):
            print(f"{Colors.RED}[ERROR]{Colors.RESET} systemctl not found; cannot install startup hook")
            return False

        pyker_exe = find_pyker_executable()
        if not pyker_exe:
            print(f"{Colors.RED}[ERROR]{Colors.RESET} Could not locate pyker executable")
            return False

        unit_path = self.paths["systemd_unit"]
        unit_path.parent.mkdir(parents=True, exist_ok=True)
        unit_path.write_text(
            f"""[Unit]
Description=Pyker resurrect processes on login/boot
After=default.target

[Service]
Type=oneshot
ExecStart={pyker_exe} resurrect
RemainAfterExit=yes

[Install]
WantedBy=default.target
""",
            encoding="utf-8",
        )

        try:
            subprocess.run(["systemctl", "--user", "daemon-reload"], check=True, capture_output=True)
            subprocess.run(
                ["systemctl", "--user", "enable", "pyker-resurrect.service"],
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as e:
            err = (e.stderr or b"").decode().strip() or str(e)
            print(f"{Colors.RED}[ERROR]{Colors.RESET} Failed to enable systemd unit: {err}")
            return False

        print(f"{Colors.GREEN}[SUCCESS]{Colors.RESET} Installed startup hook: {unit_path}")
        print(f"{Colors.BLUE}[INFO]{Colors.RESET} Processes with on_boot will start on login")
        print(
            f"{Colors.YELLOW}[HINT]{Colors.RESET} For start at boot without login, run: "
            f"{Colors.CYAN}loginctl enable-linger $USER{Colors.RESET}"
        )
        if boot_process_count == 0:
            print(
                f"{Colors.YELLOW}[HINT]{Colors.RESET} No processes marked yet — "
                f"use '{Colors.CYAN}pyker enable <name>{Colors.RESET}' or "
                f"'{Colors.CYAN}--on-boot{Colors.RESET}'"
            )
        return True

    def _uninstall_linux(self) -> bool:
        unit_path = self.paths["systemd_unit"]
        if shutil.which("systemctl"):
            subprocess.run(
                ["systemctl", "--user", "disable", "--now", "pyker-resurrect.service"],
                capture_output=True,
            )
            subprocess.run(["systemctl", "--user", "daemon-reload"], capture_output=True)

        if unit_path.exists():
            unit_path.unlink()
            print(f"{Colors.GREEN}[SUCCESS]{Colors.RESET} Removed startup hook: {unit_path}")
        else:
            print(f"{Colors.YELLOW}[INFO]{Colors.RESET} Startup hook was not installed")
        return True

    def _install_macos(self) -> bool:
        pyker_exe = find_pyker_executable()
        if not pyker_exe:
            print(f"{Colors.RED}[ERROR]{Colors.RESET} Could not locate pyker executable")
            return False

        plist_path = self.paths["launch_agent"]
        plist_path.parent.mkdir(parents=True, exist_ok=True)

        if " " in pyker_exe:
            parts = pyker_exe.split()
            program_args = "".join(f"    <string>{p}</string>\n" for p in parts)
            program_args += "    <string>resurrect</string>\n"
        else:
            program_args = f"    <string>{pyker_exe}</string>\n    <string>resurrect</string>\n"

        log_path = self.home / ".pyker" / "logs" / "startup.log"
        plist_path.write_text(
            f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.pyker.resurrect</string>
  <key>ProgramArguments</key>
  <array>
{program_args}  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>StandardOutPath</key>
  <string>{log_path}</string>
  <key>StandardErrorPath</key>
  <string>{log_path}</string>
</dict>
</plist>
""",
            encoding="utf-8",
        )

        subprocess.run(["launchctl", "unload", str(plist_path)], capture_output=True)
        result = subprocess.run(["launchctl", "load", str(plist_path)], capture_output=True)
        if result.returncode != 0:
            err = (result.stderr or b"").decode().strip()
            print(f"{Colors.YELLOW}[WARNING]{Colors.RESET} launchctl load: {err or 'non-zero exit'}")

        print(f"{Colors.GREEN}[SUCCESS]{Colors.RESET} Installed startup hook: {plist_path}")
        print(f"{Colors.BLUE}[INFO]{Colors.RESET} Processes with on_boot will start at login")
        return True

    def _uninstall_macos(self) -> bool:
        plist_path = self.paths["launch_agent"]
        if plist_path.exists():
            subprocess.run(["launchctl", "unload", str(plist_path)], capture_output=True)
            plist_path.unlink()
            print(f"{Colors.GREEN}[SUCCESS]{Colors.RESET} Removed startup hook: {plist_path}")
        else:
            print(f"{Colors.YELLOW}[INFO]{Colors.RESET} Startup hook was not installed")
        return True

    def _install_windows(self) -> bool:
        pyker_exe = find_pyker_executable()
        if not pyker_exe:
            print(f"{Colors.RED}[ERROR]{Colors.RESET} Could not locate pyker executable")
            return False

        cmd_path = self.paths["windows_cmd"]
        cmd_path.parent.mkdir(parents=True, exist_ok=True)
        cmd_path.write_text(f"@echo off\r\n{pyker_exe} resurrect\r\n", encoding="utf-8")
        print(f"{Colors.GREEN}[SUCCESS]{Colors.RESET} Installed startup hook: {cmd_path}")
        print(f"{Colors.BLUE}[INFO]{Colors.RESET} Processes with on_boot will start at Windows login")
        return True

    def _uninstall_windows(self) -> bool:
        cmd_path = self.paths["windows_cmd"]
        if cmd_path.exists():
            cmd_path.unlink()
            print(f"{Colors.GREEN}[SUCCESS]{Colors.RESET} Removed startup hook: {cmd_path}")
        else:
            print(f"{Colors.YELLOW}[INFO]{Colors.RESET} Startup hook was not installed")
        return True
