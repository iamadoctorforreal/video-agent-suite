# Video Agent Suite — Architecture Diagram

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          VIDEO AGENT SUITE                                       │
│              AI-Powered Video Creation & Editing Pipeline                        │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌──────────────────────┐    ┌──────────────────────┐                          │
│  │   WORKFLOW 1:        │    │   WORKFLOW 2:        │                          │
│  │   CREATIVE           │    │   POST-PRODUCTION    │                          │
│  │   PRODUCTION         │    │   EDITING            │                          │
│  └──────────┬───────────┘    └──────────┬───────────┘                          │
│             │                           │                                       │
│  ┌──────────▼───────────────────────────▼───────────┐                          │
│  │              ORCHESTRATOR (main.py)                │                          │
│  │         Intent Router → Workflow Selection         │                          │
│  └──────────┬───────────────────────────┬───────────┘                          │
│             │                           │                                       │
│  ┌──────────▼───────────┐  ┌───────────▼──────────┐                           │
│  │   CREATION PIPELINE  │  │  EDITING PIPELINE    │                           │
│  │                      │  │                      │                           │
│  │  1. Scripting Agent  │  │  1. Analyzer Agent   │                           │
│  │  2. Director Agent   │  │  2. Silence Remover  │                           │
│  │  3. Asset Sourcing   │  │  3. Color Grading    │                           │
│  │  4. Voiceover (TTS)  │  │  4. Transcription    │                           │
│  │  5. Motion Graphics  │  │  5. B-Roll Insert    │                           │
│  │  6. Dual Render      │  │  6. FFmpeg Assembly  │                           │
│  │  7. FFmpeg Assembly  │  │                      │                           │
│  └──────────┬───────────┘  └───────────┬──────────┘                           │
│             │                           │                                       │
│  ┌──────────▼───────────────────────────▼───────────┐                          │
│  │              DUAL RENDER ENGINE                    │                          │
│  │                                                    │                          │
│  │  ┌─────────────────┐    ┌─────────────────┐       │                          │
│  │  │   REMOTION      │    │   HYPERFRAMES   │       │                          │
│  │  │   (React/TS)    │    │   (HTML/GSAP)   │       │                          │
│  │  │                 │    │                 │       │                          │
│  │  │  npx remotion   │    │  npx hyperframes│       │                          │
│  │  │    render       │    │     render      │       │                          │
│  │  └────────┬────────┘    └────────┬────────┘       │                          │
│  │           │                      │                 │                          │
│  │           ▼                      ▼                 │                          │
│  │    video_remotion.mp4    video_hyperframes.mp4     │                          │
│  └──────────────────────────────────────────────────┘                          │
│                                                                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                          ALIBABA CLOUD APIs                                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │  LLM         │  │  Image Gen   │  │  Video Gen   │  │  TTS         │        │
│  │  qwen3.7-max │  │  wan2.6-t2i  │  │  happyhorse  │  │  cosyvoice   │        │
│  │              │  │              │  │  -1.1-t2v    │  │  -v3-plus    │        │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘        │
│                                                                                 │
│  ┌──────────────┐  ┌──────────────┐                                            │
│  │  ASR         │  │  Vision      │                                            │
│  │  fun-asr     │  │  qwen-vl-max │                                            │
│  └──────────────┘  └──────────────┘                                            │
│                                                                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                          EXTERNAL SERVICES                                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                          │
│  │  Pexels API  │  │  FFmpeg      │  │  Figma       │                          │
│  │  (B-Roll)    │  │  7.1.1       │  │  (Assets)    │                          │
│  └──────────────┘  └──────────────┘  └──────────────┘                          │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Agent Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    BaseAgent (Abstract)                       │
│  - get_llm_client() → OpenAI-compatible client              │
│  - call_llm() → Unified LLM call with enable_thinking       │
│  - run() → Execute with logging + error handling            │
└──────────────────────────┬──────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
┌─────────▼──────┐ ┌──────▼───────┐ ┌──────▼───────┐
│ ScriptingAgent │ │ DirectorAgent│ │ AssetSourcing│
│                │ │              │ │    Agent     │
│ - Generate     │ │ - Storyboard │ │ - Pexels API │
│   scripts      │ │   creation   │ │ - Local      │
│ - JSON output  │ │ - Shot types │ │   assets     │
│ - Tone/audience│ │ - Animations │ │ - AI image   │
│                │ │ - SFX design │ │   generation │
└────────────────┘ └──────────────┘ └──────────────┘

