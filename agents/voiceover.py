"""
Voiceover Agent — generates voiceover from script using Alibaba TTS.
Primary: CosyVoice v3 Plus
Fallback: Qwen3 TTS Instruct Flash
"""

from pathlib import Path
from typing import Optional

from agents.base import BaseAgent, AgentInput, AgentOutput


class VoiceoverAgent(BaseAgent):
    """Generates voiceover audio from script text using Alibaba TTS."""

    name = "voiceover"
    description = "Generates voiceover audio (Alibaba TTS)"

    # Alibaba TTS models in priority order
    TTS_MODELS = [
        "cosyvoice-v3-plus",        # Primary: best quality
        "qwen3-tts-instruct-flash", # Fallback: fast, instruction-following
    ]

    def execute(self, input_data: AgentInput) -> AgentOutput:
        script_text = input_data.prompt
        project_dir = input_data.project_dir

        if not script_text:
            return AgentOutput(success=False, message="No script text provided")

        # Create audio directory
        audio_dir = project_dir / "audio" if project_dir else Path("audio")
        audio_dir.mkdir(parents=True, exist_ok=True)

        # Extract full script if available
        if isinstance(input_data.data, dict):
            full_script = input_data.data.get("full_script", script_text)
        else:
            full_script = script_text

        output_path = audio_dir / "voiceover.mp3"
        srt_path = audio_dir / "captions.srt"

        try:
            # Try each Alibaba TTS model in order
            vo_path = None
            used_model = None

            for model in self.TTS_MODELS:
                self.console.print(f"  [dim]Trying {model}...[/dim]")
                vo_path = self._alibaba_tts(full_script, output_path, model)
                if vo_path:
                    used_model = model
                    break

            if vo_path:
                # Generate SRT captions from the script
                srt_path = self._generate_srt(full_script, audio_dir)

                return AgentOutput(
                    success=True,
                    data={"voiceover_path": str(vo_path), "srt_path": str(srt_path), "model": used_model},
                    artifact_path=vo_path,
                    message=f"Voiceover generated with {used_model}",
                    metadata={"duration": "TBD", "model": used_model},
                )
            else:
                return AgentOutput(success=False, message="All Alibaba TTS models failed")

        except Exception as e:
            return AgentOutput(success=False, message=f"Voiceover failed: {str(e)}")

    def _alibaba_tts(self, text: str, output_path: Path, model: str) -> Optional[Path]:
        """Generate voiceover using Alibaba TTS."""
        try:
            import requests
            from config import ALIBABA_API_KEY

            # Alibaba DashScope TTS API (direct HTTP, not OpenAI-compatible)
            url = "https://dashscope-intl.aliyuncs.com/api/v1/services/audio/tts"
            
            headers = {
                "Authorization": f"Bearer {ALIBABA_API_KEY}",
                "Content-Type": "application/json",
            }

            # CosyVoice API format
            payload = {
                "model": model,
                "input": {
                    "text": text,
                },
                "parameters": {
                    "voice": "longxiaochun",  # Default voice
                    "format": "mp3",
                    "sample_rate": 16000,
                },
            }

            response = requests.post(url, headers=headers, json=payload, timeout=60)

            if response.status_code == 200:
                # Check if response is audio data or JSON with audio URL
                content_type = response.headers.get("Content-Type", "")
                
                if "audio" in content_type or "octet-stream" in content_type:
                    # Direct audio data
                    with open(output_path, "wb") as f:
                        f.write(response.content)
                    self.console.print(f"  [green]✓[/green] Voiceover generated ({model})")
                    return output_path
                else:
                    # JSON response with audio URL or base64
                    data = response.json()
                    if "output" in data and "audio" in data["output"]:
                        import base64
                        audio_data = base64.b64decode(data["output"]["audio"])
                        with open(output_path, "wb") as f:
                            f.write(audio_data)
                        self.console.print(f"  [green]✓[/green] Voiceover generated ({model})")
                        return output_path
                    else:
                        self.console.print(f"  [yellow]⚠️ {model} returned unexpected format: {data}[/yellow]")
            else:
                self.console.print(f"  [yellow]⚠️ {model} failed: {response.status_code} - {response.text[:100]}[/yellow]")

        except Exception as e:
            self.console.print(f"  [yellow]⚠️ {model} failed: {str(e)[:80]}[/yellow]")

        return None

    def _generate_srt(self, text: str, output_dir: Path) -> Path:
        """Generate basic SRT from script text.
        For hackathon: split by sentences with estimated timing.
        Production: use Alibaba ASR for actual alignment."""
        import re

        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())

        # Estimate words per minute (natural speech ~150 WPM)
        wpm = 150
        words_per_sec = wpm / 60

        srt_path = output_dir / "captions.srt"
        current_time = 0.0

        with open(srt_path, "w") as f:
            for i, sentence in enumerate(sentences, 1):
                word_count = len(sentence.split())
                duration = word_count / words_per_sec

                start_time = current_time
                end_time = current_time + duration

                f.write(f"{i}\n")
                f.write(f"{self._format_srt_time(start_time)} --> {self._format_srt_time(end_time)}\n")
                f.write(f"{sentence}\n\n")

                current_time = end_time

        self.console.print(f"  [green]✓[/green] SRT captions generated: {srt_path.name}")
        return srt_path

    @staticmethod
    def _format_srt_time(seconds: float) -> str:
        """Format seconds as SRT timestamp."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
