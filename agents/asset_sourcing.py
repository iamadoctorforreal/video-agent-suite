"""
Asset Sourcing Agent — sources images, b-roll, logos from various sources.
Sources: Pexels API, local brand folders, Alibaba image generation.
"""

import os
import requests
from pathlib import Path
from typing import Optional

from agents.base import BaseAgent, AgentInput, AgentOutput


class AssetSourcingAgent(BaseAgent):
    """Sources visual assets from Pexels, local folders, and AI image generation."""

    name = "asset_sourcing"
    description = "Sources visual assets (images, b-roll, logos)"

    def execute(self, input_data: AgentInput) -> AgentOutput:
        storyboard = input_data.data  # The storyboard from director agent
        project_dir = input_data.project_dir

        if not storyboard or "scenes" not in storyboard:
            return AgentOutput(success=False, message="No storyboard data provided")

        # Create asset directories
        assets_dir = project_dir / "assets" if project_dir else Path("assets")
        (assets_dir / "images").mkdir(parents=True, exist_ok=True)
        (assets_dir / "broll").mkdir(parents=True, exist_ok=True)
        (assets_dir / "logos").mkdir(parents=True, exist_ok=True)
        (assets_dir / "icons").mkdir(parents=True, exist_ok=True)

        sourced_assets = {}

        for scene in storyboard.get("scenes", []):
            scene_num = scene.get("scene_number", 0)
            scene_assets = []

            # 1. Check visual elements for brand assets
            for element in scene.get("visual_elements", []):
                asset_type = self._classify_element(element)
                if asset_type == "logo":
                    # Check local brand folder first
                    logo_path = self._find_local_asset(element, "logos")
                    if logo_path:
                        scene_assets.append({"type": "logo", "name": element, "path": str(logo_path), "source": "local"})

            # 2. Source b-roll if needed
            if scene.get("shot_type") in ["screen_recording", "wide", "medium"]:
                broll_query = scene.get("background", "office workspace")
                broll_path = self._search_pexels(broll_query, assets_dir / "broll", f"scene_{scene_num}")
                if broll_path:
                    scene_assets.append({"type": "broll", "name": broll_query, "path": str(broll_path), "source": "pexels"})

            # 3. Generate images with AI if no asset found
            if not scene_assets and not scene.get("has_avatar") and not scene.get("has_character"):
                image_query = scene.get("background", "modern abstract background")
                image_path = self._generate_image(image_query, assets_dir / "images", f"scene_{scene_num}")
                if image_path:
                    scene_assets.append({"type": "image", "name": image_query, "path": str(image_path), "source": "ai_generated"})

            sourced_assets[f"scene_{scene_num}"] = scene_assets

        # Save asset manifest
        if project_dir:
            manifest_path = project_dir / "assets" / "manifest.json"
            import json
            with open(manifest_path, "w") as f:
                json.dump(sourced_assets, f, indent=2)

        total_sourced = sum(len(v) for v in sourced_assets.values())
        return AgentOutput(
            success=True,
            data=sourced_assets,
            artifact_path=project_dir / "assets" / "manifest.json" if project_dir else None,
            message=f"Sourced {total_sourced} assets across {len(sourced_assets)} scenes",
            metadata=sourced_assets,
        )

    def _classify_element(self, element: str) -> str:
        """Classify a visual element type."""
        element_lower = element.lower()
        if any(k in element_lower for k in ["logo", "brand", "icon"]):
            return "logo"
        elif any(k in element_lower for k in ["photo", "image", "picture", "broll"]):
            return "image"
        elif any(k in element_lower for k in ["text", "title", "caption"]):
            return "text"
        else:
            return "image"

    def _find_local_asset(self, name: str, asset_type: str) -> Optional[Path]:
        """Look for an asset in local brand/project folders."""
        from config import PROJECTS_DIR

        # Check common locations
        search_dirs = [
            PROJECTS_DIR / "brand" / asset_type,
            PROJECTS_DIR / "assets" / asset_type,
            Path.home() / "Desktop" / "brand_assets" / asset_type,
        ]

        for search_dir in search_dirs:
            if search_dir.exists():
                # Search for files matching the name
                for ext in [".png", ".svg", ".jpg", ".jpeg", ".webp"]:
                    candidate = search_dir / f"{name}{ext}"
                    if candidate.exists():
                        return candidate
                    # Also try fuzzy match
                    for f in search_dir.iterdir():
                        if name.lower() in f.stem.lower():
                            return f

        return None

    def _search_pexels(self, query: str, output_dir: Path, filename: str) -> Optional[Path]:
        """Search Pexels for b-roll footage or images."""
        from config import PEXELS_API_KEY

        if not PEXELS_API_KEY:
            self.console.print(f"  [dim]⚠️ Pexels API key not set, skipping b-roll for: {query}[/dim]")
            return None

        try:
            # Try video first
            response = requests.get(
                "https://api.pexels.com/videos/search",
                headers={"Authorization": PEXELS_API_KEY},
                params={"query": query, "per_page": 3, "orientation": "portrait"},
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("videos"):
                    video = data["videos"][0]
                    # Get the best quality video file
                    video_files = video.get("video_files", [])
                    if video_files:
                        # Just record the URL for now (download would need additional code)
                        video_url = video_files[0].get("link", "")
                        self.console.print(f"  [green]✓[/green] Pexels video found: {video_url[:80]}...")
                        # For hackathon: just record the URL
                        import json
                        url_file = output_dir / f"{filename}_pexels_url.json"
                        with open(url_file, "w") as f:
                            json.dump({"url": video_url, "query": query}, f)
                        return url_file

            # Fallback: search images
            img_response = requests.get(
                "https://api.pexels.com/v1/search",
                headers={"Authorization": PEXELS_API_KEY},
                params={"query": query, "per_page": 1, "orientation": "portrait"},
                timeout=10,
            )

            if img_response.status_code == 200:
                data = img_response.json()
                if data.get("photos"):
                    photo = data["photos"][0]
                    img_url = photo.get("src", {}).get("original", "")
                    self.console.print(f"  [green]✓[/green] Pexels image found for: {query}")
                    import json
                    url_file = output_dir / f"{filename}_pexels_url.json"
                    with open(url_file, "w") as f:
                        json.dump({"url": img_url, "query": query}, f)
                    return url_file

        except Exception as e:
            self.console.print(f"  [red]✗[/red] Pexels search failed: {e}")

        return None

    def _generate_image(self, query: str, output_dir: Path, filename: str) -> Optional[Path]:
        """Generate an image using Alibaba's image model."""
        from config import ALIBABA_API_KEY, ALIBABA_BASE_URL, IMAGE_MODEL

        if not ALIBABA_API_KEY:
            self.console.print(f"  [dim]⚠️ Alibaba API key not set, skipping image gen for: {query}[/dim]")
            return None

        try:
            from openai import OpenAI
            client = OpenAI(api_key=ALIBABA_API_KEY, base_url=ALIBABA_BASE_URL)

            # Using Alibaba's image generation model
            response = client.images.generate(
                model=IMAGE_MODEL,
                prompt=f"Social media video background: {query}. Clean, modern, abstract. Vertical 9:16 aspect ratio. No text.",
                size="1024x1792",  # ~9:16
                n=1,
            )

            if response.data:
                img_url = response.data[0].url
                img_path = output_dir / f"{filename}.png"

                # Download the image
                img_response = requests.get(img_url, timeout=30)
                if img_response.status_code == 200:
                    with open(img_path, "wb") as f:
                        f.write(img_response.content)
                    self.console.print(f"  [green]✓[/green] AI image generated: {filename}.png")
                    return img_path

        except Exception as e:
            self.console.print(f"  [red]✗[/red] Image generation failed for '{query}': {e}")

        return None
