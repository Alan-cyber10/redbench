"""Runs one or more plugins against a target model and aggregates results."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from redbench.core.plugin_base import AttackPrompt, EvalResult, RedTeamPlugin

TargetFn = Callable[[str], str]


@dataclass
class PluginReport:
    plugin_name: str
    results: list[EvalResult] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def successes(self) -> int:
        return sum(1 for r in self.results if r.success)

    @property
    def attack_success_rate(self) -> float:
        return self.successes / self.total if self.total else 0.0


class RedTeamRunner:
    """Wires plugins + a target model together and produces reports."""

    def __init__(self, target_fn: TargetFn) -> None:
        """`target_fn` takes a prompt string and returns the model's response string.

        Wrap whatever you're testing (an API call, a local model, an agent
        loop) in a plain function with this signature.
        """
        self.target_fn = target_fn

    def run_plugin(self, plugin: RedTeamPlugin) -> PluginReport:
        plugin.setup()
        report = PluginReport(plugin_name=plugin.name)
        try:
            for attack in plugin.generate_prompts():
                response = self.target_fn(attack.prompt)
                result = plugin.evaluate(attack, response)
                result.raw_response = response
                report.results.append(result)
        finally:
            plugin.teardown()
        return report

    def run(self, plugins: list[RedTeamPlugin]) -> dict[str, PluginReport]:
        return {p.name: self.run_plugin(p) for p in plugins}


def format_report(reports: dict[str, PluginReport]) -> str:
    """Render reports as a small human-readable text summary."""
    lines = []
    for name, report in reports.items():
        lines.append(
            f"[{name}] {report.successes}/{report.total} attacks succeeded "
            f"(ASR={report.attack_success_rate:.1%})"
        )
        for r in report.results:
            if r.success:
                lines.append(f"    FAIL  {r.prompt_id}: {r.reason or ''}")
    return "\n".join(lines)
