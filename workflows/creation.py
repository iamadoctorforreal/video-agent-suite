"""
Workflow 1: Creative Production
Script → Storyboard → Assets → Voiceover → Sound → Motion Graphics → Dual Render → Assembly → QC → Final Video
"""

import json
from pathlib import Path
from datetime import datetime

from rich.console import Console
from rich.panel import Panel

from config import PROJECTS_DIR
from agents import (
    ScriptingAgent, DirectorAgent, AssetSourcingAgent, VoiceoverAgent,
    MotionGraphicsAgent, SoundAgent, AssemblyAgent, QCAgent,
)
from renderers.dual_render import DualRenderEngine


class CreationWorkflow:
    """Complete creative production workflow."""

    def __init__(
        self,
        topic: str,
        duration: int = 30,
        aspect_ratio: str = "9:16",
        style: str = "marketing",
        project_name: str = None,
    ):
        self.topic = topic
        self.duration = duration
        self.aspect_ratio = aspect_ratio
        self.style = style
        self.project_name = project_name or f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        self.console = Console()
        self.project_dir = PROJECTS_DIR / self.project_name
        self.project_dir.mkdir(parents=True, exist_ok=True)

        # Initialize agents
        self.scripting = ScriptingAgent(self.console)
        self.director = DirectorAgent(self.console)
        self.asset_sourcing = AssetSourcingAgent(self.console)
        self.voiceover = VoiceoverAgent(self.console)
        self.sound = SoundAgent(self.console)
        self.motion_graphics = MotionGraphicsAgent(self.console)
        self.assembly = AssemblyAgent(self.console)
        self.qc = QCAgent(self.console)
        self.dual_render = DualRenderEngine(self.console)

    def run(self) -> str:
        """Execute the full creative production pipeline."""
        self.console.print(Panel(
            f"[bold]Project:[/bold] {self.project_name}\n"
            f"[bold]Topic:[/bold] {self.topic}\n"
            f"[bold]Duration:[/bold] {self.duration}s | [bold]Aspect:[/bold] {self.aspect_ratio} | [bold]Style:[/bold] {self.style}",
            title="🎬 Creative Production Pipeline",
            border_style="green",
        ))

        config = {
            "duration": self.duration,
            "aspect_ratio": self.aspect_ratio,
            "style": self.style,
        }

        # Step 1: Generate Script
        self.console.print("\n[bold green]Step 1/9: Generating Script[/bold green]")
        script_result = self.scripting.run(type("AgentInput", (), {
            "prompt": self.topic,
            "project_dir": self.project_dir,
            "context": {"style": self.style},
            "config": config,
        })())

        if not script_result.success:
            self.console.print(f"[red]Script generation failed: {script_result.message}[/red]")
            return f"Failed at Step 1: {script_result.message}"

        self.console.print(f"  [green]✓[/green] {script_result.message}")

        # Step 2: Create Storyboard
        self.console.print("\n[bold green]Step 2/9: Creating Storyboard[/bold green]")
        director_result = self.director.run(type("AgentInput", (), {
            "prompt": json.dumps(script_result.data, indent=2),
            "project_dir": self.project_dir,
            "context": {"script": script_result.data},
            "config": config,
        })())

        if not director_result.success:
            self.console.print(f"[red]Storyboard creation failed: {director_result.message}[/red]")
            return f"Failed at Step 2: {director_result.message}"

        self.console.print(f"  [green]✓[/green] {director_result.message}")

        # Step 3: Source Assets
        self.console.print("\n[bold green]Step 3/9: Sourcing Assets[/bold green]")
        asset_result = self.asset_sourcing.run(type("AgentInput", (), {
            "prompt": "Source visual assets for all scenes",
            "project_dir": self.project_dir,
            "data": director_result.data,
            "config": config,
        })())

        if asset_result.success:
            self.console.print(f"  [green]✓[/green] {asset_result.message}")
        else:
            self.console.print(f"  [yellow]⚠️ Asset sourcing had issues: {asset_result.message}[/yellow]")

        # Step 4: Generate Voiceover
        self.console.print("\n[bold green]Step 4/9: Generating Voiceover[/bold green]")
        vo_result = self.voiceover.run(type("AgentInput", (), {
            "prompt": script_result.data.get("full_script", self.topic),
            "project_dir": self.project_dir,
            "data": script_result.data,
            "config": config,
        })())

        if vo_result.success:
            self.console.print(f"  [green]✓[/green] {vo_result.message}")
        else:
            self.console.print(f"  [yellow]⚠️ Voiceover had issues: {vo_result.message}[/yellow]")

        # Step 5: Source Sound (BGM + SFX)
        self.console.print("\n[bold green]Step 5/9: Sourcing Sound (BGM + SFX)[/bold green]")
        sound_result = self.sound.run(type("AgentInput", (), {
            "prompt": "Source BGM and SFX for all scenes",
            "project_dir": self.project_dir,
            "data": director_result.data,
            "config": config,
        })())

        if sound_result.success:
            self.console.print(f"  [green]✓[/green] {sound_result.message}")
        else:
            self.console.print(f"  [yellow]⚠️ Sound sourcing had issues: {sound_result.message}[/yellow]")

        # Step 6: Create Motion Graphics
        self.console.print("\n[bold green]Step 6/9: Creating Motion Graphics (Remotion + Hyperframes)[/bold green]")
        mg_result = self.motion_graphics.run(type("AgentInput", (), {
            "prompt": "Create motion graphics compositions",
            "project_dir": self.project_dir,
            "data": director_result.data,
            "config": config,
        })())

        if not mg_result.success:
            self.console.print(f"[red]Motion graphics failed: {mg_result.message}[/red]")
            return f"Failed at Step 5: {mg_result.message}"

        self.console.print(f"  [green]✓[/green] {mg_result.message}")

        # Step 7: Dual Render
        self.console.print("\n[bold green]Step 7/9: Dual Render (Remotion + Hyperframes)[/bold green]")
        render_results = self.dual_render.render_both(self.project_dir, mg_result.data)

        if render_results["remotion"]:
            self.console.print(f"  [green]✓[/green] Remotion: {render_results['remotion']}")
        else:
            self.console.print("  [yellow]⚠️ Remotion render skipped (dependencies may be needed)[/yellow]")

        if render_results["hyperframes"]:
            self.console.print(f"  [green]✓[/green] Hyperframes: {render_results['hyperframes']}")
        else:
            self.console.print("  [yellow]⚠️ Hyperframes render skipped (CLI may need setup)[/yellow]")

        # Step 8: Assemble Final Video
        self.console.print("\n[bold green]Step 8/9: Assembling Final Video[/bold green]")
        assembly_result = self.assembly.run(type("AgentInput", (), {
            "prompt": "Assemble final video from all components",
            "project_dir": self.project_dir,
            "data": {
                "render_results": render_results,
                "voiceover": vo_result.data if vo_result.success else None,
                "sound": sound_result.data if sound_result.success else None,
            },
            "config": config,
        })())

        if assembly_result.success:
            self.console.print(f"  [green]✓[/green] {assembly_result.message}")
        else:
            self.console.print(f"  [yellow]⚠️ Assembly had issues: {assembly_result.message}[/yellow]")

        # Step 9: Quality Check
        self.console.print("\n[bold green]Step 9/9: Quality Check[/bold green]")
        qc_result = self.qc.run(type("AgentInput", (), {
            "prompt": "Run quality checks on final output",
            "project_dir": self.project_dir,
            "data": assembly_result.data if assembly_result.success else None,
            "config": {"stage": "final"},
        })())

        if qc_result.success:
            self.console.print(f"  [green]✓[/green] {qc_result.message}")
        else:
            self.console.print(f"  [yellow]⚠️ QC: {qc_result.message}[/yellow]")

        # Save project metadata
        self.console.print("\n[bold green]Finalizing Project[/bold green]")
        project_meta = {
            "name": self.project_name,
            "topic": self.topic,
            "duration": self.duration,
            "aspect_ratio": self.aspect_ratio,
            "style": self.style,
            "created_at": datetime.now().isoformat(),
            "script": script_result.data if script_result.success else None,
            "storyboard": director_result.data if director_result.success else None,
            "assets": asset_result.data if asset_result.success else None,
            "voiceover": vo_result.data if vo_result.success else None,
            "motion_graphics": mg_result.data if mg_result.success else None,
            "renders": render_results,
        }

        meta_path = self.project_dir / "project.json"
        with open(meta_path, "w") as f:
            json.dump(project_meta, f, indent=2, default=str)

        self.console.print(f"  [green]✓[/green] Project metadata saved: {meta_path}")

        # Create output directory with summary
        output_dir = self.project_dir / "output"
        output_dir.mkdir(exist_ok=True)

        summary_path = output_dir / "SUMMARY.md"
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(f"# {self.project_name}\n\n")
            f.write(f"## Topic\n{self.topic}\n\n")
            f.write(f"## Duration\n{self.duration}s | {self.aspect_ratio} | {self.style}\n\n")
            f.write("## Pipeline Status\n")
            f.write(f"- Script: {'✅' if script_result.success else '❌'}\n")
            f.write(f"- Storyboard: {'✅' if director_result.success else '❌'}\n")
            f.write(f"- Assets: {'✅' if asset_result.success else '⚠️'}\n")
            f.write(f"- Voiceover: {'✅' if vo_result.success else '️'}\n")
            f.write(f"- Sound: {'✅' if sound_result.success else '⚠️'}\n")
            f.write(f"- Motion Graphics: {'✅' if mg_result.success else '❌'}\n")
            f.write(f"- Remotion Render: {'✅' if render_results.get('remotion') else '⚠️'}\n")
            f.write(f"- Hyperframes Render: {'✅' if render_results.get('hyperframes') else '⚠️'}\n")
            f.write(f"- Assembly: {'✅' if assembly_result.success else '⚠️'}\n")
            f.write(f"- QC: {'✅' if qc_result.success else '⚠️'}\n")

        self.console.print(f"  [green]✓[/green] Summary saved: {summary_path}")

        # Generate thumbnails, titles, captions (stub for now)
        self._generate_metadata(output_dir, script_result.data)

        return str(self.project_dir)

    def _generate_metadata(self, output_dir: Path, script_data: dict):
        """Generate thumbnails, titles, and descriptions."""
        if not script_data:
            return

        # Generate titles
        titles = [
            script_data.get("hook", ""),
            f"Why {self.topic} Matters" if self.topic else "Watch This",
        ]

        # Generate descriptions
        descriptions = [
            script_data.get("full_script", "")[:200] + "...",
            f"Learn about {self.topic} in under {self.duration} seconds. {script_data.get('hook', '')}",
        ]

        metadata = {
            "titles": titles,
            "descriptions": descriptions,
            "thumbnails": [],  # Would need image gen for thumbnails
        }

        meta_path = output_dir / "metadata.json"
        with open(meta_path, "w") as f:
            json.dump(metadata, f, indent=2)

        self.console.print(f"  [green]✓[/green] Metadata generated: titles, descriptions")
