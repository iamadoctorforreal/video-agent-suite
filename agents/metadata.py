"""
Title/Description Generator Agent — creates SEO-optimized titles and descriptions.
Generates 2 title variants and 2 description variants per video.
"""

import json
from pathlib import Path

from agents.base import BaseAgent, AgentInput, AgentOutput


class MetadataAgent(BaseAgent):
    """Generates titles, descriptions, and tags."""

    name = "metadata"
    description = "Generates video metadata (titles, descriptions, tags)"

    TITLE_SYSTEM_PROMPT = """You are an expert YouTube/social media title writer.
Generate 2 compelling, click-worthy titles for a video.
Titles should be:
- Under 60 characters
- Include power words
- Create curiosity or urgency
- SEO-optimized

Return VALID JSON:
{"titles": ["Title 1", "Title 2"]}"""

    DESC_SYSTEM_PROMPT = """You are an expert YouTube/social media description writer.
Generate 2 engaging descriptions for a video.
Descriptions should be:
- 100-200 words
- Include key points from the video
- Have a call-to-action
- Include relevant hashtags

Return VALID JSON:
{"descriptions": ["Description 1...", "Description 2..."], "tags": ["tag1", "tag2", "tag3"]}"""

    def execute(self, input_data: AgentInput) -> AgentOutput:
        project_dir = input_data.project_dir
        script_data = input_data.data

        if not project_dir:
            return AgentOutput(success=False, message="No project directory")

        if not script_data:
            return AgentOutput(success=False, message="No script data")

        # Create metadata directory
        meta_dir = project_dir / "metadata"
        meta_dir.mkdir(parents=True, exist_ok=True)

        # Generate titles
        topic = script_data.get("topic", "Video")
        hook = script_data.get("hook", "")
        full_script = script_data.get("full_script", "")

        titles = self._generate_titles(topic, hook)
        descriptions = self._generate_descriptions(topic, full_script)

        # Combine results
        metadata = {
            "titles": titles,
            "descriptions": descriptions.get("descriptions", []),
            "tags": descriptions.get("tags", []),
        }

        # Save metadata
        meta_path = meta_dir / "video_metadata.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        return AgentOutput(
            success=True,
            data=metadata,
            artifact_path=meta_path,
            message=f"Generated {len(titles)} titles, {len(metadata['descriptions'])} descriptions",
            metadata={
                "title_count": len(titles),
                "desc_count": len(metadata["descriptions"]),
                "tag_count": len(metadata["tags"]),
            },
        )

    def _generate_titles(self, topic: str, hook: str) -> list:
        """Generate 2 title variants."""
        user_prompt = f"Video topic: {topic}\nHook: {hook}\n\nGenerate 2 compelling titles."

        try:
            response = self.call_llm(self.TITLE_SYSTEM_PROMPT, user_prompt)

            # Parse JSON
            import re
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
                return data.get("titles", [])
        except Exception as e:
            self.console.print(f"  [yellow]⚠️ Title gen failed: {str(e)[:50]}[/yellow]")

        # Fallback titles
        return [
            f"{topic}: What You Need to Know",
            f"Why {topic} Matters in 2026",
        ]

    def _generate_descriptions(self, topic: str, script: str) -> dict:
        """Generate 2 description variants with tags."""
        script_preview = script[:500] if script else topic
        user_prompt = f"Video topic: {topic}\nScript preview: {script_preview}\n\nGenerate 2 descriptions and tags."

        try:
            response = self.call_llm(self.DESC_SYSTEM_PROMPT, user_prompt)

            import re
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
                return {
                    "descriptions": data.get("descriptions", []),
                    "tags": data.get("tags", []),
                }
        except Exception as e:
            self.console.print(f"  [yellow]⚠️ Description gen failed: {str(e)[:50]}[/yellow]")

        # Fallback
        return {
            "descriptions": [
                f"Learn about {topic} in this quick video. {script[:100] if script else ''}...",
                f"Everything you need to know about {topic}. Watch now!",
            ],
            "tags": [topic.lower(), "tutorial", "2026"],
        }
