"""Read-only Zen preview report without browsing-history details."""
from __future__ import annotations
import json
from pathlib import Path
from .reader import Inventory, inspect_zen

def summary(inventory: Inventory) -> dict:
    return {
        "format": 1,
        "direction": "zen-to-arc",
        "mode": "preview-only",
        "counts": {
            "spaces": len(inventory.spaces),
            "tabs": inventory.tab_count,
            "pinned": inventory.pinned_count,
            "essentials": inventory.essential_count,
            "groups": inventory.groups,
            "folders": sum(len(s.folders) for s in inventory.spaces),
            "unassigned_tabs": len(inventory.orphan_tabs),
        },
        "spaces": [{"tab_count": len(s.tabs), "folder_count": len(s.folders)}
                   for s in inventory.spaces],
        "warnings": list(inventory.warnings),
        "capability": "Arc sidebar writes are blocked pending verification",
    }

def write_report(profile: Path, destination: Path) -> dict:
    result = summary(inspect_zen(profile))
    destination = Path(destination).expanduser()
    if destination.exists():
        raise FileExistsError("Refusing to overwrite existing report")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("x", encoding="utf-8") as output:
        json.dump(result, output, indent=2)
        output.write("\n")
    return result
