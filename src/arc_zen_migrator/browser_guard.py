"""Browser process guard for potentially destructive recovery operations."""
from __future__ import annotations

def running_browsers() -> list[str]:
    """Return active Arc/Zen browser executable names, excluding helper tools."""
    try:
        import psutil
    except ImportError as exc:
        raise RuntimeError("psutil is required to check running browsers") from exc
    active = set()
    for process in psutil.process_iter(["name", "exe"]):
        try:
            name = (process.info.get("name") or "").lower()
            executable = (process.info.get("exe") or "").lower().replace("\\", "/")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
        if name in {"arc", "arc.exe"} or "/arc.app/contents/macos/arc" in executable:
            active.add("Arc")
        if name in {"zen", "zen.exe"} or "/zen.app/contents/macos/zen" in executable:
            active.add("Zen")
    return sorted(active)

def require_browsers_closed() -> None:
    active = running_browsers()
    if active:
        raise RuntimeError("Close these browsers before modifying profile files: " + ", ".join(active))
