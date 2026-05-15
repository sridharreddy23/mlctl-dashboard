#!/bin/bash

# MLCtl Dashboard Startup Script

echo "🚀 Starting MLCtl Dashboard..."

# Load environment variables if .env exists
if [ -f .env ]; then
    export $(cat .env | xargs)
    echo "✓ Environment variables loaded"
fi

# Start backend
echo "📦 Starting backend..."
cd backend
python3 -m venv venv 2>/dev/null
source venv/bin/activate
pip install -q -r requirements.txt 2>/dev/null
python3 main.py &
BACKEND_PID=$!
echo "✓ Backend started (PID: $BACKEND_PID)"

# Start frontend
echo "🎨 Starting frontend..."
cd ../frontend
npm install >/dev/null 2>&1
npm run dev &
FRONTEND_PID=$!
echo "✓ Frontend started (PID: $FRONTEND_PID)"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "MLCtl Dashboard is running!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📱 Frontend: http://localhost:5173"
echo "🔧 Backend:  http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
