"""
Base Agent — all specialized agents inherit from this.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional
from pathlib import Path

from rich.console import Console

console = Console()
logger = logging.getLogger("agents")


@dataclass
class AgentInput:
    """Standardized input for all agents."""
    prompt: str = ""
    project_dir: Optional[Path] = None
    context: dict = field(default_factory=dict)
    config: dict = field(default_factory=dict)


@dataclass
class AgentOutput:
    """Standardized output from all agents."""
    success: bool = False
    data: Any = None
    artifact_path: Optional[Path] = None
    message: str = ""
    metadata: dict = field(default_factory=dict)


class BaseAgent(ABC):
    """Abstract base class for all agents."""

    name: str = "base"
    description: str = ""

    def __init__(self, console: Optional[Console] = None):
        self.console = console or console
        logger.info(f"Agent initialized: {self.name}")

    def run(self, input_data: AgentInput) -> AgentOutput:
        """Main entry point — wraps the actual work with logging."""
        self.console.print(f"[dim]└─ 🤖 {self.name}: {self.description}[/dim]")
        logger.info(f"Agent {self.name} started with input: {input_data.prompt[:100]}...")

        try:
            result = self.execute(input_data)
            logger.info(f"Agent {self.name} completed: {result.message}")
            return result
        except Exception as e:
            logger.error(f"Agent {self.name} failed: {str(e)}")
            return AgentOutput(
                success=False,
                message=f"Agent {self.name} failed: {str(e)}",
            )

    @abstractmethod
    def execute(self, input_data: AgentInput) -> AgentOutput:
        """Implement the agent's actual work here."""
        ...

    def get_llm_client(self):
        """Get configured LLM client (OpenAI-compatible)."""
        from openai import OpenAI
        from config import ALIBABA_API_KEY, ALIBABA_BASE_URL, LLM_MODEL

        return OpenAI(
            api_key=ALIBABA_API_KEY,
            base_url=ALIBABA_BASE_URL,
            timeout=300.0,
        )

    def call_llm(self, system_prompt: str, user_prompt: str, model: str = None) -> str:
        """Simple LLM call helper."""
        client = self.get_llm_client()
        model = model or "qwen3.7-max"

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=4096,
            extra_body={"enable_thinking": True},
        )

        return response.choices[0].message.content
