#!/usr/bin/env python3
"""Core MLCtl logic — config, token management, restart helpers, and daemon workers."""

import os
import time
import json
import datetime
import threading
import requests
from typing import Dict, Any, Union

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

from utils import (
    APP_DIR, load_json, save_json, is_process_alive,
    register_term_handler, JobLogger, format_time_until,
)


# ================= ENV =================

class MLCtlConfig:
    def __init__(self):
        self.client_id = os.environ.get("ML_CLIENT_ID", "")
        self.client_secret = os.environ.get("ML_CLIENT_SECRET", "")
        self.base_url = os.environ.get("ML_BASE_URL", "").rstrip("/")
        self.blip_domain = os.environ.get("ML_BLIP_DOMAIN", "").strip("/")
        self.token_buffer = 60

    def is_configured(self) -> bool:
        return all([self.client_id, self.client_secret, self.base_url, self.blip_domain])

    def validate(self):
        if not self.is_configured():
            missing = [var for var in ["ML_CLIENT_ID", "ML_CLIENT_SECRET", "ML_BASE_URL", "ML_BLIP_DOMAIN"]
                      if not os.environ.get(var)]
            raise ValueError(f"Missing environment variables: {', '.join(missing)}")


config = MLCtlConfig()

# State files now live in ~/.mlctl/ (secured directory) instead of /tmp
JOBS_FILE = str(APP_DIR / "mlctl_jobs.json")
CACHE_FILE = str(APP_DIR / "ml_token_cache.json")
LOGS_DIR = str(APP_DIR / "logs")
os.makedirs(LOGS_DIR, exist_ok=True)


# ================= TOKEN =================

_token_lock = threading.Lock()

def get_token():
    with _token_lock:
        config.validate()
        now = int(time.time())

        if os.path.exists(CACHE_FILE):
            data = load_json(CACHE_FILE)
            if now < data.get("expiry", 0):
                return data["access_token"]

        resp = requests.post(
            f"{config.base_url}/token/generate",
            auth=(config.client_id, config.client_secret),
            data={"grant_type": "client_credentials"},
            timeout=15,
        )
        resp.raise_for_status()

        data = resp.json()
        token = data["access_token"]
        expiry = now + data.get("expires_in", 3600) - config.token_buffer

        save_json(CACHE_FILE, {"access_token": token, "expiry": expiry})

        return token


# ================= API =================

# MediaLive states returned by Cloudport status API
MEDIALIVE_STATES = frozenset({
    "RUNNING", "IDLE", "STARTING", "STOPPING", "UNKNOWN",
})


def parse_channel_state(payload: Union[Dict[str, Any], str, None]) -> str:
    """Normalize Cloudport status JSON to a MediaLive state string."""
    if payload is None:
        return "UNKNOWN"
    if isinstance(payload, str):
        return payload.strip().upper() or "UNKNOWN"
    if not isinstance(payload, dict):
        return "UNKNOWN"

    for key in (
        "state", "status", "channelState", "channel_state",
        "State", "Status", "mediaLiveChannelState",
    ):
        if key not in payload or payload[key] in (None, ""):
            continue
        value = payload[key]
        if isinstance(value, dict):
            return parse_channel_state(value)
        normalized = str(value).strip().upper()
        if normalized:
            return normalized

    if "data" in payload and isinstance(payload["data"], dict):
        return parse_channel_state(payload["data"])
    if "result" in payload and isinstance(payload["result"], dict):
        return parse_channel_state(payload["result"])

    return "UNKNOWN"


def get_status_with_token(arn: str, token: str, timeout: int = 12) -> str:
    """Fetch channel status using a pre-fetched OAuth token (for parallel bulk refresh)."""
    if not arn or not arn.strip():
        raise ValueError("Channel ARN is required")

    url = f"{config.base_url}/cloudport/medialive/{config.blip_domain}/status"
    resp = requests.get(
        url,
        params={"arn": arn.strip()},
        headers={"Authorization": f"Bearer {token}"},
        timeout=timeout,
    )
    resp.raise_for_status()
    state = parse_channel_state(resp.json())
    if state not in MEDIALIVE_STATES:
        return state if state else "UNKNOWN"
    return state


def get_status(arn: str) -> str:
    """GET /cloudport/medialive/<blip_domain>/status?arn=<channel_arn>"""
    config.validate()
    token = get_token()
    return get_status_with_token(arn, token)


