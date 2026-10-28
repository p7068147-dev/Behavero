import json
from pathlib import Path
from typing import Any

def load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).expanduser().open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return value

def save_json(value: dict[str, Any], path: str | Path) -> None:
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_suffix(target.suffix + ".tmp")
    with temp.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
    temp.replace(target)
