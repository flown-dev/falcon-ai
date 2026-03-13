#!/usr/bin/env python3
"""Invoice Collector — collects, renames, and files tech invoices."""

import argparse
import sys
from datetime import datetime
from pathlib import Path

from config import OUTPUT_DIR


def print_summary(results: dict, mode: str, dry_run: bool):
    """Print the summary report."""
    today = datetime.now().strftime("%Y-%m-%d")
    prefix = "[DRY RUN] " if dry_run else ""

    print(f"\n{prefix}Invoice Collector — {today}")
    print("=" * 40)
    print(f"\nProcessed: {len(results['processed'])}")
    print(f"Skipped:   {len(results['skipped'])}")
    print(f"Errors:    {len(results['errors'])}")

    if results["processed"]:
        print()
        for filename, vendor in results["processed"]:
            print(f"+ {filename:<40} -> {vendor}/")

    if results["skipped"]:
        print()
        for filename, reason in results["skipped"]:
            print(f"= {filename:<40} -> {reason}")

    if results["errors"]:
        print()
        for source, reason in results["errors"]:
            print(f"x {source:<40} -> {reason}")

    # New senders (Gmail mode only)
    new_senders = results.get("new_senders", [])
    if new_senders:
        print("\nNew senders (not in vendor list):")
        for sender, subject in new_senders:
            print(f'  - {sender} — "{subject}"')


def main():
    parser = argparse.ArgumentParser(description="Invoice Collector")
    parser.add_argument("mode", nargs="?", default="gmail", choices=["gmail", "inbox"],
                        help="Processing mode (default: gmail)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview changes without writing files")
    args = parser.parse_args()

    if args.mode == "gmail":
        from gmail import process_gmail
        output_dir = Path(OUTPUT_DIR).expanduser()
        results = process_gmail(output_dir, dry_run=args.dry_run)
    else:
        from inbox import process_inbox
        results = process_inbox(dry_run=args.dry_run)

    print_summary(results, args.mode, args.dry_run)


if __name__ == "__main__":
    main()
