# MLCtl Dashboard

A professional, full-featured web application for managing MediaLive channel restarts. Built with Vue 3 + TypeScript frontend and FastAPI backend.

## Features

✨ **Professional UI**
- Modern, flawless design with Tailwind CSS
- Responsive layout for desktop and tablet
- Dark mode support
- Smooth animations and transitions

🎯 **Core Functionality**
- Schedule channel restarts with timezone support
- Real-time job status monitoring
- Live job logs viewer
- Job cancellation
- Dashboard with statistics
- MediaLive input URL scheduling add-on with AWS session credentials

🔧 **Configuration**
- Easy API configuration UI
- Environment variable management
- Channel configuration loading

## Tech Stack

**Frontend:**
- Vue 3 with TypeScript
- Vite (build tool)
- Tailwind CSS (styling)
- Pinia (state management)
- Axios (HTTP client)

**Backend:**
- FastAPI (Python web framework)
- Pydantic (data validation)
- Uvicorn (ASGI server)

## Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn

## Installation & Setup

### 1. Backend Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Frontend Setup

```bash
cd frontend
npm install
```

### 3. Environment Configuration

Create a `.env` file in the project root:

```bash
export ML_CLIENT_ID="your-client-id"
export ML_CLIENT_SECRET="your-client-secret"
export ML_BASE_URL="https://your-api-base-url.com"
export ML_BLIP_DOMAIN="your-blip-domain"
```

Or configure through the Settings panel in the UI.

### 4. Channels Configuration

Create/update channels file at: `~/bin/config/channels.json`

```json
[
  {
    "name": "Channel 1",
    "arn": "arn:aws:medialive:us-east-1:123456789:channel/1"
  },
  {
    "name": "Channel 2",
    "arn": "arn:aws:medialive:us-east-1:123456789:channel/2"
  }
]
```

## Running the Application

### Development Mode

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
python3 main.py
```

Backend runs on: `http://localhost:8000`

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

Frontend runs on: `http://localhost:5173`

The frontend is configured to proxy API requests to the backend.

### Production Mode

**Build Frontend:**
```bash
cd frontend
npm run build
```

**Run Backend (serves frontend):**
```bash
cd backend
source venv/bin/activate
python3 main.py
```

Visit: `http://localhost:8000`

## Usage

### Dashboard Tab
- View overall statistics
- See active jobs
- Check recent activity

### Schedule Tab
- Select a channel to restart
- Choose timezone and schedule time
- Confirm and schedule the restart

### Jobs Tab
- View all active and completed jobs
- Check job status and time remaining
- View job logs in real-time
- Cancel waiting/running jobs

### Settings Tab
- Configure API credentials
- Set API base URL and BLIP domain
- Reload channels configuration

### Inputs Tab
- Export AWS access key, secret key, and session token for MediaLive operations
- Schedule a channel input URL change with HLS playlist precheck
- Roll back a channel to the last backed-up input URL
- View and cancel MediaLive input jobs separately from restart jobs

## Project Structure

```
mlctl-dashboard/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── mlctl_core.py        # Core MLCtl logic
│   ├── requirements.txt     # Python dependencies
│   └── venv/               # Virtual environment
├── frontend/
│   ├── src/
│   │   ├── components/     # Vue components
│   │   ├── stores/         # Pinia store
│   │   ├── App.vue         # Main app component
│   │   ├── main.ts         # Entry point
│   │   └── index.css       # Global styles
│   ├── index.html          # HTML template
│   ├── package.json        # NPM dependencies
│   ├── vite.config.ts      # Vite configuration
│   └── tailwind.config.js  # Tailwind configuration
└── README.md
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/config` | Get current configuration |
| POST | `/api/config` | Update configuration |
| GET | `/api/channels` | Get all channels |
| GET | `/api/status/{arn}` | Get channel status |
| POST | `/api/schedule` | Schedule a restart |
| GET | `/api/jobs` | Get all jobs |
| GET | `/api/jobs/{id}` | Get specific job |
| POST | `/api/jobs/{id}/cancel` | Cancel a job |
| GET | `/api/jobs/{id}/logs` | Get job logs |
| GET | `/api/medialive/aws-credentials` | Get AWS credential status |
| POST | `/api/medialive/aws-credentials` | Export AWS credentials for the add-on |
| GET | `/api/medialive/channels` | Get MediaLive add-on channels |
| POST | `/api/medialive/input-details` | Get current attached input URL |
| POST | `/api/medialive/schedule-input-url` | Schedule input URL update or rollback |
| GET | `/api/medialive/jobs` | Get MediaLive input jobs |
| POST | `/api/medialive/jobs/{id}/cancel` | Cancel a MediaLive input job |
| GET | `/api/medialive/jobs/{id}/logs` | Get MediaLive input job logs |
| GET | `/api/health` | Health check |

## Troubleshooting

### Frontend won't connect to backend
- Ensure backend is running on `http://localhost:8000`
- Check CORS is enabled (it is by default)
- Verify proxy settings in `vite.config.ts`

### Configuration not saving
- Check environment variables are set correctly
- Verify write permissions to `/tmp/mlctl_jobs.json`
- Check browser console for errors

### No channels showing
- Verify channels file exists at `~/bin/config/channels.json`
- Check JSON format is valid
- Reload through Settings > Reload Channels

### Jobs not updating
- Frontend refreshes jobs every 10 seconds automatically
- Check backend logs for API errors
- Verify job PID is still running

## Notes

- Job logs are stored in `/tmp/mlctl_*.log`
- Job state persists in `/tmp/mlctl_jobs.json`
- Token cache stored in `/tmp/ml_token_cache.json`
- MediaLive input job logs are stored in `/tmp/mlctl_medialive_*.log`
- MediaLive input URL backups are stored in `/tmp/mlctl_input_backups`
- All timestamps are ISO 8601 format with timezone support
- Frontend auto-refreshes job list every 10 seconds

## License

MIT
