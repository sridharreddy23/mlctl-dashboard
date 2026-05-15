#!/usr/bin/env python3

import datetime
import json
import os
import signal
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import boto3
import requests
from botocore.exceptions import ClientError


DEFAULT_REGION = "us-east-1"
DEFAULT_CHANNEL_ARNS = [
    "arn:aws:medialive:us-east-1:149306543115:channel:2238084",
    "arn:aws:medialive:us-east-1:149306543115:channel:771047",
    "arn:aws:medialive:us-east-1:149306543115:channel:363722",
]

AWS_CREDENTIALS_FILE = Path("/tmp/mlctl_aws_credentials.json")
MEDIALIVE_JOBS_FILE = "/tmp/mlctl_medialive_jobs.json"
BACKUP_DIR = Path("/tmp/mlctl_input_backups")


class AwsCredentials:
    def __init__(self):
        stored = load_stored_credentials()
        self.access_key_id = os.environ.get("AWS_ACCESS_KEY_ID") or stored.get("access_key_id", "")
        self.secret_access_key = os.environ.get("AWS_SECRET_ACCESS_KEY") or stored.get("secret_access_key", "")
        self.session_token = os.environ.get("AWS_SESSION_TOKEN") or stored.get("session_token", "")
        self.region = (
            os.environ.get("AWS_REGION")
            or os.environ.get("AWS_DEFAULT_REGION")
            or stored.get("region")
            or DEFAULT_REGION
        )

    def is_configured(self) -> bool:
        return all([self.access_key_id, self.secret_access_key, self.session_token])

    def masked(self) -> Dict[str, Any]:
        return {
            "configured": self.is_configured(),
            "region": self.region,
            "has_access_key": bool(self.access_key_id),
            "has_secret_key": bool(self.secret_access_key),
            "has_session_token": bool(self.session_token),
            "access_key_preview": mask_secret(self.access_key_id),
        }


def mask_secret(value: str) -> Optional[str]:
    if not value:
        return None
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}...{value[-4:]}"


def load_stored_credentials() -> Dict[str, str]:
    if not AWS_CREDENTIALS_FILE.exists():
        return {}

    try:
        with AWS_CREDENTIALS_FILE.open() as f:
            data = json.load(f)
    except Exception:
        return {}

    return {
        "access_key_id": str(data.get("access_key_id", "")).strip(),
        "secret_access_key": str(data.get("secret_access_key", "")).strip(),
        "session_token": str(data.get("session_token", "")).strip(),
        "region": str(data.get("region", "")).strip(),
    }


def save_stored_credentials(creds: "AwsCredentials"):
    if not creds.is_configured():
        return

    data = {
        "access_key_id": creds.access_key_id,
        "secret_access_key": creds.secret_access_key,
        "session_token": creds.session_token,
        "region": creds.region,
    }
    AWS_CREDENTIALS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with AWS_CREDENTIALS_FILE.open("w") as f:
        json.dump(data, f)
    os.chmod(AWS_CREDENTIALS_FILE, 0o600)


def export_credentials(data: Dict[str, str]) -> AwsCredentials:
    os.environ["AWS_ACCESS_KEY_ID"] = data.get("access_key_id", "").strip()
    os.environ["AWS_SECRET_ACCESS_KEY"] = data.get("secret_access_key", "").strip()
    os.environ["AWS_SESSION_TOKEN"] = data.get("session_token", "").strip()
    region = data.get("region", DEFAULT_REGION).strip() or DEFAULT_REGION
    os.environ["AWS_REGION"] = region
    os.environ["AWS_DEFAULT_REGION"] = region
    creds = AwsCredentials()
    save_stored_credentials(creds)
    return creds


def export_shell_commands() -> str:
    creds = AwsCredentials()
    lines = [
        f"export AWS_ACCESS_KEY_ID={shell_quote(creds.access_key_id)}",
        f"export AWS_SECRET_ACCESS_KEY={shell_quote(creds.secret_access_key)}",
        f"export AWS_SESSION_TOKEN={shell_quote(creds.session_token)}",
        f"export AWS_REGION={shell_quote(creds.region)}",
        f"export AWS_DEFAULT_REGION={shell_quote(creds.region)}",
    ]
    return "\n".join(lines)


def shell_quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def credentials_from_data(data: Dict[str, str]) -> AwsCredentials:
    creds = AwsCredentials()
    if data.get("access_key_id"):
        creds.access_key_id = data["access_key_id"].strip()
    if data.get("secret_access_key"):
        creds.secret_access_key = data["secret_access_key"].strip()
    if data.get("session_token"):
        creds.session_token = data["session_token"].strip()
    if data.get("region"):
        creds.region = data["region"].strip()
    return creds


def get_client(creds: AwsCredentials):
    if not creds.is_configured():
        raise ValueError("AWS credentials are not configured")
    return boto3.client(
        "medialive",
        region_name=creds.region,
        aws_access_key_id=creds.access_key_id,
        aws_secret_access_key=creds.secret_access_key,
        aws_session_token=creds.session_token,
    )


def channel_id_from_arn(arn: str) -> str:
    return arn.split(":")[-1].split("/")[-1]


def default_channels() -> List[Dict[str, str]]:
    return [
        {"name": f"MediaLive {channel_id_from_arn(arn)}", "arn": arn, "channel_id": channel_id_from_arn(arn)}
        for arn in DEFAULT_CHANNEL_ARNS
    ]


