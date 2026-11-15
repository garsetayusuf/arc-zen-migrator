"""Persistent checksummed backups; explicit restoration only."""
from __future__ import annotations
import hashlib
import json
import os
import shutil
import tempfile
import uuid
from pathlib import Path

def checksum(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def create_backup(source: Path, backup_root: Path) -> Path:
    source = Path(source).expanduser()
    if source.is_symlink() or not source.is_file():
        raise ValueError("Source must be a regular file, not a symlink")
    source = source.resolve(strict=True)
    backup_root = Path(backup_root).expanduser().resolve()
    if backup_root == source.parent or backup_root in source.parents or source.parent in backup_root.parents:
        raise ValueError("Backup must be outside source directory")
    backup_root.mkdir(parents=True, exist_ok=True)
    folder = backup_root / ("backup-" + uuid.uuid4().hex)
    folder.mkdir(mode=0o700)
    try:
        target = folder / "payload.bin"
        shutil.copy2(source, target, follow_symlinks=False)
        sha = checksum(source)
        if checksum(target) != sha:
            raise RuntimeError("Source changed during backup")
        manifest = {"format": 1, "original": str(source),
                    "sha256": sha, "size": target.stat().st_size}
        (folder / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return folder
    except BaseException:
        shutil.rmtree(folder)
        raise

def verify_backup(folder: Path) -> dict:
    folder = Path(folder).expanduser().resolve(strict=True)
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    payload = folder / "payload.bin"
    if manifest.get("format") != 1 or payload.is_symlink() or not payload.is_file():
        raise ValueError("Invalid backup")
    if payload.stat().st_size != manifest["size"] or checksum(payload) != manifest["sha256"]:
        raise ValueError("Backup checksum mismatch")
    return manifest

def restore_backup(folder: Path, destination: Path, *, expected_sha256: str | None = None) -> None:
    """Restore to explicitly chosen destination; caller must close browser first."""
    manifest = verify_backup(folder)
    destination = Path(destination).expanduser()
    if destination.is_symlink():
        raise ValueError("Refusing symlink destination")
    if destination.exists():
        if expected_sha256 is None or checksum(destination) != expected_sha256:
            raise ValueError("Existing destination requires matching current checksum")
    elif expected_sha256 is not None:
        raise ValueError("Destination is missing")
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".arc-zen-restore-", dir=destination.parent)
    try:
        with os.fdopen(fd, "wb") as output, (Path(folder) / "payload.bin").open("rb") as source:
            shutil.copyfileobj(source, output)
            output.flush()
            os.fsync(output.fileno())
        if checksum(Path(name)) != manifest["sha256"]:
            raise ValueError("Restore verification failed")
        os.replace(name, destination)
    finally:
        if os.path.exists(name):
            os.unlink(name)
