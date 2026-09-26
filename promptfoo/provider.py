"""Promptfoo <-> RedBench bridge (provider side).

Promptfoo's Python provider support calls `call_api(prompt, options, context)`
for every generated adversarial test case. Here we forward that prompt to
whatever RedBench "target_fn" you're testing, so Promptfoo's attack engine
(strategies, multi-turn, grading) runs against the same target your RedBench
plugins run against.

Which target to call is chosen via the PROMPTFOO_TARGET env var, formatted
as "module.path:function_name" (same convention as `redbench run --target`).
Defaults to the harmless echo target so `promptfoo redteam run` works out of
the box before you've wired up a real model.
"""

from __future__ import annotations

import importlib
import os
import sys

# Make the repo root importable (this file lives in <repo>/promptfoo/).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "examples"))

DEFAULT_TARGET = "dummy_target:echo_target"
_cached_fn = None


def _load_target():
    global _cached_fn
    if _cached_fn is not None:
        return _cached_fn
    spec = os.environ.get("PROMPTFOO_TARGET", DEFAULT_TARGET)
    module_path, _, func_name = spec.partition(":")
    module = importlib.import_module(module_path)
    _cached_fn = getattr(module, func_name)
    return _cached_fn


def call_api(prompt: str, options: dict, context: dict) -> dict:
    """Entry point Promptfoo calls for each generated test case.

    `context['test']['metadata']` carries pluginId / strategyId when this
    call is part of a redteam run — useful later if you want to route
    different plugin IDs to different targets.
    """
    target_fn = _load_target()
    try:
        output = target_fn(prompt)
    except Exception as exc:  # surface target errors as a normal eval failure
        return {"error": f"target_fn raised: {exc!r}"}
    return {"output": output}
