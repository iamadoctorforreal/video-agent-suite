"""
Asset Orchestrator — coordinates asset sourcing across sub-agents.

Priority order (cheapest first):
  1. LogoLookupAgent  — free local brand assets
  2. StockMediaAgent  — free Pexels stock video/images
  3. ImageGenAgent    — AI generation (costs API credits)

Merges all results into a unified asset manifest.
"""

import json
from pathlib import Path

from agents.base import BaseAgent, AgentInput, AgentOutput
from agents.logo_lookup import LogoLookupAgent
from agents.stock_media import StockMediaAgent
from agents.image_gen import ImageGenAgent


class AssetOrchestrator(BaseAgent):
    """Orchestrates asset sourcing — local logos first, Pexels stock second, AI generation last."""

    name = "asset_orchestrator"
    description = "Coordinates asset sourcing across sub-agents"

    def execute(self, input_data: AgentInput) -> AgentOutput:
        project_dir = input_data.project_dir
        data = input_data.data or {}

        if not project_dir:
            return AgentOutput(success=False, message="No project directory")

        assets_dir = project_dir / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)

        manifest = {}
        scenes = data.get("scenes", [])

        # ── Phase 1: Local brand assets (free) ──
        self.console.print("\n  [bold]Phase 1: Local Brand Assets[/bold]")
        logo_agent = LogoLookupAgent(self.console)
        logo_result = logo_agent.run(AgentInput(project_dir=project_dir, data=data))
        local_assets = logo_result.data.get("local_assets", []) if logo_result.data else []

        for asset in local_assets:
            scene_key = f"scene_{asset['scene']}"
            manifest.setdefault(scene_key, []).append(asset)

        # ── Phase 2: Pexels stock media (free) ──
        self.console.print("\n  [bold]Phase 2: Pexels Stock Media[/bold]")

        # Only search for scenes that don't have assets yet
        scenes_needing_stock = [
            s for s in scenes
            if f"scene_{s.get('scene_number', 0)}" not in manifest
        ]

        if scenes_needing_stock:
            stock_agent = StockMediaAgent(self.console)
            stock_result = stock_agent.run(AgentInput(
                project_dir=project_dir,
                data={"scenes": scenes_needing_stock},
            ))
            stock_media = stock_result.data.get("stock_media", []) if stock_result.data else []

            for asset in stock_media:
                scene_key = f"scene_{asset['scene']}"
                manifest.setdefault(scene_key, []).append(asset)
        else:
            self.console.print("  [dim]All scenes have assets, skipping Pexels[/dim]")

        # ── Phase 3: AI image generation (costs credits) ──
        self.console.print("\n  [bold]Phase 3: AI Image Generation[/bold]")

        # Only generate for scenes still missing assets (no avatar/character scenes)
        scenes_needing_ai = [
            s for s in scenes
            if f"scene_{s.get('scene_number', 0)}" not in manifest
            and not s.get("has_avatar")
            and not s.get("has_character")
        ]

        if scenes_needing_ai:
            image_agent = ImageGenAgent(self.console)
            image_result = image_agent.run(AgentInput(
                project_dir=project_dir,
                data={"scenes": scenes_needing_ai},
            ))
            ai_images = image_result.data.get("images", []) if image_result.data else []

            for asset in ai_images:
                scene_key = f"scene_{asset['scene']}"
                manifest.setdefault(scene_key, []).append(asset)
        else:
            self.console.print("  [dim]No scenes need AI images[/dim]")

        # ── Save manifest ──
        manifest_path = assets_dir / "manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        # ── Summary ──
        total = sum(len(v) for v in manifest.values())
        local_count = sum(1 for v in manifest.values() for a in v if a.get("source") == "local")
        pexels_count = sum(1 for v in manifest.values() for a in v if "pexels" in a.get("source", ""))
        ai_count = sum(1 for v in manifest.values() for a in v if a.get("source") == "ai_generated")

        self.console.print(f"\n  [bold]Asset Summary:[/bold]")
        self.console.print(f"  Local: {local_count} | Pexels: {pexels_count} | AI: {ai_count} | Total: {total}")

        return AgentOutput(
            success=total > 0,
            data=manifest,
            artifact_path=manifest_path,
            message=f"Orchestrated {total} assets ({local_count} local, {pexels_count} stock, {ai_count} AI)",
            metadata={
                "total": total,
                "local": local_count,
                "pexels": pexels_count,
                "ai_generated": ai_count,
                "scenes": len(manifest),
            },
        )
