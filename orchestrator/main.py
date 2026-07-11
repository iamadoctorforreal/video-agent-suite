"""
Master orchestrator for Video Agent Suite.
CLI entry point — routes user requests to the correct workflow.
"""

import typer
from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree

from orchestrator.router import WorkflowRouter, Workflow
from workflows.creation import CreationWorkflow
from workflows.editing import EditingWorkflow

app = typer.Typer(
    name="video-agent-suite",
    help="AI-powered video creation and editing agent suite",
    add_completion=False,
)
console = Console()
router = WorkflowRouter()


@app.command()
def create(
    topic: str = typer.Argument(..., help="Topic or prompt for the video"),
    duration: int = typer.Option(30, "--duration", "-d", help="Target duration in seconds"),
    aspect: str = typer.Option("9:16", "--aspect", "-a", help="Aspect ratio: 9:16, 16:9, 1:1, 4:5"),
    style: str = typer.Option("marketing", "--style", "-s", help="Video style: marketing, explainer, social, product-launch"),
    project_name: str = typer.Option(None, "--name", "-n", help="Project name (auto-generated if not provided)"),
):
    """
    Workflow 1: Creative Production — Script → Storyboard → Assets → Final Video.

    Generates a complete video from a topic/prompt, including:
    - Script generation
    - Storyboard with shot design
    - Asset sourcing (images, b-roll, music, SFX)
    - Voiceover generation (TTS)
    - Motion graphics (Remotion + Hyperframes dual render)
    - Captions / kinetic typography
    - Final assembly with thumbnails, titles, descriptions
    """
    console.print(Panel(f"[bold green]Workflow 1: Creative Production[/bold green]\nTopic: {topic}\nDuration: {duration}s | Aspect: {aspect} | Style: {style}"))

    workflow = CreationWorkflow(
        topic=topic,
        duration=duration,
        aspect_ratio=aspect,
        style=style,
        project_name=project_name,
    )
    result = workflow.run()
    console.print(Panel(f"[bold green]Done![/bold green]\nOutput: {result}", title="Video Created"))


@app.command()
def edit(
    input_video: str = typer.Argument(..., help="Path to raw footage to edit"),
    project_name: str = typer.Option(None, "--name", "-n", help="Project name"),
    captions: bool = typer.Option(True, "--captions/--no-captions", help="Add captions"),
    color_grade: bool = typer.Option(True, "--color-grade/--no-color-grade", help="Apply color grading"),
    remove_silences: bool = typer.Option(True, "--remove-silences/--keep-silences", help="Remove awkward silences"),
    add_broll: bool = typer.Option(False, "--add-broll/--no-broll", help="Auto-insert b-roll"),
    add_music: bool = typer.Option(True, "--add-music/--no-music", help="Add background music"),
):
    """
    Workflow 2: Post-Production Editing — Raw Footage → Polished Cut.

    Takes raw footage and applies professional editing:
    - Silence and filler word removal
    - Color grading
    - Sound effects and music
    - B-roll insertion
    - Captions and lower thirds
    - Branding elements
    """
    console.print(Panel(f"[bold blue]Workflow 2: Post-Production Editing[/bold blue]\nInput: {input_video}\nCaptions: {captions} | Color: {color_grade} | Silences: {remove_silences}"))

    workflow = EditingWorkflow(
        input_video=input_video,
        project_name=project_name,
        captions=captions,
        color_grade=color_grade,
        remove_silences=remove_silences,
        add_broll=add_broll,
        add_music=add_music,
    )
    result = workflow.run()
    console.print(Panel(f"[bold blue]Done![/bold blue]\nOutput: {result}", title="Video Edited"))


@app.command()
def status():
    """Check system status and available tools."""
    tree = Tree("[bold]Video Agent Suite — Status[/bold]")

    # Check FFmpeg
    import shutil
    ffmpeg_ok = shutil.which("ffmpeg") is not None
    tree.add(f"{'✅' if ffmpeg_ok else '❌'} FFmpeg: {'Found' if ffmpeg_ok else 'Not found'}")

    # Check Node.js
    node_ok = shutil.which("node") is not None
    tree.add(f"{'✅' if node_ok else '❌'} Node.js: {'Found' if node_ok else 'Not found'}")

    # Check Hyperframes
    hf_ok = shutil.which("npx") is not None  # Simplified check
    tree.add(f"{'✅' if hf_ok else '❌'} Hyperframes CLI: {'Available' if hf_ok else 'Not available'}")

    # Check API keys
    from config import ALIBABA_API_KEY, PEXELS_API_KEY
    tree.add(f"{'✅' if ALIBABA_API_KEY else '⚠️'} Alibaba API Key: {'Configured' if ALIBABA_API_KEY else 'Not set'}")
    tree.add(f"{'✅' if PEXELS_API_KEY else '⚠️'} Pexels API Key: {'Configured' if PEXELS_API_KEY else 'Not set'}")

    console.print(tree)


@app.command()
def list_projects():
    """List all generated video projects."""
    from config import PROJECTS_DIR
    import os

    projects = [d for d in os.listdir(PROJECTS_DIR) if os.path.isdir(PROJECTS_DIR / d)]

    if not projects:
        console.print("[dim]No projects yet. Use 'create' or 'edit' to start.[/dim]")
        return

    tree = Tree("[bold]Projects[/bold]")
    for proj in sorted(projects):
        branch = tree.add(proj)
        # Show output files if any
        output_dir = PROJECTS_DIR / proj / "output"
        if output_dir.exists():
            files = os.listdir(output_dir)
            for f in files:
                branch.add(f"📄 {f}")

    console.print(tree)


def main():
    app()


if __name__ == "__main__":
    main()
