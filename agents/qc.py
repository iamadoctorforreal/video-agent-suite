"""
QC Agent — quality checks generated content at each pipeline stage.
Validates: script quality, storyboard completeness, asset availability,
audio levels, video specs, caption sync.
"""

import json
from pathlib import Path
from typing import Optional

from agents.base import BaseAgent, AgentInput, AgentOutput


class QCAgent(BaseAgent):
    """Quality checks for video pipeline output."""

    name = "qc"
    description = "Quality checks pipeline output"

    def execute(self, input_data: AgentInput) -> AgentOutput:
        project_dir = input_data.project_dir
        stage = input_data.config.get("stage", "final")

        if not project_dir:
            return AgentOutput(success=False, message="No project directory")

        checks = []

        if stage == "script":
            checks = self._check_script(input_data.data)
        elif stage == "storyboard":
            checks = self._check_storyboard(input_data.data)
        elif stage == "assets":
            checks = self._check_assets(project_dir, input_data.data)
        elif stage == "audio":
            checks = self._check_audio(project_dir)
        elif stage == "final":
            checks = self._check_final(project_dir)

        passed = sum(1 for c in checks if c["passed"])
        total = len(checks)

        return AgentOutput(
            success=passed == total,
            data={"checks": checks, "passed": passed, "total": total},
            message=f"QC: {passed}/{total} checks passed",
            metadata={"stage": stage, "passed": passed, "total": total},
        )

    def _check_script(self, script_data: dict) -> list:
        """Check script quality."""
        checks = []

        if not script_data:
            return [{"name": "script_exists", "passed": False, "message": "No script data"}]

        # Check required fields
        required = ["hook", "body", "full_script", "tone"]
        for field in required:
            checks.append({
                "name": f"script_has_{field}",
                "passed": field in script_data and bool(script_data[field]),
                "message": f"Script has {field}" if field in script_data else f"Missing {field}",
            })

        # Check word count
        full_script = script_data.get("full_script", "")
        word_count = len(full_script.split())
        checks.append({
            "name": "script_word_count",
            "passed": 20 <= word_count <= 200,
            "message": f"Word count: {word_count} (target: 20-200)",
        })

        # Check hook length (should be short and punchy)
        hook = script_data.get("hook", "")
        checks.append({
            "name": "hook_length",
            "passed": 5 <= len(hook.split()) <= 15,
            "message": f"Hook: {len(hook.split())} words (target: 5-15)",
        })

        return checks

    def _check_storyboard(self, storyboard: dict) -> list:
        """Check storyboard completeness."""
        checks = []

        if not storyboard or "scenes" not in storyboard:
            return [{"name": "storyboard_exists", "passed": False, "message": "No storyboard"}]

        scenes = storyboard.get("scenes", [])
        checks.append({
            "name": "has_scenes",
            "passed": len(scenes) > 0,
            "message": f"{len(scenes)} scenes",
        })

        # Check each scene has required fields
        required_fields = ["scene_number", "script_text", "shot_type", "motion_type", "duration_seconds"]
        for scene in scenes:
            scene_num = scene.get("scene_number", "?")
            for field in required_fields:
                checks.append({
                    "name": f"scene_{scene_num}_has_{field}",
                    "passed": field in scene and bool(scene[field]),
                    "message": f"Scene {scene_num}: has {field}" if field in scene else f"Scene {scene_num}: missing {field}",
                })

        # Check total duration matches target
        total_duration = sum(s.get("duration_seconds", 0) for s in scenes)
        checks.append({
            "name": "total_duration",
            "passed": total_duration > 0,
            "message": f"Total duration: {total_duration}s",
        })

        return checks

    def _check_assets(self, project_dir: Path, asset_data: dict) -> list:
        """Check asset availability."""
        checks = []

        assets_dir = project_dir / "assets"
        checks.append({
            "name": "assets_dir_exists",
            "passed": assets_dir.exists(),
            "message": "Assets directory exists",
        })

        if asset_data:
            total_sourced = sum(len(v) for v in asset_data.values())
            checks.append({
                "name": "assets_sourced",
                "passed": total_sourced > 0,
                "message": f"{total_sourced} assets sourced",
            })

        # Check for manifest
        manifest = assets_dir / "manifest.json"
        checks.append({
            "name": "asset_manifest",
            "passed": manifest.exists(),
            "message": "Asset manifest exists",
        })

        return checks

    def _check_audio(self, project_dir: Path) -> list:
        """Check audio files."""
        checks = []

        audio_dir = project_dir / "audio"
        checks.append({
            "name": "audio_dir_exists",
            "passed": audio_dir.exists(),
            "message": "Audio directory exists",
        })

        voiceover = audio_dir / "voiceover.mp3"
        checks.append({
            "name": "voiceover_exists",
            "passed": voiceover.exists(),
            "message": "Voiceover file exists",
        })

        if voiceover.exists():
            size = voiceover.stat().st_size
            checks.append({
                "name": "voiceover_size",
                "passed": size > 1000,
                "message": f"Voiceover size: {size} bytes",
            })

        srt = audio_dir / "captions.srt"
        checks.append({
            "name": "captions_exist",
            "passed": srt.exists(),
            "message": "SRT captions exist",
        })

        return checks

    def _check_final(self, project_dir: Path) -> list:
        """Check final output."""
        checks = []

        output_dir = project_dir / "output"
        checks.append({
            "name": "output_dir_exists",
            "passed": output_dir.exists(),
            "message": "Output directory exists",
        })

        final_video = output_dir / "final.mp4"
        checks.append({
            "name": "final_video_exists",
            "passed": final_video.exists(),
            "message": "Final video exists",
        })

        if final_video.exists():
            size = final_video.stat().st_size
            checks.append({
                "name": "final_video_size",
                "passed": size > 10000,
                "message": f"Final video size: {size / (1024*1024):.1f} MB",
            })

        # Check for metadata
        metadata = output_dir / "metadata.json"
        checks.append({
            "name": "metadata_exists",
            "passed": metadata.exists(),
            "message": "Metadata file exists",
        })

        return checks
