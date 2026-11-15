"""Read-only Zen session inventory. Never writes to the source profile."""
from __future__ import annotations
import json
import struct
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

MAX_JSON = 256 * 1024 * 1024

@dataclass
class Space:
    id: str
    name: str
    tabs: list[dict] = field(default_factory=list)
    folders: list[dict] = field(default_factory=list)

@dataclass
class Inventory:
    spaces: list[Space]
    orphan_tabs: list[dict]
    warnings: list[str]
    groups: int = 0

    @property
    def tab_count(self):
        return sum(len(space.tabs) for space in self.spaces) + len(self.orphan_tabs)

    @property
    def pinned_count(self):
        return sum(bool(t["pinned"]) for s in self.spaces for t in s.tabs) + sum(bool(t["pinned"]) for t in self.orphan_tabs)

    @property
    def essential_count(self):
        return sum(bool(t["essential"]) for s in self.spaces for t in s.tabs) + sum(bool(t["essential"]) for t in self.orphan_tabs)

def read_mozlz4(path: Path) -> dict:
    import lz4.block
    with path.open("rb") as stream:
        if stream.read(8) != b"mozLz40\x00":
            raise ValueError("Invalid Mozilla LZ4 header")
        raw_size = stream.read(4)
        if len(raw_size) != 4:
            raise ValueError("Truncated session header")
        size = struct.unpack("<I", raw_size)[0]
        if size < 1 or size > MAX_JSON:
            raise ValueError("Session exceeds size limit")
        data = lz4.block.decompress(stream.read(), uncompressed_size=size)
    if len(data) != size:
        raise ValueError("Session length mismatch")
    result = json.loads(data)
    if not isinstance(result, dict):
        raise ValueError("Expected JSON object")
    return result

def inspect_zen(profile: Path) -> Inventory:
    profile = Path(profile).expanduser().resolve(strict=True)
    primary = profile / "zen-sessions.jsonlz4"
    data = read_mozlz4(primary)
    candidates = [profile / "sessionstore-backups" / "recovery.jsonlz4",
                  profile / "sessionstore-backups" / "recovery.baklz4",
                  profile / "sessionstore.jsonlz4"]
    # Do not combine live sessions with stale recovery snapshots: that silently
    # resurrects closed tabs and creates misleading migration plans.
    # Recovery is a fallback only if the primary session contains no windows/tabs.
    docs = [data]
    warnings = []
    if not data.get("windows") and not data.get("tabs"):
        for candidate in candidates:
            if not candidate.is_file():
                continue
            try:
                recovered = read_mozlz4(candidate)
            except (ValueError, OSError, json.JSONDecodeError):
                warnings.append("An optional session file could not be read")
                continue
            if recovered.get("windows") or recovered.get("tabs"):
                docs = [recovered]
                warnings.append("Using recovery session because primary session is empty")
                break
    def windows(doc):
        return doc.get("windows", []) if "windows" in doc else [doc]
    raw_spaces = []
    for doc in docs:
        for window in windows(doc):
            if window.get("spaces"):
                raw_spaces = window["spaces"]
                break
        if raw_spaces:
            break
    spaces = [Space(str(s.get("uuid") or s.get("id") or i), str(s.get("name") or "Unnamed Space"))
              for i, s in enumerate(raw_spaces) if isinstance(s, dict)]
    by_id = {s.id: s for s in spaces}
    folders = {}
    groups = set()
    for doc in docs:
        for window in windows(doc):
            for folder in window.get("folders", []):
                if isinstance(folder, dict) and folder.get("id"):
                    folders[str(folder["id"])] = folder
            for group in window.get("groups", []):
                if isinstance(group, dict) and group.get("id"):
                    groups.add(str(group["id"]))
    for folder in folders.values():
        space = by_id.get(str(folder.get("workspaceId") or ""))
        if space:
            space.folders.append({"id": str(folder["id"]), "name": str(folder.get("name") or ""),
                                  "parentId": folder.get("parentId")})
        else:
            warnings.append("Folder without a matching workspace")
    seen = set()
    orphans = []
    for doc in docs:
        for window in windows(doc):
            for tab in window.get("tabs", []):
                if not isinstance(tab, dict) or tab.get("zenIsEmpty"):
                    continue
                entries = tab.get("entries") or []
                if not isinstance(entries, list) or not entries:
                    continue
                index = tab.get("index")
                entry = entries[index - 1] if isinstance(index, int) and 0 < index <= len(entries) else entries[-1]
                if not isinstance(entry, dict):
                    continue
                url = str(entry.get("url") or "")
                if urlsplit(url).scheme.lower() not in {"http", "https", "about"}:
                    warnings.append("Unsupported or invalid tab URL skipped")
                    continue
                workspace = str(tab.get("zenWorkspace") or "")
                key = str(tab.get("zenSyncId") or "") or (workspace, url, str(tab.get("groupId")), str(tab.get("pinned")))
                if key in seen:
                    continue
                seen.add(key)
                item = {"url": url, "title": str(entry.get("title") or url),
                        "pinned": bool(tab.get("pinned")), "essential": bool(tab.get("zenEssential")),
                        "folder": str(tab.get("groupId") or "") if str(tab.get("groupId") or "") in folders else None}
                if workspace in by_id:
                    by_id[workspace].tabs.append(item)
                else:
                    orphans.append(item)
    return Inventory(spaces, orphans, warnings, len(groups))
