from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from repo_scout.models import Repository


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"updated_at": None, "repositories": {}}
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise ValueError(f"Không đọc được state tại {path}: {exc}") from exc
    if not isinstance(state, dict) or not isinstance(state.get("repositories", {}), dict):
        raise ValueError(f"State tại {path} không hợp lệ")
    state.setdefault("updated_at", None)
    state.setdefault("repositories", {})
    return state


def previous_snapshot(state: dict[str, Any], full_name: str) -> dict[str, Any] | None:
    value = state.get("repositories", {}).get(full_name)
    return value if isinstance(value, dict) else None


def update_state(state: dict[str, Any], repositories: list[Repository], now: datetime) -> None:
    store = state.setdefault("repositories", {})
    now_text = now.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    for repository in repositories:
        previous = store.get(repository.full_name, {})
        first_seen = previous.get("first_seen_at", now_text) if isinstance(previous, dict) else now_text
        store[repository.full_name] = {
            "first_seen_at": first_seen,
            "last_seen_at": now_text,
            "stars": repository.stars,
            "forks": repository.forks,
            "pushed_at": repository.pushed_at,
        }
    state["updated_at"] = now_text


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)

