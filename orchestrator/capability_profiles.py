"""
Capability Profiles — swappable execution personas for the DAG orchestrator.

From hackathon Day 3: capability profiles define which skills are active,
which tools are available, and what system instructions govern the session.

Profile 1 (Creative Production): Script → Director → Assets → Video → VO → Sound → Motion → Render → Assembly → QC → Meta
Profile 2 (Post-Production Editing): Analyze → Transcribe → Silence Cut → Color → Captions → B-Roll → Overlays → Assembly → QC
"""

from pathlib import Path
from rich.console import Console


class CapabilityProfile:
    """Defines an execution persona — which agents, tools, and tiers are active."""

    def __init__(self, profile_id: str, name: str, description: str):
        self.profile_id = profile_id
        self.name = name
        self.description = description
        self.node_configs = []

    def add_node(self, node_id: str, agent_class, description: str = "",
                 tier: str = "read", depends_on: list = None, config: dict = None):
        """Register a node config for this profile."""
        self.node_configs.append({
            "node_id": node_id,
            "agent_class": agent_class,
            "description": description,
            "tier": tier,
            "depends_on": depends_on or [],
            "config": config or {},
        })

    def build_dag(self, project_dir: Path, console: Console):
        """Instantiate the DAG orchestrator with this profile's nodes."""
        from orchestrator.dag import DAGOrchestrator, DAGNode

        dag = DAGOrchestrator(project_dir, console)

        for nc in self.node_configs:
            agent = nc["agent_class"](console)
            node = DAGNode(
                node_id=nc["node_id"],
                agent=agent,
                description=nc["description"],
                tier=nc["tier"],
                depends_on=nc["depends_on"],
            )
            dag.add_node(node)

        return dag


def creative_production_profile() -> CapabilityProfile:
    """Workflow 1: Creative Production — topic to finished video."""
    from agents.scripting import ScriptingAgent
    from agents.director import DirectorAgent
    from agents.asset_orchestrator import AssetOrchestrator
    from agents.video_generation import VideoGenerationAgent
    from agents.voiceover import VoiceoverAgent
    from agents.sound import SoundAgent
    from agents.motion_graphics import MotionGraphicsAgent
    from agents.assembly import AssemblyAgent
    from agents.qc import QCAgent
    from agents.thumbnail import ThumbnailAgent
    from agents.metadata import MetadataAgent

    profile = CapabilityProfile(
        profile_id="creative_production",
        name="Creative Production",
        description="Topic → Script → Storyboard → Assets → Video → VO → Sound → Motion → Assembly → QC → Metadata",
    )

    # Read tier: produce text artifacts (no API cost)
    profile.add_node("scripting", ScriptingAgent,
        description="Generate video script with hook, body & CTA",
        tier="read")

    profile.add_node("director", DirectorAgent,
        description="Create scene-by-scene storyboard",
        tier="read", depends_on=["scripting"])

    # Draft tier: produce assets for review (some cost)
    profile.add_node("assets", AssetOrchestrator,
        description="Source images, logos, b-roll (Pexels-first, AI fallback)",
        tier="draft", depends_on=["director"])

    profile.add_node("video_gen", VideoGenerationAgent,
        description="Generate AI video clips (human approved)",
        tier="draft", depends_on=["assets"])

    profile.add_node("voiceover", VoiceoverAgent,
        description="Generate voiceover via CosyVoice TTS",
        tier="draft", depends_on=["scripting"])

    profile.add_node("sound", SoundAgent,
        description="Source BGM and sound effects",
        tier="draft", depends_on=["director"])

    # Act tier: irreversible operations
    profile.add_node("motion", MotionGraphicsAgent,
        description="Create Remotion + Hyperframes compositions",
        tier="act", depends_on=["assets", "director"])

    profile.add_node("assembly", AssemblyAgent,
        description="FFmpeg final video assembly",
        tier="act", depends_on=["video_gen", "voiceover", "sound", "motion"])

    profile.add_node("qc", QCAgent,
        description="Quality checks on final output",
        tier="read", depends_on=["assembly"])

    profile.add_node("metadata", MetadataAgent,
        description="Generate thumbnails, titles & descriptions",
        tier="read", depends_on=["assembly"])

    return profile


def post_production_profile() -> CapabilityProfile:
    """Workflow 2: Post-Production Editing — raw footage to polished cut."""
    from agents.transcription import TranscriptionAgent
    from agents.broll import BRollAgent
    from agents.overlay import OverlayAgent
    from agents.assembly import AssemblyAgent
    from agents.qc import QCAgent

    profile = CapabilityProfile(
        profile_id="post_production",
        name="Post-Production Editing",
        description="Raw Footage → Analyze → Transcribe → Edit → Polish → Final Cut",
    )

    profile.add_node("analyze", TranscriptionAgent,
        description="Analyze and transcribe input footage",
        tier="read")

    profile.add_node("transcribe", TranscriptionAgent,
        description="Speech-to-text via Alibaba ASR",
        tier="read", depends_on=["analyze"])

    profile.add_node("broll", BRollAgent,
        description="Source and insert stock B-roll footage",
        tier="draft", depends_on=["transcribe"])

    profile.add_node("overlay", OverlayAgent,
        description="Add kinetic captions and lower thirds",
        tier="draft", depends_on=["transcribe"])

    profile.add_node("edit_assembly", AssemblyAgent,
        description="Combine all edits into final cut",
        tier="act", depends_on=["broll", "overlay"])

    profile.add_node("edit_qc", QCAgent,
        description="Final quality check",
        tier="read", depends_on=["edit_assembly"])

    return profile


# Registry of all available profiles
PROFILES = {
    "creative_production": creative_production_profile,
    "post_production": post_production_profile,
}


def get_profile(profile_id: str) -> CapabilityProfile:
    """Get a capability profile by ID."""
    if profile_id not in PROFILES:
        raise ValueError(f"Unknown profile: {profile_id}. Available: {list(PROFILES.keys())}")
    return PROFILES[profile_id]()
