from __future__ import annotations
import hashlib
import os
import platform
import stat
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def _record(path: Path, root: Path) -> dict[str, Any]:
    info = path.lstat()
    item = {
        "path": path.relative_to(root).as_posix(),
        "kind": ("symlink" if stat.S_ISLNK(info.st_mode) else
                 "file" if stat.S_ISREG(info.st_mode) else
                 "directory" if stat.S_ISDIR(info.st_mode) else "other"),
        "size": info.st_size,
        "mtime_ns": info.st_mtime_ns,
        "mode": stat.S_IMODE(info.st_mode),
    }
    if stat.S_ISREG(info.st_mode):
        item["sha256"] = sha256_file(path)
    elif stat.S_ISLNK(info.st_mode):
        item["symlink_target"] = os.readlink(path)
    return item

def snapshot_tree(directory: str | Path) -> dict[str, Any]:
    root = Path(directory).expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(f"Directory does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Not a directory: {root}")
    entries: dict[str, dict[str, Any]] = {}
    for current, dirs, filenames in os.walk(root, followlinks=False):
        current_path = Path(current)
        kept = []
        for name in sorted(dirs):
            child = current_path / name
            entries[child.relative_to(root).as_posix()] = _record(child, root)
            if not child.is_symlink():
                kept.append(name)
        dirs[:] = kept
        for name in sorted(filenames):
            child = current_path / name
            rel = child.relative_to(root).as_posix()
            try:
                entries[rel] = _record(child, root)
            except (OSError, PermissionError) as exc:
                entries[rel] = {"path": rel, "kind": "unreadable", "error": type(exc).__name__}
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at": utc_now(),
        "root": str(root),
        "platform": platform.platform(),
        "entries": dict(sorted(entries.items())),
        "limitations": [
            "Snapshots are point-in-time observations; concurrent changes can be missed.",
            "Symlinks are recorded but not followed.",
            "Changes outside the monitored directory are not observed.",
        ],
    }

def compare_snapshots(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    if before.get("schema_version") != SCHEMA_VERSION or after.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Unsupported snapshot schema version")
    old, new = before.get("entries"), after.get("entries")
    if not isinstance(old, dict) or not isinstance(new, dict):
        raise ValueError("Snapshot is missing a valid entries mapping")
    old_paths, new_paths = set(old), set(new)
    created, deleted, modified = [], [], []
    keys = ("kind", "size", "mode", "sha256", "symlink_target", "error")
    for path in sorted(new_paths - old_paths):
        created.append({"path": path, "evidence": new[path]})
    for path in sorted(old_paths - new_paths):
        deleted.append({"path": path, "evidence": old[path]})
    for path in sorted(old_paths & new_paths):
        changed = [key for key in keys if old[path].get(key) != new[path].get(key)]
        if changed:
            modified.append({"path": path, "changed_fields": changed,
                             "before": old[path], "after": new[path]})
    return {
        "schema_version": SCHEMA_VERSION, "tool": "Behavero", "created_at": utc_now(),
        "baseline_created_at": before.get("created_at"), "after_created_at": after.get("created_at"),
        "root_before": before.get("root"), "root_after": after.get("root"),
        "summary": {"created": len(created), "deleted": len(deleted), "modified": len(modified),
                    "unchanged": len(old_paths & new_paths) - len(modified),
                    "total_paths_compared": len(old_paths | new_paths)},
        "created": created, "deleted": deleted, "modified": modified,
        "limitations": [
            "Differences are observations, not proof of malicious behavior.",
            "Timestamp-only changes are not currently counted as modifications.",
            "Changes outside the monitored directory and concurrent changes may be missed.",
        ],
    }

def run_command(command: list[str], cwd: str | Path, timeout: float) -> dict[str, Any]:
    import subprocess
    if not command:
        raise ValueError("Provide a command after '--'")
    workdir = Path(cwd).expanduser().resolve()
    if not workdir.is_dir():
        raise NotADirectoryError(f"Working directory does not exist: {workdir}")
    started = utc_now()
    start = time.monotonic()
    try:
        result = subprocess.run(command, cwd=workdir, shell=False, check=False, timeout=timeout)
        return {"command": command, "cwd": str(workdir), "started_at": started,
                "duration_seconds": round(time.monotonic() - start, 6),
                "exit_code": result.returncode, "timed_out": False,
                "output_capture": "stdout/stderr inherited from terminal; not stored"}
    except subprocess.TimeoutExpired:
        return {"command": command, "cwd": str(workdir), "started_at": started,
                "duration_seconds": round(time.monotonic() - start, 6),
                "exit_code": None, "timed_out": True, "timeout_seconds": timeout,
                "output_capture": "stdout/stderr inherited from terminal; not stored"}
