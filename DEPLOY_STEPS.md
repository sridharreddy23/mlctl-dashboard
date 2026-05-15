# MLCtl Dashboard - Deployment for amagi@10.0.33.81

## Quick Deployment (One Command)

```bash
cd /home/prs/Desktop/mlctl-dashboard
chmod +x deploy.sh
./deploy.sh 7654  # Use any random port you want
```

This will:
1. Build frontend
2. Upload entire `mlctl-dashboard/` directory via SFTP
3. Setup Python venv
4. Install dependencies  
5. Configure the port
6. Start the application

---

## Manual Step-by-Step (If script fails)

### Step 1: Build Frontend

```bash
cd /home/prs/Desktop/mlctl-dashboard/frontend
npm run build
```

### Step 2: Upload via SFTP

```bash
cd /home/prs/Desktop
sftp amagi@10.0.33.81
```

In SFTP prompt:
```
put -r mlctl-dashboard/
bye
```

### Step 3: SSH and Setup Backend

```bash
ssh amagi@10.0.33.81
cd ~/mlctl-dashboard/backend
```

Create venv:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 4: Choose Port and Configure

Edit `main.py` to change port:

```bash
nano ~/mlctl-dashboard/backend/main.py
```

Find the last line and change `port=8000` to your port (e.g., `port=7654`):

```python
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7654)
```

Save: `Ctrl+X`, `Y`, `Enter`

### Step 5: Start Application

```bash
cd ~/mlctl-dashboard/backend
source venv/bin/activate
nohup python3 main.py > ../app.log 2>&1 &
```

### Step 6: Verify Running

```bash
ps aux | grep "python3 main.py"
```

Should see your Python process running.

---

## Access Your Application

Open browser:
```
http://10.0.33.81:7654
```

(Replace 7654 with the port you chose)

---

## Useful Commands

### View Application Logs
```bash
ssh amagi@10.0.33.81
tail -f ~/mlctl-dashboard/app.log
```

### Check If Running
```bash
ssh amagi@10.0.33.81
ps aux | grep "python3 main.py"
```

### Check Port
```bash
ssh amagi@10.0.33.81
netstat -tlnp | grep 7654
```

### Test API Health
```bash
ssh amagi@10.0.33.81
curl http://localhost:7654/api/health
```

### Stop Application
```bash
ssh amagi@10.0.33.81
ps aux | grep "python3 main.py"
# Note the PID from output, then:
kill -9 <PID>
```

### Restart Application
```bash
ssh amagi@10.0.33.81
# Stop
ps aux | grep "python3 main.py" | grep -v grep | awk '{print $2}' > /tmp/pid.txt && xargs kill -9 < /tmp/pid.txt 2>/dev/null || true
sleep 2
# Start again
cd ~/mlctl-dashboard/backend
source venv/bin/activate
nohup python3 main.py > ../app.log 2>&1 &
```

---

## Configuration

### API Credentials

They should auto-load from your bashrc environment variables. If not, go to Settings tab in the UI and configure:
- Client ID
- Client Secret  
- Base URL
- BLIP Domain

### Change Port

If you need to change the port later:

```bash
ssh amagi@10.0.33.81
nano ~/mlctl-dashboard/backend/main.py
# Change the port number
# Restart the app
```

---

## Troubleshooting

### Can't upload via SFTP?
- SSH works: `ssh amagi@10.0.33.81`
- SFTP uses same SSH key

### Application won't start?
- Check logs: `tail -f ~/mlctl-dashboard/app.log`
- Check Python version: `python3 --version`
- Check port available: `netstat -tlnp | grep 7654`

### Frontend shows blank?
- Check if built: `ls ~/mlctl-dashboard/frontend/dist/`
- Rebuild: `npm run build` in frontend directory
- Re-upload entire directory

### Can't access from browser?
- Check if running: `ps aux | grep python`
- Check port: `netstat -tlnp | grep 7654`
- Try locally first: `curl http://localhost:7654`
- Check firewall: Port 7654 needs to be open

---

## That's It!

Your MLCtl Dashboard is now deployed and accessible at:

```
http://10.0.33.81:7654
```

(Replace 7654 with your chosen port)

Enjoy! 🚀
