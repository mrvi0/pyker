"""Persistent process state and config under ~/.pyker."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional


DEFAULT_CONFIG: Dict[str, Any] = {
    "log_rotation": {
        "enabled": True,
        "max_size_mb": 10,
        "max_files": 5,
    },
    "process_check_interval": 5,
    "auto_cleanup_stopped": False,
    "watcher_interval": 3,
}


class ProcessStore:
    """Load/save processes.json and config.json."""

    def __init__(self, root: Optional[Path] = None):
        self.root = Path(root) if root else Path.home() / ".pyker"
        self.state_file = self.root / "processes.json"
        self.config_file = self.root / "config.json"
        self.logs_dir = self.root / "logs"
        self.watcher_pid_file = self.root / "watcher.pid"
        self.ensure_dirs()
        self.config = self.load_config()
        self.processes: Dict[str, Dict[str, Any]] = self.load_state()

    def ensure_dirs(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def load_state(self) -> Dict[str, Dict[str, Any]]:
        if not self.state_file.exists():
            return {}
        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except (OSError, json.JSONDecodeError, TypeError):
            return {}

    def save_state(self) -> None:
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(self.processes, f, indent=2, ensure_ascii=False)

    def reload_state(self) -> None:
        self.processes = self.load_state()

    def load_config(self) -> Dict[str, Any]:
        config = dict(DEFAULT_CONFIG)
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                if isinstance(loaded, dict):
                    for key, value in DEFAULT_CONFIG.items():
                        if key not in loaded:
                            loaded[key] = value
                        elif key == "log_rotation" and isinstance(value, dict):
                            merged = dict(value)
                            merged.update(loaded.get("log_rotation") or {})
                            loaded["log_rotation"] = merged
                    config = loaded
            except (OSError, json.JSONDecodeError, TypeError):
                pass
        self.save_config(config)
        return config

    def save_config(self, config: Dict[str, Any]) -> None:
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
