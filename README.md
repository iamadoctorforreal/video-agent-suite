# Video Agent Suite

> **Qwen Cloud Global AI Hackathon 2026** — Track: AI Showrunner
>
> AI-driven content production pipeline: script → storyboard → assets → dual render → final video.
> 15+ specialized agents, DAG orchestration, file message bus, policy server.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        VIDEO AGENT SUITE — DAG PIPELINE                     │
└─────────────────────────────────────────────────────────────────────────────┘

USER INPUT ──► Workflow Router ──► Capability Profile (Creative | Editing)
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  WORKFLOW 1: CREATIVE PRODUCTION (11 nodes, DAG with file message bus)      │
│                                                                             │
│  ┌──────────┐    ┌──────────┐    ──────────────┐    ┌──────────────┐      │
│  │ Scripting│───►│ Director │───►│   Assets     │───►│  Video Gen   │      │
│  │  (read)  │    │  (read)  │    │ (draft)      │    │  (draft)     │      │
│  └──────────┘    └──────────┘    └──────────────┘    └──────────────┘      │
│       │                                  │                    │            │
│       │              ┌───────────────────┘                    │            │
│       │              ▼                                        │            │
│       │         ┌──────────┐                                  │            │
│       │         │Voiceover │                                  │            │
│       │         │ (draft)  │                                  │            │
│       │         └──────────                                  │            │
│       │                                                      │            │
│       ▼                                                      ▼            │
│  ┌──────────┐    ──────────┐    ┌──────────┐    ┌──────────────┐        │
│  │  Sound   │───►│  Motion  │───►│ Assembly │───►│     QC       │        │
│  │ (draft)  │    │  (act)   │    │  (act)   │    │    (read)    │        │
│  └──────────┘    └──────────┘    └──────────┘    └──────────────┘        │
│       │                                                │                  │
│       │                                                ▼                  │
│       │                                          ┌──────────┐            │
│       │                                          │ Metadata │            │
│       │                                          │ (read)   │            │
│       │                                          └──────────            │
│       ▼                                                                  │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │  POLICY SERVER — Budget gating ($5/project, $20/session)         │    │
│  │  Tier access control: read → draft → act (authority levels)      │    │
│  └──────────────────────────────────────────────────────────────────    │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  WORKFLOW 2: POST-PRODUCTION EDITING (6 nodes)                              │
│                                                                             │
│  ┌──────────┐    ────────────┐    ┌──────────┐    ┌──────────┐           │
│  │ Analyze  │───►│ Transcribe │───►│   B-Roll │───►│ Overlays │           │
│  │  (read)  │    │   (read)   │    │ (draft)  │    │ (draft)  │           │
│  └──────────┘    └────────────┘    └──────────┘    └──────────┘           │
│       │                                                │                   │
│       └────────────────────────────────────────────────┘                   │
│                                    │                                       │
│                                    ▼                                       │
│                              ┌──────────┐    ──────────┐                 │
│                              │ Assembly │───►│    QC    │                 │
│                              │  (act)   │    │ (read)   │                 │
│                              └──────────┘    └──────────┘                 │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  FILE MESSAGE BUS — Decoupled state, protected attention                    │
│                                                                             │
│  Nodes pass FILE PATHS (not raw text) between stages:                       │
│  script.json → storyboard.json → assets/ → video_clips/ → final.mp4         │
│                                                                             │
│  This prevents context window bloat and keeps the LLM focused.              │
─────────────────────────────────────────────────────────────────────────────┘
```

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

# Run Workflow 1 (Creative Production)
python -m orchestrator.main create "Your video topic" --duration 30 --style marketing

# Run Workflow 2 (Post-Production Editing)
python -m orchestrator.main edit ./raw_footage.mp4 --captions --color-grade

# Check status
python -m orchestrator.main status
```

---

## Features

### Workflow 1: Creative Production
**Script → Storyboard → Assets → Voiceover → Motion Graphics → Dual Render → Final Video**

