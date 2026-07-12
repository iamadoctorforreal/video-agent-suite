"""
B-Roll Insertion Agent — sources and inserts b-roll footage into edited videos.
Analyzes transcript for visual cues, sources matching footage from Pexels,
and creates an edit decision list for FFmpeg assembly.
"""

import json
import requests
from pathlib import Path
from typing import Optional

from agents.base import BaseAgent, AgentInput, AgentOutput


class BRollAgent(BaseAgent):
    """Sources and plans b-roll insertion points."""

    name = "broll"
    description = "Sources and inserts b-roll footage"

    def execute(self, input_data: AgentInput) -> AgentOutput:
        transcript = input_data.prompt
        project_dir = input_data.project_dir

        if not transcript:
            return AgentOutput(success=False, message="No transcript provided")

        # Create b-roll directory
        broll_dir = project_dir / "broll" if project_dir else Path("broll")
        broll_dir.mkdir(parents=True, exist_ok=True)

        # Analyze transcript for visual cues
        insertion_points = self._find_insertion_points(transcript)

        # Source b-roll for each insertion point
        sourced_broll = []
        for point in insertion_points:
            broll_path = self._source_broll(point["query"], broll_dir, point["timestamp"])
            if broll_path:
                point["broll_path"] = str(broll_path)
                sourced_broll.append(point)

        # Save b-roll plan
        if project_dir:
            plan_path = broll_dir / "broll_plan.json"
            with open(plan_path, "w", encoding="utf-8") as f:
                json.dump({
                    "insertion_points": insertion_points,
                    "sourced": sourced_broll,
                    "total_found": len(insertion_points),
                    "total_sourced": len(sourced_broll),
                }, f, indent=2)

        return AgentOutput(
            success=True,
            data={
                "insertion_points": insertion_points,
                "sourced_broll": sourced_broll,
            },
            artifact_path=broll_dir / "broll_plan.json" if project_dir else None,
            message=f"Found {len(insertion_points)} b-roll opportunities, sourced {len(sourced_broll)}",
            metadata={"found": len(insertion_points), "sourced": len(sourced_broll)},
        )

    def _find_insertion_points(self, transcript: str) -> list:
        """Analyze transcript for visual b-roll opportunities."""
        # Simple keyword-based detection
        visual_keywords = {
            "technology": ["tech", "computer", "software", "app", "digital", "AI", "code"],
            "business": ["meeting", "office", "team", "work", "business", "corporate"],
            "nature": ["nature", "outdoor", "sky", "water", "tree", "landscape"],
            "people": ["person", "people", "hand", "face", "crowd", "group"],
            "data": ["data", "chart", "graph", "number", "statistic", "analytics"],
            "creative": ["design", "art", "creative", "color", "paint", "draw"],
        }

        sentences = transcript.replace("\n", " ").split(". ")
        insertion_points = []

        for i, sentence in enumerate(sentences):
            sentence_lower = sentence.lower()
            for category, keywords in visual_keywords.items():
                if any(kw in sentence_lower for kw in keywords):
                    # Estimate timestamp (rough: ~150 WPM = 2.5 words/sec)
                    words_before = sum(len(s.split()) for s in sentences[:i])
                    timestamp = words_before / 2.5

                    insertion_points.append({
                        "timestamp": round(timestamp, 1),
                        "sentence": sentence.strip(),
                        "category": category,
                        "query": f"{category} {keywords[0]} professional",
                        "duration": 3.0,  # Default 3 seconds
                    })
                    break  # One category per sentence

        return insertion_points

    def _source_broll(self, query: str, output_dir: Path, timestamp: float) -> Optional[Path]:
        """Source b-roll footage from Pexels."""
        from config import PEXELS_API_KEY

        if not PEXELS_API_KEY:
            return None

        try:
            response = requests.get(
                "https://api.pexels.com/videos/search",
                headers={"Authorization": PEXELS_API_KEY},
                params={"query": query, "per_page": 1, "orientation": "portrait"},
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("videos"):
                    video = data["videos"][0]
                    video_files = video.get("video_files", [])
                    if video_files:
                        # Save video URL for later download
                        url_file = output_dir / f"broll_{timestamp:.1f}s_{query.replace(' ', '_')[:20]}.json"
                        with open(url_file, "w", encoding="utf-8") as f:
                            json.dump({
                                "url": video_files[0].get("link", ""),
                                "query": query,
                                "timestamp": timestamp,
                                "pexels_id": video.get("id"),
                            }, f, indent=2)
                        return url_file

        except Exception as e:
            self.console.print(f"  [yellow]️ B-roll source failed for '{query}': {str(e)[:50]}[/yellow]")

        return None