def restart_api(arn: str):
    token = get_token()
    resp = requests.post(
        f"{config.base_url}/cloudport/medialive/{config.blip_domain}/restart",
        headers={"Authorization": f"Bearer {token}"},
        json={"arn": arn},
        timeout=45,  # API can be slow to respond; 15s was causing false timeouts
    )
    resp.raise_for_status()


# ================= LOGIC =================

# MediaLive channels can take 5-8 min to cycle STOPPING → IDLE → STARTING → RUNNING.
# Give each wait up to 10 minutes so we never time-out a healthy restart.
_RUNNING_TIMEOUT = 600  # seconds
_TRANSITION_STATES = frozenset({"STOPPING", "STARTING", "UNKNOWN"})


def wait_for_running(arn: str, timeout: int = _RUNNING_TIMEOUT, write=None) -> bool:
    """Poll until the channel is RUNNING or timeout is exceeded.

    During STOPPING / STARTING the channel is still in a valid transition;
    we never give up while the channel is actively moving through states.
    Pass a ``write`` callable to get live state-change log entries.
    """
    _log = write if callable(write) else lambda msg: None
    start = time.time()
    last_state = ""

    while time.time() - start < timeout:
        try:
            state = get_status(arn)
        except Exception as exc:
            # Transient API error — keep waiting
            _log(f"Status check error (retrying): {exc}")
            time.sleep(10)
            continue

        if state != last_state:
            _log(f"Channel state: {state}")
            last_state = state

        if state == "RUNNING":
            return True

        # Channel is still transitioning — keep polling
        time.sleep(10)

    _log(f"Timed out after {timeout}s waiting for RUNNING (last state: {last_state})")
    return False


def restart_with_retry(arn: str, retries: int = 3, write=None) -> bool:
    """Call the restart API and wait for the channel to be RUNNING.

    Timeout handling: the restart API sometimes takes >15s to respond but
    the request IS accepted on the server side. On a ReadTimeout we treat
    the restart as likely triggered and go straight to polling instead of
    retrying (which would cause 400s because the channel is already stopping).
    """
    _log = write if callable(write) else lambda msg: None
    for i in range(1, retries + 1):
        _log(f"Restart attempt {i}/{retries}")
        api_accepted = False
        try:
            restart_api(arn)
            _log("Restart API call accepted")
            api_accepted = True
        except requests.exceptions.Timeout:
            # Server likely accepted the request but took too long to reply.
            # Go straight to polling — do NOT retry or we'll get 400 (channel already stopping).
            _log("Restart API timed out — assuming request was accepted, polling for RUNNING")
            api_accepted = True
        except Exception as exc:
            _log(f"Restart API error: {exc}")
            if i < retries:
                time.sleep(10)
                continue
            else:
                break

        if api_accepted:
            # Brief pause before polling so the channel has time to begin transitioning
            time.sleep(15)
            if wait_for_running(arn, write=_log):
                return True
            _log(f"Attempt {i} did not reach RUNNING, {'retrying' if i < retries else 'giving up'}")

    return False


# ================= JOB STORAGE =================

def load_jobs() -> Dict[str, Any]:
    return load_json(JOBS_FILE)


def save_jobs(jobs: Dict[str, Any]):
    save_json(JOBS_FILE, jobs)


# Re-export for backward compat
is_alive = is_process_alive


# ================= DAEMON WORKER =================

def daemon_worker(job_id: str, arn: str, name: str, delay: float):
    log_path = os.path.join(LOGS_DIR, f"mlctl_{job_id}.log")

    os.setsid()

    with JobLogger(log_path) as logger:
        register_term_handler(logger.write)

        try:
            remaining = delay
            while remaining > 0:
                time.sleep(min(30, remaining))
                remaining -= 30

            jobs = load_jobs()
            jobs[job_id]["status"] = "running"
            save_jobs(jobs)

            logger.write(f"Restarting {name}")
            logger.write(f"ARN: {arn}")
            logger.write(f"Waiting up to {_RUNNING_TIMEOUT}s for channel to reach RUNNING")

            success = restart_with_retry(arn, write=logger.write)

            jobs = load_jobs()
            jobs[job_id]["status"] = "done" if success else "failed"
            save_jobs(jobs)

            logger.write("SUCCESS" if success else "FAILED")

        except Exception as e:
            logger.write(f"ERROR: {e}")
            jobs = load_jobs()
            if job_id in jobs:
                jobs[job_id]["status"] = "failed"
                save_jobs(jobs)

    os._exit(0)
