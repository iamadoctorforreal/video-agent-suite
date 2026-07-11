"""
Reusable skill definitions for the Video Agent Suite.
These define common patterns and formats used across agents.
"""

# Storyboard format definition
STORYBOARD_FORMAT = """
{
  "scenes": [
    {
      "scene_number": 1,
      "script_text": "The spoken text for this scene",
      "shot_type": "close_up | medium | wide | over_shoulder | top_down | macro | screen_recording",
      "motion_type": "static | slow_zoom | pan_left | pan_right | tilt_up | tilt_down | push_in | pull_out | slide_in | slide_out | fade | dissolve",
      "has_avatar": false,
      "has_character": false,
      "has_headshot": false,
      "background": "Description of background",
      "visual_elements": ["list", "of", "elements"],
      "animation_description": "How elements animate",
      "feel": "energetic | calm | dramatic | playful | professional",
      "emotion_evoked": "Target emotional response",
      "sound_effects": ["whoosh", "pop"],
      "bg_mood": "Background music mood",
      "transition": "cut | dissolve | slide | zoom | wipe",
      "duration_seconds": 3
    }
  ],
  "total_scenes": 5,
  "total_duration_seconds": 30,
  "overall_style": "Description of overall visual style",
  "color_palette": ["#hex1", "#hex2", "#hex3"],
  "font_style": "Typography approach"
}
"""

# Asset resolution strategy
ASSET_RESOLUTION_ORDER = [
    "local_brand_folder",   # Check local brand/project assets first
    "figma_import",          # Import from Figma if available
    "pexels_api",            # Free stock footage/images
    "ai_generation",         # AI image generation (Alibaba)
    "placeholder",           # Generate placeholder
]

# Caption styles
CAPTION_STYLES = {
    "kinetic": "Word-by-word animated captions",
    "subtitle": "Standard subtitle style at bottom",
    "pop": "Pop-in animation, centered",
    "typewriter": "Typewriter-style reveal",
    "karaoke": "Karaoke-style word highlighting",
}

# Transition presets
TRANSITION_PRESETS = {
    "cut": {"duration": 0, "type": "instant"},
    "dissolve": {"duration": 0.5, "type": "crossfade"},
    "slide_left": {"duration": 0.5, "type": "slide", "direction": "left"},
    "slide_right": {"duration": 0.5, "type": "slide", "direction": "right"},
    "zoom_in": {"duration": 0.5, "type": "zoom", "direction": "in"},
    "zoom_out": {"duration": 0.5, "type": "zoom", "direction": "out"},
    "wipe": {"duration": 0.5, "type": "wipe", "direction": "left"},
}
