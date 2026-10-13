"""Core process management."""

from __future__ import annotations

import os
import sys
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import psutil

from pyker.colors import Colors
from pyker.hooks import StartupHooks
from pyker.store import ProcessStore
from pyker.watcher import Watcher, is_pid_running


class ProcessManager:
    """Start/stop/list managed Python scripts."""

    # Back-compat aliases used by cli help formatting
    RESET = Colors.RESET
    BOLD = Colors.BOLD
    GREEN = Colors.GREEN
    RED = Colors.RED
    YELLOW = Colors.YELLOW
    CYAN = Colors.CYAN
    BLUE = Colors.BLUE

    def __init__(self, store: Optional[ProcessStore] = None):
        self.store = store or ProcessStore()
        default_root = (Path.home() / ".pyker").resolve()
        home = (
            Path.home()
            if self.store.root.resolve() == default_root
            else self.store.root.parent
        )
        self.hooks = StartupHooks(home=home)
        self.watcher = Watcher(self.store)
        self.processes = self.store.processes
        self.config = self.store.config
        self.state_file = self.store.state_file
        self.logs_dir = self.store.logs_dir
        self.config_file = self.store.config_file

    def _save_state(self) -> None:
        self.store.processes = self.processes
        self.store.save_state()

    def update_process_status(self, name: str) -> None:
        if name not in self.processes:
            return
        info = self.processes[name]
        pid = info.get("pid")
        if pid and is_pid_running(pid):
            try:
                process = psutil.Process(pid)
                info["status"] = "running"
                info["cpu_percent"] = process.cpu_percent()
                info["memory_mb"] = round(process.memory_info().rss / 1024 / 1024, 1)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                info["status"] = "stopped"
                info["pid"] = None
                info.setdefault("stop_time", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        else:
            info["status"] = "stopped"
            if pid:
                info["pid"] = None
                info.setdefault("stop_time", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def _rotate_log_if_needed(self, log_file_path: Path) -> None:
        rotation = self.config.get("log_rotation") or {}
        if not rotation.get("enabled", True):
            return
        log_file = Path(log_file_path)
        if not log_file.exists():
            return
        max_size = rotation.get("max_size_mb", 10) * 1024 * 1024
        if log_file.stat().st_size <= max_size:
            return
        max_files = rotation.get("max_files", 5)
        oldest = log_file.with_suffix(f".log.{max_files}")
        if oldest.exists():
            oldest.unlink()
        for i in range(max_files - 1, 0, -1):
            current = log_file.with_suffix(f".log.{i}")
            nxt = log_file.with_suffix(f".log.{i + 1}")
            if current.exists():
                current.rename(nxt)
        log_file.rename(log_file.with_suffix(".log.1"))
        log_file.touch()

    def _get_python_executable(self, venv_path: Optional[str] = None, quiet: bool = False) -> Optional[str]:
        if not venv_path:
            return sys.executable
        venv_path = os.path.abspath(os.path.expanduser(venv_path))
        if not os.path.exists(venv_path):
            if not quiet:
                print(f"{Colors.RED}[ERROR]{Colors.RESET} Virtual environment not found: {venv_path}")
            return None
        candidates = [
            os.path.join(venv_path, "bin", "python"),
            os.path.join(venv_path, "bin", "python3"),
            os.path.join(venv_path, "Scripts", "python.exe"),
            os.path.join(venv_path, "Scripts", "python3.exe"),
        ]
        for python_exe in candidates:
            if os.path.exists(python_exe) and os.access(python_exe, os.X_OK):
                if not quiet:
                    print(f"{Colors.BLUE}[INFO]{Colors.RESET} Using Python from venv: {python_exe}")
                return python_exe
        if not quiet:
            print(f"{Colors.RED}[ERROR]{Colors.RESET} No Python executable found in venv: {venv_path}")
        return None

    def start(
        self,
        name: str,
        script_path: str,
        auto_restart: bool = False,
        venv_path: Optional[str] = None,
        on_boot: bool = False,
        quiet: bool = False,
        ensure_watcher: bool = True,
    ) -> bool:
        script_path = os.path.abspath(script_path)
        if not os.path.exists(script_path):
            if not quiet:
                print(f"{Colors.RED}[ERROR]{Colors.RESET} File not found: {script_path}")
            return False
        if not script_path.endswith(".py"):
            if not quiet:
                print(f"{Colors.RED}[ERROR]{Colors.RESET} File must be a Python script: {script_path}")
            return False

        if name in self.processes:
            self.update_process_status(name)
            if self.processes[name].get("status") == "running":
                if not quiet:
                    print(f"{Colors.YELLOW}[WARNING]{Colors.RESET} Process '{name}' is already running")
                return False
            existing = self.processes[name]
            if not on_boot:
                on_boot = existing.get("on_boot", False)
            if not auto_restart:
                auto_restart = existing.get("auto_restart", False)
            if venv_path is None:
                venv_path = existing.get("venv_path")

        log_file = self.logs_dir / f"{name}.log"
        self._rotate_log_if_needed(log_file)
        python_exe = self._get_python_executable(venv_path, quiet=quiet)
        if not python_exe:
            return False

        try:
            log_handle = open(log_file, "a", encoding="utf-8")
            process = subprocess.Popen(
                [python_exe, "-u", script_path],
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                cwd=os.path.dirname(script_path) or ".",
                start_new_session=True,
            )
            self.processes[name] = {
                "pid": process.pid,
                "script_path": script_path,
                "venv_path": venv_path,
                "python_exe": python_exe,
                "status": "running",
                "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "log_file": str(log_file),
                "auto_restart": auto_restart,
                "on_boot": on_boot,
                "stopped_by_user": False,
                "cpu_percent": 0.0,
                "memory_mb": 0.0,
            }
            self._save_state()
            if not quiet:
                print(f"{Colors.GREEN}[SUCCESS]{Colors.RESET} Process '{name}' started (PID: {process.pid})")
                print(f"{Colors.BLUE}[INFO]{Colors.RESET} Logs: {log_file}")
                if on_boot and not self.hooks.is_installed():
                    print(
                        f"{Colors.BLUE}[INFO]{Colors.RESET} Marked for boot — "
                        f"run '{Colors.CYAN}pyker startup{Colors.RESET}' to install the OS hook"
                    )
            if auto_restart and ensure_watcher:
                self.watcher.ensure_running(quiet=quiet)
            return True
        except OSError as e:
            if not quiet:
                print(f"{Colors.RED}[ERROR]{Colors.RESET} Failed to start process: {e}")
            return False

    def stop(self, name: str, quiet: bool = False) -> bool:
        if name not in self.processes:
            if not quiet:
                print(f"{Colors.RED}[ERROR]{Colors.RESET} Process '{name}' not found")
            return False

        info = self.processes[name]
        # Mark intentional stop BEFORE killing so watcher won't race-restart
        info["stopped_by_user"] = True
        self._save_state()

        pid = info.get("pid")
        if not pid:
            if not quiet:
                print(f"{Colors.YELLOW}[WARNING]{Colors.RESET} Process '{name}' is already stopped")
            return True

        try:
            process = psutil.Process(pid)
            process.terminate()
            try:
                process.wait(timeout=2)
            except psutil.TimeoutExpired:
                process.kill()
                process.wait(timeout=2)
            info["status"] = "stopped"
            info["pid"] = None
            info["stop_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self._save_state()
            if not quiet:
                print(f"{Colors.GREEN}[SUCCESS]{Colors.RESET} Process '{name}' stopped")
            return True
        except psutil.NoSuchProcess:
            info["status"] = "stopped"
            info["pid"] = None
            info["stop_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self._save_state()
            if not quiet:
                print(f"{Colors.GREEN}[SUCCESS]{Colors.RESET} Process '{name}' was already terminated")
            return True
        except (psutil.AccessDenied, OSError) as e:
            if not quiet:
                print(f"{Colors.RED}[ERROR]{Colors.RESET} Failed to stop process: {e}")
            return False

    def restart(self, name: str) -> bool:
        if name not in self.processes:
            print(f"{Colors.RED}[ERROR]{Colors.RESET} Process '{name}' not found")
            return False
        info = self.processes[name]
        if info.get("pid"):
            print(f"{Colors.BLUE}[INFO]{Colors.RESET} Stopping process '{name}'...")
            self.stop(name)
        print(f"{Colors.BLUE}[INFO]{Colors.RESET} Starting process '{name}'...")
        return self.start(
            name,
            info["script_path"],
            info.get("auto_restart", False),
            info.get("venv_path"),
            info.get("on_boot", False),
        )

    def delete(self, name: str) -> bool:
        if name not in self.processes:
            print(f"{Colors.RED}[ERROR]{Colors.RESET} Process '{name}' not found")
            return False
        self.stop(name)
        del self.processes[name]
        self._save_state()
        print(f"{Colors.GREEN}[SUCCESS]{Colors.RESET} Process '{name}' deleted")
        return True

    def enable(self, name: str) -> bool:
        if name not in self.processes:
            print(f"{Colors.RED}[ERROR]{Colors.RESET} Process '{name}' not found")
            return False
        self.processes[name]["on_boot"] = True
        self._save_state()
        print(f"{Colors.GREEN}[SUCCESS]{Colors.RESET} Process '{name}' will start on boot")
        if not self.hooks.is_installed():
            print(
                f"{Colors.YELLOW}[HINT]{Colors.RESET} Run "
                f"'{Colors.CYAN}pyker startup{Colors.RESET}' to install the boot hook"
            )
        return True

    def disable(self, name: str) -> bool:
        if name not in self.processes:
            print(f"{Colors.RED}[ERROR]{Colors.RESET} Process '{name}' not found")
            return False
        self.processes[name]["on_boot"] = False
        self._save_state()
        print(f"{Colors.GREEN}[SUCCESS]{Colors.RESET} Process '{name}' will no longer start on boot")
        return True

    def resurrect(self) -> bool:
        boot = [n for n, i in self.processes.items() if i.get("on_boot")]
        if not boot:
            print(f"{Colors.YELLOW}[INFO]{Colors.RESET} No processes marked for boot start")
            print(
                f"{Colors.BLUE}[HINT]{Colors.RESET} Use "
                f"'{Colors.CYAN}pyker enable <name>{Colors.RESET}' or "
                f"'{Colors.CYAN}pyker start ... --on-boot{Colors.RESET}'"
            )
            return True

        print(f"{Colors.BLUE}[INFO]{Colors.RESET} Resurrecting {len(boot)} process(es)...")
        started = skipped = failed = 0
        for name in boot:
            self.update_process_status(name)
            info = self.processes[name]
            if info.get("status") == "running":
                print(f"{Colors.YELLOW}[SKIP]{Colors.RESET} '{name}' is already running")
                skipped += 1
                continue
            ok = self.start(
                name,
                info["script_path"],
                info.get("auto_restart", False),
                info.get("venv_path"),
                True,
            )
            if ok:
                started += 1
            else:
                failed += 1

        if any(i.get("auto_restart") for i in self.processes.values()):
            self.watcher.ensure_running()

        print(f"{Colors.GREEN}[DONE]{Colors.RESET} started={started}, skipped={skipped}, failed={failed}")
        return failed == 0

    def startup(self) -> bool:
        boot_count = sum(1 for p in self.processes.values() if p.get("on_boot"))
        return self.hooks.install(boot_process_count=boot_count)

    def unstartup(self) -> bool:
        return self.hooks.uninstall()

    def list_processes(self) -> None:
        from pyker.display import print_process_list

        if not self.processes:
            print(f"{Colors.YELLOW}No processes{Colors.RESET}")
            return
        for name in self.processes:
            self.update_process_status(name)
        self._save_state()
        print_process_list(self.processes)

    def logs(self, name: str, lines: int = 50, follow: bool = False) -> None:
        if name not in self.processes:
            print(f"{Colors.RED}[ERROR]{Colors.RESET} Process '{name}' not found")
            return
        log_file = Path(self.processes[name].get("log_file", ""))
        if not log_file.exists():
            print(f"{Colors.YELLOW}[WARNING]{Colors.RESET} No logs found for process '{name}'")
            return
        if follow:
            print(f"{Colors.CYAN}[LOGS]{Colors.RESET} Following logs for process '{name}' (Ctrl+C to exit):")
            print("─" * 80)
            try:
                result = subprocess.run(
                    ["tail", "-n", str(lines), str(log_file)],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if result.stdout:
                    print(result.stdout, end="")
            except OSError:
                pass
            try:
                subprocess.run(["tail", "-f", str(log_file)], check=False)
            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}[INFO]{Colors.RESET} Stopped")
        else:
            print(f"{Colors.CYAN}[LOGS]{Colors.RESET} Last {lines} lines from process '{name}':")
            print("─" * 80)
            try:
                result = subprocess.run(
                    ["tail", "-n", str(lines), str(log_file)],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                print(result.stdout if result.stdout else "No logs available")
            except OSError as e:
                print(f"{Colors.RED}[ERROR]{Colors.RESET} Failed to read logs: {e}")

    def info(self, name: Optional[str] = None) -> None:
        if name:
            if name not in self.processes:
                print(f"{Colors.RED}[ERROR]{Colors.RESET} Process '{name}' not found")
                return
            self.update_process_status(name)
            info = self.processes[name]
            status = info["status"]
            if status == "running":
                status_display = f"{Colors.GREEN}✓ Running{Colors.RESET}"
            elif status == "stopped":
                status_display = f"{Colors.RED}✗ Stopped{Colors.RESET}"
            else:
                status_display = f"{Colors.YELLOW}⚠ Error{Colors.RESET}"
            print(f"\n{Colors.BOLD}{Colors.CYAN}Process Information: {name}{Colors.RESET}")
            print(f"{Colors.BOLD}Status:{Colors.RESET} {status_display}")
            print(f"{Colors.BOLD}PID:{Colors.RESET} {info.get('pid', '-')}")
            print(f"{Colors.BOLD}Script:{Colors.RESET} {info.get('script_path', '-')}")
            print(f"{Colors.BOLD}CPU Usage:{Colors.RESET} {info.get('cpu_percent', 0.0):.1f}%")
            print(f"{Colors.BOLD}Memory:{Colors.RESET} {info.get('memory_mb', 0.0):.1f} MB")
            if info.get("start_time"):
                print(f"{Colors.BOLD}Started:{Colors.RESET} {info['start_time']}")
            if info.get("stop_time"):
                print(f"{Colors.BOLD}Stopped:{Colors.RESET} {info['stop_time']}")
            if info.get("log_file"):
                print(f"{Colors.BOLD}Log file:{Colors.RESET} {info['log_file']}")
            print(f"{Colors.BOLD}Auto restart:{Colors.RESET} {'Yes' if info.get('auto_restart') else 'No'}")
            print(f"{Colors.BOLD}On boot:{Colors.RESET} {'Yes' if info.get('on_boot') else 'No'}")
            if info.get("venv_path"):
                print(f"{Colors.BOLD}Virtual env:{Colors.RESET} {info['venv_path']}")
                if info.get("python_exe"):
                    print(f"{Colors.BOLD}Python executable:{Colors.RESET} {info['python_exe']}")
            else:
                print(f"{Colors.BOLD}Virtual env:{Colors.RESET} System Python")
            return

        for n in self.processes:
            self.update_process_status(n)
        running = sum(1 for p in self.processes.values() if p["status"] == "running")
        stopped = sum(1 for p in self.processes.values() if p["status"] == "stopped")
        print(f"\n{Colors.BOLD}{Colors.CYAN}Pyker System Information{Colors.RESET}")
        print(f"{Colors.BOLD}Total processes:{Colors.RESET} {Colors.BLUE}{len(self.processes)}{Colors.RESET}")
        print(f"{Colors.BOLD}Running:{Colors.RESET} {Colors.GREEN}{running}{Colors.RESET}")
        print(f"{Colors.BOLD}Stopped:{Colors.RESET} {Colors.RED}{stopped}{Colors.RESET}")
        print(f"{Colors.BOLD}State file:{Colors.RESET} {self.state_file}")
        print(f"{Colors.BOLD}Logs directory:{Colors.RESET} {self.logs_dir}")
        print(f"{Colors.BOLD}Config file:{Colors.RESET} {self.config_file}")
        on_boot_count = sum(1 for p in self.processes.values() if p.get("on_boot"))
        print(f"{Colors.BOLD}On boot:{Colors.RESET} {on_boot_count} process(es)")
        print(f"{Colors.BOLD}Startup hook:{Colors.RESET} {'enabled' if self.hooks.is_installed() else 'not installed'}")
        print(
            f"{Colors.BOLD}Watcher:{Colors.RESET} "
            f"{'running' if self.watcher.is_running() else 'stopped'}"
        )

    def uninstall(self) -> None:
        print(f"\n{Colors.BOLD}{Colors.RED}⚠ Pyker Uninstallation{Colors.RESET}")
        print(f"{Colors.YELLOW}This will:{Colors.RESET}")
        print("  • Stop all running processes")
        print("  • Stop auto-restart watcher")
        print("  • Remove boot startup hook (if installed)")
        print("  • Remove Pyker executable")
        print("  • Remove completion scripts")
        print("  • Keep logs and config (optional cleanup)")

        running = [n for n, i in self.processes.items() if i.get("status") == "running"]
        if running:
            print(f"\n{Colors.RED}Running processes that will be stopped:{Colors.RESET}")
            for name in running:
                print(f"  • {name}")

        print(f"\n{Colors.BOLD}Do you want to continue? [y/N]:{Colors.RESET} ", end="")
        try:
            response = input().strip().lower()
        except (KeyboardInterrupt, EOFError):
            print(f"\n{Colors.YELLOW}[INFO]{Colors.RESET} Uninstallation cancelled")
            return
        if response not in ("y", "yes"):
            print(f"{Colors.YELLOW}[INFO]{Colors.RESET} Uninstallation cancelled")
            return

        print(f"\n{Colors.YELLOW}Stopping all processes...{Colors.RESET}")
        stopped = 0
        for name, info in list(self.processes.items()):
            if info.get("status") == "running" or info.get("pid"):
                if self.stop(name):
                    stopped += 1
        if stopped:
            print(f"{Colors.GREEN}✓ Stopped {stopped} processes{Colors.RESET}")

        self.watcher.stop(quiet=True)
        if self.hooks.is_installed():
            print(f"{Colors.YELLOW}Removing startup hook...{Colors.RESET}")
            self.unstartup()

        print(f"\n{Colors.BOLD}Remove logs and configuration? [y/N]:{Colors.RESET} ", end="")
        try:
            cleanup = input().strip().lower()
        except (KeyboardInterrupt, EOFError):
            cleanup = "n"
        self._remove_pyker_files(cleanup in ("y", "yes"))
        print(f"\n{Colors.GREEN}✓ Pyker has been uninstalled successfully{Colors.RESET}")
        print(f"{Colors.BLUE}Thank you for using Pyker!{Colors.RESET}")

    def _remove_pyker_files(self, remove_data: bool) -> None:
        for location in (
            Path.home() / ".local" / "bin" / "pyker",
            Path("/usr/local/bin/pyker"),
            Path("/usr/bin/pyker"),
        ):
            if location.exists():
                try:
                    location.unlink()
                    print(f"{Colors.GREEN}✓ Removed {location}{Colors.RESET}")
                except OSError as e:
                    print(f"{Colors.RED}✗ Failed to remove {location}: {e}{Colors.RESET}")

        for location in (
            Path.home() / ".local" / "share" / "bash-completion" / "completions" / "pyker",
            Path.home() / ".oh-my-zsh" / "completions" / "_pyker",
            Path.home() / ".local" / "share" / "zsh" / "site-functions" / "_pyker",
        ):
            if location.exists():
                try:
                    location.unlink()
                    print(f"{Colors.GREEN}✓ Removed completion {location.name}{Colors.RESET}")
                except OSError as e:
                    print(f"{Colors.RED}✗ Failed to remove completion: {e}{Colors.RESET}")

        if remove_data:
            pyker_dir = Path.home() / ".pyker"
            if pyker_dir.exists():
                try:
                    shutil.rmtree(pyker_dir)
                    print(f"{Colors.GREEN}✓ Removed data directory ~/.pyker{Colors.RESET}")
                except OSError as e:
                    print(f"{Colors.RED}✗ Failed to remove data directory: {e}{Colors.RESET}")
        else:
            print(f"{Colors.BLUE}ℹ Data directory ~/.pyker preserved{Colors.RESET}")
