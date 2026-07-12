"""
FastAPI Backend for Video Agent Suite UI.
Wraps existing agents and provides REST + WebSocket endpoints.
"""

import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from config import PROJECTS_DIR
from workflows.creation import CreationWorkflow
from workflows.editing import EditingWorkflow

app = FastAPI(title="Video Agent Suite API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
OUTPUT_DIR = PROJECTS_DIR.parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)
app.mount("/output", StaticFiles(directory=str(OUTPUT_DIR)), name="output")


# ============================================================
# Models
# ============================================================

class CreateVideoRequest(BaseModel):
    topic: str
    duration: int = 30
    aspect_ratio: str = "9:16"
    style: str = "marketing"
    project_name: Optional[str] = None


class EditVideoRequest(BaseModel):
    input_video: str
    project_name: Optional[str] = None
    captions: bool = True
    color_grade: bool = True
    remove_silences: bool = True
    add_broll: bool = False
    add_music: bool = True


class ProjectInfo(BaseModel):
    name: str
    topic: str
    created_at: str
    status: str


# ============================================================
# REST Endpoints
# ============================================================

@app.get("/")
async def root():
    return {"message": "Video Agent Suite API", "version": "1.0.0"}


@app.get("/api/projects")
async def list_projects():
    """List all video projects."""
    projects = []
    if PROJECTS_DIR.exists():
        for proj_dir in PROJECTS_DIR.iterdir():
            if proj_dir.is_dir():
                meta_path = proj_dir / "project.json"
                if meta_path.exists():
                    with open(meta_path, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    projects.append({
                        "name": meta.get("name", proj_dir.name),
                        "topic": meta.get("topic", ""),
                        "created_at": meta.get("created_at", ""),
                        "type": "creation" if "script" in meta else "editing",
                    })
    return {"projects": projects}


@app.get("/api/projects/{project_name}")
async def get_project(project_name: str):
    """Get project details."""
    proj_dir = PROJECTS_DIR / project_name
    if not proj_dir.exists():
        raise HTTPException(status_code=404, detail="Project not found")

    meta_path = proj_dir / "project.json"
    if not meta_path.exists():
        raise HTTPException(status_code=404, detail="Project metadata not found")

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    return meta


@app.post("/api/create")
async def create_video(request: CreateVideoRequest):
    """Create a new video (Workflow 1)."""
    try:
        workflow = CreationWorkflow(
            topic=request.topic,
            duration=request.duration,
            aspect_ratio=request.aspect_ratio,
            style=request.style,
            project_name=request.project_name,
        )
        result = workflow.run()
        return {"success": True, "project_dir": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/edit")
async def edit_video(request: EditVideoRequest):
    """Edit existing footage (Workflow 2)."""
    try:
        workflow = EditingWorkflow(
            input_video=request.input_video,
            project_name=request.project_name,
            captions=request.captions,
            color_grade=request.color_grade,
            remove_silences=request.remove_silences,
            add_broll=request.add_broll,
            add_music=request.add_music,
        )
        result = workflow.run()
        return {"success": True, "project_dir": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/projects/{project_name}/output")
async def get_project_output(project_name: str):
    """Get project output files."""
    proj_dir = PROJECTS_DIR / project_name
    output_dir = proj_dir / "output"

    if not output_dir.exists():
        return {"files": []}

    files = []
    for f in output_dir.iterdir():
        if f.is_file():
            files.append({
                "name": f.name,
                "size": f.stat().st_size,
                "path": str(f),
            })

    return {"files": files}


# ============================================================
# WebSocket for Real-Time Progress
# ============================================================

@app.websocket("/ws/pipeline/{project_name}")
async def pipeline_websocket(websocket: WebSocket, project_name: str):
    """WebSocket endpoint for real-time pipeline progress."""
    await websocket.accept()

    try:
        # Send initial connection message
        await websocket.send_json({
            "type": "connected",
            "project": project_name,
            "message": "Connected to pipeline stream",
        })

        # Watch project directory for changes
        proj_dir = PROJECTS_DIR / project_name
        if not proj_dir.exists():
            await websocket.send_json({
                "type": "error",
                "message": f"Project {project_name} not found",
            })
            return

        # Stream progress updates
        while True:
            # Check for status updates
            status_path = proj_dir / "status.json"
            if status_path.exists():
                with open(status_path, "r", encoding="utf-8") as f:
                    status = json.load(f)
                await websocket.send_json({
                    "type": "progress",
                    "data": status,
                })

            await asyncio.sleep(1)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": str(e),
        })


# ============================================================
# Health Check
# ============================================================

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "projects_dir": str(PROJECTS_DIR),
    }


# ============================================================
# Run Server
# ============================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
