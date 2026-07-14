"""
Stock Media Agent — sources free stock video and images from Pexels API.
Tries video search first, then image search. Downloads actual files.
"""

import json
import requests
from pathlib import Path
from typing import Optional

from agents.base import BaseAgent, AgentInput, AgentOutput


class StockMediaAgent(BaseAgent):
    """Sources free stock video and images from Pexels API."""

    name = "stock_media"
    description = "Sources stock video/images from Pexels (free)"

    def execute(self, input_data: AgentInput) -> AgentOutput:
        project_dir = input_data.project_dir
        data = input_data.data or {}

        if not project_dir:
            return AgentOutput(success=False, message="No project directory")

        video_dir = project_dir / "assets" / "broll"
        image_dir = project_dir / "assets" / "images"
        video_dir.mkdir(parents=True, exist_ok=True)
        image_dir.mkdir(parents=True, exist_ok=True)

        scenes = data.get("scenes", [])
        prompt = data.get("prompt", "")
        sourced = []

        if scenes:
            for scene in scenes:
                scene_num = scene.get("scene_number", len(sourced) + 1)
                query = scene.get("background", scene.get("script_text", ""))
                if not query:
                    continue

                # Try video first, then image
                vid_path = self._search_pexels_video(query, video_dir, f"scene_{scene_num}")
                if vid_path:
                    sourced.append({"scene": scene_num, "path": str(vid_path), "source": "pexels_video"})
                    continue

                img_path = self._search_pexels_image(query, image_dir, f"scene_{scene_num}_stock")
                if img_path:
                    sourced.append({"scene": scene_num, "path": str(img_path), "source": "pexels_image"})
        elif prompt:
            vid_path = self._search_pexels_video(prompt, video_dir, "stock_1")
            if vid_path:
                sourced.append({"scene": 1, "path": str(vid_path), "source": "pexels_video"})
            else:
                img_path = self._search_pexels_image(prompt, image_dir, "stock_1")
                if img_path:
                    sourced.append({"scene": 1, "path": str(img_path), "source": "pexels_image"})

        return AgentOutput(
            success=len(sourced) > 0,
            data={"stock_media": sourced},
            artifact_path=sourced[0]["path"] if sourced else None,
            message=f"Sourced {len(sourced)} stock media file(s) from Pexels",
            metadata={"count": len(sourced)},
        )

    def _extract_search_terms(self, prompt: str) -> str:
        """Extract key visual terms from a prompt for Pexels search."""
        words = prompt.lower().split()
        filler = {"a", "an", "the", "of", "in", "on", "at", "with", "and", "or", "is", "are",
                   "was", "were", "to", "for", "by", "from", "that", "this", "it", "its", "as"}
        key_words = [w for w in words if w not in filler and len(w) > 2]
        query = " ".join(key_words[:5])
        return query if query else "cinematic"

    def _search_pexels_video(self, query: str, output_dir: Path, filename: str) -> Optional[Path]:
        """Search Pexels for stock video and download it."""
        from config import PEXELS_API_KEY

        if not PEXELS_API_KEY:
            return None

        try:
            search_query = self._extract_search_terms(query)
            self.console.print(f"  [dim]🔍 Pexels video: \"{search_query}\"[/dim]")

            resp = requests.get(
                "https://api.pexels.com/videos/search",
                headers={"Authorization": PEXELS_API_KEY},
                params={"query": search_query, "per_page": 3, "orientation": "portrait"},
                timeout=15,
            )

            if resp.status_code != 200:
                self.console.print(f"  [yellow]⚠ Pexels video search failed: {resp.status_code}[/yellow]")
                return None

            videos = resp.json().get("videos", [])
            if not videos:
                return None

            for video in videos:
                for vf in video.get("video_files", []):
                    if vf.get("height", 0) >= 720 and vf.get("width", 0) > 0:
                        video_url = vf["link"]
                        self.console.print(f"  [green]✓[/green] Pexels video: {vf['width']}x{vf['height']}")

                        vid_path = output_dir / f"{filename}.mp4"
                        vid_data = requests.get(video_url, timeout=60)
                        if vid_data.status_code == 200:
                            with open(vid_path, "wb") as f:
                                f.write(vid_data.content)
                            self.console.print(f"  [green]✓ Downloaded:[/green] {filename}.mp4")
                            return vid_path
                        break

            return None

        except Exception as e:
            self.console.print(f"  [yellow]⚠ Pexels video error: {e}[/yellow]")
            return None

    def _search_pexels_image(self, query: str, output_dir: Path, filename: str) -> Optional[Path]:
        """Search Pexels for stock image and download it."""
        from config import PEXELS_API_KEY

        if not PEXELS_API_KEY:
            return None

        try:
            search_query = self._extract_search_terms(query)
            self.console.print(f"  [dim]🔍 Pexels image: \"{search_query}\"[/dim]")

            resp = requests.get(
                "https://api.pexels.com/v1/search",
                headers={"Authorization": PEXELS_API_KEY},
                params={"query": search_query, "per_page": 3, "orientation": "portrait"},
                timeout=15,
            )

            if resp.status_code != 200:
                return None

            photos = resp.json().get("photos", [])
            if not photos:
                return None

            img_url = photos[0].get("src", {}).get("original", "")
            if not img_url:
                return None

            self.console.print(f"  [green]✓[/green] Pexels image found")

            img_path = output_dir / f"{filename}.jpg"
            img_data = requests.get(img_url, timeout=30)
            if img_data.status_code == 200:
                with open(img_path, "wb") as f:
                    f.write(img_data.content)
                self.console.print(f"  [green]✓ Downloaded:[/green] {filename}.jpg")
                return img_path

            return None

        except Exception as e:
            self.console.print(f"  [yellow]⚠ Pexels image error: {e}[/yellow]")
            return None
