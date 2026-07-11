"""
Transcription Agent — transcribes audio/video to text using Alibaba ASR.
Primary: fun-asr
Fallback: fun-asr-realtime, qwen3-asr-flash-realtime
Replaces Whisper entirely.
"""

import subprocess
from pathlib import Path
from typing import Optional

from agents.base import BaseAgent, AgentInput, AgentOutput


class TranscriptionAgent(BaseAgent):
    """Transcribes audio/video to text using Alibaba ASR models."""

    name = "transcription"
    description = "Transcribes audio to text (Alibaba ASR)"

    # Alibaba ASR models in priority order
    ASR_MODELS = [
        "fun-asr",                    # Primary: batch transcription
        "fun-asr-realtime",           # Fallback: realtime capable
        "qwen3-asr-flash-realtime",   # Fallback: fast flash model
    ]

    def execute(self, input_data: AgentInput) -> AgentOutput:
        audio_path = input_data.prompt
        project_dir = input_data.project_dir

        if not audio_path:
            return AgentOutput(success=False, message="No audio/video path provided")

        audio_file = Path(audio_path)
        if not audio_file.exists():
            return AgentOutput(success=False, message=f"File not found: {audio_path}")

        # Create output directory
        output_dir = project_dir / "transcripts" if project_dir else Path("transcripts")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Extract audio if video
        wav_path = self._extract_audio(audio_file, output_dir)
        if not wav_path:
            return AgentOutput(success=False, message="Failed to extract audio")

        # Try each ASR model
        result = None
        used_model = None

        for model in self.ASR_MODELS:
            self.console.print(f"  [dim]Transcribing with {model}...[/dim]")
            result = self._transcribe(wav_path, model)
            if result and result.get("text"):
                used_model = model
                break

        if not result or not result.get("text"):
            return AgentOutput(success=False, message="All Alibaba ASR models failed")

        # Save transcript
        transcript_path = output_dir / f"{audio_file.stem}_transcript.txt"
        with open(transcript_path, "w") as f:
            f.write(result["text"])

        # Save SRT if timestamps available
        srt_path = None
        if result.get("segments"):
            srt_path = output_dir / f"{audio_file.stem}.srt"
            self._save_srt(result["segments"], srt_path)

        return AgentOutput(
            success=True,
            data={
                "text": result["text"],
                "segments": result.get("segments", []),
                "transcript_path": str(transcript_path),
                "srt_path": str(srt_path) if srt_path else None,
                "model": used_model,
            },
            artifact_path=transcript_path,
            message=f"Transcribed with {used_model}: {len(result['text'])} chars",
            metadata={"model": used_model, "char_count": len(result["text"])},
        )

    def _extract_audio(self, input_file: Path, output_dir: Path) -> Optional[Path]:
        """Extract audio from video file as WAV."""
        from config import FFMPEG_BINARY, FFPROBE_BINARY

        wav_path = output_dir / f"{input_file.stem}.wav"

        # Check if already WAV
        if input_file.suffix.lower() == ".wav":
            return input_file

        try:
            subprocess.run(
                [
                    FFMPEG_BINARY, "-i", str(input_file),
                    "-vn", "-acodec", "pcm_s16le",
                    "-ar", "16000", "-ac", "1",
                    "-y", str(wav_path),
                ],
                capture_output=True,
                timeout=120,
            )

            if wav_path.exists():
                return wav_path

        except Exception as e:
            self.console.print(f"  [red]✗[/red] Audio extraction failed: {e}")

        return None

    def _transcribe(self, audio_path: Path, model: str) -> Optional[dict]:
        """Transcribe audio using Alibaba ASR."""
        try:
            from openai import OpenAI
            from config import ALIBABA_API_KEY, ALIBABA_BASE_URL
            import base64

            client = OpenAI(api_key=ALIBABA_API_KEY, base_url=ALIBABA_BASE_URL)

            # Read audio file
            with open(audio_path, "rb") as f:
                audio_data = f.read()

            # Encode as base64
            audio_b64 = base64.b64encode(audio_data).decode("utf-8")

            # Call ASR model
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_audio",
                                "input_audio": {
                                    "data": audio_b64,
                                    "format": "wav",
                                },
                            },
                            {
                                "type": "text",
                                "text": "Transcribe this audio accurately. Return the text only.",
                            },
                        ],
                    }
                ],
                max_tokens=4096,
                extra_body={"enable_thinking": False},
            )

            if response.choices and response.choices[0].message.content:
                text = response.choices[0].message.content.strip()

                # Try to parse segments if available
                segments = self._parse_segments(text)

                return {
                    "text": text,
                    "segments": segments,
                }

        except Exception as e:
            self.console.print(f"  [yellow]⚠️ {model} failed: {str(e)[:80]}[/yellow]")

        return None

    def _parse_segments(self, text: str) -> list:
        """Parse transcript text into segments with timestamps.
        Basic implementation — production would use proper ASR output format."""
        import re

        # Try to find timestamp patterns like [00:00:01] or (1.5s)
        segments = []
        lines = text.split("\n")

        current_time = 0.0
        for line in lines:
            # Check for timestamp
            ts_match = re.search(r'\[(\d+):(\d+):(\d+)\]', line)
            if ts_match:
                h, m, s = int(ts_match.group(1)), int(ts_match.group(2)), int(ts_match.group(3))
                current_time = h * 3600 + m * 60 + s
                line = line[ts_match.end():].strip()

            if line:
                segments.append({
                    "start": current_time,
                    "end": current_time + 3.0,  # Estimate 3s per segment
                    "text": line,
                })
                current_time += 3.0

        return segments

    def _save_srt(self, segments: list, output_path: Path):
        """Save segments as SRT file."""
        with open(output_path, "w") as f:
            for i, seg in enumerate(segments, 1):
                f.write(f"{i}\n")
                f.write(f"{self._format_srt_time(seg['start'])} --> {self._format_srt_time(seg['end'])}\n")
                f.write(f"{seg['text']}\n\n")

    @staticmethod
    def _format_srt_time(seconds: float) -> str:
        """Format seconds as SRT timestamp."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
