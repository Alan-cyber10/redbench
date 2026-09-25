from redbench.core.registry import PluginRegistry
from redbench.core.runner import RedTeamRunner
from redbench.plugins.redbench_plugin.plugin import RedBenchPlugin


def test_register_and_get():
    registry = PluginRegistry()
    registry.register(RedBenchPlugin)
    assert registry.get("redbench") is RedBenchPlugin


def test_generate_prompts_nonempty():
    plugin = RedBenchPlugin()
    prompts = plugin.generate_prompts()
    assert len(prompts) > 0
    assert all(p.id for p in prompts)


def test_runner_all_refused_gives_zero_asr():
    plugin = RedBenchPlugin()
    runner = RedTeamRunner(target_fn=lambda p: "I can't help with that.")
    report = runner.run_plugin(plugin)
    assert report.attack_success_rate == 0.0


def test_runner_never_refused_gives_full_asr():
    plugin = RedBenchPlugin()
    runner = RedTeamRunner(target_fn=lambda p: "Sure, here's how...")
    report = runner.run_plugin(plugin)
    assert report.attack_success_rate == 1.0
