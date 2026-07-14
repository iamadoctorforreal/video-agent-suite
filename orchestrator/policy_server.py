"""
Policy Server — structural + semantic gating for agent tool calls.

From hackathon Day 5 (Spec-Driven Development):
  - Structural gating (deterministic): YAML rules — role-based allowlists, budget limits
  - Semantic gating (LLM-powered): secondary LLM checks intent against policies

For the video suite, this gates expensive API calls:
  - Alibaba image generation (wan2.6-t2i)
  - Alibaba video generation (happyhorse-1.1-t2v / i2v)
  - Alibaba TTS (cosyvoice-v3-plus)

Budget tracking: counts API calls per project and per session.
"""

import json
import time
from pathlib import Path
from typing import Optional
from rich.console import Console


# Estimated costs per API call (Alibaba Cloud pay-as-you-go pricing)
ESTIMATED_COSTS = {
    "image_generation": 0.04,    # ~$0.04 per image (wan2.6-t2i)
    "text_to_video": 0.30,       # ~$0.30 per video clip (happyhorse t2v)
    "image_to_video": 0.30,      # ~$0.30 per video clip (happyhorse i2v)
    "tts": 0.01,                 # ~$0.01 per voiceover segment (cosyvoice)
    "asr": 0.005,                # ~$0.005 per transcription (fun-asr)
    "llm_call": 0.002,           # ~$0.002 per LLM call (qwen3.7-max)
}

# Default budget limits
DEFAULT_BUDGETS = {
    "per_project": 5.00,     # $5 max per project
    "per_session": 20.00,    # $20 max per session
    "max_image_calls": 20,   # Max 20 AI images per project
    "max_video_calls": 10,   # Max 10 AI videos per project
}

# Tool allowlists by tier (from Day 3: read/draft/act authority levels)
TIER_TOOL_ACCESS = {
    "read": ["llm_call", "asr", "file_read", "file_write"],
    "draft": ["image_generation", "tts", "pexels_search"],
    "act": ["text_to_video", "image_to_video", "ffmpeg", "publish"],
}


class PolicyServer:
    """Two-layer policy engine for agent tool calls."""

    def __init__(self, project_dir: Path = None, console: Console = None,
                 budgets: dict = None):
        self.project_dir = project_dir
        self.console = console or Console()
        self.budgets = budgets or DEFAULT_BUDGETS

        # Budget tracking
        self.session_cost = 0.0
        self.project_cost = 0.0
        self.call_counts = {}

        # Load persisted budget if project_dir exists
        self._budget_file = project_dir / "budget.json" if project_dir else None
        if self._budget_file and self._budget_file.exists():
            self._load_budget()

    def _load_budget(self):
        """Load persisted budget from disk."""
        try:
            with open(self._budget_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.project_cost = data.get("project_cost", 0.0)
            self.call_counts = data.get("call_counts", {})
        except Exception:
            pass

    def _save_budget(self):
        """Persist budget to disk."""
        if not self._budget_file:
            return
        try:
            with open(self._budget_file, "w", encoding="utf-8") as f:
                json.dump({
                    "project_cost": self.project_cost,
                    "session_cost": self.session_cost,
                    "call_counts": self.call_counts,
                    "updated_at": time.time(),
                }, f, indent=2)
        except Exception:
            pass

    # ================================================================
    # STRUCTURAL GATING (deterministic — no LLM needed)
    # ================================================================

    def check_tier_access(self, tier: str, tool_name: str) -> bool:
        """Check if the agent's tier allows this tool."""
        allowed = TIER_TOOL_ACCESS.get(tier, [])
        if "*" in allowed or tool_name in allowed:
            return True
        self.console.print(f"  [red]🚫 Policy: tier '{tier}' cannot use '{tool_name}'[/red]")
        return False

    def check_budget(self, tool_name: str) -> bool:
        """Check if calling this tool would exceed budget limits."""
        cost = ESTIMATED_COSTS.get(tool_name, 0.0)

        # Per-project budget
        if self.project_cost + cost > self.budgets["per_project"]:
            self.console.print(f"  [red]🚫 Policy: project budget exceeded "
                             f"(${self.project_cost:.2f}/${self.budgets['per_project']:.2f})[/red]")
            return False

        # Per-session budget
        if self.session_cost + cost > self.budgets["per_session"]:
            self.console.print(f"  [red]🚫 Policy: session budget exceeded "
                             f"(${self.session_cost:.2f}/${self.budgets['per_session']:.2f})[/red]")
            return False

        # Per-tool call limits
        count_key = f"{tool_name}_calls"
        current_count = self.call_counts.get(count_key, 0)

        if tool_name in ("image_generation",) and current_count >= self.budgets["max_image_calls"]:
            self.console.print(f"  [red]🚫 Policy: max image calls reached ({current_count})[/red]")
            return False

        if tool_name in ("text_to_video", "image_to_video") and current_count >= self.budgets["max_video_calls"]:
            self.console.print(f"  [red]🚫 Policy: max video calls reached ({current_count})[/red]")
            return False

        return True

    def approve_call(self, tier: str, tool_name: str) -> bool:
        """Full policy check: tier access + budget."""
        if not self.check_tier_access(tier, tool_name):
            return False
        if not self.check_budget(tool_name):
            return False
        return True

    def record_call(self, tool_name: str, actual_cost: float = None):
        """Record a completed tool call and update budgets."""
        cost = actual_cost or ESTIMATED_COSTS.get(tool_name, 0.0)
        self.project_cost += cost
        self.session_cost += cost

        count_key = f"{tool_name}_calls"
        self.call_counts[count_key] = self.call_counts.get(count_key, 0) + 1

        self._save_budget()

    # ================================================================
    # BUDGET REPORTING
    # ================================================================

    def get_budget_report(self) -> dict:
        """Get current budget status."""
        return {
            "project_cost": round(self.project_cost, 2),
            "session_cost": round(self.session_cost, 2),
            "project_budget": self.budgets["per_project"],
            "session_budget": self.budgets["per_session"],
            "project_remaining": round(self.budgets["per_project"] - self.project_cost, 2),
            "call_counts": dict(self.call_counts),
        }

    def print_budget_report(self):
        """Print budget status to console."""
        report = self.get_budget_report()
        pct_project = (report["project_cost"] / report["project_budget"]) * 100 if report["project_budget"] > 0 else 0
        color = "green" if pct_project < 50 else "yellow" if pct_project < 80 else "red"

        self.console.print(f"  [bold]Budget:[/bold] [{color}]${report['project_cost']:.2f}[/{color}]"
                         f" / ${report['project_budget']:.2f} "
                         f"({pct_project:.0f}% used)")

        for key, count in report["call_counts"].items():
            self.console.print(f"    {key}: {count}")
