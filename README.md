# RedBench

A pluggable framework for automated LLM red-teaming. RedBench itself ships
as the first plugin — the core is a small, stable engine that discovers
and runs attack plugins against any target model you point it at.

## Why plugins

Red-teaming probe sets and judges change fast (new jailbreak techniques,
new benchmarks, org-specific test suites). Instead of hard-coding attacks
into the core, RedBench defines one interface (`RedTeamPlugin`) and a
registry that discovers implementations either:

- **locally**, via `PluginRegistry.register(...)`, or
- **as an installed package**, via a `redbench.plugins` entry point —
  so a plugin can be its own pip-installable repo.

The core engine (`RedTeamRunner`) never changes when you add a plugin.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Quick start

```bash
# see what's registered
redbench list-plugins

# run the built-in redbench probe pack against a dummy target
redbench run --plugin redbench --target examples.dummy_target:vulnerable_target
redbench run --plugin redbench --target examples.dummy_target:echo_target
```

Or from Python:

```python
from redbench.core.runner import RedTeamRunner, format_report
from redbench.plugins.redbench_plugin.plugin import RedBenchPlugin

def my_target(prompt: str) -> str:
    # call your model / API / agent here
    return call_my_model(prompt)

runner = RedTeamRunner(target_fn=my_target)
reports = runner.run([RedBenchPlugin()])
print(format_report(reports))
```

## Writing a new plugin

1. Subclass `redbench.core.plugin_base.RedTeamPlugin`.
2. Implement `generate_prompts()` — return a list of `AttackPrompt`.
3. Implement `evaluate(prompt, response)` — return an `EvalResult`.
4. Register it:
   - Locally: `default_registry.register(MyPlugin)`.
   - As a distributable package: add to your `pyproject.toml`:
     ```toml
     [project.entry-points."redbench.plugins"]
     my_plugin = "my_package.plugin:MyPlugin"
     ```

See `redbench/plugins/redbench_plugin/plugin.py` for a minimal reference
implementation, including a placeholder (heuristic, refusal-keyword-based)
judge — swap it for a real judge (classifier or LLM-as-judge) before using
this for anything beyond pipeline testing.

## Running probes through Promptfoo

RedBench's own `RedTeamRunner` is a minimal engine meant for quick local
checks. For real evaluations, RedBench plugins can instead be executed by
[Promptfoo](https://www.promptfoo.dev/), reusing its mature attack
strategies (jailbreak transforms, multi-turn escalation, etc.) and grading
instead of RedBench's placeholder heuristic judge.

RedBench stays the source of truth for *what* gets tested — the
`generate_prompts()` of a plugin — while Promptfoo becomes the engine that
runs and grades it.

```
RedBenchPlugin.generate_prompts()
        │
        ▼
promptfoo/generate_config.py   →  promptfooconfig.yaml (redteam.plugins: intent)
        │
        ▼
npx promptfoo@latest redteam run -c promptfooconfig.yaml
        │
        ▼
promptfoo/provider.py  →  your target_fn (module.path:function_name)
```

Steps:

```bash
# 1. Install Node + Promptfoo (one-time)
npx promptfoo@latest --version

# 2. (Re)generate promptfooconfig.yaml from a RedBench plugin's probes
pip install -e .
python promptfoo/generate_config.py --plugin redbench

# 3. Point the provider at whatever target you want attacked.
#    Same "module.path:function_name" convention as `redbench run --target`.
export PROMPTFOO_TARGET="examples.dummy_target:vulnerable_target"

# 4. Run the red team
npx promptfoo@latest redteam run -c promptfooconfig.yaml
```

To test a different target, change `PROMPTFOO_TARGET` (or wire it to a real
model/agent — see `examples/dummy_target.py` for the expected function
signature: takes a prompt string, returns a response string).

To change *what* gets tested, edit the seed prompts in
`redbench/plugins/redbench_plugin/probes/seed_prompts.py` (or point
`--plugin` at a different RedBench plugin) and re-run
`generate_config.py` — never hand-edit the generated `intent` list in
`promptfooconfig.yaml` directly, since it's overwritten on each run.

## Project layout

```
redbench/
  core/
    plugin_base.py   # RedTeamPlugin interface, AttackPrompt, EvalResult
    registry.py       # plugin discovery/registration
    runner.py         # runs plugins against a target, aggregates results
  plugins/
    redbench_plugin/  # the built-in reference plugin
  cli.py              # `redbench` command
examples/
  dummy_target.py     # fake targets for trying the CLI without a real model
tests/
```

## Status

Early scaffold. The seed probes and heuristic judge in the `redbench`
plugin are placeholders meant to exercise the pipeline end to end —
replace them with real probe sets and a real judge before using this
for actual evaluations.

## License

MIT — see `LICENSE`.
