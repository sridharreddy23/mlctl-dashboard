# MLCtl Dashboard - Manual SSH/SFTP Deployment

## Step-by-Step Deployment Guide

### Prerequisites
- SSH access to 10.0.33.81
- SFTP access (via SSH)
- Environment credentials already in bashrc on remote server
- Python 3 and Node.js installed on remote

---

## Step 1: Prepare Local Files

Navigate to project directory and ensure frontend is built:

```bash
cd /home/prs/Desktop/mlctl-dashboard
npm run build  # Build frontend (if not already built)
```

Verify these files exist:
- `backend/main.py`
- `backend/mlctl_core.py`
- `backend/requirements.txt`
- `frontend/dist/` (built frontend)

---

## Step 2: Connect via SFTP

Open SFTP connection to the server:

```bash
sftp prs@10.0.33.81
```

Create the application directory:

```
mkdir mlctl-dashboard
cd mlctl-dashboard
```

---

## Step 3: Upload Backend Files

```
mkdir backend
put backend/main.py backend/
put backend/mlctl_core.py backend/
put backend/requirements.txt backend/
```

---

## Step 4: Upload Frontend Files

```
mkdir frontend
put -r frontend/dist frontend/
put frontend/package.json frontend/
```

---

## Step 5: Upload Utility Files

```
put start.sh .
bye
```

**Or use this all-in-one SFTP script:**

```bash
sftp prs@10.0.33.81 << EOF
mkdir mlctl-dashboard
cd mlctl-dashboard
mkdir backend
mkdir frontend
put backend/main.py backend/
put backend/mlctl_core.py backend/
put backend/requirements.txt backend/
put -r frontend/dist frontend/
put frontend/package.json frontend/
put start.sh .
bye
EOF
```

---

## Step 6: SSH Into Server & Setup Backend

```bash
ssh prs@10.0.33.81
cd mlctl-dashboard/backend
```

Create Python virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Verify installation:

```bash
python3 -c "import fastapi; print('✓ FastAPI installed')"
```

---

## Step 7: Choose a Port & Configure

Pick a random port (e.g., 7654) and edit main.py:

```bash
cd ~/mlctl-dashboard/backend
nano main.py
```

Find the last lines and change the port:

**Before:**
```python
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**After (using port 7654):**
```python
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7654)
```

Save: Press `Ctrl+X`, then `Y`, then `Enter`

---

## Step 8: Verify Frontend Files

```bash
cd ~/mlctl-dashboard/frontend
ls -la dist/
```

You should see:
- `index.html`
- `assets/` folder

---

## Step 9: Start the Application

### Option A: Background Start (Recommended)

```bash
cd ~/mlctl-dashboard/backend
source venv/bin/activate
nohup python3 main.py > ../app.log 2>&1 &
```

Verify it's running:

```bash
ps aux | grep python | grep main.py
```

View logs:

```bash
tail -f ~/mlctl-dashboard/app.log
```

---

## Step 10: Access the Application

From your local machine, open browser:

```
http://10.0.33.81:7654
```

You should see the MLCtl Dashboard UI!

---

## Step 11: Configure API Credentials

1. Go to **Settings** tab
2. Enter your API credentials (or they'll be auto-loaded from bashrc):
   - Client ID
   - Client Secret
   - Base URL
   - BLIP Domain
3. Click "Save Configuration"
4. Click "Reload Channels"

---

## Verification Commands

### Check if app is running:
```bash
ps aux | grep python | grep main.py
```

### Check the port:
```bash
netstat -tlnp | grep 7654
```

### Test API endpoint:
```bash
curl http://localhost:7654/api/health
```

### View application logs:
```bash
tail -f ~/mlctl-dashboard/app.log
```

---

## Stopping the Application

```bash
pkill -f "python3 main.py"
```

---

## Restarting the Application

```bash
# Stop
pkill -f "python3 main.py"

# Wait 2 seconds
sleep 2

# Start again
cd ~/mlctl-dashboard/backend
source venv/bin/activate
nohup python3 main.py > ../app.log 2>&1 &
```

---

## Troubleshooting

### Port already in use:
```bash
lsof -i :7654
```

### Can't connect to API:
```bash
# Check if running
ps aux | grep python

# Check if port is listening
netstat -tlnp | grep 7654

# Test locally
curl http://localhost:7654/api/health
```

### Permissions denied:
```bash
chmod +x ~/mlctl-dashboard/start.sh
chmod +x ~/mlctl-dashboard/backend/main.py
```

---

## Quick Reference Commands

```bash
# SSH in
ssh prs@10.0.33.81

# Navigate to app
cd ~/mlctl-dashboard

# Check status
ps aux | grep python
netstat -tlnp | grep 7654

# View logs
tail -f app.log

# Stop app
pkill -f "python3 main.py"

# Start app
cd backend && source venv/bin/activate && nohup python3 main.py > ../app.log 2>&1 &
```

---

## All-in-One: SFTP Upload + Setup

**From your local machine:**

```bash
cd /home/prs/Desktop/mlctl-dashboard

# Ensure frontend is built
npm run build

# Upload via SFTP
sftp prs@10.0.33.81 << SFTPCMDS
mkdir mlctl-dashboard
cd mlctl-dashboard
mkdir backend
mkdir frontend
put backend/main.py backend/
put backend/mlctl_core.py backend/
put backend/requirements.txt backend/
put -r frontend/dist frontend/
put frontend/package.json frontend/
put start.sh .
bye
SFTPCMDS

# Setup on remote
ssh prs@10.0.33.81 << SETUP
cd mlctl-dashboard/backend
python3 -m venv venv
source venv/bin/activate
pip install -q -r requirements.txt
sed -i 's/port=8000/port=7654/' main.py
cd ..
nohup bash -c 'source backend/venv/bin/activate && python3 main.py' > app.log 2>&1 &
sleep 2
echo "✅ Application started on port 7654"
ps aux | grep python
SETUP

echo "🌐 Access at: http://10.0.33.81:7654"
```

---

## Done!

Your MLCtl Dashboard is now deployed and accessible at:

```
http://10.0.33.81:7654
```

(Replace 7654 with your chosen port)
