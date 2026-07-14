"""
Image Generation Agent — generates AI images for scene backgrounds using Alibaba wan2.6-t2i.
Uses DashScope SDK (proven working pattern from desktop/qwen agent/).
"""

import time
import requests
from pathlib import Path
from typing import Optional

from agents.base import BaseAgent, AgentInput, AgentOutput


class ImageGenAgent(BaseAgent):
    """Generates AI images for scene backgrounds using Alibaba wan2.6-t2i."""

    name = "image_gen"
    description = "Generates AI images via Alibaba wan2.6-t2i"

    def execute(self, input_data: AgentInput) -> AgentOutput:
        project_dir = input_data.project_dir
        data = input_data.data or {}

        if not project_dir:
            return AgentOutput(success=False, message="No project directory")

        images_dir = project_dir / "assets" / "images"
        images_dir.mkdir(parents=True, exist_ok=True)

        scenes = data.get("scenes", [])
        prompt = data.get("prompt", "")
        generated = []

        if scenes:
            for scene in scenes:
                scene_num = scene.get("scene_number", len(generated) + 1)
                bg = scene.get("background", scene.get("script_text", ""))
                if not bg:
                    continue

                self.console.print(f"  [dim]Scene {scene_num}: generating image...[/dim]")
                img_path = self._generate_image(bg, images_dir, f"scene_{scene_num}")
                if img_path:
                    generated.append({"scene": scene_num, "path": str(img_path), "source": "ai_generated"})
        elif prompt:
            img_path = self._generate_image(prompt, images_dir, "image_1")
            if img_path:
                generated.append({"scene": 1, "path": str(img_path), "source": "ai_generated"})

        return AgentOutput(
            success=len(generated) > 0,
            data={"images": generated},
            artifact_path=generated[0]["path"] if generated else None,
            message=f"Generated {len(generated)} AI image(s)",
            metadata={"count": len(generated)},
        )

    def _generate_image(self, prompt: str, output_dir: Path, filename: str) -> Optional[Path]:
        """Generate an image using DashScope SDK."""
        from config import ALIBABA_API_KEY, IMAGE_MODEL

        if not ALIBABA_API_KEY:
            self.console.print("  [dim]Alibaba API key not set, skipping image gen[/dim]")
            return None

        try:
            import dashscope
            from dashscope.aigc.image_generation import ImageGeneration
            from dashscope.api_entities.dashscope_response import Message

            dashscope.api_key = ALIBABA_API_KEY
            dashscope.base_http_api_url = 'https://dashscope-intl.aliyuncs.com/api/v1'

            full_prompt = f"Social media video background: {prompt}. Clean, modern. Vertical 9:16. No text."
            message = Message(role="user", content=[{"text": full_prompt}])

            self.console.print(f"  [dim]Image gen: {prompt[:60]}...[/dim]")

            response = ImageGeneration.async_call(
                model=IMAGE_MODEL,
                api_key=ALIBABA_API_KEY,
                messages=[message],
                n=1,
                size="1280*1280",
                prompt_extend=True,
            )

            if response.status_code != 200:
                self.console.print(f"  [red]✗[/red] Image gen submit failed: {response.message}")
                return None

            task_id = response.output.task_id

            for attempt in range(24):
                time.sleep(5)
                task_status = ImageGeneration.fetch(task_id, api_key=ALIBABA_API_KEY)
                status = task_status.output.task_status

                if status == "SUCCEEDED":
                    if hasattr(task_status.output, 'results') and task_status.output.results:
                        img_url = task_status.output.results[0].url
                    else:
                        img_url = task_status.output.choices[0].message.content[0]["image"]

                    img_path = output_dir / f"{filename}.png"
                    img_data = requests.get(img_url, timeout=30)
                    if img_data.status_code == 200:
                        with open(img_path, "wb") as f:
                            f.write(img_data.content)
                        self.console.print(f"  [green]✓[/green] AI image: {filename}.png")
                        return img_path

                elif status == "FAILED":
                    self.console.print(f"  [red]✗[/red] Image gen failed: {task_status.message}")
                    return None

                if attempt % 3 == 0:
                    self.console.print(f"  [dim]  ...polling ({attempt * 5}s)[/dim]")

            self.console.print("  [yellow]⚠️ Image gen timed out[/yellow]")
            return None

        except Exception as e:
            self.console.print(f"  [red]✗[/red] Image gen error: {e}")
            return None
