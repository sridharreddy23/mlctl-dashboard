#!/usr/bin/env python3
"""MLCtl Dashboard API — FastAPI application with Pydantic request models."""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
import json
import os
import time
import datetime
import multiprocessing

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root if present
load_dotenv(Path(__file__).parent.parent / ".env")

from mlctl_core import (
    config, get_token, get_status, restart_api,
    load_jobs, save_jobs, is_alive, daemon_worker,
    MLCtlConfig, LOGS_DIR,
)
from medialive_addon import (
    AwsCredentials,
    channel_id_from_arn,
    credentials_from_data,
    describe_channel_input,
    export_credentials,
    export_shell_commands,
    get_client,
    is_process_alive,
    load_medialive_jobs,
    medialive_worker,
    save_medialive_jobs,
    LOGS_DIR as ML_LOGS_DIR,
)
from utils import format_time_until

app = FastAPI(title="MLCtl Dashboard API", version="1.1.0")

# CORS middleware — restrict to known origins
ALLOWED_ORIGINS = os.environ.get(
    "MLCTL_CORS_ORIGINS",
    "http://localhost:8000,http://localhost:5173,http://localhost:7500"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in ALLOWED_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ================= PYDANTIC REQUEST MODELS =================

class ConfigUpdate(BaseModel):
    client_id: str = ""
    client_secret: str = ""
    base_url: str = ""
    blip_domain: str = ""


class ScheduleRequest(BaseModel):
    channel_name: str = ""
    arn: str
    scheduled_time: str
    timezone: str = "Asia/Kolkata"


class AwsCredentialsUpdate(BaseModel):
    access_key_id: str = ""
    secret_access_key: str = ""
    session_token: str = ""
    region: str = "us-east-1"


class MediaLiveInputDetailsRequest(BaseModel):
    arn: str
    access_key_id: str = ""
    secret_access_key: str = ""
    session_token: str = ""
    region: str = "us-east-1"


class MediaLiveScheduleRequest(BaseModel):
    arn: str
    channel_name: str = ""
    mode: str = "update"
    target_url: str = ""
    scheduled_time: str
    timezone: str = "Asia/Kolkata"
    precheck: bool = True
    access_key_id: str = ""
    secret_access_key: str = ""
    session_token: str = ""
    region: str = "us-east-1"


# ================= CONFIG ENDPOINTS =================

@app.get("/api/config")
def get_config():
    """Get current configuration status"""
    return {
        "configured": config.is_configured(),
        "base_url": config.base_url if config.base_url else None,
        "blip_domain": config.blip_domain if config.blip_domain else None,
        "has_client_id": bool(config.client_id),
        "has_client_secret": bool(config.client_secret),
    }

@app.post("/api/config")
def update_config(data: ConfigUpdate):
    """Update configuration (sets environment variables)"""
    os.environ["ML_CLIENT_ID"] = data.client_id
    os.environ["ML_CLIENT_SECRET"] = data.client_secret
    os.environ["ML_BASE_URL"] = data.base_url
    os.environ["ML_BLIP_DOMAIN"] = data.blip_domain

    # Reload config
    global config
    config = MLCtlConfig()

    return {"status": "ok", "configured": config.is_configured()}

# ================= CHANNELS ENDPOINTS =================

CHANNELS_CONFIG_PATH = "~/bin/config/channels.json"


def load_channels_config() -> List[Dict[str, str]]:
    """Load channels from config file."""
    try:
        path = os.path.expanduser(CHANNELS_CONFIG_PATH)
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail="Channels config file not found")

        with open(path) as f:
            channels = json.load(f)

        return channels
    except HTTPException:
        raise
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Channels config file not found at {CHANNELS_CONFIG_PATH}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/channels")
def get_channels() -> List[Dict[str, str]]:
    """Load channels from config file."""
    return load_channels_config()

# ================= MEDIALIVE INPUT ADD-ON ENDPOINTS =================

@app.get("/api/medialive/aws-credentials")
def get_aws_credentials():
    """Get AWS credential status for the MediaLive input add-on."""
    return AwsCredentials().masked()

@app.post("/api/medialive/aws-credentials")
def update_aws_credentials(data: AwsCredentialsUpdate):
    """Export AWS credentials into the backend process environment."""
    creds = export_credentials(data.dict())
    if not creds.is_configured():
        raise HTTPException(
            status_code=400,
            detail="AWS access key, secret key, and session token are required",
        )
    return creds.masked()

