"""
Scripting Agent — generates video scripts from topics/prompts.
"""

import json
from typing import Optional
from dataclasses import dataclass

from agents.base import BaseAgent, AgentInput, AgentOutput


SCRIPTING_SYSTEM_PROMPT = """You are an expert video scriptwriter for social media and marketing content.

Your task is to write a compelling, engaging script for a short-form video.
The script must be:
- Hook-driven: first 3 seconds grab attention
- Concise: every word earns its place
- Structured: clear beginning, middle, end
- Optimized for the target platform and audience
- Written for voiceover (natural spoken rhythm)

Return your response as VALID JSON with this exact structure:
{
  "hook": "The opening line (first 3 seconds)",
  "body": "The main content, broken into short paragraphs",
  "cta": "Call to action (if applicable)",
  "full_script": "The complete script as one string, ready for TTS",
  "tone": "The emotional tone (energetic, professional, casual, etc.)",
  "target_audience": "Who this is for",
  "estimated_words": "Approximate word count",
  "estimated_duration_seconds": "Estimated duration when spoken at natural pace"
}

Do NOT include any text outside the JSON object."""


class ScriptingAgent(BaseAgent):
    """Generates video scripts from topic prompts."""

    name = "scripting"
    description = "Generates compelling video scripts"

    def execute(self, input_data: AgentInput) -> AgentOutput:
        topic = input_data.prompt
        style = input_data.config.get("style", "marketing")
        duration = input_data.config.get("duration", 30)
        target_audience = input_data.config.get("target_audience", "general")

        user_prompt = f"""Write a {duration}-second video script about: {topic}

Style: {style}
Target audience: {target_audience}
Platform: Short-form social media (vertical video)
Language: English

The script should be optimized for voiceover generation with TTS.
Keep sentences short and natural. Avoid complex punctuation."""

        try:
            response = self.call_llm(SCRIPTING_SYSTEM_PROMPT, user_prompt)

            # Parse JSON response
            script_data = json.loads(response)

            return AgentOutput(
                success=True,
                data=script_data,
                message=f"Script generated: {script_data.get('estimated_words', '?')} words, ~{script_data.get('estimated_duration_seconds', duration)}s",
                metadata={
                    "tone": script_data.get("tone"),
                    "target_audience": script_data.get("target_audience"),
                    "hook": script_data.get("hook"),
                },
            )

        except json.JSONDecodeError as e:
            # Fallback: try to extract JSON from response
            import re
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                try:
                    script_data = json.loads(json_match.group())
                    return AgentOutput(
                        success=True,
                        data=script_data,
                        message="Script generated (JSON extracted from response)",
                        metadata=script_data,
                    )
                except json.JSONDecodeError:
                    pass

            return AgentOutput(
                success=False,
                message=f"Failed to parse script JSON: {e}",
            )
        except Exception as e:
            return AgentOutput(
                success=False,
                message=f"Script generation failed: {str(e)}",
            )
