"""Portable Netscape bookmarks export for manual import into Arc/Chromium.

The HTML file contains browsing URLs and titles. Store it privately and delete
it when no longer needed. No Arc profile files are accessed.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from urllib.parse import urlsplit

from .planner import MigrationPlan

def _folder(label: str, items: list[str]) -> list[str]:
    return ["<DT><H3>" + escape(label, quote=True) + "</H3>",
            "<DL><p>", *items, "</DL><p>"]

def render_bookmarks(plan: MigrationPlan, *, space_names: dict[str, str] | None = None) -> str:
    """Produce portable HTML; group by Space, status, and folder."""
    names = space_names or {}
    grouped: dict[str, dict[str, dict[str, list[str]]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(list)))
    for tab in plan.tabs:
        if urlsplit(tab.url).scheme.lower() not in {"http", "https"}:
            continue
        space = names.get(tab.source_space, tab.source_space or "Unassigned")
        status = "Essentials" if tab.essential else "Pinned" if tab.pinned else "Regular"
        folder = tab.folder or "No folder"
        grouped[space][status][folder].append(
            '<DT><A HREF="' + escape(tab.url, quote=True) + '">' +
            escape(tab.title, quote=True) + "</A>")
    lines = ['<!DOCTYPE NETSCAPE-Bookmark-file-1>',
             '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">',
             '<TITLE>Zen Migrator bookmarks</TITLE>', '<H1>Zen Migrator bookmarks</H1>',
             '<DL><p>']
    for space, statuses in grouped.items():
        status_items = []
        for status, folders in statuses.items():
            status_items.extend(_folder(status, [
                line for folder, links in folders.items()
                for line in _folder(folder, links)]))
        lines.extend(_folder(space, status_items))
    lines.append("</DL><p>")
    return "\n".join(lines) + "\n"

def export_bookmarks(plan: MigrationPlan, destination: Path, *,
                     space_names: dict[str, str] | None = None) -> Path:
    destination = Path(destination).expanduser()
    if destination.is_symlink() or destination.exists():
        raise FileExistsError("Export destination already exists; refusing overwrite")
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive create prevents clobbering a file created between validation and write.
    with destination.open("x", encoding="utf-8") as output:
        output.write(render_bookmarks(plan, space_names=space_names))
    return destination
