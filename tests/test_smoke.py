"""Smoke tests for start/stop/state/resurrect."""

from __future__ import annotations

import json
import time

import pytest

from pyker.manager import ProcessManager
from pyker.store import ProcessStore


@pytest.fixture
def pyker_home(tmp_path):
    store = ProcessStore(root=tmp_path / ".pyker")
    manager = ProcessManager(store=store)
    yield manager
    for name in list(manager.processes):
        manager.stop(name, quiet=True)


@pytest.fixture
def sleeper(tmp_path):
    script = tmp_path / "sleeper.py"
    script.write_text(
        "import time\nwhile True:\n    time.sleep(0.2)\n",
        encoding="utf-8",
    )
    return script


@pytest.fixture
def flaky(tmp_path):
    script = tmp_path / "flaky.py"
    script.write_text("import sys\nsys.exit(1)\n", encoding="utf-8")
    return script


def test_start_stop_updates_state(pyker_home, sleeper):
    mgr = pyker_home
    assert mgr.start("bot", str(sleeper), ensure_watcher=False)
    assert "bot" in mgr.processes
    assert mgr.processes["bot"]["status"] == "running"
    assert mgr.processes["bot"]["pid"]

    state = json.loads(mgr.state_file.read_text(encoding="utf-8"))
    assert state["bot"]["status"] == "running"

    assert mgr.stop("bot")
    assert mgr.processes["bot"]["status"] == "stopped"
    assert mgr.processes["bot"]["pid"] is None
    assert mgr.processes["bot"]["stopped_by_user"] is True


def test_resurrect_starts_on_boot_processes(pyker_home, sleeper):
    mgr = pyker_home
    assert mgr.start("bootbot", str(sleeper), on_boot=True, ensure_watcher=False)
    pid = mgr.processes["bootbot"]["pid"]
    assert mgr.stop("bootbot")

    assert mgr.resurrect()
    mgr.update_process_status("bootbot")
    assert mgr.processes["bootbot"]["status"] == "running"
    assert mgr.processes["bootbot"]["pid"] != pid
    assert mgr.processes["bootbot"]["on_boot"] is True

    mgr.delete("bootbot")


def test_auto_restart_flag_and_watcher_tick(pyker_home, flaky):
    mgr = pyker_home
    assert mgr.start("flaky", str(flaky), auto_restart=True, ensure_watcher=False)
    time.sleep(0.3)
    mgr.update_process_status("flaky")
    assert mgr.processes["flaky"].get("auto_restart") is True

    mgr.watcher._tick(mgr)
    assert mgr.processes["flaky"]["stopped_by_user"] is False
    assert mgr.processes["flaky"].get("auto_restart") is True

    mgr.processes["flaky"]["stopped_by_user"] = True
    mgr._save_state()
    mgr.stop("flaky", quiet=True)


def test_user_stop_skips_auto_restart(pyker_home, sleeper):
    mgr = pyker_home
    assert mgr.start("keep", str(sleeper), auto_restart=True, ensure_watcher=False)
    assert mgr.stop("keep")
    assert mgr.processes["keep"]["stopped_by_user"] is True

    before = mgr.processes["keep"].get("start_time")
    mgr.watcher._tick(mgr)
    assert mgr.processes["keep"]["status"] == "stopped"
    assert mgr.processes["keep"].get("start_time") == before
