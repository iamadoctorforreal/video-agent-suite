"""
Workflow Router — detects intent and routes to the correct workflow.
"""

from enum import Enum
from typing import Optional


class Workflow(str, Enum):
    CREATION = "creation"
    EDITING = "editing"


class WorkflowRouter:
    """Routes user intent to the appropriate workflow."""

    # Keywords that signal editing workflow
    EDIT_KEYWORDS = {
        "edit", "cut", "trim", "raw footage", "footage", "clip",
        "remove silence", "color grade", "color grading", "add captions",
        "add b-roll", "insert broll", "polish", "clean up",
        "remove filler", "filler words", "recut",
    }

    # Keywords that signal creation workflow
    CREATE_KEYWORDS = {
        "create", "generate", "make a video", "storyboard", "script",
        "marketing video", "social media", "explainer", "product launch",
        "from scratch", "new video",
    }

    def route(self, prompt: str) -> Workflow:
        """Determine which workflow to use based on user prompt."""
        prompt_lower = prompt.lower()

        # Check for editing signals
        edit_score = sum(1 for kw in self.EDIT_KEYWORDS if kw in prompt_lower)
        create_score = sum(1 for kw in self.CREATE_KEYWORDS if kw in prompt_lower)

        if edit_score > create_score:
            return Workflow.EDITING
        elif create_score > 0:
            return Workflow.CREATION
        else:
            # Default to creation if ambiguous
            return Workflow.CREATION

    def detect_subtasks(self, prompt: str, workflow: Workflow) -> list[str]:
        """Extract subtasks from the prompt for the chosen workflow."""
        subtasks = []

        if workflow == Workflow.CREATION:
            if "script" in prompt.lower() or "storyboard" in prompt.lower():
                subtasks.append("generate_script_and_storyboard")
            if "voice" in prompt.lower() or "voiceover" in prompt.lower() or "tts" in prompt.lower():
                subtasks.append("generate_voiceover")
            if "caption" in prompt.lower():
                subtasks.append("generate_captions")
            if "music" in prompt.lower() or "bgm" in prompt.lower():
                subtasks.append("source_music")
            if "thumbnail" in prompt.lower():
                subtasks.append("generate_thumbnails")
            # Default full pipeline
            if not subtasks:
                subtasks = [
                    "generate_script_and_storyboard",
                    "source_assets",
                    "generate_voiceover",
                    "generate_captions",
                    "create_motion_graphics",
                    "source_music_and_sfx",
                    "dual_render",
                    "assemble_final",
                    "generate_metadata",
                ]

        elif workflow == Workflow.EDITING:
            if "silence" in prompt.lower() or "filler" in prompt.lower():
                subtasks.append("remove_silences_and_fillers")
            if "color" in prompt.lower():
                subtasks.append("color_grade")
            if "caption" in prompt.lower():
                subtasks.append("add_captions")
            if "b-roll" in prompt.lower() or "broll" in prompt.lower():
                subtasks.append("insert_broll")
            if "music" in prompt.lower() or "bgm" in prompt.lower():
                subtasks.append("add_music")
            if not subtasks:
                subtasks = [
                    "analyze_footage",
                    "create_edit_storyboard",
                    "remove_silences_and_fillers",
                    "color_grade",
                    "add_captions",
                    "insert_broll",
                    "add_music_and_sfx",
                    "assemble_final",
                ]

        return subtasks
