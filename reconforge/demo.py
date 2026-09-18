"""Run with python3 -m reconforge.demo from the project root."""

import argparse
import json
from pathlib import Path

from . import __version__
from .money import format_eur
from .reconciliation import InputError, reconcile


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the offline ReconForge financial example.")
    parser.add_argument("--data-dir", type=Path, default=Path(__file__).resolve().parents[1] / "examples" / "invoice_deduction")
    parser.add_argument("--json", action="store_true", help="Print the complete machine-readable result.")
    args = parser.parse_args()
    try:
        result = reconcile(args.data_dir)
    except InputError as exc:
        parser.exit(2, f"Input error: {exc}\n")
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return

    print(f"ReconForge {__version__} — deterministic synthetic example")
    print("No model calls, MCP services or financial actions are used.\n")
    for source, amount in result["totals_minor"].items():
        print(f"{source.capitalize():<12} {format_eur(amount)}")
    print()
    for name, comparison in result["comparisons"].items():
        print(f"{name}: {format_eur(comparison['residual_minor'])} ({comparison['status']})")
    for finding in result["event_differences"]:
        print(f"\nFinding: {finding['kind']} — {finding['event_id']}")
        for source in ("ledger_source", "provider_source"):
            ref = finding[source]
            if ref:
                print(f"  {ref['file']}, data record {ref['record_number']}, SHA-256 {ref['sha256'][:12]}…")
    print(f"\nReview required: {result['review_required']}")
    print("External reporting completeness has not been verified.")


if __name__ == "__main__":
    main()
