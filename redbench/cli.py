"""`redbench` command-line entry point.

Examples:
    redbench list-plugins
    redbench run --plugin redbench --target examples.dummy_target:echo_target
"""

from __future__ import annotations

import argparse
import importlib

from redbench.core.registry import default_registry
from redbench.core.runner import RedTeamRunner, format_report
from redbench.plugins.redbench_plugin.plugin import RedBenchPlugin

# Built-in plugins are always available without needing pip-installed
# entry points; third-party plugins are picked up via load_entry_points().
default_registry.register(RedBenchPlugin)


def _load_target(spec: str):
    """Load a target callable from a 'module.path:function_name' spec."""
    module_path, _, func_name = spec.partition(":")
    if not func_name:
        raise ValueError("Target must be given as 'module.path:function_name'")
    module = importlib.import_module(module_path)
    return getattr(module, func_name)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="redbench")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list-plugins", help="List all registered plugins.")

    run_p = sub.add_parser("run", help="Run one or more plugins against a target.")
    run_p.add_argument(
        "--plugin",
        action="append",
        required=True,
        help="Plugin name to run; repeat to run several.",
    )
    run_p.add_argument(
        "--target",
        required=True,
        help="Target callable as 'module.path:function_name'. "
        "The function must take a prompt string and return a response string.",
    )

    args = parser.parse_args(argv)
    default_registry.load_entry_points()

    if args.command == "list-plugins":
        for plugin_cls in default_registry.list_plugins():
            print(f"{plugin_cls.name}: {plugin_cls.description}")
        return 0

    if args.command == "run":
        target_fn = _load_target(args.target)
        plugins = [default_registry.get(name)() for name in args.plugin]
        runner = RedTeamRunner(target_fn)
        reports = runner.run(plugins)
        print(format_report(reports))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
