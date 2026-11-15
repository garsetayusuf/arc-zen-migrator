"""Feature gates: never claim reverse Arc sidebar writes are safe without tests."""
from enum import Enum
class Status(str, Enum):
    VERIFIED = "verified"
    EXPERIMENTAL = "experimental"
    PARTIAL = "partial"
    EXPORT_ONLY = "export-only"
    UNSUPPORTED = "unsupported"
    BLOCKED = "blocked"

ZEN_TO_ARC = {
    "spaces": Status.BLOCKED,
    "tabs": Status.BLOCKED,
    "pinned_tabs": Status.BLOCKED,
    "essentials": Status.BLOCKED,
    "folders": Status.BLOCKED,
    "groups": Status.BLOCKED,
    "profiles": Status.BLOCKED,
    "cookies": Status.BLOCKED,
    "passwords": Status.BLOCKED,
    "local_storage": Status.BLOCKED,
    "bookmarks": Status.EXPERIMENTAL,
    "history": Status.EXPERIMENTAL,
    "extensions": Status.UNSUPPORTED,
}
def require_verified(feature: str):
    status = ZEN_TO_ARC.get(feature, Status.UNSUPPORTED)
    if status is not Status.VERIFIED:
        raise RuntimeError(f"{feature}: {status.value}; direct Arc import is disabled")
