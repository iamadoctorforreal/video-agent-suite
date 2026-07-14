"""
Logo Lookup Agent — finds brand assets (logos, icons) from local folders.
Checks project brand folders and user Desktop for reusable assets.
"""

from pathlib import Path
from typing import Optional

from agents.base import BaseAgent, AgentInput, AgentOutput


class LogoLookupAgent(BaseAgent):
    """Finds brand assets (logos, icons) from local folders."""

    name = "logo_lookup"
    description = "Finds local brand assets (logos, icons)"

    def execute(self, input_data: AgentInput) -> AgentOutput:
        project_dir = input_data.project_dir
        data = input_data.data or {}

        scenes = data.get("scenes", [])
        found = []

        if scenes:
            for scene in scenes:
                scene_num = scene.get("scene_number", len(found) + 1)
                elements = scene.get("visual_elements", [])

                for element in elements:
                    if self._is_brand_element(element):
                        local_path = self._find_local(element, "logos")
                        if not local_path:
                            local_path = self._find_local(element, "icons")
                        if local_path:
                            self.console.print(f"  [green]✓[/green] Local asset: {element} → {local_path.name}")
                            found.append({
                                "scene": scene_num,
                                "name": element,
                                "path": str(local_path),
                                "source": "local",
                            })
                        else:
                            self.console.print(f"  [dim]No local asset for: {element}[/dim]")

        return AgentOutput(
            success=len(found) > 0,
            data={"local_assets": found},
            message=f"Found {len(found)} local brand asset(s)",
            metadata={"count": len(found)},
        )

    def _is_brand_element(self, element: str) -> bool:
        """Check if a visual element is a brand asset (logo/icon)."""
        keywords = ["logo", "brand", "icon", "emblem", "badge", "watermark"]
        return any(k in element.lower() for k in keywords)

    def _find_local(self, name: str, asset_type: str) -> Optional[Path]:
        """Search local folders for a brand asset."""
        from config import PROJECTS_DIR

        search_dirs = [
            PROJECTS_DIR / "brand" / asset_type,
            PROJECTS_DIR / "assets" / asset_type,
            Path.home() / "Desktop" / "brand_assets" / asset_type,
        ]

        extensions = [".png", ".svg", ".jpg", ".jpeg", ".webp"]

        for search_dir in search_dirs:
            if not search_dir.exists():
                continue

            # Exact match
            for ext in extensions:
                candidate = search_dir / f"{name}{ext}"
                if candidate.exists():
                    return candidate

            # Fuzzy match (substring)
            for f in search_dir.iterdir():
                if f.is_file() and name.lower() in f.stem.lower() and f.suffix.lower() in extensions:
                    return f

        return None
