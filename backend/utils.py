#!/usr/bin/env python3
"""Shared utilities for the MLCtl Dashboard backend.

Provides file-locked JSON storage, process helpers, and
a configurable application data directory.
"""

import fcntl
import json
import os
import signal
import datetime
from pathlib import Path
from typing import Any, Dict


# --------------- App data directory ---------------

def get_app_dir() -> Path:
    """Return (and create) the application data directory.

    Uses ``~/.mlctl`` by default, overridable via the
    ``MLCTL_DATA_DIR`` environment variable.
    """
    base = os.environ.get("MLCTL_DATA_DIR", "")
    if base:
        p = Path(base)
    else:
        p = Path.home() / ".mlctl"
    p.mkdir(parents=True, exist_ok=True)
    os.chmod(str(p), 0o700)
    return p


APP_DIR = get_app_dir()


# --------------- File-locked JSON store ---------------

def load_json(path: str) -> Dict[str, Any]:
    """Load a JSON file with a shared (read) lock."""
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r") as f:
            fcntl.flock(f, fcntl.LOCK_SH)
            data = json.load(f)
            fcntl.flock(f, fcntl.LOCK_UN)
            return data
    except (json.JSONDecodeError, IOError):
        return {}


def save_json(path: str, data: Dict[str, Any]) -> None:
    """Save a JSON file with an exclusive (write) lock."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        json.dump(data, f, indent=2)
        fcntl.flock(f, fcntl.LOCK_UN)


# --------------- Process helpers ---------------

def is_process_alive(pid: int) -> bool:
    """Check whether a process with the given PID is still running."""
    if not pid:
        return False
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def register_term_handler(write_fn):
    """Install a SIGTERM handler that logs cancellation and exits."""

    def _handle(signum, frame):
        write_fn("Cancelled before execution")
        os._exit(0)

    signal.signal(signal.SIGTERM, _handle)


# --------------- Logging helper ---------------

class JobLogger:
    """Simple timestamped logger that writes to a file."""

    def __init__(self, path: str):
        self._path = path
        self._file = open(path, "w", buffering=1)

    def write(self, msg: str) -> None:
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self._file.write(f"[{ts}] {msg}\n")

    def close(self) -> None:
        if self._file and not self._file.closed:
            self._file.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


# --------------- Time formatting ---------------

def format_time_until(iso_time: str) -> str:
    """Return a human-readable relative time string like 'in 2h 15m' or '1h 5m ago'."""
    try:
        now = datetime.datetime.now(datetime.timezone.utc)
        dt = datetime.datetime.fromisoformat(iso_time)
        delta = dt.astimezone(datetime.timezone.utc) - now
        secs = int(delta.total_seconds())
        if secs > 0:
            h, r = divmod(secs, 3600)
            return f"in {h}h {r // 60}m"
        else:
            h, r = divmod(-secs, 3600)
            return f"{h}h {r // 60}m ago"
    except Exception:
        return "-"
