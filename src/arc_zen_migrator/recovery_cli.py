"""Explicit backup and restore commands for advanced users.

Never restores to a path from a manifest automatically.
"""
from __future__ import annotations
import argparse
from pathlib import Path
from .recovery import create_backup, restore_backup, verify_backup
from .browser_guard import require_browsers_closed

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Arc ↔ Zen backup and recovery")
    sub = parser.add_subparsers(dest="action", required=True)
    backup = sub.add_parser("backup", help="Copy a single regular file into persistent backup storage")
    backup.add_argument("source", type=Path)
    backup.add_argument("--directory", required=True, type=Path)
    verify = sub.add_parser("verify", help="Verify an existing backup's SHA-256 checksum")
    verify.add_argument("backup", type=Path)
    restore = sub.add_parser("restore", help="Restore to an explicitly selected destination")
    restore.add_argument("backup", type=Path)
    restore.add_argument("--destination", required=True, type=Path)
    restore.add_argument("--expected-sha256", help="Current destination checksum; required for overwrite")
    args = parser.parse_args(argv)
    if args.action == "backup":
        require_browsers_closed()
        result = create_backup(args.source, args.directory)
        print("Backup created:", result)
    elif args.action == "verify":
        result = verify_backup(args.backup)
        print("Verified SHA-256:", result["sha256"])
    else:
        require_browsers_closed()
        restore_backup(args.backup, args.destination, expected_sha256=args.expected_sha256)
        print("Restored successfully")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
