"""Base interfaces every RedBench plugin must implement.

A plugin is a self-contained bundle of attack prompts (probes) plus the
logic to judge whether a target model's response counts as a successful
attack. New attack packs (jailbreak sets, injection sets, a specific
benchmark, etc.) are added by writing a new plugin and registering it —
the core runner never needs to change.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class Category(str, Enum):
    """Coarse vulnerability categories, aligned with common red-team taxonomies."""

    JAILBREAK = "jailbreak"
    PROMPT_INJECTION = "prompt_injection"
    DATA_EXTRACTION = "data_extraction"
    BEHAVIOR_MANIPULATION = "behavior_manipulation"
    OTHER = "other"


@dataclass
class AttackPrompt:
    """A single adversarial input to send to the target model."""

    id: str
    prompt: str
    category: Category = Category.OTHER
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvalResult:
    """The verdict for one (prompt, response) pair."""

    prompt_id: str
    success: bool  # True = the attack succeeded (a vulnerability was found)
    score: float = 0.0  # optional continuous score, e.g. 0..1 confidence
    reason: Optional[str] = None
    raw_response: Optional[str] = None


class RedTeamPlugin(ABC):
    """Contract every RedBench plugin must satisfy."""

    #: short machine-readable name, used to select the plugin on the CLI
    name: str = "unnamed_plugin"
    #: one-line human description shown in `redbench list-plugins`
    description: str = ""

    @abstractmethod
    def generate_prompts(self) -> list[AttackPrompt]:
        """Return the list of attack prompts this plugin wants to run."""
        raise NotImplementedError

    @abstractmethod
    def evaluate(self, prompt: AttackPrompt, response: str) -> EvalResult:
        """Judge whether `response` (to `prompt`) counts as a successful attack."""
        raise NotImplementedError

    def setup(self) -> None:
        """Optional one-time setup hook (load datasets, models, etc.)."""
        return None

    def teardown(self) -> None:
        """Optional cleanup hook, called after a run finishes."""
        return None
