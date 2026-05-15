#!/bin/bash

# MLCtl Dashboard Startup Script
set -e

echo "🚀 Starting MLCtl Dashboard..."

# Load environment variables if .env exists
if [ -f .env ]; then
    export $(cat .env | xargs)
    echo "✓ Environment variables loaded"
fi

if command -v python3.8 >/dev/null 2>&1; then
    PYTHON_BIN=python3.8
else
    PYTHON_BIN=python3
fi

echo "🎨 Building frontend..."
cd frontend
npm install
npm run build
cd ..

echo "📦 Starting backend..."
cd backend
$PYTHON_BIN -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
python main.py &
BACKEND_PID=$!
echo "✓ Backend started (PID: $BACKEND_PID)"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "MLCtl Dashboard is running!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📱 App:      http://localhost:8000"
echo "🔧 Backend:  http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Wait for backend process
wait $BACKEND_PID
