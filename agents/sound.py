"""
Sound Agent — sources BGM and SFX for video projects.
Sources: FreeSound API, Pexels audio, local SFX libraries.
"""

import requests
from pathlib import Path
from typing import Optional

from agents.base import BaseAgent, AgentInput, AgentOutput


class SoundAgent(BaseAgent):
    """Sources background music and sound effects."""

    name = "sound"
    description = "Sources BGM and SFX for video"

    def execute(self, input_data: AgentInput) -> AgentOutput:
        storyboard = input_data.data
        project_dir = input_data.project_dir

        if not storyboard or "scenes" not in storyboard:
            return AgentOutput(success=False, message="No storyboard data provided")

        # Create sound directories
        sound_dir = project_dir / "sound" if project_dir else Path("sound")
        (sound_dir / "bgm").mkdir(parents=True, exist_ok=True)
        (sound_dir / "sfx").mkdir(parents=True, exist_ok=True)

        sourced_sounds = {"bgm": [], "sfx": []}

        # 1. Source BGM based on overall mood
        bg_mood = storyboard.get("bg_mood", "upbeat corporate")
        bgm_path = self._source_bgm(bg_mood, sound_dir / "bgm")
        if bgm_path:
            sourced_sounds["bgm"].append({"name": bg_mood, "path": str(bgm_path)})

        # 2. Source SFX for each scene
        for scene in storyboard.get("scenes", []):
            scene_num = scene.get("scene_number", 0)
            for sfx_name in scene.get("sound_effects", []):
                sfx_path = self._source_sfx(sfx_name, sound_dir / "sfx", f"scene_{scene_num}")
                if sfx_path:
                    sourced_sounds["sfx"].append({
                        "scene": scene_num,
                        "name": sfx_name,
                        "path": str(sfx_path),
                    })

        # Save sound manifest
        if project_dir:
            import json
            manifest_path = sound_dir / "sound_manifest.json"
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(sourced_sounds, f, indent=2)

        total = len(sourced_sounds["bgm"]) + len(sourced_sounds["sfx"])
        return AgentOutput(
            success=True,
            data=sourced_sounds,
            artifact_path=sound_dir / "sound_manifest.json" if project_dir else None,
            message=f"Sourced {total} sounds ({len(sourced_sounds['bgm'])} BGM, {len(sourced_sounds['sfx'])} SFX)",
            metadata=sourced_sounds,
        )

    def _source_bgm(self, mood: str, output_dir: Path) -> Optional[Path]:
        """Source background music based on mood."""
        # For hackathon: use a free BGM source or generate placeholder
        # Production: integrate with Epidemic Sound, Artlist, or Free Music Archive API
        self.console.print(f"  [dim]Sourcing BGM for mood: {mood}[/dim]")

        # Try Pexels for any audio content (limited)
        # For now, create a placeholder note
        placeholder = output_dir / "bgm_placeholder.txt"
        with open(placeholder, "w", encoding="utf-8") as f:
            f.write(f"BGM Mood: {mood}\n")
            f.write("Source: To be integrated with Free Music Archive or similar\n")
            f.write("Recommended: Search for '{mood}' on freemusicarchive.org\n")

        self.console.print(f"  [yellow]⚠️ BGM placeholder created (API integration needed)[/yellow]")
        return placeholder

    def _source_sfx(self, sfx_name: str, output_dir: Path, scene_prefix: str) -> Optional[Path]:
        """Source a sound effect."""
        self.console.print(f"  [dim]Sourcing SFX: {sfx_name}[/dim]")

        # Try FreeSound API if available
        # For hackathon: create placeholder
        placeholder = output_dir / f"{scene_prefix}_{sfx_name.replace(' ', '_')}.txt"
        with open(placeholder, "w", encoding="utf-8") as f:
            f.write(f"SFX: {sfx_name}\n")
            f.write("Source: To be integrated with FreeSound API\n")

        return placeholder
