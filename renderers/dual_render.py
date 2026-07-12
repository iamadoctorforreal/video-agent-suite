"""
Dual Render Engine — renders the same composition in both Remotion and Hyperframes.
Generates two video outputs for platform comparison.
"""

import subprocess
import shutil
from pathlib import Path
from typing import Optional

from agents.base import AgentOutput


class DualRenderEngine:
    """Renders compositions in both Remotion and Hyperframes."""

    def __init__(self, console):
        self.console = console

    def render_remotion(self, project_dir: Path, composition_data: dict) -> Optional[Path]:
        """Render the Remotion composition to video."""
        self.console.print("  [dim]Rendering Remotion video...[/dim]")

        remotion_dir = project_dir / "render" / "remotion"
        output_dir = project_dir / "render" / "remotion" / "out"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "video.mp4"

        # Check if npm dependencies are installed
        package_json = remotion_dir / "package.json"
        if package_json.exists():
            # Install dependencies
            self.console.print("  [dim]Installing Remotion dependencies...[/dim]")
            try:
                subprocess.run(
                    ["npm", "install"],
                    cwd=str(remotion_dir),
                    capture_output=True,
                    timeout=300,
                    shell=True,
                )
            except Exception as e:
                self.console.print(f"  [yellow]⚠️ npm install skipped: {e}[/yellow]")

        # Render using Remotion CLI
        try:
            result = subprocess.run(
                ["npx", "remotion", "render", "Root", str(output_path), "--overwrite"],
                cwd=str(remotion_dir),
                capture_output=True,
                text=True,
                timeout=600,
                shell=True,
            )

            if result.returncode == 0 and output_path.exists():
                self.console.print(f"  [green]✓[/green] Remotion render complete: {output_path.name}")
                return output_path
            else:
                self.console.print(f"  [yellow]⚠️ Remotion render had issues (exit {result.returncode})[/yellow]")
                if result.stderr:
                    self.console.print(f"  [dim]{result.stderr[:500]}[/dim]")
                return None

        except subprocess.TimeoutExpired:
            self.console.print("  [red]✗[/red] Remotion render timed out")
            return None
        except Exception as e:
            self.console.print(f"  [red]✗[/red] Remotion render failed: {e}")
            return None

    def render_hyperframes(self, project_dir: Path, composition_data: dict) -> Optional[Path]:
        """Render the Hyperframes composition to video."""
        self.console.print("  [dim]Rendering Hyperframes video...[/dim]")

        hf_dir = project_dir / "render" / "hyperframes"
        output_dir = project_dir / "render" / "hyperframes" / "out"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "video.mp4"

        # Render using Hyperframes CLI
        try:
            result = subprocess.run(
                ["npx", "hyperframes", "render"],
                cwd=str(hf_dir),
                capture_output=True,
                text=True,
                timeout=600,
                shell=True,
            )

            if result.returncode == 0:
                # Hyperframes may output to a different location
                # Check common output locations
                for candidate in [
                    hf_dir / "out" / "video.mp4",
                    hf_dir / "output" / "video.mp4",
                    hf_dir / "render.mp4",
                ]:
                    if candidate.exists():
                        self.console.print(f"  [green]✓[/green] Hyperframes render complete: {candidate.name}")
                        return candidate

                # If we can't find the output, note it
                self.console.print("  [yellow]⚠️ Hyperframes rendered but output location unknown[/yellow]")
                return None
            else:
                self.console.print(f"  [yellow]⚠️ Hyperframes render had issues (exit {result.returncode})[/yellow]")
                if result.stderr:
                    self.console.print(f"  [dim]{result.stderr[:500]}[/dim]")
                return None

        except subprocess.TimeoutExpired:
            self.console.print("  [red]✗[/red] Hyperframes render timed out")
            return None
        except Exception as e:
            self.console.print(f"  [red]✗[/red] Hyperframes render failed: {e}")
            return None

    def render_both(self, project_dir: Path, render_data: dict) -> dict:
        """Render both Remotion and Hyperframes, return both outputs."""
        results = {
            "remotion": None,
            "hyperframes": None,
        }

        remotion_data = render_data.get("remotion", {})
        hyperframes_data = render_data.get("hyperframes", {})

        # Render Remotion
        remotion_path = self.render_remotion(project_dir, remotion_data)
        if remotion_path:
            results["remotion"] = str(remotion_path)

        # Render Hyperframes
        hyperframes_path = self.render_hyperframes(project_dir, hyperframes_data)
        if hyperframes_path:
            results["hyperframes"] = str(hyperframes_path)

        return results
