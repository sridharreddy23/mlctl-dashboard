#!/bin/bash

# MLCtl Dashboard - Simple SFTP Upload & Deploy
# Usage: ./upload-to-server.sh [port]
# Example: ./upload-to-server.sh 7654

set -e

REMOTE_USER="amagi"
REMOTE_HOST="10.0.33.81"
PORT="${1:-7654}"  # Default port 7654, or use first argument
LOCAL_PATH="/home/prs/Desktop/mlctl-dashboard"

echo "════════════════════════════════════════════════════════════════"
echo "  MLCtl Dashboard - SFTP Upload & Deploy"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "📍 Configuration:"
echo "   Remote: $REMOTE_USER@$REMOTE_HOST"
echo "   Port: $PORT"
echo ""

# Verify we're in the right directory
if [ ! -f "$LOCAL_PATH/backend/main.py" ]; then
    echo "❌ Error: Not in mlctl-dashboard directory"
    echo "   Expected: $LOCAL_PATH/backend/main.py"
    exit 1
fi

# Verify frontend is built
if [ ! -d "$LOCAL_PATH/frontend/dist" ]; then
    echo "⚠️  Frontend not built. Building now..."
    cd "$LOCAL_PATH/frontend"
    npm run build
    cd "$LOCAL_PATH"
fi

# Step 1: Upload entire directory via SFTP
echo "📦 Step 1: Uploading mlctl-dashboard directory..."
cd /home/prs/Desktop

sftp -b /dev/stdin "$REMOTE_USER@$REMOTE_HOST" << 'SFTPCMDS'
put -r mlctl-dashboard/
bye
SFTPCMDS

echo "✅ Files uploaded"

# Step 2: Setup on remote server
echo ""
echo "⚙️  Step 2: Setting up on remote server..."
ssh "$REMOTE_USER@$REMOTE_HOST" << SETUP
cd ~/mlctl-dashboard/backend

# Create virtual environment
echo "   Creating Python venv..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "   Installing dependencies..."
pip install -q -r requirements.txt

# Update port
echo "   Configuring port $PORT..."
sed -i "s/port=8000/port=$PORT/" main.py

cd ..

# Start application
echo "   Starting application..."
nohup bash -c 'source backend/venv/bin/activate && python3 backend/main.py' > app.log 2>&1 &

sleep 2

# Verify
if ps aux | grep -q "[p]ython3 backend/main.py"; then
    echo "✅ Application started successfully"
else
    echo "⚠️  Warning: Application may not have started. Check logs:"
    echo "   tail -f ~/mlctl-dashboard/app.log"
fi

SETUP

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✨ Deployment Complete!"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "🌐 Access your application at:"
echo "   http://10.0.33.81:$PORT"
echo ""
echo "📝 Next Steps:"
echo "   1. Open browser: http://10.0.33.81:$PORT"
echo "   2. Go to Settings tab"
echo "   3. Configure API credentials (or rely on bashrc env vars)"
echo "   4. Click Reload Channels"
echo ""
echo "💻 Useful SSH Commands:"
echo "   View logs:        tail -f ~/mlctl-dashboard/app.log"
echo "   Stop app:         pkill -f 'python3 main.py'"
echo "   Check running:    ps aux | grep python"
echo "   Check port:       netstat -tlnp | grep $PORT"
echo "   Test API:         curl http://localhost:$PORT/api/health"
echo ""
echo "════════════════════════════════════════════════════════════════"
