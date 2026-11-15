"""Zen → Arc preview, selective planning and isolated bookmark test import."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from .reader import inspect_zen
from .planner import plan_zen_to_arc
from .bookmarks import import_bookmarks
from .report import summary

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Zen → Arc preview and isolated testing")
    parser.add_argument("--zen-profile", required=True, type=Path)
    parser.add_argument("--space", action="append", default=None,
                        help="Select Zen Space ID; repeat for multiple Spaces")
    parser.add_argument("--preview", action="store_true", help="Print privacy-safe summary")
    parser.add_argument("--test-bookmarks-profile", type=Path,
                        help="Isolated test copy with marker and existing Bookmarks file")
    parser.add_argument("--backup-dir", type=Path)
    parser.add_argument("--confirm-isolated", action="store_true")
    args = parser.parse_args(argv)
    inventory = inspect_zen(args.zen_profile)
    plan = plan_zen_to_arc(inventory, selected_spaces=set(args.space) if args.space is not None else None)
    report = summary(inventory)
    report["plan"] = {"unique_tabs": len(plan.tabs), "duplicates": plan.duplicate_count,
                      "excluded": plan.excluded_count, "status": plan.status}
    if args.test_bookmarks_profile:
        if args.backup_dir is None:
            parser.error("--backup-dir required for isolated test import")
        result = import_bookmarks(plan, args.test_bookmarks_profile, args.backup_dir,
                                  confirm_isolated=args.confirm_isolated)
        # Do not emit paths from backups or private profile locations.
        report["test_import"] = {"imported": result["imported"], "skipped": result["skipped"],
                                 "mode": result["mode"]}
    elif args.backup_dir or args.confirm_isolated:
        parser.error("Backup/confirmation options require --test-bookmarks-profile")
    print(json.dumps(report, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
