#!/usr/bin/env python3

import os
import sys
import time
import json
import signal
import datetime
import requests
from pathlib import Path
from typing import List, Optional, Dict, Any
try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

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
JOBS_FILE = "/tmp/mlctl_jobs.json"
CACHE_FILE = "/tmp/ml_token_cache.json"

# ================= TOKEN =================

def get_token():
    config.validate()
    now = int(time.time())

    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE) as f:
            data = json.load(f)
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

    with open(CACHE_FILE, "w") as f:
        json.dump({"access_token": token, "expiry": expiry}, f)

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
        except Exception as e:
            time.sleep(5)
            continue

        time.sleep(10)

        if wait_for_running(arn):
            return True

    return False


# ================= JOB STORAGE =================

def load_jobs() -> Dict[str, Any]:
    if os.path.exists(JOBS_FILE):
        with open(JOBS_FILE) as f:
            return json.load(f)
    return {}


def save_jobs(jobs: Dict[str, Any]):
    Path(JOBS_FILE).parent.mkdir(parents=True, exist_ok=True)
    with open(JOBS_FILE, "w") as f:
        json.dump(jobs, f, indent=2)


def is_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except:
        return False


# ================= DAEMON WORKER =================

def daemon_worker(job_id: str, arn: str, name: str, delay: float):
    log_path = f"/tmp/mlctl_{job_id}.log"

    os.setsid()
    log = open(log_path, "w", buffering=1)

    def write(msg: str):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        log.write(f"[{ts}] {msg}\n")

    def handle_term(signum, frame):
        write("Cancelled before execution")
        os._exit(0)

    signal.signal(signal.SIGTERM, handle_term)

    try:
        remaining = delay
        while remaining > 0:
            time.sleep(min(30, remaining))
            remaining -= 30

        jobs = load_jobs()
        jobs[job_id]["status"] = "running"
        save_jobs(jobs)

        write(f"Restarting {name}")
        write(f"ARN: {arn}")

        success = restart_with_retry(arn)

        jobs = load_jobs()
        jobs[job_id]["status"] = "done" if success else "failed"
        save_jobs(jobs)

        write("SUCCESS" if success else "FAILED")

    except Exception as e:
        write(f"ERROR: {e}")

    os._exit(0)
