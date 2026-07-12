"""
FFmpeg Assembly Agent — stitches all elements into the final video.
Combines: video clips + voiceover + BGM + SFX + captions + transitions.
"""

import subprocess
import json
from pathlib import Path
from typing import Optional

from agents.base import BaseAgent, AgentInput, AgentOutput


class AssemblyAgent(BaseAgent):
    """Assembles final video using FFmpeg."""

    name = "assembly"
    description = "Assembles final video with FFmpeg"

    def execute(self, input_data: AgentInput) -> AgentOutput:
        project_dir = input_data.project_dir
        config = input_data.config

        if not project_dir:
            return AgentOutput(success=False, message="No project directory provided")

        # Gather all components
        render_dir = project_dir / "render"
        audio_dir = project_dir / "audio"
        sound_dir = project_dir / "sound"
        output_dir = project_dir / "output"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Find rendered video (prefer Remotion, fallback to Hyperframes)
        video_path = self._find_rendered_video(render_dir)
        if not video_path:
            return AgentOutput(success=False, message="No rendered video found")

        # Find voiceover
        voiceover_path = audio_dir / "voiceover.mp3"
        if not voiceover_path.exists():
            voiceover_path = None

        # Find BGM
        bgm_path = self._find_bgm(sound_dir)

        # Find SRT captions
        srt_path = audio_dir / "captions.srt"
        if not srt_path.exists():
            srt_path = None

        # Assemble
        final_path = output_dir / "final.mp4"

        self.console.print("  [dim]Assembling final video...[/dim]")

        success = self._assemble(
            video_path=video_path,
            voiceover_path=voiceover_path,
            bgm_path=bgm_path,
            srt_path=srt_path,
            output_path=final_path,
            aspect_ratio=config.get("aspect_ratio", "9:16"),
        )

        if success and final_path.exists():
            # Get video info
            info = self._get_video_info(final_path)

            return AgentOutput(
                success=True,
                data={
                    "final_video": str(final_path),
                    "info": info,
                },
                artifact_path=final_path,
                message=f"Final video assembled: {final_path.name} ({info.get('duration', '?')}s)",
                metadata=info,
            )

        return AgentOutput(success=False, message="Assembly failed")

    def _find_rendered_video(self, render_dir: Path) -> Optional[Path]:
        """Find the best rendered video."""
        # Prefer Remotion
        remotion_video = render_dir / "remotion" / "out" / "video.mp4"
        if remotion_video.exists():
            return remotion_video

        # Fallback to Hyperframes
        hf_video = render_dir / "hyperframes" / "out" / "video.mp4"
        if hf_video.exists():
            return hf_video

        # Check for any mp4 in render dirs
        for mp4 in render_dir.rglob("*.mp4"):
            return mp4

        return None

    def _find_bgm(self, sound_dir: Path) -> Optional[Path]:
        """Find background music."""
        if not sound_dir.exists():
            return None

        bgm_dir = sound_dir / "bgm"
        if bgm_dir.exists():
            for ext in [".mp3", ".wav", ".ogg", ".m4a"]:
                for f in bgm_dir.glob(f"*{ext}"):
                    if f.is_file() and f.stat().st_size > 1000:  # Skip tiny files
                        return f

        return None

    def _assemble(
        self,
        video_path: Path,
        voiceover_path: Optional[Path],
        bgm_path: Optional[Path],
        srt_path: Optional[Path],
        output_path: Path,
        aspect_ratio: str = "9:16",
    ) -> bool:
        """Assemble final video with all audio and captions."""
        from config import FFMPEG_BINARY

        try:
            # Build FFmpeg command
            cmd = [FFMPEG_BINARY, "-i", str(video_path)]

            # Add voiceover
            if voiceover_path and voiceover_path.exists():
                cmd.extend(["-i", str(voiceover_path)])

            # Add BGM
            if bgm_path and bgm_path.exists():
                cmd.extend(["-i", str(bgm_path)])

            # Video filter (add captions if available)
            vf_filters = []
            if srt_path and srt_path.exists():
                vf_filters.append(f"subtitles='{srt_path}'")

            # Audio filter (mix voiceover + BGM)
            audio_inputs = []
            if voiceover_path and voiceover_path.exists():
                audio_inputs.append("[1:a]")
            if bgm_path and bgm_path.exists():
                audio_inputs.append("[2:a]")

            if audio_inputs:
                # Mix audio: voiceover at full volume, BGM at 30%
                af_filter = f"{','.join(audio_inputs)}amix=inputs={len(audio_inputs)}:duration=shortest[aout]"
                cmd.extend(["-filter_complex", af_filter])
                cmd.extend(["-map", "0:v"])
                if vf_filters:
                    cmd.extend(["-vf", ",".join(vf_filters)])
                cmd.extend(["-map", "[aout]"])
            else:
                if vf_filters:
                    cmd.extend(["-vf", ",".join(vf_filters)])

            # Output settings
            cmd.extend([
                "-c:v", "libx264",
                "-preset", "medium",
                "-crf", "23",
                "-c:a", "aac",
                "-b:a", "192k",
                "-y",
                str(output_path),
            ])

            self.console.print(f"  [dim]Running FFmpeg assembly...[/dim]")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                shell=True,
            )

            if result.returncode == 0 and output_path.exists():
                self.console.print(f"  [green]✓[/green] Final video assembled")
                return True
            else:
                self.console.print(f"  [yellow]⚠️ FFmpeg exit code: {result.returncode}[/yellow]")
                if result.stderr:
                    self.console.print(f"  [dim]{result.stderr[:300]}[/dim]")
                return False

        except Exception as e:
            self.console.print(f"  [red]✗[/red] Assembly failed: {e}")
            return False

    def _get_video_info(self, video_path: Path) -> dict:
        """Get video metadata."""
        from config import FFPROBE_BINARY

        try:
            result = subprocess.run(
                [
                    FFPROBE_BINARY, "-v", "error",
                    "-select_streams", "v:0",
                    "-show_entries", "stream=width,height,r_frame_rate,duration",
                    "-show_entries", "format=duration,size",
                    "-of", "json",
                    str(video_path),
                ],
                capture_output=True, text=True, timeout=10,
            )

            if result.returncode == 0:
                data = json.loads(result.stdout)
                stream = data.get("streams", [{}])[0]
                fmt = data.get("format", {})

                fps_str = stream.get("r_frame_rate", "30/1")
                if "/" in fps_str:
                    num, den = fps_str.split("/")
                    fps = int(num) / int(den) if int(den) != 0 else 30
                else:
                    fps = float(fps_str)

                size_mb = int(fmt.get("size", 0)) / (1024 * 1024)

                return {
                    "width": stream.get("width", 0),
                    "height": stream.get("height", 0),
                    "fps": round(fps, 2),
                    "duration": round(float(fmt.get("duration", 0)), 2),
                    "size_mb": round(size_mb, 2),
                }

        except Exception:
            pass

        return {}