- AI script generation (Alibaba Qwen)
- Scene-by-scene storyboard with shot design
- Asset sourcing (Pexels-first, AI fallback, local brand folders)
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
| Image Gen | Alibaba Wan 2.6 (wan2.6-t2i) |
| Video Gen | Alibaba HappyHorse (happyhorse-1.1-t2v, happyhorse-1.1-i2v) |
| TTS | Alibaba CosyVoice v3 Plus |
| ASR | Alibaba fun-asr |
| Motion Graphics | Remotion 4.x + Hyperframes |
| Video Processing | FFmpeg 7.1.1 |
| B-Roll | Pexels API (free stock media) |
| Orchestration | DAG with file message bus |
| Policy | Budget gating + tier-based access control |
| CLI | Typer + Rich |

**All AI models are Alibaba Cloud only** — no OpenAI, no Edge TTS, no Whisper.

---

## Project Structure

```
video-agent-suite/
├── orchestrator/              # Master CLI + DAG orchestration
│   ├── main.py               # CLI entry point
│   ├── router.py             # Intent detection
│   ├── dag.py                # DAG orchestrator with file message bus
│   ├── capability_profiles.py # Workflow 1 & 2 as swappable profiles
│   └── policy_server.py      # Budget gating + tier access control
├── agents/                    # 15+ specialized AI agents
│   ├── base.py               # BaseAgent abstract class
│   ├── scripting.py          # Script generation
│   ├── director.py           # Storyboard creation
│   ├── asset_sourcing.py     # Legacy monolithic asset agent
│   ├── asset_orchestrator.py # Coordinates sub-agents (cheapest first)
│   ├── image_gen.py          # AI image generation sub-agent
│   ├── stock_media.py        # Pexels stock media sub-agent
│   ├── logo_lookup.py        # Local brand asset sub-agent
│   ├── video_generation.py   # Pexels-first + human approval
│   ├── voiceover.py          # TTS voiceover
│   ├── motion_graphics.py    # Remotion + Hyperframes compositions
│   ├── sound.py              # BGM + SFX sourcing
│   ├── assembly.py           # FFmpeg final assembly
│   ├── qc.py                 # Quality checks
│   ├── thumbnail.py          # Thumbnail generation
│   ── metadata.py           # Titles + descriptions
── workflows/                 # End-to-end pipelines
│   ├── creation.py           # Workflow 1: Creative Production
│   └── editing.py            # Workflow 2: Post-Production
├── renderers/                 # Video rendering
│   └── dual_render.py        # Remotion + Hyperframes dual output
├── templates/                 # Base project templates
│   ├── remotion-starter/
│   └── hyperframes-starter/
├── projects/                  # Generated video projects
├── output/                    # Final rendered videos
├── hackathon_docs/            # Reference docs from Antigravity/Gemini hackathon
├── config.py                  # API keys, models, settings
├── .env.example               # Environment template
├── LICENSE                    # MIT License
└── README.md                  # This file
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

## Architecture Patterns (from Hackathon Docs)

This project implements patterns from the Antigravity/Gemini hackathon (Days 2-5):

| Pattern | Source | Implementation |
|---------|--------|----------------|
| **DAG Orchestration** | Day 3 | `orchestrator/dag.py` — graph-based pipeline with file message bus |
| **Capability Profiles** | Day 3 | `orchestrator/capability_profiles.py` — Workflow 1 & 2 as swappable personas |
| **Read/Draft/Act Tiers** | Day 3 | Authority levels per DAG node (text → assets → irreversible ops) |
| **Policy Server** | Day 5 | `orchestrator/policy_server.py` — budget gating ($5/project, $20/session) |
| **Pexels-First Cost Saving** | Custom | Free stock media before paid AI generation |
| **Human-in-the-Loop** | Custom | Approval gate before expensive API calls |

---

## Demo Instructions

### Workflow 1: Creative Production (Full Pipeline)

```bash
# 1. Navigate to project
cd C:\Users\RUKAYYAH IBRAHIM\video-agent-suite

