#!/usr/bin/env python3

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import List, Optional, Dict, Any
import json
import os
import time
import datetime
try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo
from pathlib import Path

from mlctl_core import (
    config, get_token, get_status, restart_api, 
    load_jobs, save_jobs, is_alive, daemon_worker,
    MLCtlConfig
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
)

app = FastAPI(title="MLCtl Dashboard API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
def update_config(data: dict):
    """Update configuration (sets environment variables)"""
    os.environ["ML_CLIENT_ID"] = data.get("client_id", "")
    os.environ["ML_CLIENT_SECRET"] = data.get("client_secret", "")
    os.environ["ML_BASE_URL"] = data.get("base_url", "")
    os.environ["ML_BLIP_DOMAIN"] = data.get("blip_domain", "")
    
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
def update_aws_credentials(data: dict):
    """Export AWS credentials into the backend process environment."""
    creds = export_credentials(data)
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
def get_medialive_input_details(data: dict):
    """Describe the first input attached to a MediaLive channel."""
    try:
        arn = data.get("arn", "")
        if not arn:
            raise HTTPException(status_code=400, detail="Channel ARN is required")
        creds = credentials_from_data(data)
        client = get_client(creds)
        channel_id = arn.split(":")[-1].split("/")[-1]
        return describe_channel_input(client, channel_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/medialive/schedule-input-url")
def schedule_medialive_input_url(data: dict):
    """Schedule a MediaLive input URL update or rollback."""
    try:
        arn = data.get("arn", "")
        channel_name = data.get("channel_name", "") or arn
        mode = data.get("mode", "update")
        target_url = data.get("target_url", "")
        scheduled_time = data.get("scheduled_time", "")
        timezone = data.get("timezone", "Asia/Kolkata")
        precheck = bool(data.get("precheck", True))

        if not arn:
            raise HTTPException(status_code=400, detail="Channel ARN is required")
        if mode not in ["update", "rollback"]:
            raise HTTPException(status_code=400, detail="Mode must be update or rollback")
        if mode == "update" and not target_url:
            raise HTTPException(status_code=400, detail="Target HLS URL is required")

        creds = credentials_from_data(data)
        if not creds.is_configured():
            raise HTTPException(
                status_code=400,
                detail="AWS access key, secret key, and session token are required",
            )

        try:
            zone = ZoneInfo(timezone)
            dt = datetime.datetime.fromisoformat(scheduled_time)
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
            "arn": arn,
            "mode": mode,
            "target_url": target_url if mode == "update" else "",
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

        pid = os.fork()
        if pid == 0:
            medialive_worker(job_id, arn, channel_name, target_url, mode, delay, creds_data, precheck)
        else:
            jobs = load_medialive_jobs()
            jobs[job_id]["pid"] = pid
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
    now = datetime.datetime.now(datetime.timezone.utc)
    result = []

    for job_id, job in jobs.items():
        status = job.get("status", "unknown")
        if status == "waiting" and not is_process_alive(job.get("pid", 0)):
            status = "failed"

        try:
            dt = datetime.datetime.fromisoformat(job["time"])
            delta = dt.astimezone(datetime.timezone.utc) - now
            secs = int(delta.total_seconds())
            if secs > 0:
                h, r = divmod(secs, 3600)
                time_until = f"in {h}h {r//60}m"
            else:
                h, r = divmod(-secs, 3600)
                time_until = f"{h}h {r//60}m ago"
        except Exception:
            time_until = "-"

        result.append({
            "id": job_id,
            "name": job.get("name", ""),
            "arn": job.get("arn", ""),
            "mode": job.get("mode", "update"),
            "target_url": job.get("target_url", ""),
            "status": status,
            "time": job.get("time", ""),
            "time_until": time_until,
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
        except Exception:
            pass

    jobs[job_id]["status"] = "cancelled"
    save_medialive_jobs(jobs)
    return {"status": "cancelled", "job_id": job_id}

@app.get("/api/medialive/jobs/{job_id}/logs")
def get_medialive_logs(job_id: str):
    """Get MediaLive input URL job logs."""
    log_path = f"/tmp/mlctl_medialive_{job_id}.log"
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
def schedule_restart(data: dict):
    """Schedule a channel restart"""
    try:
        # Validate configuration
        config.validate()
        
        # Parse and validate datetime
        try:
            scheduled_time = data.get("scheduled_time", "")
            timezone = data.get("timezone", "Asia/Kolkata")
            channel_name = data.get("channel_name", "")
            arn = data.get("arn", "")
            
            zone = ZoneInfo(timezone)
            dt = datetime.datetime.fromisoformat(scheduled_time)
            
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
            "name": channel_name,
            "arn": arn,
            "pid": None,
            "time": dt.isoformat(),
            "status": "waiting",
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        save_jobs(jobs)
        
        # Fork daemon process
        pid = os.fork()
        if pid == 0:
            daemon_worker(job_id, arn, channel_name, delay)
        else:
            jobs = load_jobs()
            jobs[job_id]["pid"] = pid
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
    now = datetime.datetime.now(datetime.timezone.utc)
    result = []
    
    for job_id, job in jobs.items():
        name = job.get("name") or job.get("arn", "").split(":")[-1]
        status = job.get("status", "unknown")
        
        # Check if process is still alive
        if status == "waiting" and not is_alive(job.get("pid", 0)):
            status = "failed"
        
        # Calculate time string
        try:
            dt = datetime.datetime.fromisoformat(job["time"])
            delta = dt.astimezone(datetime.timezone.utc) - now
            secs = int(delta.total_seconds())
            
            if secs > 0:
                h, r = divmod(secs, 3600)
                time_until = f"in {h}h {r//60}m"
            else:
                h, r = divmod(-secs, 3600)
                time_until = f"{h}h {r//60}m ago"
        except:
            time_until = "-"
        
        result.append({
            "id": job_id,
            "name": name,
            "arn": job.get("arn", ""),
            "status": status,
            "time": job.get("time", ""),
            "time_until": time_until,
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
    now = datetime.datetime.now(datetime.timezone.utc)
    
    name = job.get("name") or job.get("arn", "").split(":")[-1]
    status = job.get("status", "unknown")
    
    if status == "waiting" and not is_alive(job.get("pid", 0)):
        status = "failed"
    
    try:
        dt = datetime.datetime.fromisoformat(job["time"])
        delta = dt.astimezone(datetime.timezone.utc) - now
        secs = int(delta.total_seconds())
        
        if secs > 0:
            h, r = divmod(secs, 3600)
            time_until = f"in {h}h {r//60}m"
        else:
            h, r = divmod(-secs, 3600)
            time_until = f"{h}h {r//60}m ago"
    except:
        time_until = "-"
    
    return {
        "id": job_id,
        "name": name,
        "arn": job.get("arn", ""),
        "status": status,
        "time": job.get("time", ""),
        "time_until": time_until,
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
        except:
            pass
    
    job["status"] = "cancelled"
    save_jobs(jobs)
    
    return {"status": "cancelled", "job_id": job_id}

# ================= LOGS ENDPOINTS =================

@app.get("/api/jobs/{job_id}/logs")
def get_logs(job_id: str):
    """Get job logs"""
    log_path = f"/tmp/mlctl_{job_id}.log"
    
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
