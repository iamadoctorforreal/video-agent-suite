"""
Director Agent — creates storyboards from scripts.
Defines shot types, visual elements, animations, sound design per scene.
"""

import json
from pathlib import Path
from agents.base import BaseAgent, AgentInput, AgentOutput


DIRECTOR_SYSTEM_PROMPT = """You are an expert video director and storyboard artist.

Given a script, create a detailed scene-by-scene storyboard for a short-form social media video.

Each scene must specify:
- scene_number: Sequential scene number
- script_text: The exact script text for this scene
- shot_type: "close_up", "medium", "wide", "over_shoulder", "top_down", "macro", "screen_recording"
- motion_type: "static", "slow_zoom", "pan_left", "pan_right", "tilt_up", "tilt_down", "push_in", "pull_out", "slide_in", "slide_out", "fade", "dissolve"
- has_avatar: true/false — Is there a person/avatar on screen?
- has_character: true/false — Is there a illustrated character?
- has_headshot: true/false — Is there a headshot photo?
- background: Description of the background
- visual_elements: Array of UI/graphic elements needed (logos, text overlays, icons, etc.)
- animation_description: How elements animate into/out of the frame
- feel: The mood/energy of this scene (e.g., "energetic", "calm", "dramatic")
- emotion_evoked: The target emotional response
- sound_effects: Array of SFX needed (e.g., "whoosh", "pop", "click")
- bg_mood: Background music mood for this scene
- transition: How this scene transitions to the next ("cut", "dissolve", "slide", "zoom", "wipe")
- duration_seconds: Estimated duration of this scene

Return VALID JSON only, with this structure:
{
  "scenes": [
    {
      "scene_number": 1,
      "script_text": "...",
      "shot_type": "...",
      "motion_type": "...",
      "has_avatar": false,
      "has_character": false,
      "has_headshot": false,
      "background": "...",
      "visual_elements": ["element1", "element2"],
      "animation_description": "...",
      "feel": "...",
      "emotion_evoked": "...",
      "sound_effects": ["sfx1", "sfx2"],
      "bg_mood": "...",
      "transition": "...",
      "duration_seconds": 3
    }
  ],
  "total_scenes": 5,
  "total_duration_seconds": 30,
  "overall_style": "description of overall visual style",
  "color_palette": ["#hex1", "#hex2", "#hex3"],
  "font_style": "description of typography approach"
}"""


class DirectorAgent(BaseAgent):
    """Creates detailed storyboards from scripts."""

    name = "director"
    description = "Creates scene-by-scene storyboards"

    def execute(self, input_data: AgentInput) -> AgentOutput:
        script_text = input_data.prompt
        aspect_ratio = input_data.config.get("aspect_ratio", "9:16")

        user_prompt = f"""Create a storyboard for this script:

{script_text}

Aspect ratio: {aspect_ratio} (vertical social media)
Total target duration: {input_data.config.get('duration', 30)} seconds

Break the script into scenes. Each scene should be 3-8 seconds.
Make sure the visual elements can be sourced from:
- Brand assets (logos, colors, fonts from Figma)
- Stock imagery (Pexels for b-roll)
- AI-generated images (when nothing else fits)
- Motion graphics (text animations, kinetic typography)"""

        try:
            response = self.call_llm(DIRECTOR_SYSTEM_PROMPT, user_prompt)

            # Parse JSON
            storyboard = json.loads(response)

            # Save storyboard to project directory
            if input_data.project_dir:
                sb_path = input_data.project_dir / "storyboard.json"
                with open(sb_path, "w", encoding="utf-8") as f:
                    json.dump(storyboard, f, indent=2, ensure_ascii=False)

                # Also save a human-readable version
                md_path = input_data.project_dir / "STORYBOARD.md"
                md_content = self._to_markdown(storyboard)
                with open(md_path, "w", encoding="utf-8") as f:
                    f.write(md_content)

            return AgentOutput(
                success=True,
                data=storyboard,
                artifact_path=input_data.project_dir / "storyboard.json" if input_data.project_dir else None,
                message=f"Storyboard created: {storyboard.get('total_scenes', '?')} scenes, {storyboard.get('total_duration_seconds', '?')}s total",
                metadata={
                    "scenes": storyboard.get("total_scenes"),
                    "style": storyboard.get("overall_style"),
                },
            )

        except json.JSONDecodeError as e:
            import re
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                try:
                    storyboard = json.loads(json_match.group())
                    return AgentOutput(
                        success=True,
                        data=storyboard,
                        message="Storyboard generated (JSON extracted from response)",
                        metadata=storyboard,
                    )
                except json.JSONDecodeError:
                    pass

            return AgentOutput(
                success=False,
                message=f"Failed to parse storyboard JSON: {e}",
            )

    def _to_markdown(self, storyboard: dict) -> str:
        """Convert storyboard to human-readable Markdown."""
        lines = [
            "# Video Storyboard\n",
            f"**Style:** {storyboard.get('overall_style', 'N/A')}\n",
            f"**Total Scenes:** {storyboard.get('total_scenes', '?')}\n",
            f"**Total Duration:** {storyboard.get('total_duration_seconds', '?')}s\n",
            f"**Color Palette:** {', '.join(storyboard.get('color_palette', []))}\n",
            f"**Typography:** {storyboard.get('font_style', 'N/A')}\n",
            "---\n",
        ]

        for scene in storyboard.get("scenes", []):
            lines.extend([
                f"\n## Scene {scene.get('scene_number', '?')}\n",
                f"- **Script:** {scene.get('script_text', '')}",
                f"- **Shot:** {scene.get('shot_type', '')} | **Motion:** {scene.get('motion_type', '')}",
                f"- **Duration:** {scene.get('duration_seconds', '?')}s | **Transition:** {scene.get('transition', '')}",
                f"- **Background:** {scene.get('background', '')}",
                f"- **Feel:** {scene.get('feel', '')} → **Emotion:** {scene.get('emotion_evoked', '')}",
                f"- **Elements:** {', '.join(scene.get('visual_elements', []))}",
                f"- **Animation:** {scene.get('animation_description', '')}",
                f"- **SFX:** {', '.join(scene.get('sound_effects', []))} | **BGM:** {scene.get('bg_mood', '')}",
                "",
            ])

        return "\n".join(lines)
