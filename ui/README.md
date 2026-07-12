# Video Agent Suite - Interactive UI

Web-based interface for the Video Agent Suite with real-time pipeline visualization.

## Quick Start

### Backend (FastAPI)

```bash
cd ui/backend
pip install fastapi uvicorn websockets
python main.py
```

Server runs at: http://localhost:8080

### Frontend

Open `ui/frontend/index.html` in a browser, or serve it:

```bash
cd ui/frontend
python -m http.server 3000
```

Then visit: http://localhost:3000

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API info |
| `/api/projects` | GET | List all projects |
| `/api/projects/{name}` | GET | Get project details |
| `/api/create` | POST | Create new video (Workflow 1) |
| `/api/edit` | POST | Edit footage (Workflow 2) |
| `/api/health` | GET | Health check |
| `/ws/pipeline/{name}` | WS | Real-time pipeline progress |

## Features

- **Visual Pipeline Canvas** — See all 11 stages of video creation
- **Real-Time Progress** — WebSocket updates as agents work
- **Project Library** — Browse all generated videos
- **Video Preview** — Watch rendered videos in-browser
- **Dual Render Comparison** — Compare Remotion vs Hyperframes outputs
