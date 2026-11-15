"""Conservative Zen → Arc bookmark import into an explicitly isolated test copy.

This writes only Chromium's Bookmarks JSON, NOT Arc's CloudKit sidebar.
Never pass a live Arc profile. Caller must create a disposable copy and place
.arc-zen-isolated-test-profile marker in that copy's root.
"""
from __future__ import annotations
import json
import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from arc_zen_migrator.recovery import create_backup
from arc_zen_migrator.browser_guard import require_browsers_closed
from .planner import MigrationPlan

MARKER = ".arc-zen-isolated-test-profile"
BOOKMARKS = "Bookmarks"

def _safe_url(url: str) -> bool:
    return urlsplit(url).scheme.lower() in {"https", "http"}

def _walk(node: dict):
    if node.get("type") == "url":
        yield node
    for child in node.get("children", []):
        if isinstance(child, dict):
            yield from _walk(child)

def import_bookmarks(plan: MigrationPlan, destination: Path, backup_root: Path, *,
                     confirm_isolated: bool = False) -> dict:
    if not confirm_isolated:
        raise PermissionError("Explicit isolated test-profile confirmation required")
    require_browsers_closed()
    destination = Path(destination).expanduser()
    if destination.is_symlink() or not destination.is_dir():
        raise ValueError("Destination must be an existing non-symlink test profile")
    destination = destination.resolve(strict=True)
    if not (destination / MARKER).is_file():
        raise PermissionError("Missing isolated test-profile marker")
    bookmark_file = destination / BOOKMARKS
    if bookmark_file.is_symlink() or not bookmark_file.is_file():
        raise ValueError("Existing regular Chromium Bookmarks file required")
    backup_root = Path(backup_root).expanduser().resolve()
    if backup_root == destination or destination in backup_root.parents or backup_root in destination.parents:
        raise ValueError("Backup directory must be outside test profile")
    original = bookmark_file.read_bytes()
    data = json.loads(original)
    roots = data.get("roots")
    if not isinstance(roots, dict) or not isinstance(roots.get("other"), dict):
        raise ValueError("Unsupported Chromium bookmark structure")
    other = roots["other"]
    if not isinstance(other.get("children"), list):
        raise ValueError("Unsupported bookmark children")
    existing = {node.get("url") for root in roots.values() if isinstance(root, dict)
                for node in _walk(root)}
    imported = []
    seen = set(existing)
    for tab in plan.tabs:
        if not _safe_url(tab.url) or tab.url in seen:
            continue
        seen.add(tab.url)
        imported.append(tab)
    if not imported:
        return {"imported": 0, "skipped": len(plan.tabs), "backup": None}
    backup = create_backup(bookmark_file, backup_root)
    # A single dedicated folder is intentionally used: Arc sidebar/Spaces are
    # not equivalent to Chromium bookmarks and must not be misrepresented.
    stamp = str(int(datetime.now(timezone.utc).timestamp() * 1_000_000))
    folder = {"type": "folder", "name": "Zen Migrator (test import)",
              "guid": str(uuid.uuid4()), "id": stamp, "date_added": stamp,
              "date_modified": stamp, "children": []}
    for index, tab in enumerate(imported, 1):
        folder["children"].append({"type": "url", "name": tab.title,
                                   "url": tab.url, "guid": str(uuid.uuid4()),
                                   "id": str(int(stamp) + index), "date_added": stamp})
    other["children"].append(folder)
    fd, temp = tempfile.mkstemp(prefix=".arc-zen-bookmarks-", dir=destination)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as output:
            json.dump(data, output, ensure_ascii=False, indent=2)
            output.flush()
            os.fsync(output.fileno())
        # Refuse to replace the file if it changed after backup.
        if bookmark_file.read_bytes() != original:
            raise RuntimeError("Bookmarks changed during import; backup retained")
        os.replace(temp, bookmark_file)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)
    return {"imported": len(imported), "skipped": len(plan.tabs) - len(imported),
            "backup": str(backup), "mode": "isolated-test-only"}
