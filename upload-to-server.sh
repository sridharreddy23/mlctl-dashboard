#!/bin/bash

# MLCtl Dashboard - SFTP Upload Script
# Usage: ./upload-to-server.sh [port]
# Example: ./upload-to-server.sh 7654

set -e

REMOTE_USER="prs"
REMOTE_HOST="10.0.33.81"
PORT="${1:-7654}"  # Default port 7654, or use first argument
REMOTE_PATH="/home/$REMOTE_USER/mlctl-dashboard"
LOCAL_PATH="/home/prs/Desktop/mlctl-dashboard"

echo "════════════════════════════════════════════════════════════════"
echo "  MLCtl Dashboard - SFTP Upload & Deploy"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "📍 Configuration:"
echo "   Remote: $REMOTE_USER@$REMOTE_HOST"
echo "   Path: $REMOTE_PATH"
echo "   Port: $PORT"
echo ""

# Verify frontend is built
if [ ! -d "$LOCAL_PATH/frontend/dist" ]; then
    echo "⚠️  Frontend not built. Building now..."
    cd "$LOCAL_PATH/frontend"
    npm run build
    cd "$LOCAL_PATH"
fi

# Step 1: Upload via SFTP
echo "📦 Step 1: Uploading files via SFTP..."
sftp -b /dev/stdin "$REMOTE_USER@$REMOTE_HOST" << 'SFTPCMDS'
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

echo "✅ Files uploaded"

# Step 2: Setup on remote server
echo ""
echo "⚙️  Step 2: Setting up on remote server..."
ssh "$REMOTE_USER@$REMOTE_HOST" << SETUP
cd $REMOTE_PATH/backend

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
    echo "   ssh $REMOTE_USER@$REMOTE_HOST"
    echo "   tail -f $REMOTE_PATH/app.log"
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
echo "   3. Configure API credentials if needed"
echo "   4. Click Reload Channels"
echo ""
echo "💻 SSH Commands:"
echo "   View logs:  ssh $REMOTE_USER@$REMOTE_HOST 'tail -f $REMOTE_PATH/app.log'"
echo "   Stop app:   ssh $REMOTE_USER@$REMOTE_HOST 'pkill -f \"python3 main.py\"'"
echo "   Check status: ssh $REMOTE_USER@$REMOTE_HOST 'ps aux | grep python'"
echo ""
echo "════════════════════════════════════════════════════════════════"
