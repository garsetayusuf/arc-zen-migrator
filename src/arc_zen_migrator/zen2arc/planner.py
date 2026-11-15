"""Deterministic, read-only migration plan for Zen → Arc.

No Arc profile files are opened or modified by this module.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from urllib.parse import urlsplit

from .reader import Inventory

@dataclass(frozen=True)
class PlannedTab:
    source_space: str
    url: str
    title: str
    pinned: bool
    essential: bool
    folder: str | None
    fingerprint: str

@dataclass(frozen=True)
class MigrationPlan:
    tabs: tuple[PlannedTab, ...]
    duplicate_count: int
    excluded_count: int
    status: str = "preview-only"

def _fingerprint(space: str, url: str, folder: str | None, pinned: bool, essential: bool) -> str:
    raw = "\x00".join((space, url, folder or "", str(pinned), str(essential)))
    return sha256(raw.encode("utf-8")).hexdigest()

def plan_zen_to_arc(inventory: Inventory, *, selected_spaces: set[str] | None = None) -> MigrationPlan:
    """Build a stable plan; selected_spaces=None means all spaces plus orphans.

    Empty selected_spaces means none. Deduplication is scoped to space, URL,
    folder and pinned/essential status. Fingerprints are for comparisons only.
    """
    planned = []
    seen = set()
    duplicates = 0
    excluded = 0
    sources = [(space.id, space.tabs) for space in inventory.spaces]
    sources.append(("", inventory.orphan_tabs))
    for space_id, tabs in sources:
        if selected_spaces is not None and space_id not in selected_spaces:
            excluded += len(tabs)
            continue
        for tab in tabs:
            url = tab["url"]
            if urlsplit(url).scheme not in {"http", "https", "about"}:
                excluded += 1
                continue
            pinned = bool(tab.get("pinned"))
            essential = bool(tab.get("essential"))
            folder = tab.get("folder")
            key = _fingerprint(space_id, url, folder, pinned, essential)
            if key in seen:
                duplicates += 1
                continue
            seen.add(key)
            planned.append(PlannedTab(space_id, url, tab.get("title") or url,
                                      pinned, essential, folder, key))
    return MigrationPlan(tuple(planned), duplicates, excluded)
