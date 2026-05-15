# MLCtl Dashboard - Quick Start Guide

## What's Included

Your professional MLCtl Dashboard is ready to deploy! This is a **complete, production-ready application** with:

✨ **Beautiful, Flawless UI**
- Modern responsive design with Tailwind CSS
- Dark mode support
- Professional card-based layout
- Smooth animations and transitions

🎯 **Full-Featured Application**
- Schedule channel restarts with timezone support
- Real-time job status monitoring
- Live job logs viewer
- Complete job management
- Professional dashboard with statistics

## Installation (30 seconds)

### 1. Set Up Environment Variables

Create a `.env` file in the project root:

```bash
export ML_CLIENT_ID="your-api-client-id"
export ML_CLIENT_SECRET="your-api-client-secret"
export ML_BASE_URL="https://your-api-base-url.com"
export ML_BLIP_DOMAIN="your-blip-domain"
```

### 2. Quick Start

**Option A: Using the Start Script (Recommended)**

```bash
cd /home/prs/Desktop/mlctl-dashboard
chmod +x start.sh
./start.sh
```

Then visit: `http://localhost:5173`

**Option B: Manual Start**

```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate
python3 main.py
# Backend runs on http://localhost:8000

# Terminal 2 - Frontend (new terminal)
cd frontend
npm run dev
# Frontend runs on http://localhost:5173
```

## First Time Setup

1. Go to **Settings** tab
2. Enter your API credentials
3. Click "Save Configuration"
4. Click "Reload Channels"

## Usage

### Schedule a Restart
1. Go to **Schedule** tab
2. Select a channel
3. Choose date and time (in your timezone)
4. Click "Schedule Restart"

### View Jobs
1. Go to **Jobs** tab
2. View active or completed jobs
3. Click "Logs" to see real-time execution logs
4. Click "Cancel" to cancel waiting jobs

### Monitor Everything
1. **Dashboard** shows:
   - Total jobs count
   - Active jobs
   - Completed/failed jobs count
   - Recent activity feed

## Production Deployment

### Build for Production

```bash
cd frontend
npm run build
# Builds to frontend/dist/

cd ../backend
# Backend is already ready
python3 main.py
```

The backend will serve the frontend at `http://your-server:8000`

### Using Docker (Optional)

Create a `Dockerfile` in the project root:

```dockerfile
FROM python:3.11-slim as backend
WORKDIR /app/backend
COPY backend/requirements.txt .
RUN pip install -r requirements.txt

FROM node:18-alpine as frontend
WORKDIR /app/frontend
COPY frontend/package*.json .
RUN npm install
COPY frontend .
RUN npm run build

FROM python:3.11-slim
WORKDIR /app
COPY --from=backend /app/backend /app/backend
COPY --from=frontend /app/frontend/dist /app/frontend/dist

EXPOSE 8000
WORKDIR /app/backend
CMD ["python3", "main.py"]
```

Build and run:
```bash
docker build -t mlctl-dashboard .
docker run -p 8000:8000 -e ML_CLIENT_ID=xxx -e ML_CLIENT_SECRET=xxx mlctl-dashboard
```

## Troubleshooting

### Port Already in Use
```bash
# Change port in backend/main.py (last line)
# Or kill existing process:
lsof -i :8000  # Find process
kill -9 <PID>  # Kill it
```

### Frontend not connecting to backend
- Ensure backend is running on `http://localhost:8000`
- Check browser console for CORS errors
- Verify proxy settings in `frontend/vite.config.ts`

### No channels showing
- Create `~/bin/config/channels.json` with channels
- Reload through Settings > Reload Channels

### Jobs not updating
- Check backend is running
- Try refreshing the page
- Check browser console for API errors

## Project Structure

```
mlctl-dashboard/
├── backend/              # Python FastAPI backend
│   ├── main.py          # FastAPI application
│   ├── mlctl_core.py    # Core logic
│   ├── requirements.txt # Dependencies
│   └── venv/           # Virtual environment
├── frontend/            # Vue 3 + TypeScript frontend
│   ├── src/
│   │   ├── components/ # Vue components
│   │   ├── stores/     # Pinia store
│   │   ├── App.vue     # Main app
│   │   └── index.css   # Global styles
│   ├── dist/           # Built frontend (after npm run build)
│   ├── index.html      # HTML entry point
│   └── package.json    # Dependencies
├── README.md           # Full documentation
├── .gitignore         # Git ignore rules
└── start.sh           # Startup script
```

## Key Features

✅ **Dashboard**
- Real-time statistics
- Active jobs overview
- Recent activity feed

✅ **Schedule**
- Channel picker
- Timezone support
- Date/time scheduler
- Confirmation modal

✅ **Jobs Management**
- Active jobs tab
- Completed jobs tab
- All jobs view
- Status indicators
- Time-to-execution display

✅ **Logs Viewer**
- Real-time log display
- Modal popup
- Auto-refresh capability
- Scrollable log viewer

✅ **Settings**
- API configuration panel
- Environment variable management
- Channels reloader
- Configuration status display

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/config` | Get configuration |
| POST | `/api/config` | Update configuration |
| GET | `/api/channels` | Get all channels |
| GET | `/api/status/{arn}` | Get channel status |
| POST | `/api/schedule` | Schedule restart |
| GET | `/api/jobs` | Get all jobs |
| GET | `/api/jobs/{id}` | Get specific job |
| POST | `/api/jobs/{id}/cancel` | Cancel job |
| GET | `/api/jobs/{id}/logs` | Get job logs |

## Environment Variables

- `ML_CLIENT_ID` - API client ID
- `ML_CLIENT_SECRET` - API client secret
- `ML_BASE_URL` - API base URL
- `ML_BLIP_DOMAIN` - BLIP domain name

## Support

For issues or questions, check:
1. Browser console (F12)
2. Backend logs (Terminal 1)
3. `/README.md` for detailed documentation

---

**Your professional MLCtl Dashboard is ready to use!** 🚀
