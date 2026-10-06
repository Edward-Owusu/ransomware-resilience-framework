"""Command-line interface.

Examples:
    ransomware-check samples/riverbend_components_systems.csv --practices samples/riverbend_components_practices.json
    ransomware-check systems.csv --practices practices.json --format html md --fail-below 60
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from . import __version__
from .engine import DataError, assess, load_model, load_practices, load_systems
from .reporting import WRITERS


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="ransomware-check", description="Assess ransomware recovery readiness.")
    p.add_argument("systems", help="Path to the systems inventory CSV")
    p.add_argument("--practices", help="Path to the organization-wide practices JSON")
    p.add_argument("--org", help="Organization name (overrides the practices file)")
    p.add_argument("--as-of", help="Date to measure restore test age against (YYYY-MM-DD, default: today)")
    p.add_argument("--format", nargs="+", choices=sorted(WRITERS), default=["html", "csv"])
    p.add_argument("--out", default="reports", help="Output directory (default: reports)")
    p.add_argument("--model", help="JSON file overriding the scoring model")
    p.add_argument("--fail-below", type=float, help="Exit with code 2 if readiness is below this score")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        systems = load_systems(args.systems)
        practices = load_practices(args.practices) if args.practices else None
        model = load_model(args.model)
        as_of = date.fromisoformat(args.as_of) if args.as_of else None
        r = assess(systems, practices, args.org, model, as_of)
    except (OSError, DataError, ValueError) as exc:
        print(f"Could not read input: {exc}", file=sys.stderr)
        return 1
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    stem = Path(args.systems).stem
    for fmt in args.format:
        path = out / f"{stem}.{fmt}"
        path.write_text(WRITERS[fmt](r), encoding="utf-8")
        print(f"Wrote {path}")
    c = r.counts()
    print(f"\n{r.organization} | {c['systems']} systems | as of {r.as_of}")
    print(f"Readiness: {r.readiness:.0f}/100 ({r.band}) | systems {r.system_score:.0f}, practices {r.practice_score:.0f}")
    print(f"Miss downtime target: {c['miss_rto']} | No safe backup copy: {c['no_safe_copy']} | Untested restores: {c['untested']}")
    for s in r.systems:
        rec = "cannot recover" if s.effective_recovery_hours is None else f"{s.effective_recovery_hours:g} h"
        print(f"  {s.system:<28} {s.criticality:<9} recovery {rec:<15} target {s.rto_hours:g} h")
    if args.fail_below is not None and r.readiness < args.fail_below:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
