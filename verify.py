"""
Comprehensive verification test for Video Agent Suite.
Checks all components, APIs, and integrations.
"""

import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.table import Table

console = Console()

def test_imports():
    """Test all agent imports."""
    console.print("\n[bold]Testing Imports...[/bold]")
    try:
        from agents import (
            ScriptingAgent, DirectorAgent, AssetSourcingAgent,
            VoiceoverAgent, MotionGraphicsAgent, TranscriptionAgent,
            SoundAgent, AssemblyAgent, QCAgent, BRollAgent,
            OverlayAgent, ThumbnailAgent, MetadataAgent,
        )
        console.print("  [green]✓[/green] All 13 agents imported successfully")
        return True
    except Exception as e:
        console.print(f"  [red]✗[/red] Import failed: {e}")
        return False

def test_config():
    """Test configuration loading."""
    console.print("\n[bold]Testing Configuration...[/bold]")
    try:
        from config import (
            ALIBABA_API_KEY, PEXELS_API_KEY,
            LLM_MODEL, TTS_MODEL, ASR_MODEL, IMAGE_MODEL,
        )
        console.print(f"  [green]✓[/green] Alibaba API Key: {'Set' if ALIBABA_API_KEY else 'NOT SET'}")
        console.print(f"  [green]✓[/green] Pexels API Key: {'Set' if PEXELS_API_KEY else 'NOT SET'}")
        console.print(f"  [green]✓[/green] LLM Model: {LLM_MODEL}")
        console.print(f"  [green]✓[/green] TTS Model: {TTS_MODEL}")
        console.print(f"  [green]✓[/green] ASR Model: {ASR_MODEL}")
        console.print(f"  [green]✓[/green] Image Model: {IMAGE_MODEL}")
        return bool(ALIBABA_API_KEY)
    except Exception as e:
        console.print(f"  [red]✗[/red] Config failed: {e}")
        return False

def test_alibaba_api():
    """Test Alibaba API connectivity."""
    console.print("\n[bold]Testing Alibaba API...[/bold]")
    try:
        from openai import OpenAI
        from config import ALIBABA_API_KEY, ALIBABA_BASE_URL, LLM_MODEL

        client = OpenAI(
            api_key=ALIBABA_API_KEY,
            base_url=ALIBABA_BASE_URL,
            timeout=30.0,
        )

        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": "Say OK"}],
            max_tokens=5,
            extra_body={"enable_thinking": True},
        )

        console.print(f"  [green]✓[/green] LLM API working: {response.choices[0].message.content}")
        return True
    except Exception as e:
        console.print(f"  [red][/red] LLM API failed: {e}")
        return False

def test_pexels_api():
    """Test Pexels API connectivity."""
    console.print("\n[bold]Testing Pexels API...[/bold]")
    try:
        import requests
        from config import PEXELS_API_KEY

        response = requests.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": PEXELS_API_KEY},
            params={"query": "test", "per_page": 1},
            timeout=10,
        )

        if response.status_code == 200:
            data = response.json()
            console.print(f"  [green]✓[/green] Pexels API working: {data.get('total_results', 0)} results")
            return True
        else:
            console.print(f"  [red]✗[/red] Pexels API failed: {response.status_code}")
            return False
    except Exception as e:
        console.print(f"  [red]✗[/red] Pexels API failed: {e}")
        return False

def test_cli():
    """Test CLI entry point."""
    console.print("\n[bold]Testing CLI...[/bold]")
    try:
        from orchestrator.main import app
        console.print("  [green]✓[/green] CLI app loaded")
        return True
    except Exception as e:
        console.print(f"  [red]✗[/red] CLI failed: {e}")
        return False

def test_workflows():
    """Test workflow imports."""
    console.print("\n[bold]Testing Workflows...[/bold]")
    try:
        from workflows import CreationWorkflow, EditingWorkflow
        console.print("  [green]✓[/green] Both workflows imported")
        return True
    except Exception as e:
        console.print(f"  [red]✗[/red] Workflows failed: {e}")
        return False

def test_ui_backend():
    """Test UI backend imports."""
    console.print("\n[bold]Testing UI Backend...[/bold]")
    try:
        from ui.backend.main import app
        console.print("  [green]✓[/green] FastAPI backend loaded")
        return True
    except Exception as e:
        console.print(f"  [red]✗[/red] UI backend failed: {e}")
        return False

def check_placeholders():
    """Check for placeholder files."""
    console.print("\n[bold]Checking for Placeholders...[/bold]")
    project_root = Path(__file__).parent

    placeholders = []
    for txt_file in project_root.rglob("*.txt"):
        if "placeholder" in txt_file.name.lower() or "temp" in txt_file.name.lower():
            placeholders.append(txt_file)

    if placeholders:
        console.print(f"  [yellow]⚠[/yellow] Found {len(placeholders)} placeholder files:")
        for p in placeholders[:5]:
            console.print(f"    - {p.relative_to(project_root)}")
    else:
        console.print("  [green]✓[/green] No placeholder files found")

    return len(placeholders) == 0

def main():
    console.print(Panel("Video Agent Suite — Verification Test", border_style="blue"))

    results = {
        "Imports": test_imports(),
        "Configuration": test_config(),
        "Alibaba API": test_alibaba_api(),
        "Pexels API": test_pexels_api(),
        "CLI": test_cli(),
        "Workflows": test_workflows(),
        "UI Backend": test_ui_backend(),
        "No Placeholders": check_placeholders(),
    }

    # Summary table
    table = Table(title="Test Results")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")

    for component, passed in results.items():
        table.add_row(component, "PASS" if passed else "FAIL")

    console.print(table)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    console.print(f"\n[bold]Results: {passed}/{total} tests passed[/bold]")

    if passed == total:
        console.print("[green]All systems operational![/green]")
    else:
        console.print("[yellow]Some tests failed. Check output above.[/yellow]")

    return passed == total

if __name__ == "__main__":
    from rich.panel import Panel
    success = main()
    sys.exit(0 if success else 1)
