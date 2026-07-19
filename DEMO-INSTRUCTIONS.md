# Demo Instructions — Video Agent Suite

> **For:** Qwen Cloud Global AI Hackathon 2026 — Track: AI Showrunner
> **Purpose:** Step-by-step guide to demo Workflow 1 and Workflow 2 for the 1-3 minute video submission

---

## Will the Workflow Create a Structure Like `empire-downfall-skool-pack`?

**Yes, but only if the pipeline runs all the way through.**

The `empire-downfall-skool-pack` structure looks like this:
```
empire-downfall-project-pack/
├── audio/              # Voiceover + BGM
├── final-output/       # Final rendered video
├── README.md           # Project documentation
├── scenes/             # Per-scene folders
│   ├── scene-01-peace-deal/
│   ├── scene-02-downfall-newspaper/
│   └── ...
├── shared/             # Shared assets
├── SPEC.md             # Project specification
├── START-HERE.md       # Quick start guide
└── website/            # Web assets
```

Your workflow **can** produce a similar structure, but currently your test projects only have:
```
test_run/
├── storyboard.json
└── STORYBOARD.md
```

This is because the pipeline stops early (after the Director agent). To get the full structure, you need to run the **complete pipeline** which produces:

```
projects/<project-name>/
├── storyboard.json          # From Director agent
├── STORYBOARD.md            # Human-readable storyboard
├── assets/                  # From Asset Orchestrator
│   ├── images/              # AI-generated images
│   ├── broll/               # Pexels stock videos
│   └── logos/               # Local brand assets
├── video_clips/             # From Video Generation agent
│   ├── scene_1.mp4
│   ├── scene_2.mp4
│   └── ...
├── audio/                   # From Voiceover + Sound agents
│   ├── voiceover.mp3
│   ── bgm/
├── render/                  # From Motion Graphics + Dual Render
│   ├── remotion/
│   │   └── out/video.mp4
│   └── hyperframes/
│       └── out/video.mp4
── output/                  # From Assembly agent
│   ├── final.mp4            # Final assembled video
│   ├── thumbnail_1.png
│   ├── thumbnail_2.png
│   └── SUMMARY.md
├── project.json             # Full metadata
└── dag_execution.json       # DAG execution record
```

**To get the empire-downfall-style structure**, you'd need to add a post-processing step that organizes the output into per-scene folders. This is not currently implemented but could be added to the Assembly or Metadata agent.

---

## Demo Workflow 1: Creative Production

### Option A: Full Automated Pipeline (Recommended for Demo)

This runs all 11 steps automatically. Best for showing the complete system.

```bash
# Step 1: Open terminal
cd C:\Users\RUKAYYAH IBRAHIM\video-agent-suite

# Step 2: Run the creation workflow
python -m orchestrator.main create "5 productivity tips for students" --duration 30 --style explainer

# Step 3: Watch the pipeline execute (takes 5-15 minutes)
# The console will show:
#   - Scripting agent generating the script
#   - Director agent creating storyboard
#   - Asset orchestrator sourcing images (Pexels first, then AI)
#   - Video generation agent creating clips (with human approval prompts)
#   - Voiceover agent generating TTS
#   - Sound agent sourcing BGM
#   - Motion graphics agent creating compositions
#   - Dual render engine rendering both Remotion and Hyperframes
#   - Assembly agent stitching final video
#   - QC agent checking quality
#   - Metadata agent generating thumbnails/titles

# Step 4: Find your output
# projects/<project-name>/output/final.mp4
```

**For the video demo:** Record your screen showing:
1. The command being typed
2. The pipeline executing (show the console output)
3. The final video playing

### Option B: Manual Remotion Demo (Faster, More Visual)

This is faster and more visual — good for a short demo.

```bash
# Step 1: Navigate to Remotion starter
cd C:\Users\RUKAYYAH IBRAHIM\video-agent-suite\templates\remotion-starter

# Step 2: Install dependencies (first time only)
npm install

# Step 3: Open Remotion Studio (visual editor)
npx remotion studio

# This opens a browser at http://localhost:3000
# You can see the composition visually and edit it in real-time

# Step 4: Edit the composition (optional)
# Open src/Root.tsx in VS Code
# Change the text, colors, animations

# Step 5: Render to MP4
npx remotion render Root out/video.mp4

# Step 6: Play the video
# templates/remotion-starter/out/video.mp4
```

**For the video demo:** Record your screen showing:
1. Remotion Studio opening in the browser
2. The composition playing in real-time
3. The render command
4. The final video playing

### Option C: Manual HyperFrames Demo

```bash
# Step 1: Navigate to HyperFrames starter
cd C:\Users\RUKAYYAH IBRAHIM\video-agent-suite\templates\hyperframes-starter

# Step 2: Edit the composition
# Open index.html in VS Code or browser
# Change the text, colors, animations

# Step 3: Render to MP4
npx hyperframes render

# Step 4: Play the video
# templates/hyperframes-starter/out/video.mp4
```

