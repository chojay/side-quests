"""Command line interface."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from xpslint.config import Config, ConfigError
from xpslint.engine import run
from xpslint.io import load
from xpslint.io.declarative import FitFormatError
from xpslint.report import render_json, render_text


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="xpslint",
        description="Audit XPS peak fits against tiered physics rules.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check", help="check one or more fit files")
    check.add_argument("paths", nargs="+", type=Path)
    check.add_argument(
        "--strict",
        action="store_true",
        help="exit non-zero when any rule could not be checked",
    )
    check.add_argument(
        "--min-coverage",
        type=float,
        default=None,
        metavar="FRACTION",
        help="exit non-zero below this coverage. No default: an arbitrary threshold "
        "would be exactly the kind of unjustified round number this tool exists to "
        "eliminate, so you have to choose one deliberately.",
    )
    check.add_argument("--format", choices=("text", "json"), default="text")
    check.add_argument("--show-all", action="store_true", help="include passes and n/a")
    check.add_argument("--no-color", action="store_true")
    check.add_argument("--config", type=Path, default=None, help="path to a pyproject.toml")

    sub.add_parser("rules", help="list the rule catalog")
    return parser


def _config(path: Path | None) -> Config:
    """Load the config named by --config, else ./pyproject.toml, else the defaults.

    A broken ./pyproject.toml is an error, not a reason to fall back to the defaults:
    falling back would quietly run checks that differ from the ones the project wrote.
    """
    if path is not None:
        return Config.from_pyproject(path)
    default = Path("pyproject.toml")
    if default.exists():
        return Config.from_pyproject(default)
    return Config()


def _cmd_rules() -> int:
    from xpslint.rules import all_rules

    current: int | None = None
    for rule in all_rules():
        if rule.tier.value != current:
            current = rule.tier.value
            heading = {
                1: "Tier 1  derivable physics (unconditional, cannot be downgraded)",
                2: "Tier 2  instrument-specific (cannot-check without declared metadata)",
                3: "Tier 3  convention (prompts for a declaration, never fails)",
            }[current]
            print(f"\n{heading}\n")
        requires = f"  requires: {', '.join(sorted(rule.requires))}" if rule.requires else ""
        print(f"  {rule.code}  {rule.summary}{requires}")
    print()
    return 0


def _cmd_check(args: argparse.Namespace) -> int:
    try:
        cfg = _config(args.config)
    except ConfigError as exc:
        print(f"xpslint: configuration error: {exc}", file=sys.stderr)
        return 2

    status = 0
    for path in args.paths:
        try:
            fit = load(path)
        except (OSError, FitFormatError, ValueError) as exc:
            print(f"xpslint: {path}: {exc}", file=sys.stderr)
            status = max(status, 2)
            continue

        try:
            report = run(fit, cfg)
        except ConfigError as exc:
            print(f"xpslint: configuration error: {exc}", file=sys.stderr)
            return 2

        if args.format == "json":
            print(render_json(report))
        else:
            color = False if args.no_color else None
            print(render_text(report, show_all=args.show_all, color=color))
            print()

        status = max(
            status,
            report.exit_code(strict=args.strict, min_coverage=args.min_coverage),
        )
    return status


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "rules":
        return _cmd_rules()
    return _cmd_check(args)


if __name__ == "__main__":
    raise SystemExit(main())
