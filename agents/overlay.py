"""
Motion Graphics Overlay Agent — adds captions, lower thirds, and branded overlays.
Generates HTML/GSAP compositions for Hyperframes or Remotion components.
"""

import json
from pathlib import Path
from typing import Optional

from agents.base import BaseAgent, AgentInput, AgentOutput


class OverlayAgent(BaseAgent):
    """Creates motion graphics overlays (captions, lower thirds, branding)."""

    name = "overlay"
    description = "Creates caption and lower-third overlays"

    def execute(self, input_data: AgentInput) -> AgentOutput:
        project_dir = input_data.project_dir
        config = input_data.config

        if not project_dir:
            return AgentOutput(success=False, message="No project directory")

        # Create overlay directory
        overlay_dir = project_dir / "overlays" if project_dir else Path("overlays")
        (overlay_dir / "captions").mkdir(parents=True, exist_ok=True)
        (overlay_dir / "lower_thirds").mkdir(parents=True, exist_ok=True)
        (overlay_dir / "branding").mkdir(parents=True, exist_ok=True)

        overlays_created = []

        # 1. Generate caption overlay (kinetic typography)
        srt_path = input_data.data.get("srt_path") if isinstance(input_data.data, dict) else None
        if srt_path:
            caption_overlay = self._create_caption_overlay(srt_path, overlay_dir / "captions", config)
            if caption_overlay:
                overlays_created.append({"type": "captions", "path": str(caption_overlay)})

        # 2. Generate lower thirds
        lower_thirds = self._create_lower_thirds(overlay_dir / "lower_thirds", config)
        if lower_thirds:
            overlays_created.append({"type": "lower_thirds", "path": str(lower_thirds)})

        # 3. Generate branding overlay (logo, colors)
        branding = self._create_branding_overlay(overlay_dir / "branding", config)
        if branding:
            overlays_created.append({"type": "branding", "path": str(branding)})

        # Save overlay manifest
        if project_dir:
            manifest_path = overlay_dir / "overlay_manifest.json"
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump({"overlays": overlays_created}, f, indent=2)

        return AgentOutput(
            success=True,
            data={"overlays": overlays_created},
            artifact_path=overlay_dir / "overlay_manifest.json" if project_dir else None,
            message=f"Created {len(overlays_created)} overlay types",
            metadata={"count": len(overlays_created)},
        )

    def _create_caption_overlay(self, srt_path: str, output_dir: Path, config: dict) -> Optional[Path]:
        """Create kinetic typography caption overlay."""
        # Parse SRT and create HTML/GSAP composition
        captions = self._parse_srt(srt_path)

        html_content = self._generate_caption_html(captions, config)
        output_path = output_dir / "captions.html"

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return output_path

    def _parse_srt(self, srt_path: str) -> list:
        """Parse SRT file into caption objects."""
        captions = []
        try:
            with open(srt_path, "r", encoding="utf-8") as f:
                content = f.read()

            blocks = content.strip().split("\n\n")
            for block in blocks:
                lines = block.strip().split("\n")
                if len(lines) >= 3:
                    timestamp = lines[1]
                    text = " ".join(lines[2:])

                    # Parse timestamp
                    start_str, end_str = timestamp.split(" --> ")
                    start = self._parse_timestamp(start_str)
                    end = self._parse_timestamp(end_str)

                    captions.append({
                        "start": start,
                        "end": end,
                        "text": text,
                        "duration": end - start,
                    })
        except Exception as e:
            self.console.print(f"  [yellow]⚠️ SRT parse failed: {e}[/yellow]")

        return captions

    def _parse_timestamp(self, ts: str) -> float:
        """Parse SRT timestamp to seconds."""
        try:
            parts = ts.replace(",", ".").split(":")
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        except (ValueError, IndexError):
            return 0.0

    def _generate_caption_html(self, captions: list, config: dict) -> str:
        """Generate HTML/GSAP caption composition."""
        caption_divs = []
        gsap_tweens = []

        for i, cap in enumerate(captions):
            div_id = f"caption_{i}"
            caption_divs.append(f"""
        <div id="{div_id}" class="caption" style="
            position: absolute;
            bottom: 15%;
            left: 50%;
            transform: translateX(-50%);
            font-size: 48px;
            font-weight: bold;
            color: white;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
            opacity: 0;
            text-align: center;
            max-width: 90%;
        ">{cap['text']}</div>""")

            gsap_tweens.append(f"""
        tl.fromTo('#{div_id}', {{
            opacity: 0,
            y: 20,
            scale: 0.9,
        }}, {{
            opacity: 1,
            y: 0,
            scale: 1,
            duration: 0.3,
        }}, {cap['start']});
        tl.to('#{div_id}', {{
            opacity: 0,
            duration: 0.2,
        }}, {cap['end'] - 0.2});""")

        return f"""<!DOCTYPE html>
<html>
<head>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"></script>
    <style>
        body {{ margin: 0; padding: 0; background: transparent; }}
        .composition {{ width: 1080px; height: 1920px; position: relative; overflow: hidden; }}
    </style>
</head>
<body>
    <div id="root" class="composition">
        {''.join(caption_divs)}
    </div>
    <script>
        const tl = gsap.timeline({{ paused: true }});
        window.__timelines = window.__timelines || {{}};
        window.__timelines['captions'] = tl;
        {''.join(gsap_tweens)}
    </script>
</body>
</html>"""

    def _create_lower_thirds(self, output_dir: Path, config: dict) -> Optional[Path]:
        """Create lower third overlay template."""
        html_content = """<!DOCTYPE html>
<html>
<head>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"></script>
    <style>
        body { margin: 0; padding: 0; background: transparent; }
        .lower-third {
            position: absolute;
            bottom: 20%;
            left: 5%;
            background: linear-gradient(90deg, rgba(0,0,0,0.8) 0%, rgba(0,0,0,0.4) 100%);
            padding: 20px 40px;
            border-radius: 8px;
            opacity: 0;
        }
        .lt-title { font-size: 36px; font-weight: bold; color: white; }
        .lt-subtitle { font-size: 24px; color: #ccc; margin-top: 5px; }
    </style>
</head>
<body>
    <div id="root" style="width: 1080px; height: 1920px; position: relative;">
        <div class="lower-third" id="lowerThird">
            <div class="lt-title" id="ltTitle">Title Here</div>
            <div class="lt-subtitle" id="ltSubtitle">Subtitle Here</div>
        </div>
    </div>
    <script>
        const tl = gsap.timeline({ paused: true });
        window.__timelines = window.__timelines || {};
        window.__timelines['lowerThird'] = tl;

        // Animate in
        tl.fromTo('#lowerThird', {
            x: -100,
            opacity: 0,
        }, {
            x: 0,
            opacity: 1,
            duration: 0.5,
            ease: 'power2.out',
        }, 0);

        // Animate out
        tl.to('#lowerThird', {
            x: -100,
            opacity: 0,
            duration: 0.3,
        }, 4);
    </script>
</body>
</html>"""

        output_path = output_dir / "lower_third.html"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return output_path

    def _create_branding_overlay(self, output_dir: Path, config: dict) -> Optional[Path]:
        """Create branding overlay (logo placement, color accents)."""
        html_content = """<!DOCTYPE html>
<html>
<head>
    <style>
        body { margin: 0; padding: 0; background: transparent; }
        .brand-logo {
            position: absolute;
            top: 5%;
            right: 5%;
            width: 120px;
            height: 120px;
            opacity: 0.9;
        }
        .brand-accent {
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        }
    </style>
</head>
<body>
    <div id="root" style="width: 1080px; height: 1920px; position: relative;">
        <div class="brand-logo" id="brandLogo">
            <!-- Logo image would be inserted here -->
            <div style="width:100%;height:100%;background:rgba(255,255,255,0.2);border-radius:8px;display:flex;align-items:center;justify-content:center;color:white;font-size:14px;">LOGO</div>
        </div>
        <div class="brand-accent"></div>
    </div>
</body>
</html>"""

        output_path = output_dir / "branding.html"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return output_path