┌────────────────┐ ┌──────────────┐ ┌──────────────┐
│ VoiceoverAgent │ │  MotionGfx   │ │ Transcription│
│                │ │    Agent     │ │    Agent     │
│ - CosyVoice    │ │              │ │              │
│   v3-plus      │ │ - Remotion   │ │ - fun-asr    │
│ - Qwen3 TTS    │ │   (React)    │ │ - SRT output │
│   (fallback)   │ │ - Hyperframes│ │ - Segments   │
│ - SRT captions │ │   (HTML/GSAP)│ │              │
│                │ │ - Dual output│ │              │
└────────────────┘ └──────────────┘ └──────────────┘
```

## Data Flow

```
User Input (topic/footage)
        │
        ▼
┌───────────────┐
│   Router      │ ──→ Workflow 1 (Creation) or Workflow 2 (Editing)
└───────┬───────┘
        │
        ▼
┌───────────────┐     ┌──────────────┐     ┌──────────────┐
│   Scripting   │────▶│   Director   │────▶│   Asset      │
│   Agent       │     │   Agent      │     │   Sourcing   │
└───────────────┘     └──────┬───────┘     └──────┬───────┘
                             │                     │
                             ▼                     ▼
                      ┌──────────────┐     ┌──────────────┐
                      │  Storyboard  │     │   Assets     │
                      │  (JSON/MD)   │     │   Manifest   │
                      └──────┬───────┘     └──────┬───────┘
                             │                     │
                             ▼                     │
                      ┌──────────────┐             │
                      │  Voiceover   │◀────────────┘
                      │  Agent       │
                      └──────┬───────┘
                             │
                             ▼
                      ┌──────────────┐
                      │  Motion Gfx  │
                      │  Agent       │
                      └──────┬───────┘
                             │
                    ┌────────┴────────┐
                    ▼                 ▼
             ┌──────────┐      ┌──────────┐
             │ Remotion │      │Hyperframes│
             │ Render   │      │ Render   │
             └────┬─────┘      └────┬─────┘
                  │                 │
                  ▼                 ▼
           video_remotion.mp4  video_hf.mp4
```

## Deployment Architecture (Alibaba Cloud)

```
┌─────────────────────────────────────────────────────────┐
│              ALIBABA CLOUD (ECS / SAS)                    │
│                                                          │
│  ┌────────────────────────────────────────────────┐     │
│  │           Docker Container                      │     │
│  │                                                 │     │
│  │  ┌─────────────────────────────────────────┐   │     │
│  │  │  Video Agent Suite (Python 3.14)        │   │     │
│  │  │                                         │   │     │
│  │  │  - Orchestrator CLI                     │   │     │
│  │  │  - 7 Specialized Agents                 │   │     │
│  │  │  - Dual Render Engine                   │   │     │
│  │  │  - FFmpeg 7.1.1                         │   │     │
│  │  │  - Node.js 20.x (Remotion/Hyperframes)  │   │     │
│  │  └─────────────────────────────────────────┘   │     │
│  │                                                 │     │
│  │  Volumes:                                       │     │
│  │  - /app/output  (rendered videos)               │     │
│  │  - /app/projects (project data)                 │     │
│  │                                                 │     │
│  │  Environment:                                   │     │
│  │  - ALIBABA_API_KEY                              │     │
│  │  - PEXELS_API_KEY                               │     │
│  └────────────────────────────────────────────────┘     │
│                                                          │
│  Ports: 22 (SSH), 80 (HTTP), 443 (HTTPS), 8080 (API)   │
│                                                          │
└─────────────────────────────────────────────────────────┘
          │
          │ API Calls
          ▼
┌─────────────────────────────────────────────────────────┐
│              QWEN CLOUD APIs                              │
│  dashscope-intl.aliyuncs.com                             │
│                                                          │
│  - /compatible-mode/v1/chat/completions (qwen3.7-max)   │
│  - /services/aigc/text2audio/generation (cosyvoice)     │
│  - /compatible-mode/v1/images/generations (wan2.6-t2i)  │
│  - fun-asr (speech recognition)                          │
└─────────────────────────────────────────────────────────┘
```

## Tech Stack Summary

| Layer | Technology |
|-------|-----------|
| Language | Python 3.14 |
| LLM | Alibaba Qwen 3.7 Max |
| Image Gen | Alibaba Wan 2.6 T2I |
| Video Gen | Alibaba HappyHorse 1.1 |
| TTS | Alibaba CosyVoice v3 Plus |
| ASR | Alibaba fun-asr |
| Motion Graphics | Remotion 4.x (React) + Hyperframes (HTML/GSAP) |
| Video Processing | FFmpeg 7.1.1 |
| B-Roll | Pexels API |
| Container | Docker + Docker Compose |
| Cloud | Alibaba Cloud ECS/SAS |
| CLI | Typer + Rich |