def load_medialive_jobs() -> Dict[str, Any]:
    if os.path.exists(MEDIALIVE_JOBS_FILE):
        with open(MEDIALIVE_JOBS_FILE) as f:
            return json.load(f)
    return {}


def save_medialive_jobs(jobs: Dict[str, Any]):
    Path(MEDIALIVE_JOBS_FILE).parent.mkdir(parents=True, exist_ok=True)
    with open(MEDIALIVE_JOBS_FILE, "w") as f:
        json.dump(jobs, f, indent=2)


def is_process_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def describe_channel_input(client, channel_id: str) -> Dict[str, str]:
    channel = client.describe_channel(ChannelId=channel_id)
    attachments = channel.get("InputAttachments") or []
    if not attachments:
        raise ValueError("No input is attached to this MediaLive channel")

    input_id = attachments[0].get("InputId")
    if not input_id:
        raise ValueError("Attached input does not contain an InputId")

    input_data = client.describe_input(InputId=input_id)
    sources = input_data.get("Sources") or []
    current_url = sources[0].get("Url", "") if sources else ""

    return {
        "channel_id": channel_id,
        "input_id": input_id,
        "state": channel.get("State", "UNKNOWN"),
        "current_url": current_url,
    }


def precheck_hls(url: str):
    resp = requests.get(url, timeout=12)
    if resp.status_code != 200:
        raise ValueError(f"HLS URL is not reachable: HTTP {resp.status_code}")
    if "#EXTM3U" not in resp.text[:4096]:
        raise ValueError("HLS URL does not look like an M3U playlist")


def backup_url(channel_id: str, current_url: str):
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    (BACKUP_DIR / f"{channel_id}_latest.txt").write_text(current_url)


def rollback_url(channel_id: str) -> str:
    backup_file = BACKUP_DIR / f"{channel_id}_latest.txt"
    if not backup_file.exists():
        raise ValueError("No backup URL exists for this channel")
    return backup_file.read_text().strip()


def wait_for_state(client, channel_id: str, target_state: str, timeout: int, write):
    start = time.time()
    while time.time() - start < timeout:
        state = client.describe_channel(ChannelId=channel_id).get("State", "UNKNOWN")
        write(f"State: {state}")
        if state == target_state:
            return True
        time.sleep(5)
    return False


def update_input_url(
    arn: str,
    target_url: Optional[str],
    mode: str,
    creds: AwsCredentials,
    precheck: bool,
    write,
) -> bool:
    client = get_client(creds)
    channel_id = channel_id_from_arn(arn)

    if mode == "rollback":
        target_url = rollback_url(channel_id)
        write(f"Rolling back to backup URL: {target_url}")

    if not target_url:
        raise ValueError("Target URL is required")

    if precheck:
        write("Prechecking HLS URL")
        precheck_hls(target_url)

    details = describe_channel_input(client, channel_id)
    input_id = details["input_id"]
    current_url = details["current_url"]
    state = details["state"]

    write(f"Channel: {channel_id}")
    write(f"Input: {input_id}")
    write(f"Current URL: {current_url}")

    if current_url == target_url:
        write("URL already matches target")
        return True

    backup_url(channel_id, current_url)
    write("Backed up current URL")

    if state == "RUNNING":
        write("Stopping channel")
        client.stop_channel(ChannelId=channel_id)

    write("Waiting for IDLE")
    if not wait_for_state(client, channel_id, "IDLE", 120, write):
        write("Channel did not reach IDLE within 120 seconds; attempting update with retry")

    updated = False
    last_error = ""
    for attempt in range(1, 13):
        try:
            client.update_input(InputId=input_id, Sources=[{"Url": target_url}])
            updated = True
            write("Input updated")
            break
        except ClientError as exc:
            last_error = str(exc)
            code = exc.response.get("Error", {}).get("Code", "")
            if code == "ConflictException":
                write(f"Channel still stopping, retry {attempt}")
                time.sleep(10)
                continue
            raise

    if not updated:
        raise RuntimeError(f"Failed to update input: {last_error}")

    write("Starting channel")
    client.start_channel(ChannelId=channel_id)
    wait_for_state(client, channel_id, "RUNNING", 150, write)
    write("Channel RUNNING with target input")
    return True


def medialive_worker(
    job_id: str,
    arn: str,
    channel_name: str,
    target_url: Optional[str],
    mode: str,
    delay: float,
    creds_data: Dict[str, str],
    precheck: bool,
):
    log_path = f"/tmp/mlctl_medialive_{job_id}.log"
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
            step = min(30, remaining)
            time.sleep(step)
            remaining -= step

        jobs = load_medialive_jobs()
        if job_id in jobs:
            jobs[job_id]["status"] = "running"
            save_medialive_jobs(jobs)

        write(f"Updating MediaLive input for {channel_name}")
        success = update_input_url(
            arn=arn,
            target_url=target_url,
            mode=mode,
            creds=credentials_from_data(creds_data),
            precheck=precheck,
            write=write,
        )

        jobs = load_medialive_jobs()
        if job_id in jobs:
            jobs[job_id]["status"] = "done" if success else "failed"
            save_medialive_jobs(jobs)
        write("SUCCESS" if success else "FAILED")
    except Exception as exc:
        write(f"ERROR: {exc}")
        jobs = load_medialive_jobs()
        if job_id in jobs:
            jobs[job_id]["status"] = "failed"
            save_medialive_jobs(jobs)

    os._exit(0)