@app.get("/api/medialive/aws-credentials/export")
def get_aws_credentials_export():
    """Return shell export commands for the configured AWS credentials."""
    creds = AwsCredentials()
    if not creds.is_configured():
        raise HTTPException(status_code=400, detail="AWS credentials are not configured")
    return {"commands": export_shell_commands()}

@app.get("/api/medialive/channels")
def get_medialive_channels() -> List[Dict[str, str]]:
    """Get MediaLive channels for the input URL add-on from channels config."""
    channels = []
    for channel in load_channels_config():
        arn = channel.get("arn", "")
        if ":medialive:" not in arn or ":channel" not in arn:
            continue

        channels.append({
            **channel,
            "channel_id": channel.get("channel_id") or channel_id_from_arn(arn),
        })

    return channels

@app.post("/api/medialive/input-details")
def get_medialive_input_details(data: MediaLiveInputDetailsRequest):
    """Describe the first input attached to a MediaLive channel."""
    try:
        if not data.arn:
            raise HTTPException(status_code=400, detail="Channel ARN is required")
        creds = credentials_from_data(data.dict())
        client = get_client(creds)
        channel_id = data.arn.split(":")[-1].split("/")[-1]
        return describe_channel_input(client, channel_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/medialive/schedule-input-url")
def schedule_medialive_input_url(data: MediaLiveScheduleRequest):
    """Schedule a MediaLive input URL update or rollback."""
    try:
        channel_name = data.channel_name or data.arn

        if not data.arn:
            raise HTTPException(status_code=400, detail="Channel ARN is required")
        if data.mode not in ["update", "rollback"]:
            raise HTTPException(status_code=400, detail="Mode must be update or rollback")
        if data.mode == "update" and not data.target_url:
            raise HTTPException(status_code=400, detail="Target HLS URL is required")

        creds = credentials_from_data(data.dict())
        if not creds.is_configured():
            raise HTTPException(
                status_code=400,
                detail="AWS access key, secret key, and session token are required",
            )

        try:
            zone = ZoneInfo(data.timezone)
            dt = datetime.datetime.fromisoformat(data.scheduled_time)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=zone)
            now = datetime.datetime.now(datetime.timezone.utc)
            if dt.astimezone(datetime.timezone.utc) < now:
                raise HTTPException(status_code=400, detail="Scheduled time is in the past")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid datetime: {str(e)}")

        delay = (dt.astimezone(datetime.timezone.utc) - datetime.datetime.now(datetime.timezone.utc)).total_seconds()
        if delay <= 0:
            raise HTTPException(status_code=400, detail="Scheduled time is in the past")

        job_id = f"mlinput_{int(time.time())}"
        jobs = load_medialive_jobs()
        jobs[job_id] = {
            "name": channel_name,
            "arn": data.arn,
            "mode": data.mode,
            "target_url": data.target_url if data.mode == "update" else "",
            "pid": None,
            "time": dt.isoformat(),
            "status": "waiting",
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
        save_medialive_jobs(jobs)

        creds_data = {
            "access_key_id": creds.access_key_id,
            "secret_access_key": creds.secret_access_key,
            "session_token": creds.session_token,
            "region": creds.region,
        }

        # Use multiprocessing instead of os.fork() — safer with ASGI servers
        p = multiprocessing.Process(
            target=medialive_worker,
            args=(job_id, data.arn, channel_name, data.target_url, data.mode, delay, creds_data, data.precheck),
            daemon=True,
        )
        p.start()

        jobs = load_medialive_jobs()
        jobs[job_id]["pid"] = p.pid
        save_medialive_jobs(jobs)

        return {
            "job_id": job_id,
            "status": "scheduled",
            "scheduled_time": dt.isoformat(),
            "delay_seconds": delay,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/medialive/jobs")
def list_medialive_jobs() -> List[Dict[str, Any]]:
    """Get MediaLive input URL jobs."""
    jobs = load_medialive_jobs()
    result = []

    for job_id, job in jobs.items():
        status = job.get("status", "unknown")
        if status == "waiting" and not is_process_alive(job.get("pid", 0)):
            status = "failed"

        result.append({
            "id": job_id,
            "name": job.get("name", ""),
            "arn": job.get("arn", ""),
            "mode": job.get("mode", "update"),
            "target_url": job.get("target_url", ""),
            "status": status,
            "time": job.get("time", ""),
            "time_until": format_time_until(job.get("time", "")),
            "pid": job.get("pid"),
        })

    return result

@app.post("/api/medialive/jobs/{job_id}/cancel")
def cancel_medialive_job(job_id: str):
    """Cancel a scheduled MediaLive input URL job."""
    jobs = load_medialive_jobs()
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    pid = jobs[job_id].get("pid")
    if pid and is_process_alive(pid):
        try:
            os.kill(pid, 15)
        except OSError:
            pass

    jobs[job_id]["status"] = "cancelled"
    save_medialive_jobs(jobs)
    return {"status": "cancelled", "job_id": job_id}

@app.get("/api/medialive/jobs/{job_id}/logs")
def get_medialive_logs(job_id: str):
    """Get MediaLive input URL job logs."""
    log_path = os.path.join(str(ML_LOGS_DIR), f"mlctl_medialive_{job_id}.log")
    if not os.path.exists(log_path):
        return {"logs": "", "exists": False}
    try:
        with open(log_path) as f:
            logs = f.read()
        return {"logs": logs, "exists": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ================= STATUS ENDPOINTS =================

@app.get("/api/status/{arn:path}")
def channel_status(arn: str):
    """Get current status of a channel"""
    try:
        status = get_status(arn)
        return {"arn": arn, "status": status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ================= SCHEDULE ENDPOINTS =================

@app.post("/api/schedule")
def schedule_restart(data: ScheduleRequest):
    """Schedule a channel restart"""
    try:
        # Validate configuration
        config.validate()

        # Parse and validate datetime
        try:
            zone = ZoneInfo(data.timezone)
            dt = datetime.datetime.fromisoformat(data.scheduled_time)

            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=zone)

            now = datetime.datetime.now(datetime.timezone.utc)
            if dt.astimezone(datetime.timezone.utc) < now:
                raise HTTPException(status_code=400, detail="Scheduled time is in the past")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid datetime: {str(e)}")

        # Calculate delay in seconds
        delay = (dt.astimezone(datetime.timezone.utc) -
                datetime.datetime.now(datetime.timezone.utc)).total_seconds()

        if delay <= 0:
            raise HTTPException(status_code=400, detail="Scheduled time is in the past")

        # Create job
        job_id = f"job_{int(time.time())}"
        jobs = load_jobs()
        jobs[job_id] = {
            "name": data.channel_name,
            "arn": data.arn,
            "pid": None,
            "time": dt.isoformat(),
            "status": "waiting",
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        save_jobs(jobs)

        # Use multiprocessing instead of os.fork() — safer with ASGI servers
        p = multiprocessing.Process(
            target=daemon_worker,
            args=(job_id, data.arn, data.channel_name, delay),
            daemon=True,
        )
        p.start()

        jobs = load_jobs()
        jobs[job_id]["pid"] = p.pid
        save_jobs(jobs)

        return {
            "job_id": job_id,
            "status": "scheduled",
            "scheduled_time": dt.isoformat(),
            "delay_seconds": delay
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ================= JOBS ENDPOINTS =================

@app.get("/api/jobs")
def list_jobs() -> List[Dict[str, Any]]:
    """Get all jobs"""
    jobs = load_jobs()
    result = []

    for job_id, job in jobs.items():
        name = job.get("name") or job.get("arn", "").split(":")[-1]
        status = job.get("status", "unknown")

        # Check if process is still alive
        if status == "waiting" and not is_alive(job.get("pid", 0)):
            status = "failed"

        result.append({
            "id": job_id,
            "name": name,
            "arn": job.get("arn", ""),
            "status": status,
            "time": job.get("time", ""),
            "time_until": format_time_until(job.get("time", "")),
            "pid": job.get("pid")
        })

    return result

@app.get("/api/jobs/{job_id}")
def get_job(job_id: str) -> Dict[str, Any]:
    """Get specific job details"""
    jobs = load_jobs()
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]

    name = job.get("name") or job.get("arn", "").split(":")[-1]
    status = job.get("status", "unknown")

    if status == "waiting" and not is_alive(job.get("pid", 0)):
        status = "failed"

    return {
        "id": job_id,
        "name": name,
        "arn": job.get("arn", ""),
        "status": status,
        "time": job.get("time", ""),
        "time_until": format_time_until(job.get("time", "")),
        "pid": job.get("pid")
    }

@app.post("/api/jobs/{job_id}/cancel")
def cancel_job(job_id: str):
    """Cancel a scheduled job"""
    jobs = load_jobs()
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]
    pid = job.get("pid")

    if pid and is_alive(pid):
        try:
            os.kill(pid, 15)  # SIGTERM
        except OSError:
            pass

    job["status"] = "cancelled"
    save_jobs(jobs)

    return {"status": "cancelled", "job_id": job_id}

# ================= LOGS ENDPOINTS =================

@app.get("/api/jobs/{job_id}/logs")
def get_logs(job_id: str):
    """Get job logs"""
    log_path = os.path.join(str(LOGS_DIR), f"mlctl_{job_id}.log")

    if not os.path.exists(log_path):
        return {"logs": "", "exists": False}

    try:
        with open(log_path) as f:
            logs = f.read()
        return {"logs": logs, "exists": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ================= HEALTH ENDPOINTS =================

@app.get("/api/health")
def health():
    """Health check"""
    return {
        "status": "ok",
        "configured": config.is_configured()
    }

# ================= BULK CHANNEL STATUS =================

@app.get("/api/channels/status")
def get_all_channel_status():
    """Get live status for all configured channels."""
    channels = load_channels_config()
    results = []
    for ch in channels:
        try:
            status = get_status(ch["arn"])
        except Exception:
            status = "UNKNOWN"
        results.append({**ch, "status": status})
    return results

# ================= PURGE ENDPOINTS =================

class PurgeRequest(BaseModel):
    days: int = 7

@app.post("/api/jobs/purge")
def purge_jobs(data: PurgeRequest):
    """Delete jobs older than N days."""
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=data.days)
    jobs = load_jobs()
    kept = {}
    removed = 0
    for jid, job in jobs.items():
        try:
            created = datetime.datetime.fromisoformat(job.get("created_at", job.get("time", "")))
            if created.tzinfo is None:
                created = created.replace(tzinfo=datetime.timezone.utc)
            if created < cutoff and job.get("status") in ("done", "failed", "cancelled"):
                removed += 1
                continue
        except Exception:
            pass
        kept[jid] = job
    save_jobs(kept)

    ml_jobs = load_medialive_jobs()
    ml_kept = {}
    for jid, job in ml_jobs.items():
        try:
            created = datetime.datetime.fromisoformat(job.get("created_at", job.get("time", "")))
            if created.tzinfo is None:
                created = created.replace(tzinfo=datetime.timezone.utc)
            if created < cutoff and job.get("status") in ("done", "failed", "cancelled"):
                removed += 1
                continue
        except Exception:
            pass
        ml_kept[jid] = job
    save_medialive_jobs(ml_kept)

    return {"removed": removed, "remaining": len(kept) + len(ml_kept)}

# ================= WEBSOCKET LIVE LOGS =================

def _resolve_log_path(job_id: str) -> str:
    """Find the log file for a job (regular or MediaLive)."""
    for prefix, log_dir in [("mlctl_medialive_", str(ML_LOGS_DIR)), ("mlctl_", str(LOGS_DIR))]:
        path = os.path.join(log_dir, f"{prefix}{job_id}.log")
        if os.path.exists(path):
            return path
    # Fallback — try both possible paths
    ml_path = os.path.join(str(ML_LOGS_DIR), f"mlctl_medialive_{job_id}.log")
    reg_path = os.path.join(str(LOGS_DIR), f"mlctl_{job_id}.log")
    return ml_path if job_id.startswith("mlinput_") else reg_path

@app.websocket("/ws/logs/{job_id}")
async def websocket_logs(websocket: WebSocket, job_id: str):
    """Stream job logs in real-time via WebSocket."""
    await websocket.accept()
    log_path = _resolve_log_path(job_id)
    last_size = 0
    try:
        while True:
            if os.path.exists(log_path):
                size = os.path.getsize(log_path)
                if size > last_size:
                    with open(log_path) as f:
                        f.seek(last_size)
                        chunk = f.read()
                        if chunk:
                            await websocket.send_text(chunk)
                    last_size = size
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass

# ================= FRONTEND =================

frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
assets_dir = frontend_dist / "assets"

if assets_dir.exists():
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

@app.get("/")
def root():
    """Serve frontend"""
    frontend_path = frontend_dist / "index.html"
    if frontend_path.exists():
        return FileResponse(frontend_path)
    return {"message": "Frontend not built yet. Run: cd frontend && npm install && npm run build"}

@app.get("/{full_path:path}")
def spa_fallback(full_path: str):
    """Serve frontend routes for the single page app."""
    frontend_path = frontend_dist / "index.html"
    if frontend_path.exists():
        return FileResponse(frontend_path)
    return {"message": "Frontend not built yet. Run: cd frontend && npm install && npm run build"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
