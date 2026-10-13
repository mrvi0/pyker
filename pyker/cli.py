"""Command-line interface for Pyker."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from pyker.colors import Colors
from pyker.manager import ProcessManager


def _print_help() -> None:
    print(f"{Colors.BOLD}{Colors.CYAN}Pyker - Simple Python Process Manager{Colors.RESET}")
    print(f"\n{Colors.BOLD}Usage:{Colors.RESET} pyker <command> [options]")
    print(f"\n{Colors.BOLD}Available commands:{Colors.RESET}")
    print(f"  {Colors.GREEN}start{Colors.RESET}     <name> <script>  - Start a process [--venv] [--on-boot] [--auto-restart]")
    print(f"  {Colors.GREEN}stop{Colors.RESET}      <name>          - Stop a process")
    print(f"  {Colors.GREEN}restart{Colors.RESET}   <name>          - Restart a process")
    print(f"  {Colors.GREEN}delete{Colors.RESET}    <name>          - Delete a process")
    print(f"  {Colors.GREEN}list{Colors.RESET}                      - List all processes")
    print(f"  {Colors.GREEN}logs{Colors.RESET}      <name>          - Show process logs")
    print(f"  {Colors.GREEN}info{Colors.RESET}      [name]          - Show process/system information")
    print(f"  {Colors.GREEN}enable{Colors.RESET}    <name>          - Start process automatically on boot")
    print(f"  {Colors.GREEN}disable{Colors.RESET}   <name>          - Disable boot start for a process")
    print(f"  {Colors.GREEN}startup{Colors.RESET}                   - Install OS boot/login hook")
    print(f"  {Colors.GREEN}unstartup{Colors.RESET}                 - Remove OS boot/login hook")
    print(f"  {Colors.GREEN}resurrect{Colors.RESET}                 - Start all on-boot processes")
    print(f"  {Colors.GREEN}watch{Colors.RESET}                     - Run auto-restart watcher (foreground)")
    print(f"  {Colors.GREEN}uninstall{Colors.RESET}                 - Uninstall Pyker completely")
    print(f"\n{Colors.BOLD}Examples:{Colors.RESET}")
    print("  pyker start bot script.py --auto-restart --on-boot")
    print("  pyker enable bot && pyker startup")
    print("  pyker start webapp app.py --venv ./venv")
    print("  pyker list")
    print(f"\nUse '{Colors.CYAN}pyker <command> --help{Colors.RESET}' for more information on a command.")


def main(argv: Optional[List[str]] = None) -> None:
    argv = sys.argv[1:] if argv is None else argv

    parser = argparse.ArgumentParser(
        description="Pyker - Simple Python Process Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,
    )
    subparsers = parser.add_subparsers(dest="command")

    start_parser = subparsers.add_parser("start", help="Start a new process")
    start_parser.add_argument("name", help="Process name")
    start_parser.add_argument("script", help="Python script path")
    start_parser.add_argument("--auto-restart", action="store_true", help="Auto restart on failure")
    start_parser.add_argument("--venv", help="Virtual environment path")
    start_parser.add_argument("--on-boot", action="store_true", help="Also start on boot/login")

    stop_parser = subparsers.add_parser("stop", help="Stop a process")
    stop_parser.add_argument("name")

    restart_parser = subparsers.add_parser("restart", help="Restart a process")
    restart_parser.add_argument("name")

    delete_parser = subparsers.add_parser("delete", help="Delete a process")
    delete_parser.add_argument("name")

    subparsers.add_parser("list", help="List all processes")

    logs_parser = subparsers.add_parser("logs", help="Show process logs")
    logs_parser.add_argument("name")
    logs_parser.add_argument("-n", "--lines", type=int, default=50)
    logs_parser.add_argument("-f", "--follow", action="store_true")

    info_parser = subparsers.add_parser("info", help="Show process information")
    info_parser.add_argument("name", nargs="?")

    enable_parser = subparsers.add_parser("enable", help="Enable start on boot")
    enable_parser.add_argument("name")
    disable_parser = subparsers.add_parser("disable", help="Disable start on boot")
    disable_parser.add_argument("name")

    subparsers.add_parser("startup", help="Install OS boot/login hook")
    subparsers.add_parser("unstartup", help="Remove OS boot/login hook")
    subparsers.add_parser("resurrect", help="Start all on-boot processes")
    subparsers.add_parser("watch", help="Run auto-restart watcher in foreground")
    subparsers.add_parser("uninstall", help="Uninstall Pyker completely")

    if not argv or (len(argv) == 1 and argv[0] in ("-h", "--help", "help")):
        _print_help()
        return

    try:
        args = parser.parse_args(argv)
    except SystemExit:
        print(f"\n{Colors.RED}[ERROR]{Colors.RESET} Invalid command or arguments")
        print(f"Use '{Colors.CYAN}pyker --help{Colors.RESET}' to see available commands.")
        return

    if not args.command:
        print(f"{Colors.RED}[ERROR]{Colors.RESET} No command specified")
        _print_help()
        return

    pyker = ProcessManager()

    if args.command == "start":
        pyker.start(args.name, args.script, args.auto_restart, args.venv, args.on_boot)
    elif args.command == "stop":
        pyker.stop(args.name)
    elif args.command == "restart":
        pyker.restart(args.name)
    elif args.command == "delete":
        pyker.delete(args.name)
    elif args.command == "list":
        pyker.list_processes()
    elif args.command == "logs":
        pyker.logs(args.name, args.lines, args.follow)
    elif args.command == "info":
        pyker.info(args.name)
    elif args.command == "enable":
        pyker.enable(args.name)
    elif args.command == "disable":
        pyker.disable(args.name)
    elif args.command == "startup":
        pyker.startup()
    elif args.command == "unstartup":
        pyker.unstartup()
    elif args.command == "resurrect":
        pyker.resurrect()
    elif args.command == "watch":
        pyker.watcher.run_forever(pyker)
    elif args.command == "uninstall":
        pyker.uninstall()
