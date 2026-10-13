"""Terminal table rendering for process lists."""

from __future__ import annotations

import os
import shutil
from datetime import datetime
from typing import Any, Dict

from pyker.colors import Colors


def print_process_list(processes: Dict[str, Dict[str, Any]]) -> None:
    print(f"\n{Colors.BOLD}{Colors.CYAN}Process List:{Colors.RESET}")
    try:
        terminal_width = shutil.get_terminal_size().columns
    except OSError:
        terminal_width = 120

    min_name_width = 10
    min_pid_width = 8
    min_cpu_width = 5
    min_mem_width = 7
    min_start_width = 19
    min_stop_width = 19
    min_script_width = 8
    base_width = (
        8
        + min_name_width
        + min_pid_width
        + min_cpu_width
        + min_mem_width
        + min_start_width
        + min_stop_width
        + min_script_width
    )

    if terminal_width < max(base_width, 45):
        _show_compact_list(processes)
        return

    available_width = terminal_width - 8
    name_width = min(20, min_name_width + (available_width - base_width + 8) // 7)
    pid_width = min(12, min_pid_width)
    cpu_width = min_cpu_width
    mem_width = min_mem_width
    start_width = min(19, min_start_width + (available_width - base_width + 8) // 5)
    stop_width = min(19, min_stop_width + (available_width - base_width + 8) // 5)
    script_width = (
        available_width - name_width - pid_width - cpu_width - mem_width - start_width - stop_width
    )
    name_width = max(min_name_width, min(name_width, 25))
    start_width = max(min_start_width, min(start_width, 19))
    stop_width = max(min_stop_width, min(stop_width, 19))
    script_width = max(min_script_width, script_width)
    _print_table(processes, name_width, pid_width, cpu_width, mem_width, start_width, stop_width, script_width)


def _show_compact_list(processes: Dict[str, Dict[str, Any]]) -> None:
    name_width, pid_width, script_width = 18, 10, 15
    print("┌" + "─" * name_width + "┬" + "─" * pid_width + "┬" + "─" * script_width + "┐")
    print(
        f"│{Colors.BOLD}{'Name':<{name_width}}{Colors.RESET}│"
        f"{Colors.BOLD}{'PID':<{pid_width}}{Colors.RESET}│"
        f"{Colors.BOLD}{'Script':<{script_width}}{Colors.RESET}│"
    )
    print("├" + "─" * name_width + "┼" + "─" * pid_width + "┼" + "─" * script_width + "┤")
    for name, info in processes.items():
        status = info["status"]
        pid = info.get("pid") or "-"
        script = os.path.basename(info.get("script_path", ""))
        if status == "running":
            symbol = f"{Colors.GREEN}✓{Colors.RESET}"
        elif status == "stopped":
            symbol = f"{Colors.RED}✗{Colors.RESET}"
        else:
            symbol = f"{Colors.YELLOW}⚠{Colors.RESET}"
        pid_str = str(pid)[: pid_width - 1] if len(str(pid)) >= pid_width else str(pid)
        name_display = name[: name_width - 3] if len(name) >= name_width - 2 else name
        script_display = script[: script_width - 1] if len(script) >= script_width else script
        name_padded = f"{symbol} {name_display}" + " " * (name_width - len(name_display) - 2)
        print(f"│{name_padded}│{pid_str:<{pid_width}}│{script_display:<{script_width}}│")
    print("└" + "─" * name_width + "┴" + "─" * pid_width + "┴" + "─" * script_width + "┘")
    running = sum(1 for p in processes.values() if p["status"] == "running")
    stopped = sum(1 for p in processes.values() if p["status"] == "stopped")
    print(
        f"\n{Colors.BOLD}Total:{Colors.RESET} {len(processes)} | "
        f"{Colors.GREEN}Running:{Colors.RESET} {running} | "
        f"{Colors.RED}Stopped:{Colors.RESET} {stopped}"
    )


def _format_time(time_str: str, max_width: int) -> str:
    if not time_str:
        return "-"
    try:
        if "T" in time_str:
            dt = datetime.fromisoformat(time_str.replace("T", " "))
        else:
            dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
        if max_width >= 19:
            formatted = dt.strftime("%Y-%m-%d %H:%M:%S")
        elif max_width >= 16:
            formatted = dt.strftime("%m-%d %H:%M:%S")
        elif max_width >= 14:
            formatted = dt.strftime("%m-%d %H:%M")
        else:
            formatted = dt.strftime("%m-%d")
        return formatted[:max_width] if len(formatted) > max_width else formatted
    except ValueError:
        return time_str[:max_width]


def _print_table(
    processes,
    name_width,
    pid_width,
    cpu_width,
    mem_width,
    start_width,
    stop_width,
    script_width,
) -> None:
    print(
        "┌"
        + "─" * name_width
        + "┬"
        + "─" * pid_width
        + "┬"
        + "─" * cpu_width
        + "┬"
        + "─" * mem_width
        + "┬"
        + "─" * start_width
        + "┬"
        + "─" * stop_width
        + "┬"
        + "─" * script_width
        + "┐"
    )
    print(
        f"│{Colors.BOLD}{'Name':<{name_width}}{Colors.RESET}│"
        f"{Colors.BOLD}{'PID':<{pid_width}}{Colors.RESET}│"
        f"{Colors.BOLD}{'CPU%':<{cpu_width}}{Colors.RESET}│"
        f"{Colors.BOLD}{'RAM':<{mem_width}}{Colors.RESET}│"
        f"{Colors.BOLD}{'Started':<{start_width}}{Colors.RESET}│"
        f"{Colors.BOLD}{'Stopped':<{stop_width}}{Colors.RESET}│"
        f"{Colors.BOLD}{'Script':<{script_width}}{Colors.RESET}│"
    )
    print(
        "├"
        + "─" * name_width
        + "┼"
        + "─" * pid_width
        + "┼"
        + "─" * cpu_width
        + "┼"
        + "─" * mem_width
        + "┼"
        + "─" * start_width
        + "┼"
        + "─" * stop_width
        + "┼"
        + "─" * script_width
        + "┤"
    )
    for name, info in processes.items():
        status = info["status"]
        pid = info.get("pid") or "-"
        cpu = info.get("cpu_percent") or 0.0
        memory = info.get("memory_mb") or 0.0
        script = os.path.basename(info.get("script_path", ""))
        if status == "running":
            symbol = f"{Colors.GREEN}✓{Colors.RESET}"
            status_color = Colors.GREEN
        elif status == "stopped":
            symbol = f"{Colors.RED}✗{Colors.RESET}"
            status_color = Colors.RED
        else:
            symbol = f"{Colors.YELLOW}⚠{Colors.RESET}"
            status_color = Colors.YELLOW
        start_display = _format_time(info.get("start_time", ""), start_width)
        stop_display = _format_time(info.get("stop_time", ""), stop_width) if info.get("stop_time") else "-"
        cpu_str = f"{cpu:.1f}" if isinstance(cpu, (int, float)) else "0.0"
        mem_str = f"{memory:.1f}" if isinstance(memory, (int, float)) else "0.0"
        name_display = name[: name_width - 3] if len(name) >= name_width - 2 else name
        script_display = script[: script_width - 1] if len(script) >= script_width else script
        pid_str = str(pid)
        if len(pid_str) > pid_width:
            pid_str = pid_str[: pid_width - 3] + "..."
        pid_colored = f"{status_color}{pid_str}{Colors.RESET}" if status == "running" else pid_str
        name_padded = f"{symbol} {name_display}" + " " * (name_width - len(name_display) - 2)
        pid_padded = pid_colored + " " * (pid_width - len(pid_str))
        print(
            f"│{name_padded}│{pid_padded}│{cpu_str:<{cpu_width}}│{mem_str:<{mem_width}}│"
            f"{start_display:<{start_width}}│{stop_display:<{stop_width}}│{script_display:<{script_width}}│"
        )
    print(
        "└"
        + "─" * name_width
        + "┴"
        + "─" * pid_width
        + "┴"
        + "─" * cpu_width
        + "┴"
        + "─" * mem_width
        + "┴"
        + "─" * start_width
        + "┴"
        + "─" * stop_width
        + "┴"
        + "─" * script_width
        + "┘"
    )
    running = sum(1 for p in processes.values() if p["status"] == "running")
    stopped = sum(1 for p in processes.values() if p["status"] == "stopped")
    print(
        f"\n{Colors.BOLD}Statistics:{Colors.RESET} Total: {Colors.BLUE}{len(processes)}{Colors.RESET} | "
        f"{Colors.GREEN}Running: {running}{Colors.RESET} | "
        f"{Colors.RED}Stopped: {stopped}{Colors.RESET}"
    )
