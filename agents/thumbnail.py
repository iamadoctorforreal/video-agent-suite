"""
Thumbnail Generator Agent — creates video thumbnails using AI image generation.
Generates 2 thumbnail variants per video using wan2.6-t2i.
"""

import json
import requests
import time
from pathlib import Path
from typing import Optional

from agents.base import BaseAgent, AgentInput, AgentOutput


class ThumbnailAgent(BaseAgent):
    """Generates video thumbnails."""

    name = "thumbnail"
    description = "Generates video thumbnails"

    def execute(self, input_data: AgentInput) -> AgentOutput:
        project_dir = input_data.project_dir
        script_data = input_data.data

        if not project_dir:
            return AgentOutput(success=False, message="No project directory")

        if not script_data:
            return AgentOutput(success=False, message="No script data for thumbnail generation")

        # Create thumbnail directory
        thumb_dir = project_dir / "thumbnails"
        thumb_dir.mkdir(parents=True, exist_ok=True)

        # Generate 2 thumbnail variants
        thumbnails = []
        hook = script_data.get("hook", "")
        topic = script_data.get("topic", "Video")

        prompts = [
            f"Eye-catching YouTube thumbnail: {hook}. Bold text overlay, vibrant colors, professional. 16:9 aspect ratio.",
            f"Social media thumbnail for '{topic}': Clean design, intriguing visual, high contrast. 16:9 aspect ratio.",
        ]

        for i, prompt in enumerate(prompts, 1):
            thumb_path = self._generate_thumbnail(prompt, thumb_dir, f"thumb_{i}")
            if thumb_path:
                thumbnails.append({"variant": i, "path": str(thumb_path), "prompt": prompt})

        # Save thumbnail manifest
        if thumbnails:
            manifest_path = thumb_dir / "thumbnail_manifest.json"
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump({"thumbnails": thumbnails}, f, indent=2)

        return AgentOutput(
            success=len(thumbnails) > 0,
            data={"thumbnails": thumbnails},
            artifact_path=thumb_dir / "thumbnail_manifest.json" if thumbnails else None,
            message=f"Generated {len(thumbnails)} thumbnails",
            metadata={"count": len(thumbnails)},
        )

    def _generate_thumbnail(self, prompt: str, output_dir: Path, filename: str) -> Optional[Path]:
        """Generate a thumbnail image using wan2.6-t2i."""
        from config import ALIBABA_API_KEY, IMAGE_MODEL

        if not ALIBABA_API_KEY:
            return None

        try:
            # Use DashScope native endpoint for image generation
            url = "https://dashscope-intl.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis"
            headers = {
                "Authorization": f"Bearer {ALIBABA_API_KEY}",
                "Content-Type": "application/json",
                "X-DashScope-Async": "enable",
            }
            payload = {
                "model": IMAGE_MODEL,
                "input": {"prompt": prompt},
                "parameters": {
                    "size": "1920*1080",  # 16:9 for thumbnails
                    "n": 1,
                },
            }

            # Submit async task
            response = requests.post(url, headers=headers, json=payload, timeout=30)

            if response.status_code != 200:
                self.console.print(f"  [yellow]⚠️ Thumbnail gen failed: {response.status_code}[/yellow]")
                return None

            task_data = response.json()
            task_id = task_data.get("output", {}).get("task_id")
            if not task_id:
                return None

            # Poll for completion
            poll_url = f"https://dashscope-intl.aliyuncs.com/api/v1/tasks/{task_id}"
            poll_headers = {"Authorization": f"Bearer {ALIBABA_API_KEY}"}

            for _ in range(30):
                time.sleep(2)
                poll_response = requests.get(poll_url, headers=poll_headers, timeout=10)
                if poll_response.status_code != 200:
                    continue

                result = poll_response.json()
                status = result.get("output", {}).get("task_status", "")

                if status == "SUCCEEDED":
                    results = result.get("output", {}).get("results", [])
                    if results:
                        img_url = results[0].get("url", "")
                        if img_url:
                            img_path = output_dir / f"{filename}.png"
                            img_response = requests.get(img_url, timeout=30)
                            if img_response.status_code == 200:
                                with open(img_path, "wb") as f:
                                    f.write(img_response.content)
                                self.console.print(f"  [green]✓[/green] Thumbnail: {filename}.png")
                                return img_path

                elif status == "FAILED":
                    return None

        except Exception as e:
            self.console.print(f"  [yellow]⚠️ Thumbnail gen error: {str(e)[:50]}[/yellow]")

        return None
