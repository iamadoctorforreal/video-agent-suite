"""
Motion Graphics Agent — creates motion graphics compositions.
Supports both Remotion (React-based) and Hyperframes (HTML/GSAP-based) rendering.
Generates compositions in Remotion, then ports to Hyperframes for dual output.
"""

import json
import subprocess
from pathlib import Path
from typing import Optional

from agents.base import BaseAgent, AgentInput, AgentOutput


class MotionGraphicsAgent(BaseAgent):
    """Creates motion graphics compositions in both Remotion and Hyperframes."""

    name = "motion_graphics"
    description = "Creates motion graphics (Remotion + Hyperframes dual render)"

    def execute(self, input_data: AgentInput) -> AgentOutput:
        storyboard = input_data.data
        project_dir = input_data.project_dir

        if not storyboard or "scenes" not in storyboard:
            return AgentOutput(success=False, message="No storyboard data provided")

        # Create render directories
        remotion_dir = project_dir / "render" / "remotion" if project_dir else Path("render/remotion")
        hyperframes_dir = project_dir / "render" / "hyperframes" if project_dir else Path("render/hyperframes")
        remotion_dir.mkdir(parents=True, exist_ok=True)
        hyperframes_dir.mkdir(parents=True, exist_ok=True)

        # Step 1: Generate Remotion composition
        remotion_result = self._build_remotion_composition(storyboard, remotion_dir)

        # Step 2: Port to Hyperframes (or build native Hyperframes)
        hyperframes_result = self._build_hyperframes_composition(storyboard, hyperframes_dir)

        results = {
            "remotion": remotion_result,
            "hyperframes": hyperframes_result,
        }

        # Save render manifest
        if project_dir:
            manifest_path = project_dir / "render" / "render_manifest.json"
            with open(manifest_path, "w") as f:
                json.dump(results, f, indent=2)

        return AgentOutput(
            success=True,
            data=results,
            artifact_path=manifest_path if project_dir else None,
            message="Motion graphics compositions created (Remotion + Hyperframes)",
            metadata=results,
        )

    def _build_remotion_composition(self, storyboard: dict, output_dir: Path) -> dict:
        """Generate a Remotion composition from the storyboard."""
        self.console.print("  [dim]Building Remotion composition...[/dim]")

        # Create the Remotion project structure
        src_dir = output_dir / "src"
        src_dir.mkdir(parents=True, exist_ok=True)

        # Generate the main composition component
        scenes = storyboard.get("scenes", [])
        total_frames = sum(
            int(scene.get("duration_seconds", 3) * 30)  # 30fps
            for scene in scenes
        )

        component_code = self._generate_remotion_component(scenes, storyboard)

        # Write the Remotion component
        component_path = src_dir / "Root.tsx"
        with open(component_path, "w") as f:
            f.write(component_code)

        # Generate index.tsx (entry point)
        index_code = self._generate_remotion_index(scenes, storyboard)
        with open(src_dir / "index.tsx", "w") as f:
            f.write(index_code)

        # Generate remotion.config.ts
        config_code = self._generate_remotion_config()
        with open(output_dir / "remotion.config.ts", "w") as f:
            f.write(config_code)

        # Generate package.json
        pkg = self._generate_remotion_package()
        with open(output_dir / "package.json", "w") as f:
            json.dump(pkg, f, indent=2)

        self.console.print(f"  [green]✓[/green] Remotion composition: {component_path.name}")

        return {
            "status": "generated",
            "entry_point": str(component_path),
            "total_frames": total_frames,
            "total_scenes": len(scenes),
        }

    def _generate_remotion_component(self, scenes: list, storyboard: dict) -> str:
        """Generate Remotion React component code."""
        color_palette = storyboard.get("color_palette", ["#1a1a2e", "#16213e", "#0f3460"])
        font_style = storyboard.get("font_style", "Inter, sans-serif")

        scene_components = []
        for i, scene in enumerate(scenes):
            frames = int(scene.get("duration_seconds", 3) * 30)
            start_frame = sum(
                int(s.get("duration_seconds", 3) * 30)
                for s in scenes[:i]
            )

            scene_components.append(f"""
// Scene {scene.get('scene_number', i+1)}
<AbsoluteFill style={{
  backgroundColor: '{color_palette[i % len(color_palette)]}',
  justifyContent: 'center',
  alignItems: 'center',
  fontFamily: '{font_style}',
}}>
  <Sequence from={start_frame} durationInFrames={frames}>
    <Scene{scene.get('scene_number', i+1)} />
  </Sequence>
</AbsoluteFill>""")

        component_code = f"""import {{ AbsoluteFill, Sequence, interpolate, useCurrentFrame, useVideoConfig }} from 'remotion';
import {{ useState, useEffect }} from 'react';

// Font import
// import {{ loadFont }} from '@remotion/google-fonts/Inter';
// loadFont();

{self._generate_scene_components(scenes)}

export const Root: React.FC = () => {{
  return (
    <AbsoluteFill style={{backgroundColor: '{color_palette[0]}'}}>
      {self._generate_scene_sequences(scenes)}
    </AbsoluteFill>
  );
}};
"""
        return component_code

    def _generate_scene_components(self, scenes: list) -> str:
        """Generate individual scene component functions."""
        components = []
        for i, scene in enumerate(scenes):
            scene_num = scene.get('scene_number', i + 1)
            script_text = scene.get('script_text', '').replace("'", "\\'")
            motion = scene.get('motion_type', 'static')
            shot = scene.get('shot_type', 'medium')

            # Generate animation based on motion type
            animation_code = self._get_remotion_animation(motion)

            component = f"""
export const Scene{scene_num}: React.FC = () => {{
  const frame = useCurrentFrame();
  const {{ fps }} = useVideoConfig();
  const progress = frame / fps;

  {animation_code}

  return (
    <AbsoluteFill style={{
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center',
      alignItems: 'center',
      padding: 40,
    }}>
      <div style={{
        fontSize: 48,
        fontWeight: 'bold',
        color: 'white',
        textAlign: 'center',
        opacity: opacity,
        transform: `scale(${{scale}})`,
      }}>
        {script_text[:80]}{'...' if len(script_text) > 80 else ''}
      </div>
    </AbsoluteFill>
  );
}};"""
            components.append(component)

        return "\n".join(components)

    def _get_remotion_animation(self, motion_type: str) -> str:
        """Get Remotion animation code for a motion type."""
        animations = {
            "static": "const opacity = 1;\nconst scale = 1;",
            "slow_zoom": "const scale = interpolate(frame, [0, 90], [1, 1.2], { extrapolateRight: 'clamp' });\nconst opacity = 1;",
            "fade": "const opacity = interpolate(frame, [0, 30], [0, 1], { extrapolateRight: 'clamp' });\nconst scale = 1;",
            "slide_in": "const opacity = interpolate(frame, [0, 15], [0, 1], { extrapolateRight: 'clamp' });\nconst scale = interpolate(frame, [0, 15], [0.8, 1], { extrapolateRight: 'clamp' });",
            "push_in": "const scale = interpolate(frame, [0, 90], [1.3, 1], { extrapolateRight: 'clamp' });\nconst opacity = 1;",
            "dissolve": "const opacity = interpolate(frame, [0, 30], [0, 1], { extrapolateRight: 'clamp' });\nconst scale = interpolate(frame, [0, 30], [1.1, 1], { extrapolateRight: 'clamp' });",
        }
        return animations.get(motion_type, animations["fade"])

    def _generate_scene_sequences(self, scenes: list) -> str:
        """Generate Scene JSX sequences."""
        sequences = []
        for i, scene in enumerate(scenes):
            frames = int(scene.get("duration_seconds", 3) * 30)
            start_frame = sum(
                int(s.get("duration_seconds", 3) * 30)
                for s in scenes[:i]
            )
            sequences.append(f"      <Sequence from={{ {start_frame} }} durationInFrames={{ {frames} }}>\n        <Scene{scene.get('scene_number', i + 1)} />\n      </Sequence>")

        return "\n".join(sequences)

    def _generate_remotion_index(self, scenes: list, storyboard: dict) -> str:
        """Generate Remotion index.tsx entry point."""
        total_frames = sum(int(s.get("duration_seconds", 3) * 30) for s in scenes)

        return f"""import {{ registerRoot }} from 'remotion';
import {{ Root }} from './Root';

registerRoot(Root);
"""

    def _generate_remotion_config(self) -> str:
        """Generate Remotion config file."""
        return """import { Config } from '@remotion/cli/config';

Config.setVideoImageFormat('jpeg');
Config.setOverwriteOutput(true);
"""

    def _generate_remotion_package(self) -> dict:
        """Generate package.json for Remotion project."""
        return {
            "name": "video-agent-suite-remotion",
            "version": "1.0.0",
            "description": "Remotion video composition generated by Video Agent Suite",
            "scripts": {
                "start": "npx remotion studio",
                "build": "npx remotion render Root out/video.mp4",
                "upgrade": "npx remotion upgrade"
            },
            "dependencies": {
                "@remotion/cli": "^4.0.0",
                "react": "^19.0.0",
                "react-dom": "^19.0.0",
                "remotion": "^4.0.0"
            }
        }

    def _build_hyperframes_composition(self, storyboard: dict, output_dir: Path) -> dict:
        """Generate a Hyperframes composition from the storyboard."""
        self.console.print("  [dim]Building Hyperframes composition...[/dim]")

        scenes = storyboard.get("scenes", [])
        color_palette = storyboard.get("color_palette", ["#1a1a2e", "#16213e", "#0f3460"])

        # Generate the HTML composition
        html_code = self._generate_hyperframes_html(scenes, storyboard)

        # Write the composition
        composition_path = output_dir / "index.html"
        with open(composition_path, "w") as f:
            f.write(html_code)

        # Generate hyperframes.json config
        hf_config = {
            "name": "video-agent-suite-hyperframes",
            "width": 1080,
            "height": 1920,
            "fps": 30,
            "duration": sum(s.get("duration_seconds", 3) for s in scenes),
        }
        with open(output_dir / "hyperframes.json", "w") as f:
            json.dump(hf_config, f, indent=2)

        self.console.print(f"  [green]✓[/green] Hyperframes composition: {composition_path.name}")

        return {
            "status": "generated",
            "entry_point": str(composition_path),
            "total_scenes": len(scenes),
            "config": str(output_dir / "hyperframes.json"),
        }

    def _generate_hyperframes_html(self, scenes: list, storyboard: dict) -> str:
        """Generate Hyperframes HTML composition."""
        color_palette = storyboard.get("color_palette", ["#1a1a2e", "#16213e", "#0f3460"])

        scene_html_parts = []
        current_time = 0

        for i, scene in enumerate(scenes):
            duration = scene.get("duration_seconds", 3)
            script_text = scene.get("script_text", "")
            bg_color = color_palette[i % len(color_palette)]

            # Build scene HTML with data-* timing attributes
            scene_part = f"""    <!-- Scene {scene.get('scene_number', i+1)} -->
    <div class="clip" data-track="0" data-start="{current_time:.2f}s" data-duration="{duration}s"
         style="position:absolute; inset:0; background:{bg_color}; display:flex; flex-direction:column; justify-content:center; align-items:center; padding:40px;">
      <div style="font-size:48px; font-weight:bold; color:white; text-align:center; opacity:0;"
           class="scene-text" data-scene="{scene.get('scene_number', i+1)}">
        {script_text[:80]}{'...' if len(script_text) > 80 else ''}
      </div>
    </div>"""
            scene_html_parts.append(scene_part)
            current_time += duration

        total_duration = sum(s.get("duration_seconds", 3) for s in scenes)

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Video Agent Suite - Hyperframes</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"></script>
  <style>
    body {{ margin: 0; padding: 0; }}
    .composition {{ width: 1080px; height: 1920px; position: relative; overflow: hidden; }}
  </style>
