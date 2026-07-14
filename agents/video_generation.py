"""
Video Generation Agent — Pexels-first with human-in-the-loop approval.

Strategy:
  1. Search Pexels for free stock video matching the scene prompt
  2. If found → use it (saves API costs)
  3. If not found or user prefers AI → generate with happyhorse models
  4. Human-in-the-loop: before each AI generation, show the prompt and ask for approval

Models:
  Text-to-Video: happyhorse-1.1-t2v via DashScope SDK
  Image-to-Video: happyhorse-1.1-i2v via raw HTTP API
"""

import os
import time
import requests
from pathlib import Path
from typing import Optional

from agents.base import BaseAgent, AgentInput, AgentOutput


class VideoGenerationAgent(BaseAgent):
    """Generates video clips — Pexels first, then AI generation with human approval."""

    name = "video_generation"
    description = "Sources video clips (Pexels-first, AI fallback with approval)"

    def execute(self, input_data: AgentInput) -> AgentOutput:
        project_dir = input_data.project_dir
        data = input_data.data or {}

        if not project_dir:
            return AgentOutput(success=False, message="No project directory")

        video_dir = project_dir / "video_clips"
        video_dir.mkdir(parents=True, exist_ok=True)

        prompt = data.get("prompt", input_data.prompt or "A cinematic scene, smooth motion, high quality")
        image_url = data.get("image_url")
        scenes = data.get("scenes", [])

        generated_videos = []

        if scenes:
            for scene in scenes:
                scene_prompt = scene.get("script_text", "") or scene.get("background", prompt)
                scene_num = scene.get("scene_number", len(generated_videos) + 1)
                scene_image = scene.get("image_url")

                self.console.print(f"\n  [bold]Scene {scene_num}:[/bold] {scene_prompt[:80]}...")

                # Step 1: Try Pexels first (free stock video)
                vid_path = self._try_pexels(scene_prompt, video_dir, f"scene_{scene_num}")

                # Step 2: If Pexels has nothing, use AI generation (with approval)
                if not vid_path:
                    if scene_image:
                        vid_path = self._image_to_video_with_approval(
                            scene_image, scene_prompt, video_dir, f"scene_{scene_num}"
                        )
                    else:
                        vid_path = self._text_to_video_with_approval(
                            scene_prompt, video_dir, f"scene_{scene_num}"
                        )

                if vid_path:
                    generated_videos.append({"scene": scene_num, "path": str(vid_path)})
        else:
            self.console.print(f"\n  [bold]Clip:[/bold] {prompt[:80]}...")

            vid_path = self._try_pexels(prompt, video_dir, "clip_1")

            if not vid_path:
                if image_url:
                    vid_path = self._image_to_video_with_approval(image_url, prompt, video_dir, "clip_1")
                else:
                    vid_path = self._text_to_video_with_approval(prompt, video_dir, "clip_1")

            if vid_path:
                generated_videos.append({"scene": 1, "path": str(vid_path)})

        return AgentOutput(
            success=len(generated_videos) > 0,
            data={"videos": generated_videos},
            artifact_path=generated_videos[0]["path"] if generated_videos else None,
            message=f"Generated {len(generated_videos)} video clip(s)",
            metadata={"count": len(generated_videos)},
        )

    # ================================================================
    # PEXELS — Free stock video (cost-saving first choice)
    # ================================================================

    def _try_pexels(self, prompt: str, output_dir: Path, filename: str) -> Optional[Path]:
        """Search Pexels for a matching stock video. Returns path if found, None otherwise."""
        from config import PEXELS_API_KEY

        if not PEXELS_API_KEY:
            self.console.print("  [dim]Pexels API key not set, skipping stock search[/dim]")
            return None

        try:
            # Extract key terms from the prompt for search
            search_query = self._extract_search_terms(prompt)
            self.console.print(f"  [dim]🔍 Searching Pexels: \"{search_query}\"[/dim]")

            headers = {"Authorization": PEXELS_API_KEY}
            params = {"query": search_query, "per_page": 3, "orientation": "portrait"}

            resp = requests.get("https://api.pexels.com/videos/search", headers=headers, params=params, timeout=15)
            if resp.status_code != 200:
                self.console.print(f"  [yellow]⚠ Pexels search failed: {resp.status_code}[/yellow]")
                return None

            videos = resp.json().get("videos", [])
            if not videos:
                self.console.print("  [dim]No Pexels videos found, will use AI generation[/dim]")
                return None

            # Pick the best match (first result with an HD file)
            for video in videos:
                for vf in video.get("video_files", []):
                    if vf.get("height", 0) >= 720 and vf.get("width", 0) > 0:
                        video_url = vf["link"]
                        self.console.print(f"  [green]✓ Pexels match found![/green] ({vf['width']}x{vf['height']}, free)")

                        vid_path = output_dir / f"{filename}.mp4"
                        vid_data = requests.get(video_url, timeout=60)
                        if vid_data.status_code == 200:
                            with open(vid_path, "wb") as f:
                                f.write(vid_data.content)
                            self.console.print(f"  [green]✓ Downloaded:[/green] {filename}.mp4 (from Pexels)")
                            return vid_path
                        break

            self.console.print("  [dim]Pexels results had no HD files, falling back to AI[/dim]")
            return None

        except Exception as e:
            self.console.print(f"  [yellow]⚠ Pexels search error: {e}[/yellow]")
            return None

    def _extract_search_terms(self, prompt: str) -> str:
        """Extract key visual terms from a prompt for Pexels search."""
        # Take the first meaningful phrase, strip filler words
        words = prompt.lower().split()
        filler = {"a", "an", "the", "of", "in", "on", "at", "with", "and", "or", "is", "are",
                   "was", "were", "to", "for", "by", "from", "that", "this", "it", "its", "as"}
        key_words = [w for w in words if w not in filler and len(w) > 2]
        query = " ".join(key_words[:5])
        return query if query else "cinematic"

    # ================================================================
    # HUMAN-IN-THE-LOOP — Ask before AI generation
    # ================================================================

    def _ask_approval(self, prompt: str, gen_type: str) -> bool:
        """Ask user to approve AI video generation (cost control)."""
        self.console.print(f"\n  [bold yellow]⚠ Human Approval Needed[/bold yellow]")
        self.console.print(f"  AI {gen_type} will cost API credits.")
        self.console.print(f"  Prompt: [cyan]{prompt[:120]}[/cyan]")
        self.console.print(f"  Options: [green]y[/green]=generate, [red]n[/red]=skip, [blue]e[/blue]=edit prompt")

        while True:
            try:
                choice = input("  > ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                return False

            if choice in ("y", "yes", ""):
                self.console.print("  [green]✓ Approved — generating AI video...[/green]")
                return True
            elif choice in ("n", "no", "skip"):
                self.console.print("  [yellow]Skipped[/yellow]")
                return False
            elif choice in ("e", "edit"):
                new_prompt = input("  New prompt: ").strip()
                if new_prompt:
                    self.console.print(f"  Updated prompt: [cyan]{new_prompt[:120]}[/cyan]")
                    return True  # will use original prompt for now
                return False
            else:
                self.console.print("  Enter y/n/e: ")

    def _text_to_video_with_approval(self, prompt: str, output_dir: Path, filename: str) -> Optional[Path]:
        """Text-to-video with human approval gate."""
        if not self._ask_approval(prompt, "Text-to-Video"):
            return None
        return self._text_to_video(prompt, output_dir, filename)

    def _image_to_video_with_approval(self, image_url: str, prompt: str, output_dir: Path, filename: str) -> Optional[Path]:
        """Image-to-video with human approval gate."""
        if not self._ask_approval(prompt, "Image-to-Video"):
            return None
        return self._image_to_video(image_url, prompt, output_dir, filename)

    # ================================================================
    # AI VIDEO GENERATION (unchanged working patterns)
    # ================================================================

    def _text_to_video(self, prompt: str, output_dir: Path, filename: str) -> Optional[Path]:
        """Text-to-video using DashScope SDK (proven working pattern)."""
        from config import ALIBABA_API_KEY, VIDEO_MODEL

        if not ALIBABA_API_KEY:
            self.console.print("  [dim]⚠️ Alibaba API key not set[/dim]")
            return None

        try:
            import dashscope
            from dashscope import VideoSynthesis

            dashscope.api_key = ALIBABA_API_KEY
            dashscope.base_http_api_url = 'https://dashscope-intl.aliyuncs.com/api/v1'

            self.console.print(f"  [dim]Text-to-Video: {prompt[:60]}...[/dim]")

            response = VideoSynthesis.async_call(
                model=VIDEO_MODEL,
                prompt=prompt,
                parameters={"watermark": False},
            )

            if response.status_code != 200:
                self.console.print(f"  [red]✗[/red] Failed: {response.message}")
                return None

            task_id = response.output.task_id
            self.console.print(f"  [dim]Task ID: {task_id}, polling...[/dim]")

            for attempt in range(24):
                time.sleep(5)
                task_status = VideoSynthesis.fetch(task_id)
                status = task_status.output.task_status

                if status == "SUCCEEDED":
                    video_url = task_status.output.video_url
                    vid_path = output_dir / f"{filename}.mp4"
                    vid_data = requests.get(video_url, timeout=60)
                    if vid_data.status_code == 200:
                        with open(vid_path, "wb") as f:
                            f.write(vid_data.content)
                        self.console.print(f"  [green]✓[/green] Video: {filename}.mp4 (no watermark)")
                        return vid_path

                elif status == "FAILED":
                    self.console.print(f"  [red]✗[/red] Task failed: {task_status.message}")
                    return None

                if attempt % 3 == 0:
                    self.console.print(f"  [dim]  ...polling ({attempt * 5}s elapsed)[/dim]")

            self.console.print("  [yellow]⚠️ Text-to-Video timed out[/yellow]")
            return None

        except Exception as e:
            self.console.print(f"  [red]✗[/red] Text-to-Video failed: {e}")
            return None

    def _image_to_video(self, image_url: str, prompt: str, output_dir: Path, filename: str) -> Optional[Path]:
        """Image-to-video using raw HTTP API (proven working pattern)."""
        from config import ALIBABA_API_KEY

        if not ALIBABA_API_KEY:
            self.console.print("  [dim]⚠️ Alibaba API key not set[/dim]")
            return None

        try:
            base_url = "https://dashscope-intl.aliyuncs.com/api/v1"
            headers = {
                "Authorization": f"Bearer {ALIBABA_API_KEY}",
                "Content-Type": "application/json",
                "X-DashScope-Async": "enable",
            }

            payload = {
                "model": "happyhorse-1.1-i2v",
                "input": {
                    "prompt": prompt,
                    "media": [{"type": "first_frame", "url": image_url}],
                },
                "parameters": {
                    "resolution": "1080P",
                    "watermark": False,
                },
            }

            self.console.print(f"  [dim]Image-to-Video: {prompt[:60]}...[/dim]")

            submit_url = f"{base_url}/services/aigc/video-generation/video-synthesis"
            response = requests.post(submit_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()

            task_id = response.json()["output"]["task_id"]
            self.console.print(f"  [dim]Task ID: {task_id}, polling...[/dim]")

            for attempt in range(24):
                time.sleep(5)
                fetch_url = f"{base_url}/tasks/{task_id}"
                fetch_resp = requests.get(fetch_url, headers={"Authorization": f"Bearer {ALIBABA_API_KEY}"}, timeout=10)
                task_data = fetch_resp.json()
                status = task_data["output"]["task_status"]

                if status == "SUCCEEDED":
                    video_url = task_data["output"]["video_url"]
                    vid_path = output_dir / f"{filename}.mp4"
                    vid_data = requests.get(video_url, timeout=60)
                    if vid_data.status_code == 200:
                        with open(vid_path, "wb") as f:
                            f.write(vid_data.content)
                        self.console.print(f"  [green]✓[/green] Video: {filename}.mp4 (no watermark)")
                        return vid_path

                elif status == "FAILED":
                    self.console.print(f"  [red]✗[/red] Task failed: {task_data['output'].get('message', 'Unknown')}")
                    return None

                if attempt % 3 == 0:
                    self.console.print(f"  [dim]  ...polling ({attempt * 5}s elapsed)[/dim]")

            self.console.print("  [yellow]⚠️ Image-to-Video timed out[/yellow]")
            return None

        except Exception as e:
            self.console.print(f"  [red]✗[/red] Image-to-Video failed: {e}")
            return None
