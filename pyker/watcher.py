"""Background watcher that restarts processes with auto_restart=True."""

from __future__ import annotations

import os
import sys
import time
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import psutil

from pyker.colors import Colors
from pyker.hooks import find_pyker_executable

if TYPE_CHECKING:
    from pyker.manager import ProcessManager
    from pyker.store import ProcessStore


def is_pid_running(pid: Optional[int]) -> bool:
    if not pid:
        return False
    try:
        proc = psutil.Process(pid)
        return proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False


class Watcher:
    """Manage the auto-restart watcher daemon."""

    def __init__(self, store: "ProcessStore"):
        self.store = store

    @property
    def pid_file(self) -> Path:
        return self.store.watcher_pid_file

    def get_pid(self) -> Optional[int]:
        if not self.pid_file.exists():
            return None
        try:
            pid = int(self.pid_file.read_text(encoding="utf-8").strip())
            return pid
        except (ValueError, OSError):
            return None

    def is_running(self) -> bool:
        return is_pid_running(self.get_pid())

    def write_pid(self, pid: int) -> None:
        self.pid_file.write_text(str(pid), encoding="utf-8")

    def clear_pid(self) -> None:
        if self.pid_file.exists():
            try:
                self.pid_file.unlink()
            except OSError:
                pass

    def ensure_running(self, quiet: bool = False) -> bool:
        """Start watcher daemon if not already running."""
        if self.is_running():
            return True

        pyker_exe = find_pyker_executable()
        if not pyker_exe:
            if not quiet:
                print(f"{Colors.RED}[ERROR]{Colors.RESET} Cannot start watcher: pyker not found")
            return False

        log_file = self.store.logs_dir / "watcher.log"
        try:
            log_handle = open(log_file, "a", encoding="utf-8")
        except OSError as e:
            if not quiet:
                print(f"{Colors.RED}[ERROR]{Colors.RESET} Cannot open watcher log: {e}")
            return False

        cmd = pyker_exe.split() + ["watch"]

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                start_new_session=True,
                cwd=str(self.store.root),
            )
        except OSError as e:
            log_handle.close()
            if not quiet:
                print(f"{Colors.RED}[ERROR]{Colors.RESET} Failed to start watcher: {e}")
            return False

        self.write_pid(proc.pid)
        # Give it a moment; don't close log_handle (child owns it via dup)
        time.sleep(0.2)
        if not quiet:
            print(f"{Colors.BLUE}[INFO]{Colors.RESET} Auto-restart watcher started (PID: {proc.pid})")
        return True

    def stop(self, quiet: bool = False) -> bool:
        pid = self.get_pid()
        if not pid or not is_pid_running(pid):
            self.clear_pid()
            if not quiet:
                print(f"{Colors.YELLOW}[INFO]{Colors.RESET} Watcher is not running")
            return True
        try:
            proc = psutil.Process(pid)
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except psutil.TimeoutExpired:
                proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        self.clear_pid()
        if not quiet:
            print(f"{Colors.GREEN}[SUCCESS]{Colors.RESET} Watcher stopped")
        return True

    def run_forever(self, manager: "ProcessManager") -> None:
        """Blocking watch loop (used by `pyker watch`)."""
        self.write_pid(os.getpid())
        interval = float(self.store.config.get("watcher_interval", 3))
        print(f"{Colors.BLUE}[WATCHER]{Colors.RESET} Running (interval={interval}s, pid={os.getpid()})")

        try:
            while True:
                self._tick(manager)
                time.sleep(interval)
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}[WATCHER]{Colors.RESET} Stopped")
        finally:
            if self.get_pid() == os.getpid():
                self.clear_pid()

    def _tick(self, manager: "ProcessManager") -> None:
        self.store.reload_state()
        manager.processes = self.store.processes

        for name, info in list(self.store.processes.items()):
            if not info.get("auto_restart"):
                continue
            if info.get("stopped_by_user"):
                continue

            manager.update_process_status(name)
            info = self.store.processes.get(name, {})
            if info.get("status") == "running":
                continue

            print(f"{Colors.YELLOW}[WATCHER]{Colors.RESET} Restarting '{name}'...")
            ok = manager.start(
                name,
                info.get("script_path", ""),
                auto_restart=True,
                venv_path=info.get("venv_path"),
                on_boot=info.get("on_boot", False),
                quiet=True,
                ensure_watcher=False,
            )
            if ok:
                print(f"{Colors.GREEN}[WATCHER]{Colors.RESET} '{name}' restarted")
            else:
                print(f"{Colors.RED}[WATCHER]{Colors.RESET} Failed to restart '{name}'")