</head>
<body>
  <div id="root" class="composition">
    <div id="main-composition">
{''.join(scene_html_parts)}
    </div>
  </div>

  <script>
    // GSAP Timeline for Hyperframes
    const tl = gsap.timeline({{ paused: true }});
    window.__timelines = window.__timelines || {{}};
    window.__timelines['main'] = tl;

    // Animate each scene
    {self._generate_gsap_animations(scenes)}
  </script>
</body>
</html>"""

    def _generate_gsap_animations(self, scenes: list) -> str:
        """Generate GSAP animation code for each scene."""
        animations = []
        current_time = 0

        for i, scene in enumerate(scenes):
            duration = scene.get("duration_seconds", 3)
            motion = scene.get("motion_type", "fade")

            if motion == "fade" or motion == "static":
                anim = f"""    tl.to('.scene-text[data-scene="{scene.get("scene_number", i+1)}"]', {{
      opacity: 1,
      duration: 0.5,
    }}, {current_time});"""
            elif motion == "slow_zoom":
                anim = f"""    tl.fromTo('.scene-text[data-scene="{scene.get("scene_number", i+1)}"]', {{
      scale: 1,
      opacity: 0,
    }}, {{
      scale: 1.2,
      opacity: 1,
      duration: {duration},
    }}, {current_time});"""
            elif motion == "slide_in":
                anim = f"""    tl.fromTo('.scene-text[data-scene="{scene.get("scene_number", i+1)}"]', {{
      y: 100,
      opacity: 0,
    }}, {{
      y: 0,
      opacity: 1,
      duration: 0.8,
    }}, {current_time});"""
            else:
                anim = f"""    tl.to('.scene-text[data-scene="{scene.get("scene_number", i+1)}"]', {{
      opacity: 1,
      duration: 0.5,
    }}, {current_time});"""

            animations.append(anim)
            current_time += duration

        return "\n".join(animations)
