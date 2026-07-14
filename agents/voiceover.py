"""
Voiceover Agent — generates voiceover from script using Alibaba TTS.
Uses DashScope SDK with WebSocket (proven working pattern).
Primary: CosyVoice v3 Plus
Fallback: Qwen3 TTS Instruct Flash
"""

import json
import os
from pathlib import Path
from typing import Optional

from agents.base import BaseAgent, AgentInput, AgentOutput


class VoiceoverAgent(BaseAgent):
    """Generates voiceover audio from script text using Alibaba TTS."""

    name = "voiceover"
    description = "Generates voiceover audio (Alibaba TTS)"

    TTS_MODELS = [
        "cosyvoice-v3-plus",
        "qwen3-tts-instruct-flash",
    ]

    VOICE = "longanyang"

    def execute(self, input_data: AgentInput) -> AgentOutput:
        script_text = input_data.prompt
        project_dir = input_data.project_dir

        if not script_text:
            return AgentOutput(success=False, message="No script text provided")

        audio_dir = project_dir / "audio" if project_dir else Path("audio")
        audio_dir.mkdir(parents=True, exist_ok=True)

        if isinstance(input_data.data, dict):
            full_script = input_data.data.get("full_script", script_text)
        else:
            full_script = script_text

        output_path = audio_dir / "voiceover.mp3"
        srt_path = audio_dir / "captions.srt"

        try:
            vo_path = None
            used_model = None

            for model in self.TTS_MODELS:
                self.console.print(f"  [dim]Trying {model}...[/dim]")
                vo_path = self._dashscope_tts(full_script, output_path, model)
                if vo_path:
                    used_model = model
                    break

            if vo_path:
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

    def _dashscope_tts(self, text: str, output_path: Path, model: str) -> Optional[Path]:
        """Generate voiceover using DashScope SDK (WebSocket — proven working)."""
        try:
            import dashscope
            from dashscope.audio.tts_v2 import SpeechSynthesizer
            from config import ALIBABA_API_KEY

            dashscope.api_key = ALIBABA_API_KEY
            dashscope.base_websocket_api_url = 'wss://dashscope-intl.aliyuncs.com/api-ws/v1/inference'

            synthesizer = SpeechSynthesizer(model=model, voice=self.VOICE)

            self.console.print(f"  [dim]Calling TTS via WebSocket: {model} with {len(text)} chars...[/dim]")

            audio = synthesizer.call(text)

            if audio and len(audio) > 0:
                with open(output_path, 'wb') as f:
                    f.write(audio)
                self.console.print(f"  [green]✓[/green] Voiceover generated ({model}, voice={self.VOICE})")
                return output_path
            else:
                self.console.print(f"  [yellow]⚠️ {model} returned empty audio[/yellow]")

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