# 2. Run the creation workflow
python -m orchestrator.main create "5 productivity tips for students" --duration 30 --style explainer

# 3. Watch the pipeline execute:
#    - Scripting agent generates the script
#    - Director agent creates storyboard
#    - Asset orchestrator sources images (Pexels first, then AI)
#    - Video generation agent creates clips (with human approval)
#    - Voiceover agent generates TTS
#    - Sound agent sources BGM
#    - Motion graphics agent creates Remotion + Hyperframes compositions
#    - Dual render engine renders both
#    - Assembly agent stitches final video
#    - QC agent checks quality
#    - Metadata agent generates thumbnails/titles

# 4. Find your output:
#    projects/<project-name>/output/final.mp4
```

### Workflow 2: Post-Production Editing

```bash
# 1. Prepare raw footage
#    Place your video file in the project root or provide absolute path

# 2. Run the editing workflow
python -m orchestrator.main edit ./raw_footage.mp4 --captions --color-grade --add-music

# 3. Watch the pipeline:
#    - Analyze agent inspects footage
#    - Transcribe agent generates SRT
#    - B-roll agent sources stock footage
#    - Overlay agent adds captions/lower thirds
#    - Assembly agent combines everything
#    - QC agent checks final output

# 4. Find your output:
#    projects/<project-name>/output/final.mp4
```

### Manual Remotion Demo (for video recording)

```bash
# 1. Navigate to Remotion starter
cd C:\Users\RUKAYYAH IBRAHIM\video-agent-suite\templates\remotion-starter

# 2. Install dependencies (first time only)
npm install

# 3. Open Remotion Studio (visual editor)
npx remotion studio

# 4. Edit src/Root.tsx to customize your composition

# 5. Render to MP4
npx remotion render Root out/video.mp4

# 6. Your video is at: templates/remotion-starter/out/video.mp4
```

### Manual HyperFrames Demo

```bash
# 1. Navigate to HyperFrames starter
cd C:\Users\RUKAYYAH IBRAHIM\video-agent-suite\templates\hyperframes-starter

# 2. Edit index.html to customize your composition

# 3. Render to MP4
npx hyperframes render

# 4. Your video is at: templates/hyperframes-starter/out/video.mp4
```

---

## Hackathon Submission Status

### Judging Criteria Score

| Criterion (Weight) | Score | Notes |
|---|---|---|
| **Innovation & AI Creativity (30%)** | 9/10 | DAG orchestrator, capability profiles, policy server, 15+ agents, dual render, Pexels-first |
| **Technical Depth & Engineering (30%)** | 8/10 | 5+ QwenCloud APIs, custom agent architecture, tier-based authority, budget gating |
| **Problem Value & Impact (25%)** | 8/10 | Automated social media video production — real pain point, scalable |
| **Presentation & Documentation (15%)** | 7/10 | README + architecture diagram + this document |

### Submission Checklist

- [x] Public GitHub repo: `github.com/iamadoctorforreal/video-agent-suite`
- [x] Open source license: MIT (visible in repo About section)
- [ ] 1-3 minute video demo (screen recording of agent in action)
- [x] Architecture diagram (see above)
- [x] Written summary (this README)
- [ ] Proof of Alibaba Cloud deployment (backend must run on Alibaba Cloud)

### Critical Blockers

1. **Alibaba Cloud Deployment** — Backend must run on Alibaba Cloud (SAS, ECS, or Function Compute). Currently runs locally.
2. **Video Demo** — Need 1-3 minute screen recording showing the agent in action.

---

## License

MIT — see [LICENSE](LICENSE) file for details.

---

## Author

**Rukayyah Ibrahim** — Building AI-powered video production tools for social media and marketing.
