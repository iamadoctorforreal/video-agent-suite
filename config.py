"""
Configuration for Video Agent Suite.
All API keys, model settings, and paths live here.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
load_dotenv(Path(__file__).parent / ".env")

# Base paths
PROJECT_ROOT = Path(__file__).parent.resolve()
OUTPUT_DIR = PROJECT_ROOT / "output"
LOGS_DIR = PROJECT_ROOT / "logs"
PROJECTS_DIR = PROJECT_ROOT / "projects"
TEMPLATES_DIR = PROJECT_ROOT / "templates"

# Ensure directories exist
OUTPUT_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
PROJECTS_DIR.mkdir(exist_ok=True)

# ============================================================
# API Keys — set via environment variables or edit below
# ============================================================

# Alibaba Cloud (DashScope) — LLM, Image Gen, Video Gen, TTS, ASR
ALIBABA_API_KEY = os.getenv("ALIBABA_API_KEY", "")
ALIBABA_BASE_URL = os.getenv("ALIBABA_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1")

# LLM models
LLM_MODEL = os.getenv("LLM_MODEL", "qwen3.7-max")          # Script/storyboard generation
VISION_MODEL = os.getenv("VISION_MODEL", "qwen-vl-max")     # Image understanding

# Image/Video generation (Alibaba only — models from hackathon docs)
IMAGE_MODEL = os.getenv("IMAGE_MODEL", "wan2.6-t2i")            # Alibaba image gen (hackathon spec)
VIDEO_MODEL = os.getenv("VIDEO_MODEL", "happyhorse-1.1-t2v")    # Alibaba video gen (hackathon spec)

# TTS / ASR (Alibaba only — no Edge TTS or Whisper fallback)
TTS_MODEL = os.getenv("TTS_MODEL", "cosyvoice-v3-plus")      # Primary TTS
TTS_FALLBACK = os.getenv("TTS_FALLBACK", "qwen3-tts-instruct-flash")  # Fallback TTS
ASR_MODEL = os.getenv("ASR_MODEL", "fun-asr")                # Primary ASR (replaces Whisper)
ASR_FALLBACK = os.getenv("ASR_FALLBACK", "fun-asr-realtime") # Fallback ASR

# Pexels API (b-roll sourcing)
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")

# OpenAI-compatible fallback (optional)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

# ============================================================
# Rendering settings
# ============================================================

# Remotion
REMOTION_PROJECT_PATH = TEMPLATES_DIR / "remotion-starter"
REMOTION_RENDER_FORMAT = "mp4"
REMOTION_RESOLUTION = "1080p"
REMOTION_FPS = 30

# Hyperframes
HYPERFRAMES_PROJECT_PATH = TEMPLATES_DIR / "hyperframes-starter"
HYPERFRAMES_RENDER_FORMAT = "mp4"
HYPERFRAMES_RESOLUTION = "1080x1920"  # Default vertical for social media
HYPERFRAMES_FPS = 30

# FFmpeg
FFMPEG_BINARY = os.getenv("FFMPEG_BINARY", "ffmpeg")
FFPROBE_BINARY = os.getenv("FFPROBE_BINARY", "ffprobe")

# ============================================================
# Output settings
# ============================================================

DEFAULT_ASPECT_RATIO = "9:16"  # Social media vertical
DEFAULT_DURATION_SECONDS = 30
DEFAULT_VOICE = "longanyang"  # CosyVoice v3 Plus voice

# Thumbnail generation
THUMBNAIL_COUNT = 2
TITLE_COUNT = 2
CAPTION_COUNT = 2
