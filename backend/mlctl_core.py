#!/usr/bin/env python3
"""Core MLCtl logic — config, token management, restart helpers, and daemon workers."""

import os
import time
import json
import datetime
import requests
from typing import Dict, Any

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
        self.base_url = os.environ.get("ML_BASE_URL", "")
        self.blip_domain = os.environ.get("ML_BLIP_DOMAIN", "")
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

def get_token():
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
    )
    resp.raise_for_status()

    data = resp.json()
    token = data["access_token"]
    expiry = now + data.get("expires_in", 3600) - config.token_buffer

    save_json(CACHE_FILE, {"access_token": token, "expiry": expiry})

    return token


# ================= API =================

def get_status(arn: str):
    token = get_token()
    resp = requests.get(
        f"{config.base_url}/cloudport/medialive/{config.blip_domain}/status",
        params={"arn": arn},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp.raise_for_status()
    return resp.json().get("state", "UNKNOWN")


def restart_api(arn: str):
    token = get_token()
    resp = requests.post(
        f"{config.base_url}/cloudport/medialive/{config.blip_domain}/restart",
        headers={"Authorization": f"Bearer {token}"},
        json={"arn": arn},
    )
    resp.raise_for_status()


# ================= LOGIC =================

def wait_for_running(arn: str, timeout=180):
    start = time.time()

    while time.time() - start < timeout:
        state = get_status(arn)

        if state == "RUNNING":
            return True

        time.sleep(5)

    return False


def restart_with_retry(arn: str, retries=5):
    for i in range(1, retries + 1):
        try:
            restart_api(arn)
        except Exception:
            time.sleep(5)
            continue

        time.sleep(10)

        if wait_for_running(arn):
            return True

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

            success = restart_with_retry(arn)

            jobs = load_jobs()
            jobs[job_id]["status"] = "done" if success else "failed"
            save_jobs(jobs)

            logger.write("SUCCESS" if success else "FAILED")

        except Exception as e:
            logger.write(f"ERROR: {e}")

    os._exit(0)
