from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Settings:
    lookback_days: int = 30
    max_results_per_query: int = 50
    report_top_n: int = 15
    request_timeout_seconds: int = 30
    exclude_archived: bool = True
    exclude_forks: bool = True
    report_path: str = "reports/latest.md"
    json_report_path: str = "reports/latest.json"
    history_dir: str = "reports/history"
    state_path: str = "data/state.json"


@dataclass(frozen=True)
class Job:
    id: str
    title: str
    description: str
    queries: tuple[str, ...]
    keywords: tuple[str, ...]
    preferred_languages: tuple[str, ...]
    top_n: int | None = None


@dataclass(frozen=True)
class Config:
    settings: Settings
    jobs: tuple[Job, ...]


def _positive_int(value: Any, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValueError(f"'{field}' phải là số nguyên dương")
    return value


def load_config(path: Path) -> Config:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"Không tìm thấy cấu hình: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON cấu hình không hợp lệ: {exc}") from exc

    if not isinstance(raw, dict):
        raise ValueError("Cấu hình gốc phải là một JSON object")

    settings_raw = raw.get("settings", {})
    if not isinstance(settings_raw, dict):
        raise ValueError("'settings' phải là một JSON object")

    settings = Settings(
        lookback_days=_positive_int(settings_raw.get("lookback_days", 30), "lookback_days"),
        max_results_per_query=min(
            100,
            _positive_int(
                settings_raw.get("max_results_per_query", 50),
                "max_results_per_query",
            ),
        ),
        report_top_n=_positive_int(settings_raw.get("report_top_n", 15), "report_top_n"),
        request_timeout_seconds=_positive_int(
            settings_raw.get("request_timeout_seconds", 30),
            "request_timeout_seconds",
        ),
        exclude_archived=bool(settings_raw.get("exclude_archived", True)),
        exclude_forks=bool(settings_raw.get("exclude_forks", True)),
        report_path=str(settings_raw.get("report_path", "reports/latest.md")),
        json_report_path=str(settings_raw.get("json_report_path", "reports/latest.json")),
        history_dir=str(settings_raw.get("history_dir", "reports/history")),
        state_path=str(settings_raw.get("state_path", "data/state.json")),
    )

    jobs_raw = raw.get("jobs")
    if not isinstance(jobs_raw, list) or not jobs_raw:
        raise ValueError("'jobs' phải là một danh sách không rỗng")

    jobs: list[Job] = []
    seen_ids: set[str] = set()
    for index, item in enumerate(jobs_raw):
        if not isinstance(item, dict):
            raise ValueError(f"jobs[{index}] phải là một JSON object")
        job_id = str(item.get("id", "")).strip()
        title = str(item.get("title", "")).strip()
        queries = item.get("queries", [])
        if not job_id or not title or not isinstance(queries, list) or not queries:
            raise ValueError(f"jobs[{index}] cần có id, title và ít nhất một query")
        if job_id in seen_ids:
            raise ValueError(f"Job id bị trùng: {job_id}")
        seen_ids.add(job_id)

        top_n_raw = item.get("top_n")
        top_n = None if top_n_raw is None else _positive_int(top_n_raw, f"{job_id}.top_n")
        jobs.append(
            Job(
                id=job_id,
                title=title,
                description=str(item.get("description", "")).strip(),
                queries=tuple(str(query).strip() for query in queries if str(query).strip()),
                keywords=tuple(
                    str(keyword).strip().lower()
                    for keyword in item.get("keywords", [])
                    if str(keyword).strip()
                ),
                preferred_languages=tuple(
                    str(language).strip()
                    for language in item.get("preferred_languages", [])
                    if str(language).strip()
                ),
                top_n=top_n,
            )
        )

    return Config(settings=settings, jobs=tuple(jobs))