---

## Demo Workflow 2: Post-Production Editing

### Prerequisites

You need a raw video file to edit. You can:
- Use your own footage
- Download a sample video from Pexels
- Use a video from your phone

### Step-by-Step

```bash
# Step 1: Open terminal
cd C:\Users\RUKAYYAH IBRAHIM\video-agent-suite

# Step 2: Place your raw footage in the project root
# Example: raw_footage.mp4

# Step 3: Run the editing workflow
python -m orchestrator.main edit ./raw_footage.mp4 --captions --color-grade --add-music

# Step 4: Watch the pipeline execute (takes 3-10 minutes)
# The console will show:
#   - Analyze agent inspecting footage (duration, resolution, FPS)
#   - Transcribe agent generating SRT captions
#   - B-roll agent sourcing stock footage
#   - Overlay agent adding captions/lower thirds
#   - Assembly agent combining everything
#   - QC agent checking final output

# Step 5: Find your output
# projects/<project-name>/output/final.mp4
```

**For the video demo:** Record your screen showing:
1. The raw footage playing (before)
2. The command being typed
3. The pipeline executing
4. The final edited video playing (after)

---

## Recording the Demo Video

### Tools

- **OBS Studio** (free): https://obsproject.com/
- **Windows Game Bar** (built-in): Press `Win + G`
- **Loom** (free tier): https://www.loom.com/

### Recommended Script (1-3 minutes)

```
0:00 - 0:15  Introduction
             "This is Video Agent Suite, an AI-powered video production pipeline
              built for the Qwen Cloud Hackathon."

0:15 - 0:45  Show the architecture
             "It uses 15+ specialized agents with DAG orchestration,
              file message bus, and dual rendering with Remotion and Hyperframes."

0:45 - 1:30  Demo Workflow 1 (Creative Production)
             Show the command running, pipeline executing, final video playing

1:30 - 2:00  Demo Workflow 2 (Post-Production Editing)
             Show before/after of raw footage being edited

2:00 - 2:30  Show the code structure
             "The project implements patterns from the Antigravity/Gemini hackathon:
              DAG orchestration, capability profiles, policy server with budget gating."

2:30 - 3:00  Conclusion
             "All AI models are Alibaba Cloud only. The project is open source under MIT license."
```

### Tips

- Keep it under 3 minutes
- Show the code running, not just static screens
- Highlight the unique features (DAG, dual render, Pexels-first)
- Speak clearly and confidently
- Test your recording before submitting

---

## Troubleshooting

### "Module not found" errors
```bash
pip install -r requirements.txt
```

### "API key not set" errors
```bash
cp .env.example .env
# Edit .env with your actual API keys
```

### FFmpeg not found
```bash
# Download from: https://www.gyan.dev/ffmpeg/builds/
# Add to PATH: C:\Users\RUKAYYAH IBRAHIM\Desktop\ffmpeg\bin
```

### Node.js not found
```bash
# Download from: https://nodejs.org/
```

### Remotion render fails
```bash
cd templates/remotion-starter
npm install
npx remotion render Root out/video.mp4
```

### HyperFrames render fails
```bash
cd templates/hyperframes-starter
npx hyperframes render
```

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `python -m orchestrator.main create "topic"` | Run Workflow 1 |
| `python -m orchestrator.main edit ./video.mp4` | Run Workflow 2 |
| `python -m orchestrator.main status` | Check system status |
| `python -m orchestrator.main list-projects` | List all projects |
| `npx remotion studio` | Open Remotion visual editor |
| `npx remotion render Root out/video.mp4` | Render Remotion composition |
| `npx hyperframes render` | Render HyperFrames composition |

---

## Output Structure

After running Workflow 1, your project will look like:

```
projects/<project-name>/
├── storyboard.json          # Structured storyboard data
├── STORYBOARD.md            # Human-readable storyboard
├── assets/                  # Sourced assets
│   ├── images/              # AI-generated images
│   ├── broll/               # Pexels stock videos
│   └── manifest.json        # Asset manifest
├── video_clips/             # Generated video clips
── audio/                   # Voiceover + BGM
│   └── voiceover.mp3
── render/                  # Rendered compositions
│   ├── remotion/out/video.mp4
│   ── hyperframes/out/video.mp4
├── output/                  # Final output
│   ├── final.mp4            # Assembled video
│   ├── thumbnail_1.png
│   ├── thumbnail_2.png
│   └── SUMMARY.md
├── project.json             # Full metadata
└── dag_execution.json       # DAG execution record
```

This is similar to the `empire-downfall-skool-pack` structure, but organized by pipeline stage rather than by scene. To get per-scene folders, you'd need to modify the Assembly agent to organize output by scene number.
