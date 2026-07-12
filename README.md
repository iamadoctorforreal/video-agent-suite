# Video Agent Suite

> **Qwen Cloud Global AI Hackathon 2026** — Track: AI Showrunner
>
> Build AI-driven content production pipelines — video, audio, scripts, multimedia.

AI-powered video creation and editing agent suite with **dual rendering** (Remotion + Hyperframes).
All AI models are Alibaba Cloud only — Qwen LLM, CosyVoice TTS, fun-asr, Wan 2.6 image gen.

---

## Quick Start

```bash
# Clone
git clone https://github.com/iamadoctorforreal/video-agent-suite.git
cd video-agent-suite

# Install
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your API keys

# Run
python -m orchestrator.main create "Your video topic" --duration 30 --style marketing
python -m orchestrator.main edit ./raw_footage.mp4 --captions --color-grade
python -m orchestrator.main status
```

### Docker

```bash
docker compose up -d
docker compose exec video-agent-suite python -m orchestrator.main create "AI agents" --duration 30
```

---

## Features

### Workflow 1: Creative Production
**Script → Storyboard → Assets → Voiceover → Motion Graphics → Dual Render → Final Video**

- AI script generation (Alibaba Qwen)
- Scene-by-scene storyboard with shot design
- Asset sourcing (Pexels b-roll, local brand folders, AI image gen)
- Voiceover generation (Alibaba CosyVoice TTS)
- Motion graphics in **Remotion** (React) + **Hyperframes** (HTML/GSAP)
- Auto-captioning with kinetic typography
- Final assembly with FFmpeg
- Outputs: video + 2 thumbnails, 2 titles, 2 descriptions

### Workflow 2: Post-Production Editing
**Raw Footage → Analysis → Silence Removal → Color Grading → Captions → B-Roll → Final Cut**

- Auto-analyze raw footage (duration, resolution, FPS)
- Silence and filler word detection/removal
- Color grading with professional LUTs
- Automatic caption generation (transcription + SRT)
- B-roll insertion
- Background music overlay

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.14 |
| LLM | Alibaba Qwen (qwen3.7-max) |
| Image Gen | Alibaba Wan 2.7 (wan2.7-image-pro) |
| Video Gen | Alibaba Wan 2.7 (wan2.7t2v) |
| TTS | Alibaba CosyVoice v3 Plus → Qwen3 TTS Flash (fallback) |
| ASR | Alibaba fun-asr → fun-asr-realtime (fallback) |
| Motion Graphics | Remotion 4.x + Hyperframes |
| Video Processing | FFmpeg 7.1.1 |
| B-Roll | Pexels API |
| Orchestration | Custom Python agents |
| CLI | Typer + Rich |

**All AI models are Alibaba Cloud only** — no OpenAI, no Edge TTS, no Whisper.

---

## Setup

### 1. Install Python dependencies
```bash
cd video-agent-suite
pip install -r requirements.txt
```

### 2. Set environment variables
```bash
# Required
export ALIBABA_API_KEY="your-dashscope-api-key"
export PEXELS_API_KEY="your-pexels-api-key"

# Optional (uses defaults)
export LLM_MODEL="qwen3.7-max"
export TTS_MODEL="cosyvoice-v1"
export IMAGE_MODEL="wanx-v1"
```

### 3. Verify setup
```bash
python -m orchestrator.main status
```

---

## Usage

### Create a video from scratch
```bash
# Marketing video
python -m orchestrator.main create "Our new app helps teams collaborate 10x faster" --duration 30 --style marketing

# Social media explainer
python -m orchestrator.main create "5 tips for better productivity" --duration 45 --style explainer --aspect 1:1

# Product launch
python -m orchestrator.main create "Introducing our latest feature: AI-powered scheduling" --duration 20 --style product-launch
```

### Edit existing footage
```bash
# Full edit pipeline
python -m orchestrator.main edit ./raw_footage.mp4

# Selective editing
python -m orchestrator.main edit ./raw_footage.mp4 --captions --color-grade --no-remove-silences

# With b-roll and music
python -m orchestrator.main edit ./raw_footage.mp4 --add-broll --add-music
```

### Check status
```bash
python -m orchestrator.main status
```

### List projects
```bash
python -m orchestrator.main list-projects
```

---

## Architecture

```
video-agent-suite/
├── orchestrator/       # Master CLI + workflow router
│   ├── main.py        # CLI entry point
│   └── router.py      # Intent detection
├── agents/            # Specialized AI agents
│   ├── base.py        # BaseAgent abstract class
│   ├── scripting.py   # Script generation
│   ├── director.py    # Storyboard creation
│   ├── asset_sourcing.py  # Image/b-roll sourcing
│   ├── voiceover.py   # TTS voiceover
│   ├── motion_graphics.py # Remotion + Hyperframes compositions
│   └── ...            # More agents (WIP)
├── workflows/         # End-to-end pipelines
│   ├── creation.py    # Workflow 1: Creative Production
│   └── editing.py     # Workflow 2: Post-Production
├── renderers/         # Video rendering
│   └── dual_render.py # Remotion + Hyperframes dual output
├── templates/         # Base project templates
│   ├── remotion-starter/
│   └── hyperframes-starter/
├── projects/          # Generated video projects
├── output/            # Final rendered videos
└── config.py          # API keys, models, settings
```

---

## Dual Render Pipeline

Every motion graphics composition is rendered in **both** Remotion and Hyperframes:

```
Storyboard → Remotion (React/TypeScript) → remotion render → video_remotion.mp4
            → Hyperframes (HTML/GSAP)    → hyperframes render → video_hyperframes.mp4
```

Pick the version that looks best for your target platform.

---

## Project Roadmap

- [ ] Phase 1: Core pipeline (scripting → storyboard → dual render) ✅
- [ ] Phase 2: Full creation workflow (assets → VO → captions → assembly)
- [ ] Phase 3: Full editing workflow (silence → color → captions → broll)
- [ ] Phase 4: Thumbnail/title/description generation
- [ ] Phase 5: End-to-end automation

---

## Hackathon Notes

- Built for speed: demo-ready in single-command workflows
- Cost-effective: reuses Figma assets, uses free Pexels, falls back to Edge TTS
- Dual render: shows both Remotion and Hyperframes versions side-by-side
- Modular: each agent is independent and testable

---

## License

MIT
