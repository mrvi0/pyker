#!/usr/bin/env python3
"""
Pyker - Simple Python Process Manager
A lightweight alternative to PM2 for Python scripts
"""

import os
import sys
import json
import shutil
import psutil
import argparse
import platform
import subprocess
from pathlib import Path
from datetime import datetime

class Pyker:
    # ANSI color constants
    RESET = '\033[0m'
    BOLD = '\033[1m'
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    BLUE = '\033[94m'
    
    def __init__(self):
        self.state_file = Path.home() / ".pyker" / "processes.json"
        self.logs_dir = Path.home() / ".pyker" / "logs"
        self.config_file = Path.home() / ".pyker" / "config.json"
        self._ensure_dirs()
        self.config = self._load_config()
        self.processes = self._load_state()
    
    def _ensure_dirs(self):
        """Create necessary directories"""
        self.state_file.parent.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
    
    def _load_state(self):
        """Load processes state from JSON file"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_state(self):
        """Save processes state to JSON file"""
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(self.processes, f, indent=2, ensure_ascii=False)
    
    def _load_config(self):
        """Load configuration from JSON file"""
        default_config = {
            "log_rotation": {
                "enabled": True,
                "max_size_mb": 10,
                "max_files": 5
            },
            "process_check_interval": 5,
            "auto_cleanup_stopped": False
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # Merge with defaults to ensure all keys exist
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
            except:
                pass
        
        # Create default config file
        self._save_config(default_config)
        return default_config
    
    def _save_config(self, config):
        """Save configuration to JSON file"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    def _update_process_status(self, name: str):
        """Update process status"""
        if name not in self.processes:
            return
        
        process_info = self.processes[name]
        pid = process_info.get('pid')
        
        if pid:
            try:
                process = psutil.Process(pid)
                if process.is_running():
                    process_info['status'] = 'running'
                    process_info['cpu_percent'] = process.cpu_percent()
                    process_info['memory_mb'] = round(process.memory_info().rss / 1024 / 1024, 1)
                else:
                    process_info['status'] = 'stopped'
                    process_info['pid'] = None
                    if 'stop_time' not in process_info:
                        process_info['stop_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            except psutil.NoSuchProcess:
                process_info['status'] = 'stopped'
                process_info['pid'] = None
                if 'stop_time' not in process_info:
                    process_info['stop_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        else:
            process_info['status'] = 'stopped'
    
    def _rotate_log_if_needed(self, log_file_path):
        """Rotate log file if it exceeds maximum size"""
        if not self.config['log_rotation']['enabled']:
            return
        
        log_file = Path(log_file_path)
        if not log_file.exists():
            return
        
        max_size_bytes = self.config['log_rotation']['max_size_mb'] * 1024 * 1024
        if log_file.stat().st_size <= max_size_bytes:
            return
        
        # Rotate logs
        max_files = self.config['log_rotation']['max_files']
        
        # Remove oldest log if max files reached
        oldest_log = log_file.with_suffix(f'.log.{max_files}')
        if oldest_log.exists():
            oldest_log.unlink()
        
        # Shift existing log files
        for i in range(max_files - 1, 0, -1):
            current_log = log_file.with_suffix(f'.log.{i}')
            next_log = log_file.with_suffix(f'.log.{i + 1}')
            if current_log.exists():
                current_log.rename(next_log)
        
        # Move current log to .1
        first_rotated = log_file.with_suffix('.log.1')
        log_file.rename(first_rotated)
        
        # Create new empty log file
        log_file.touch()
    
    def start(self, name: str, script_path: str, auto_restart: bool = False, venv_path: str = None, on_boot: bool = False):
        """Start a process"""
        script_path = os.path.abspath(script_path)
        
        if not os.path.exists(script_path):
            print(f"{self.RED}[ERROR]{self.RESET} File not found: {script_path}")
            return False
        
        if not script_path.endswith('.py'):
            print(f"{self.RED}[ERROR]{self.RESET} File must be a Python script: {script_path}")
            return False
        
        # Check if process with this name is already running
        if name in self.processes:
            self._update_process_status(name)
            if self.processes[name]['status'] == 'running':
                print(f"{self.YELLOW}[WARNING]{self.RESET} Process '{name}' is already running")
                return False
            # Preserve on_boot unless explicitly enabled this call
            if not on_boot:
                on_boot = self.processes[name].get('on_boot', False)
        
        # Create log file
        log_file = self.logs_dir / f"{name}.log"
        
        # Rotate log if needed
        self._rotate_log_if_needed(log_file)
        
        # Determine Python executable (venv or system)
        python_exe = self._get_python_executable(venv_path)
        if not python_exe:
            return False
        
        # Start process
        try:
            # Open log file for writing
            log_handle = open(log_file, 'a', encoding='utf-8')
            
            process = subprocess.Popen(
                [python_exe, '-u', script_path],
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                cwd=os.path.dirname(script_path) or '.'
            )
            
            # Save process info
            self.processes[name] = {
                'pid': process.pid,
                'script_path': script_path,
                'venv_path': venv_path,
                'python_exe': python_exe,
                'status': 'running',
                'start_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'log_file': str(log_file),
                'auto_restart': auto_restart,
                'on_boot': on_boot,
                'cpu_percent': 0.0,
                'memory_mb': 0.0
            }
            
            self._save_state()
            print(f"{self.GREEN}[SUCCESS]{self.RESET} Process '{name}' started (PID: {process.pid})")
            print(f"{self.BLUE}[INFO]{self.RESET} Logs: {log_file}")
            if on_boot and not self._startup_is_installed():
                print(
                    f"{self.BLUE}[INFO]{self.RESET} Marked for boot — "
                    f"run '{self.CYAN}pyker startup{self.RESET}' to install the OS hook"
                )
            return True
            
        except Exception as e:
            print(f"{self.RED}[ERROR]{self.RESET} Failed to start process: {e}")
            return False
    
    def stop(self, name: str):
        """Stop a process"""
        if name not in self.processes:
            print(f"{self.RED}[ERROR]{self.RESET} Process '{name}' not found")
            return False
        
        process_info = self.processes[name]
        pid = process_info.get('pid')
        
        if not pid:
            print(f"{self.YELLOW}[WARNING]{self.RESET} Process '{name}' is already stopped")
            return True
        
        try:
            process = psutil.Process(pid)
            process.terminate()
            
            # Wait for graceful shutdown
            try:
                process.wait(timeout=2)
            except psutil.TimeoutExpired:
                process.kill()
                process.wait(timeout=2)
            
            process_info['status'] = 'stopped'
            process_info['pid'] = None
            process_info['stop_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self._save_state()
            
            print(f"{self.GREEN}[SUCCESS]{self.RESET} Process '{name}' stopped")
            return True
            
        except psutil.NoSuchProcess:
            process_info['status'] = 'stopped'
            process_info['pid'] = None
            process_info['stop_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self._save_state()
            print(f"{self.GREEN}[SUCCESS]{self.RESET} Process '{name}' was already terminated")
            return True
        except Exception as e:
            print(f"{self.RED}[ERROR]{self.RESET} Failed to stop process: {e}")
            return False
    
    def restart(self, name: str):
        """Restart a process"""
        if name not in self.processes:
            print(f"{self.RED}[ERROR]{self.RESET} Process '{name}' not found")
            return False
        
        process_info = self.processes[name]
        
        # Stop first
        if process_info.get('pid'):
            print(f"{self.BLUE}[INFO]{self.RESET} Stopping process '{name}'...")
            self.stop(name)
        
        # Start again
        print(f"{self.BLUE}[INFO]{self.RESET} Starting process '{name}'...")
        return self.start(
            name,
            process_info['script_path'],
            process_info.get('auto_restart', False),
            process_info.get('venv_path'),
            process_info.get('on_boot', False),
        )
    
    def delete(self, name: str):
        """Delete a process from the list"""
        if name not in self.processes:
            print(f"{self.RED}[ERROR]{self.RESET} Process '{name}' not found")
            return False
        
        # Stop first
        self.stop(name)
        
        # Remove from list
        del self.processes[name]
        self._save_state()
        
        print(f"{self.GREEN}[SUCCESS]{self.RESET} Process '{name}' deleted")
        return True
    
    def list_processes(self):
        """Show list of processes in table format"""
        if not self.processes:
            print(f"{self.YELLOW}No processes{self.RESET}")
            return
        
        # Update status of all processes
        for name in self.processes:
            self._update_process_status(name)
        
        self._save_state()
        
        print(f"\n{self.BOLD}{self.CYAN}Process List:{self.RESET}")
        
        # Get terminal size
        try:
            import shutil
            terminal_width = shutil.get_terminal_size().columns
        except:
            terminal_width = 120  # Fallback for wider display
        
        # Minimum column sizes (no separate status column now)
        min_name_width = 10  # Increased to fit status symbol + name
        min_pid_width = 8    # Increased for long PIDs
        min_cpu_width = 5
        min_mem_width = 7
        min_start_width = 19  # Increased for full date format
        min_stop_width = 19   # Increased for full date format
        min_script_width = 8
        
        # Base table width (borders + minimum columns, no status column)
        base_width = 8 + min_name_width + min_pid_width + min_cpu_width + min_mem_width + min_start_width + min_stop_width + min_script_width
        
        # If terminal is too narrow - compact output (need at least 45 chars for compact table)
        if terminal_width < max(base_width, 45):
            self._show_compact_list()
            return
        
        # Distribute available space
        available_width = terminal_width - 8  # 8 characters for borders
        
        # Priority distribution of width
        name_width = min(20, min_name_width + (available_width - base_width + 8) // 7)
        pid_width = min(12, min_pid_width)  # Max 12 chars for PID
        cpu_width = min_cpu_width
        mem_width = min_mem_width
        start_width = min(19, min_start_width + (available_width - base_width + 8) // 5)
        stop_width = min(19, min_stop_width + (available_width - base_width + 8) // 5)
        script_width = available_width - name_width - pid_width - cpu_width - mem_width - start_width - stop_width
        
        # Limit maximum sizes
        name_width = max(min_name_width, min(name_width, 25))
        start_width = max(min_start_width, min(start_width, 19))
        stop_width = max(min_stop_width, min(stop_width, 19))
        script_width = max(min_script_width, script_width)
        
        self._print_table(name_width, pid_width, cpu_width, mem_width, start_width, stop_width, script_width)
    
    def _show_compact_list(self):
        """Compact table output for narrow terminals"""
        # Fixed widths for compact mode
        name_width = 18  # Status symbol + name
        pid_width = 10
        script_width = 15
        
        # Top border
        print("┌" + "─" * name_width + "┬" + "─" * pid_width + "┬" + "─" * script_width + "┐")
        
        # Header
        print(f"│{self.BOLD}{'Name':<{name_width}}{self.RESET}│{self.BOLD}{'PID':<{pid_width}}{self.RESET}│{self.BOLD}{'Script':<{script_width}}{self.RESET}│")
        
        # Separator line
        print("├" + "─" * name_width + "┼" + "─" * pid_width + "┼" + "─" * script_width + "┤")
        
        for name, info in self.processes.items():
            status = info['status']
            pid = info.get('pid') or '-'
            script = os.path.basename(info.get('script_path', ''))
            
            # Status symbols
            if status == 'running':
                status_symbol = f"{self.GREEN}✓{self.RESET}"
            elif status == 'stopped':
                status_symbol = f"{self.RED}✗{self.RESET}"
            else:
                status_symbol = f"{self.YELLOW}⚠{self.RESET}"
            
            # Truncate long values
            pid_str = str(pid)[:pid_width-1] if len(str(pid)) >= pid_width else str(pid)
            name_display = name[:name_width-3] if len(name) >= name_width-2 else name  # -3 for symbol and space
            script_display = script[:script_width-1] if len(script) >= script_width else script
            
            # Format name with status symbol
            name_with_status = f"{status_symbol} {name_display}"
            name_padded = name_with_status + " " * (name_width - len(name_display) - 2)  # -2 for symbol and space
            
            print(f"│{name_padded}│{pid_str:<{pid_width}}│{script_display:<{script_width}}│")
        
        # Bottom border
        print("└" + "─" * name_width + "┴" + "─" * pid_width + "┴" + "─" * script_width + "┘")
        
        # Statistics
        running = sum(1 for p in self.processes.values() if p['status'] == 'running')
        stopped = sum(1 for p in self.processes.values() if p['status'] == 'stopped')
        print(f"\n{self.BOLD}Total:{self.RESET} {len(self.processes)} | {self.GREEN}Running:{self.RESET} {running} | {self.RED}Stopped:{self.RESET} {stopped}")
    
    def _print_table(self, name_width, pid_width, cpu_width, mem_width, start_width, stop_width, script_width):
        """Print full table with given column sizes"""
        # Top border
        print("┌" + "─" * name_width + "┬" + "─" * pid_width + 
              "┬" + "─" * cpu_width + "┬" + "─" * mem_width + "┬" + "─" * start_width + 
              "┬" + "─" * stop_width + "┬" + "─" * script_width + "┐")
        
        # Header
        print(f"│{self.BOLD}{'Name':<{name_width}}{self.RESET}│{self.BOLD}{'PID':<{pid_width}}{self.RESET}│{self.BOLD}{'CPU%':<{cpu_width}}{self.RESET}│{self.BOLD}{'RAM':<{mem_width}}{self.RESET}│{self.BOLD}{'Started':<{start_width}}{self.RESET}│{self.BOLD}{'Stopped':<{stop_width}}{self.RESET}│{self.BOLD}{'Script':<{script_width}}{self.RESET}│")
        
        # Separator line
        print("├" + "─" * name_width + "┼" + "─" * pid_width + 
              "┼" + "─" * cpu_width + "┼" + "─" * mem_width + "┼" + "─" * start_width + 
              "┼" + "─" * stop_width + "┼" + "─" * script_width + "┤")
        
        for name, info in self.processes.items():
            status = info['status']
            pid = info.get('pid') or '-'
            cpu = info.get('cpu_percent') or 0.0
            memory = info.get('memory_mb') or 0.0
            start_time = info.get('start_time', '')
            stop_time = info.get('stop_time', '')
            script = os.path.basename(info.get('script_path', ''))
            
            # Status symbols and colors
            if status == 'running':
                status_symbol = f"{self.GREEN}✓{self.RESET}"
                status_color = self.GREEN
            elif status == 'stopped':
                status_symbol = f"{self.RED}✗{self.RESET}"
                status_color = self.RED
            else:
                status_symbol = f"{self.YELLOW}⚠{self.RESET}"
                status_color = self.YELLOW
            
            # Format times - show only time part if same day, full date if different
            start_display = self._format_time(start_time, start_width)
            stop_display = self._format_time(stop_time, stop_width) if stop_time else "-"
            
            # Format CPU and memory
            cpu_str = f"{cpu:.1f}" if isinstance(cpu, (int, float)) else "0.0"
            mem_str = f"{memory:.1f}" if isinstance(memory, (int, float)) else "0.0"
            
            # Truncate long values
            name_display = name[:name_width-3] if len(name) >= name_width-2 else name  # -3 for symbol and space
            script_display = script[:script_width-1] if len(script) >= script_width else script
            
            # Handle long PIDs by truncating
            pid_str = str(pid)
            if len(pid_str) > pid_width:
                pid_str = pid_str[:pid_width-3] + "..."
            
            # Colored PID for running processes
            pid_colored = f"{status_color}{pid_str}{self.RESET}" if status == 'running' else pid_str
            
            # Format name with status symbol
            name_with_status = f"{status_symbol} {name_display}"
            name_padded = name_with_status + " " * (name_width - len(name_display) - 2)  # -2 for symbol and space
            pid_padded = pid_colored + " " * (pid_width - len(pid_str))
            
            print(f"│{name_padded}│{pid_padded}│{cpu_str:<{cpu_width}}│{mem_str:<{mem_width}}│{start_display:<{start_width}}│{stop_display:<{stop_width}}│{script_display:<{script_width}}│")
        
        # Bottom border
        print("└" + "─" * name_width + "┴" + "─" * pid_width + 
              "┴" + "─" * cpu_width + "┴" + "─" * mem_width + "┴" + "─" * start_width + 
              "┴" + "─" * stop_width + "┴" + "─" * script_width + "┘")
        
        # Statistics
        running = sum(1 for p in self.processes.values() if p['status'] == 'running')
        stopped = sum(1 for p in self.processes.values() if p['status'] == 'stopped')
        
        print(f"\n{self.BOLD}Statistics:{self.RESET} Total: {self.BLUE}{len(self.processes)}{self.RESET} | {self.GREEN}Running: {running}{self.RESET} | {self.RED}Stopped: {stopped}{self.RESET}")
    
    def _format_time(self, time_str, max_width):
        """Format time string to fit in column"""
        if not time_str:
            return "-"
        
        try:
            # Try to parse the time
            if 'T' in time_str:  # ISO format
                dt = datetime.fromisoformat(time_str.replace('T', ' '))
            else:
                dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
            
            # Always show date and time for clarity
            if max_width >= 19:
                # Full format: 2025-08-19 01:42:48
                formatted = dt.strftime("%Y-%m-%d %H:%M:%S")
            elif max_width >= 16:
                # Abbreviated: 08-19 01:42:48
                formatted = dt.strftime("%m-%d %H:%M:%S")
            elif max_width >= 14:
                # Short: 08-19 01:42
                formatted = dt.strftime("%m-%d %H:%M")
            else:
                # Very short: 08-19
                formatted = dt.strftime("%m-%d")
            
            return formatted[:max_width] if len(formatted) > max_width else formatted
        except:
            # Fallback: just truncate the original string
            return time_str[:max_width]
    
    def logs(self, name: str, lines: int = 50, follow: bool = False):
        """Show process logs"""
        if name not in self.processes:
            print(f"{self.RED}[ERROR]{self.RESET} Process '{name}' not found")
            return
        
        log_file = Path(self.processes[name].get('log_file', ''))
        
        if not log_file.exists():
            print(f"{self.YELLOW}[WARNING]{self.RESET} No logs found for process '{name}'")
            return
        
        if follow:
            print(f"{self.CYAN}[LOGS]{self.RESET} Following logs for process '{name}' (Ctrl+C to exit):")
            print("─" * 80)
            
            # Show last lines first
            try:
                result = subprocess.run(['tail', '-n', str(lines), str(log_file)], 
                                      capture_output=True, text=True)
                if result.stdout:
                    print(result.stdout, end='')
            except:
                pass
            
            # Follow new lines
            try:
                subprocess.run(['tail', '-f', str(log_file)])
            except KeyboardInterrupt:
                print(f"\n{self.YELLOW}[INFO]{self.RESET} Stopped")
        else:
            print(f"{self.CYAN}[LOGS]{self.RESET} Last {lines} lines from process '{name}':")
            print("─" * 80)
            
            try:
                result = subprocess.run(['tail', '-n', str(lines), str(log_file)], 
                                      capture_output=True, text=True)
                if result.stdout:
                    print(result.stdout)
                else:
                    print("No logs available")
            except Exception as e:
                print(f"{self.RED}[ERROR]{self.RESET} Failed to read logs: {e}")
    
    def info(self, name: str = None):
        """Show detailed process information"""
        if name:
            # Show info for specific process
            if name not in self.processes:
                print(f"{self.RED}[ERROR]{self.RESET} Process '{name}' not found")
                return
            
            self._update_process_status(name)
            info = self.processes[name]
            
            # Status symbol
            status = info['status']
            if status == 'running':
                status_display = f"{self.GREEN}✓ Running{self.RESET}"
            elif status == 'stopped':
                status_display = f"{self.RED}✗ Stopped{self.RESET}"
            else:
                status_display = f"{self.YELLOW}⚠ Error{self.RESET}"
            
            print(f"\n{self.BOLD}{self.CYAN}Process Information: {name}{self.RESET}")
            print(f"{self.BOLD}Status:{self.RESET} {status_display}")
            print(f"{self.BOLD}PID:{self.RESET} {info.get('pid', '-')}")
            print(f"{self.BOLD}Script:{self.RESET} {info.get('script_path', '-')}")
            print(f"{self.BOLD}CPU Usage:{self.RESET} {info.get('cpu_percent', 0.0):.1f}%")
            print(f"{self.BOLD}Memory:{self.RESET} {info.get('memory_mb', 0.0):.1f} MB")
            
            start_time = info.get('start_time', '')
            if start_time:
                print(f"{self.BOLD}Started:{self.RESET} {start_time}")
            
            stop_time = info.get('stop_time', '')
            if stop_time:
                print(f"{self.BOLD}Stopped:{self.RESET} {stop_time}")
            
            log_file = info.get('log_file', '')
            if log_file:
                print(f"{self.BOLD}Log file:{self.RESET} {log_file}")
            
            auto_restart = info.get('auto_restart', False)
            print(f"{self.BOLD}Auto restart:{self.RESET} {'Yes' if auto_restart else 'No'}")
            
            on_boot = info.get('on_boot', False)
            print(f"{self.BOLD}On boot:{self.RESET} {'Yes' if on_boot else 'No'}")
            
            venv_path = info.get('venv_path')
            if venv_path:
                print(f"{self.BOLD}Virtual env:{self.RESET} {venv_path}")
                python_exe = info.get('python_exe')
                if python_exe:
                    print(f"{self.BOLD}Python executable:{self.RESET} {python_exe}")
            else:
                print(f"{self.BOLD}Virtual env:{self.RESET} System Python")
        else:
            # Show overall system info
            for name in self.processes:
                self._update_process_status(name)
            
            running = sum(1 for p in self.processes.values() if p['status'] == 'running')
            stopped = sum(1 for p in self.processes.values() if p['status'] == 'stopped')
            
            print(f"\n{self.BOLD}{self.CYAN}Pyker System Information{self.RESET}")
            print(f"{self.BOLD}Total processes:{self.RESET} {self.BLUE}{len(self.processes)}{self.RESET}")
            print(f"{self.BOLD}Running:{self.RESET} {self.GREEN}{running}{self.RESET}")
            print(f"{self.BOLD}Stopped:{self.RESET} {self.RED}{stopped}{self.RESET}")
            print(f"{self.BOLD}State file:{self.RESET} {self.state_file}")
            print(f"{self.BOLD}Logs directory:{self.RESET} {self.logs_dir}")
            print(f"{self.BOLD}Config file:{self.RESET} {self.state_file.parent / 'config.json'}")
            on_boot_count = sum(1 for p in self.processes.values() if p.get('on_boot'))
            print(f"{self.BOLD}On boot:{self.RESET} {on_boot_count} process(es)")
            print(f"{self.BOLD}Startup hook:{self.RESET} {'enabled' if self._startup_is_installed() else 'not installed'}")
    
    def enable(self, name: str):
        """Mark a process to start automatically on boot/login"""
        if name not in self.processes:
            print(f"{self.RED}[ERROR]{self.RESET} Process '{name}' not found")
            return False
        
        self.processes[name]['on_boot'] = True
        self._save_state()
        print(f"{self.GREEN}[SUCCESS]{self.RESET} Process '{name}' will start on boot")
        if not self._startup_is_installed():
            print(f"{self.YELLOW}[HINT]{self.RESET} Run '{self.CYAN}pyker startup{self.RESET}' to install the boot hook")
        return True
    
    def disable(self, name: str):
        """Remove a process from automatic boot start"""
        if name not in self.processes:
            print(f"{self.RED}[ERROR]{self.RESET} Process '{name}' not found")
            return False
        
        self.processes[name]['on_boot'] = False
        self._save_state()
        print(f"{self.GREEN}[SUCCESS]{self.RESET} Process '{name}' will no longer start on boot")
        return True
    
    def resurrect(self):
        """Start all processes marked with on_boot that are not running"""
        boot_processes = [
            name for name, info in self.processes.items() if info.get('on_boot')
        ]
        
        if not boot_processes:
            print(f"{self.YELLOW}[INFO]{self.RESET} No processes marked for boot start")
            print(f"{self.BLUE}[HINT]{self.RESET} Use '{self.CYAN}pyker enable <name>{self.RESET}' or '{self.CYAN}pyker start ... --on-boot{self.RESET}'")
            return True
        
        print(f"{self.BLUE}[INFO]{self.RESET} Resurrecting {len(boot_processes)} process(es)...")
        started = 0
        skipped = 0
        failed = 0
        
        for name in boot_processes:
            self._update_process_status(name)
            info = self.processes[name]
            if info.get('status') == 'running':
                print(f"{self.YELLOW}[SKIP]{self.RESET} '{name}' is already running")
                skipped += 1
                continue
            
            ok = self.start(
                name,
                info['script_path'],
                info.get('auto_restart', False),
                info.get('venv_path'),
                True,
            )
            if ok:
                started += 1
            else:
                failed += 1
        
        print(
            f"{self.GREEN}[DONE]{self.RESET} started={started}, "
            f"skipped={skipped}, failed={failed}"
        )
        return failed == 0
    
    def startup(self):
        """Install OS hook to run pyker resurrect on login/boot"""
        system = platform.system()
        if system == 'Linux':
            return self._startup_linux()
        if system == 'Darwin':
            return self._startup_macos()
        if system == 'Windows':
            return self._startup_windows()
        
        print(f"{self.RED}[ERROR]{self.RESET} Unsupported platform: {system}")
        return False
    
    def unstartup(self):
        """Remove OS boot/login hook"""
        system = platform.system()
        if system == 'Linux':
            return self._unstartup_linux()
        if system == 'Darwin':
            return self._unstartup_macos()
        if system == 'Windows':
            return self._unstartup_windows()
        
        print(f"{self.RED}[ERROR]{self.RESET} Unsupported platform: {system}")
        return False
    
    def _find_pyker_executable(self):
        """Resolve absolute path to the pyker CLI"""
        candidates = []
        
        which = shutil.which('pyker')
        if which:
            candidates.append(Path(which).resolve())
        
        argv0 = Path(sys.argv[0]).expanduser()
        if not argv0.is_absolute():
            argv0 = Path.cwd() / argv0
        if argv0.exists():
            candidates.append(argv0.resolve())
        
        home_bin = Path.home() / '.local' / 'bin' / 'pyker'
        if home_bin.exists():
            candidates.append(home_bin.resolve())
        
        for path in candidates:
            if path.exists() and os.access(path, os.X_OK):
                return str(path)
        
        # Fall back to running this module via current Python
        module_path = Path(__file__).resolve()
        if module_path.exists():
            return f"{sys.executable} {module_path}"
        
        return None
    
    def _startup_unit_paths(self):
        """Return platform-specific startup artifact paths"""
        home = Path.home()
        return {
            'systemd_unit': home / '.config' / 'systemd' / 'user' / 'pyker-resurrect.service',
            'launch_agent': home / 'Library' / 'LaunchAgents' / 'com.pyker.resurrect.plist',
            'windows_cmd': home / 'AppData' / 'Roaming' / 'Microsoft' / 'Windows' / 'Start Menu' /
                           'Programs' / 'Startup' / 'pyker-resurrect.cmd',
        }
    
    def _startup_is_installed(self):
        """Check whether a startup hook is present"""
        paths = self._startup_unit_paths()
        system = platform.system()
        if system == 'Linux':
            return paths['systemd_unit'].exists()
        if system == 'Darwin':
            return paths['launch_agent'].exists()
        if system == 'Windows':
            return paths['windows_cmd'].exists()
        return False
    
    def _startup_linux(self):
        """Install systemd --user oneshot for resurrect"""
        if not shutil.which('systemctl'):
            print(f"{self.RED}[ERROR]{self.RESET} systemctl not found; cannot install startup hook")
            return False
        
        pyker_exe = self._find_pyker_executable()
        if not pyker_exe:
            print(f"{self.RED}[ERROR]{self.RESET} Could not locate pyker executable")
            return False
        
        unit_path = self._startup_unit_paths()['systemd_unit']
        unit_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Supports binary path or "python /path/pyker.py"
        unit_content = f"""[Unit]
Description=Pyker resurrect processes on login/boot
After=default.target

[Service]
Type=oneshot
ExecStart={pyker_exe} resurrect
RemainAfterExit=yes

[Install]
WantedBy=default.target
"""
        unit_path.write_text(unit_content, encoding='utf-8')
        
        try:
            subprocess.run(['systemctl', '--user', 'daemon-reload'], check=True, capture_output=True)
            subprocess.run(['systemctl', '--user', 'enable', 'pyker-resurrect.service'], check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            err = (e.stderr or b'').decode().strip() or str(e)
            print(f"{self.RED}[ERROR]{self.RESET} Failed to enable systemd unit: {err}")
            return False
        
        print(f"{self.GREEN}[SUCCESS]{self.RESET} Installed startup hook: {unit_path}")
        print(f"{self.BLUE}[INFO]{self.RESET} Processes with on_boot will start on login")
        print(
            f"{self.YELLOW}[HINT]{self.RESET} For start at boot without login, run: "
            f"{self.CYAN}loginctl enable-linger $USER{self.RESET}"
        )
        
        boot_count = sum(1 for p in self.processes.values() if p.get('on_boot'))
        if boot_count == 0:
            print(
                f"{self.YELLOW}[HINT]{self.RESET} No processes marked yet — "
                f"use '{self.CYAN}pyker enable <name>{self.RESET}' or '{self.CYAN}--on-boot{self.RESET}'"
            )
        return True
    
    def _unstartup_linux(self):
        """Remove systemd --user startup hook"""
        unit_path = self._startup_unit_paths()['systemd_unit']
        if shutil.which('systemctl'):
            subprocess.run(
                ['systemctl', '--user', 'disable', '--now', 'pyker-resurrect.service'],
                capture_output=True,
            )
            subprocess.run(['systemctl', '--user', 'daemon-reload'], capture_output=True)
        
        if unit_path.exists():
            unit_path.unlink()
            print(f"{self.GREEN}[SUCCESS]{self.RESET} Removed startup hook: {unit_path}")
        else:
            print(f"{self.YELLOW}[INFO]{self.RESET} Startup hook was not installed")
        return True
    
    def _startup_macos(self):
        """Install LaunchAgent to run resurrect at login"""
        pyker_exe = self._find_pyker_executable()
        if not pyker_exe:
            print(f"{self.RED}[ERROR]{self.RESET} Could not locate pyker executable")
            return False
        
        plist_path = self._startup_unit_paths()['launch_agent']
        plist_path.parent.mkdir(parents=True, exist_ok=True)
        
        if ' ' in pyker_exe:
            parts = pyker_exe.split()
            program_args = ''.join(f'    <string>{p}</string>\n' for p in parts)
            program_args += '    <string>resurrect</string>\n'
        else:
            program_args = f'    <string>{pyker_exe}</string>\n    <string>resurrect</string>\n'
        
        plist = f"""<?xml version="1.0" encoding="UTF-8"?>
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
  <string>{Path.home() / '.pyker' / 'logs' / 'startup.log'}</string>
  <key>StandardErrorPath</key>
  <string>{Path.home() / '.pyker' / 'logs' / 'startup.log'}</string>
</dict>
</plist>
"""
        plist_path.write_text(plist, encoding='utf-8')
        
        # Load agent (ignore errors if already loaded)
        subprocess.run(['launchctl', 'unload', str(plist_path)], capture_output=True)
        result = subprocess.run(['launchctl', 'load', str(plist_path)], capture_output=True)
        if result.returncode != 0:
            err = (result.stderr or b'').decode().strip()
            print(f"{self.YELLOW}[WARNING]{self.RESET} launchctl load: {err or 'non-zero exit'}")
        
        print(f"{self.GREEN}[SUCCESS]{self.RESET} Installed startup hook: {plist_path}")
        print(f"{self.BLUE}[INFO]{self.RESET} Processes with on_boot will start at login")
        return True
    
    def _unstartup_macos(self):
        """Remove LaunchAgent startup hook"""
        plist_path = self._startup_unit_paths()['launch_agent']
        if plist_path.exists():
            subprocess.run(['launchctl', 'unload', str(plist_path)], capture_output=True)
            plist_path.unlink()
            print(f"{self.GREEN}[SUCCESS]{self.RESET} Removed startup hook: {plist_path}")
        else:
            print(f"{self.YELLOW}[INFO]{self.RESET} Startup hook was not installed")
        return True
    
    def _startup_windows(self):
        """Install a Startup folder .cmd that runs resurrect on login"""
        pyker_exe = self._find_pyker_executable()
        if not pyker_exe:
            print(f"{self.RED}[ERROR]{self.RESET} Could not locate pyker executable")
            return False
        
        cmd_path = self._startup_unit_paths()['windows_cmd']
        cmd_path.parent.mkdir(parents=True, exist_ok=True)
        cmd_path.write_text(f'@echo off\r\n{pyker_exe} resurrect\r\n', encoding='utf-8')
        
        print(f"{self.GREEN}[SUCCESS]{self.RESET} Installed startup hook: {cmd_path}")
        print(f"{self.BLUE}[INFO]{self.RESET} Processes with on_boot will start at Windows login")
        return True
    
    def _unstartup_windows(self):
        """Remove Windows Startup folder hook"""
        cmd_path = self._startup_unit_paths()['windows_cmd']
        if cmd_path.exists():
            cmd_path.unlink()
            print(f"{self.GREEN}[SUCCESS]{self.RESET} Removed startup hook: {cmd_path}")
        else:
            print(f"{self.YELLOW}[INFO]{self.RESET} Startup hook was not installed")
        return True
    
    def uninstall(self):
        """Uninstall Pyker with confirmation"""
        print(f"\n{self.BOLD}{self.RED}⚠ Pyker Uninstallation{self.RESET}")
        print(f"{self.YELLOW}This will:{self.RESET}")
        print(f"  • Stop all running processes")
        print(f"  • Remove boot startup hook (if installed)")
        print(f"  • Remove Pyker executable")
        print(f"  • Remove completion scripts")
        print(f"  • Keep logs and config (optional cleanup)")
        
        # Show current processes
        if self.processes:
            running_processes = [name for name, info in self.processes.items() 
                               if info.get('status') == 'running']
            if running_processes:
                print(f"\n{self.RED}Running processes that will be stopped:{self.RESET}")
                for name in running_processes:
                    print(f"  • {name}")
        
        print(f"\n{self.BOLD}Do you want to continue? [y/N]:{self.RESET} ", end="")
        try:
            response = input().strip().lower()
        except (KeyboardInterrupt, EOFError):
            print(f"\n{self.YELLOW}[INFO]{self.RESET} Uninstallation cancelled")
            return
        
        if response not in ['y', 'yes']:
            print(f"{self.YELLOW}[INFO]{self.RESET} Uninstallation cancelled")
            return
        
        # Stop all running processes
        print(f"\n{self.YELLOW}Stopping all processes...{self.RESET}")
        stopped_count = 0
        for name, info in self.processes.items():
            if info.get('status') == 'running':
                if self.stop(name):
                    stopped_count += 1
        
        if stopped_count > 0:
            print(f"{self.GREEN}✓ Stopped {stopped_count} processes{self.RESET}")
        
        # Remove boot hook if present
        if self._startup_is_installed():
            print(f"{self.YELLOW}Removing startup hook...{self.RESET}")
            self.unstartup()
        
        # Ask about data cleanup
        print(f"\n{self.BOLD}Remove logs and configuration? [y/N]:{self.RESET} ", end="")
        try:
            cleanup_response = input().strip().lower()
        except (KeyboardInterrupt, EOFError):
            cleanup_response = 'n'
        
        # Remove Pyker files
        self._remove_pyker_files(cleanup_response in ['y', 'yes'])
        
        print(f"\n{self.GREEN}✓ Pyker has been uninstalled successfully{self.RESET}")
        print(f"{self.BLUE}Thank you for using Pyker!{self.RESET}")
    
    def _remove_pyker_files(self, remove_data: bool):
        """Remove Pyker installation files"""
        # Find pyker executable
        pyker_locations = [
            Path.home() / ".local" / "bin" / "pyker",
            Path("/usr/local/bin/pyker"),
            Path("/usr/bin/pyker")
        ]
        
        for location in pyker_locations:
            if location.exists():
                try:
                    location.unlink()
                    print(f"{self.GREEN}✓ Removed {location}{self.RESET}")
                except Exception as e:
                    print(f"{self.RED}✗ Failed to remove {location}: {e}{self.RESET}")
        
        # Remove completion scripts
        completion_locations = [
            Path.home() / ".local" / "share" / "bash-completion" / "completions" / "pyker",
            Path.home() / ".oh-my-zsh" / "completions" / "_pyker",
            Path.home() / ".local" / "share" / "zsh" / "site-functions" / "_pyker"
        ]
        
        for location in completion_locations:
            if location.exists():
                try:
                    location.unlink()
                    print(f"{self.GREEN}✓ Removed completion {location.name}{self.RESET}")
                except Exception as e:
                    print(f"{self.RED}✗ Failed to remove completion: {e}{self.RESET}")
        
        # Remove data if requested
        if remove_data:
            pyker_dir = Path.home() / ".pyker"
            if pyker_dir.exists():
                try:
                    shutil.rmtree(pyker_dir)
                    print(f"{self.GREEN}✓ Removed data directory ~/.pyker{self.RESET}")
                except Exception as e:
                    print(f"{self.RED}✗ Failed to remove data directory: {e}{self.RESET}")
        else:
            print(f"{self.BLUE}ℹ Data directory ~/.pyker preserved{self.RESET}")
            print(f"{self.BLUE}  You can manually remove it later if needed{self.RESET}")
    
    def _get_python_executable(self, venv_path: str = None):
        """Get Python executable from venv or system"""
        if venv_path:
            # Resolve venv path
            venv_path = os.path.expanduser(venv_path)
            if not os.path.isabs(venv_path):
                venv_path = os.path.abspath(venv_path)
            
            # Check if venv directory exists
            if not os.path.exists(venv_path):
                print(f"{self.RED}[ERROR]{self.RESET} Virtual environment not found: {venv_path}")
                return None
            
            # Try different Python executable paths in venv
            possible_paths = [
                os.path.join(venv_path, 'bin', 'python'),      # Linux/macOS
                os.path.join(venv_path, 'bin', 'python3'),     # Linux/macOS
                os.path.join(venv_path, 'Scripts', 'python.exe'),  # Windows
                os.path.join(venv_path, 'Scripts', 'python3.exe'), # Windows
            ]
            
            for python_exe in possible_paths:
                if os.path.exists(python_exe) and os.access(python_exe, os.X_OK):
                    print(f"{self.BLUE}[INFO]{self.RESET} Using Python from venv: {python_exe}")
                    return python_exe
            
            print(f"{self.RED}[ERROR]{self.RESET} No Python executable found in venv: {venv_path}")
            print(f"{self.YELLOW}[HINT]{self.RESET} Expected paths: bin/python or Scripts/python.exe")
            return None
        else:
            # Use system Python
            return sys.executable

def _print_help():
    """Print main help text"""
    print(f"{Pyker.BOLD}{Pyker.CYAN}Pyker - Simple Python Process Manager{Pyker.RESET}")
    print(f"\n{Pyker.BOLD}Usage:{Pyker.RESET} pyker <command> [options]")
    print(f"\n{Pyker.BOLD}Available commands:{Pyker.RESET}")
    print(f"  {Pyker.GREEN}start{Pyker.RESET}     <name> <script>  - Start a new process [--venv PATH] [--on-boot]")
    print(f"  {Pyker.GREEN}stop{Pyker.RESET}      <name>          - Stop a process")
    print(f"  {Pyker.GREEN}restart{Pyker.RESET}   <name>          - Restart a process")
    print(f"  {Pyker.GREEN}delete{Pyker.RESET}    <name>          - Delete a process")
    print(f"  {Pyker.GREEN}list{Pyker.RESET}                      - List all processes")
    print(f"  {Pyker.GREEN}logs{Pyker.RESET}      <name>          - Show process logs")
    print(f"  {Pyker.GREEN}info{Pyker.RESET}      [name]          - Show process/system information")
    print(f"  {Pyker.GREEN}enable{Pyker.RESET}    <name>          - Start process automatically on boot")
    print(f"  {Pyker.GREEN}disable{Pyker.RESET}   <name>          - Disable boot start for a process")
    print(f"  {Pyker.GREEN}startup{Pyker.RESET}                   - Install OS boot/login hook")
    print(f"  {Pyker.GREEN}unstartup{Pyker.RESET}                 - Remove OS boot/login hook")
    print(f"  {Pyker.GREEN}resurrect{Pyker.RESET}                 - Start all on-boot processes")
    print(f"  {Pyker.GREEN}uninstall{Pyker.RESET}                 - Uninstall Pyker completely")
    print(f"\n{Pyker.BOLD}Examples:{Pyker.RESET}")
    print(f"  pyker start bot script.py --on-boot")
    print(f"  pyker enable bot && pyker startup")
    print(f"  pyker start webapp app.py --venv ./venv")
    print(f"  pyker list")
    print(f"  pyker logs bot -f")
    print(f"\nUse '{Pyker.CYAN}pyker <command> --help{Pyker.RESET}' for more information on a command.")


def main():
    parser = argparse.ArgumentParser(
        description='Pyker - Simple Python Process Manager',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False  # We'll handle help ourselves
    )
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Start command
    start_parser = subparsers.add_parser('start', help='Start a new process')
    start_parser.add_argument('name', help='Process name')
    start_parser.add_argument('script', help='Python script path')
    start_parser.add_argument('--auto-restart', action='store_true', help='Auto restart on failure')
    start_parser.add_argument('--venv', help='Virtual environment path (e.g., ./venv or /path/to/venv)')
    start_parser.add_argument('--on-boot', action='store_true', help='Also start this process on boot/login')
    
    # Stop command
    stop_parser = subparsers.add_parser('stop', help='Stop a process')
    stop_parser.add_argument('name', help='Process name')
    
    # Restart command
    restart_parser = subparsers.add_parser('restart', help='Restart a process')
    restart_parser.add_argument('name', help='Process name')
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete a process')
    delete_parser.add_argument('name', help='Process name')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all processes')
    
    # Logs command
    logs_parser = subparsers.add_parser('logs', help='Show process logs')
    logs_parser.add_argument('name', help='Process name')
    logs_parser.add_argument('-n', '--lines', type=int, default=50, help='Number of lines to show')
    logs_parser.add_argument('-f', '--follow', action='store_true', help='Follow log output')
    
    # Info command
    info_parser = subparsers.add_parser('info', help='Show process information')
    info_parser.add_argument('name', nargs='?', help='Process name (optional, shows system info if not provided)')
    
    # Boot autostart commands
    enable_parser = subparsers.add_parser('enable', help='Enable start on boot for a process')
    enable_parser.add_argument('name', help='Process name')
    
    disable_parser = subparsers.add_parser('disable', help='Disable start on boot for a process')
    disable_parser.add_argument('name', help='Process name')
    
    subparsers.add_parser('startup', help='Install OS hook to resurrect processes on boot/login')
    subparsers.add_parser('unstartup', help='Remove OS boot/login hook')
    subparsers.add_parser('resurrect', help='Start all processes marked for boot')
    
    # Uninstall command
    uninstall_parser = subparsers.add_parser('uninstall', help='Uninstall Pyker completely')
    
    # Handle help manually
    if len(sys.argv) == 1 or (len(sys.argv) == 2 and sys.argv[1] in ['-h', '--help', 'help']):
        _print_help()
        return
    
    try:
        args = parser.parse_args()
    except SystemExit:
        print(f"\n{Pyker.RED}[ERROR]{Pyker.RESET} Invalid command or arguments")
        print(f"Use '{Pyker.CYAN}pyker --help{Pyker.RESET}' to see available commands.")
        return
    
    if not args.command:
        print(f"{Pyker.RED}[ERROR]{Pyker.RESET} No command specified")
        _print_help()
        return
    
    pyker = Pyker()
    
    if args.command == 'start':
        pyker.start(args.name, args.script, args.auto_restart, args.venv, args.on_boot)
    elif args.command == 'stop':
        pyker.stop(args.name)
    elif args.command == 'restart':
        pyker.restart(args.name)
    elif args.command == 'delete':
        pyker.delete(args.name)
    elif args.command == 'list':
        pyker.list_processes()
    elif args.command == 'logs':
        pyker.logs(args.name, args.lines, args.follow)
    elif args.command == 'info':
        pyker.info(args.name)
    elif args.command == 'enable':
        pyker.enable(args.name)
    elif args.command == 'disable':
        pyker.disable(args.name)
    elif args.command == 'startup':
        pyker.startup()
    elif args.command == 'unstartup':
        pyker.unstartup()
    elif args.command == 'resurrect':
        pyker.resurrect()
    elif args.command == 'uninstall':
        pyker.uninstall()

if __name__ == '__main__':
    main() 