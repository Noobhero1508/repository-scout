from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any

from repo_scout.config import Job
from repo_scout.models import RankedRepository, Repository


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def _parse_github_time(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _age_days(value: str, now: datetime) -> float:
    timestamp = _parse_github_time(value)
    if timestamp is None:
        return 3650.0
    return max(0.0, (now - timestamp).total_seconds() / 86400)


def _relevance(repository: Repository, job: Job) -> tuple[float, list[str]]:
    searchable = " ".join(
        [repository.full_name, repository.description, " ".join(repository.topics)]
    ).lower()
    matched = [keyword for keyword in job.keywords if keyword in searchable]
    if job.keywords:
        keyword_score = len(matched) / len(job.keywords) * 100
    else:
        keyword_score = 60.0

    preferred = {language.lower() for language in job.preferred_languages}
    language_match = bool(repository.language and repository.language.lower() in preferred)
    score = keyword_score * 0.8 + (20.0 if language_match else 0.0)
    if not job.preferred_languages:
        score += 20.0

    reasons: list[str] = []
    if matched:
        reasons.append("khớp: " + ", ".join(matched[:3]))
    if language_match:
        reasons.append(f"ngôn ngữ {repository.language}")
    return _clamp(score), reasons


def _momentum(
    repository: Repository,
    previous: dict[str, Any] | None,
    now: datetime,
) -> tuple[float, int | None, str]:
    if previous and isinstance(previous.get("stars"), int):
        delta = max(0, repository.stars - int(previous["stars"]))
        seen_at = _parse_github_time(str(previous.get("last_seen_at", "")))
        elapsed_days = max(1.0, (now - seen_at).total_seconds() / 86400) if seen_at else 1.0
        stars_per_day = delta / elapsed_days
        score = _clamp(math.log1p(stars_per_day) / math.log1p(100) * 100)
        return score, delta, f"+{delta} sao từ lần quét trước"

    age_days = max(1.0, _age_days(repository.created_at, now))
    stars_per_day = repository.stars / age_days
    score = _clamp(math.log1p(stars_per_day) / math.log1p(100) * 100)
    return score, None, f"~{stars_per_day:.1f} sao/ngày từ khi tạo"


def rank_repository(
    repository: Repository,
    job: Job,
    previous: dict[str, Any] | None,
    now: datetime | None = None,
) -> RankedRepository:
    now = now or datetime.now(timezone.utc)
    relevance, reasons = _relevance(repository, job)
    momentum, star_delta, momentum_reason = _momentum(repository, previous, now)

    push_age = _age_days(repository.pushed_at, now)
    creation_age = _age_days(repository.created_at, now)
    activity = _clamp(100 * math.exp(-push_age / 120))
    freshness = _clamp(100 * math.exp(-creation_age / 365))
    popularity = _clamp(math.log1p(repository.stars) / math.log1p(5000) * 100)

    trust = 45.0
    if repository.license_name not in {"", "Unknown", "NOASSERTION"}:
        trust += 35.0
    if repository.description:
        trust += 10.0
    if repository.topics:
        trust += 10.0
    if repository.archived:
        trust = 0.0
    elif repository.fork:
        trust *= 0.5

    components = {
        "relevance": round(relevance, 1),
        "momentum": round(momentum, 1),
        "activity": round(activity, 1),
        "popularity": round(popularity, 1),
        "freshness": round(freshness, 1),
        "trust": round(_clamp(trust), 1),
    }
    score = (
        relevance * 0.35
        + momentum * 0.20
        + activity * 0.15
        + popularity * 0.15
        + freshness * 0.10
        + trust * 0.05
    )

    reasons.append(momentum_reason)
    if push_age <= 7:
        reasons.append("cập nhật trong 7 ngày")
    elif push_age <= 30:
        reasons.append("cập nhật trong 30 ngày")
    if repository.license_name not in {"", "Unknown", "NOASSERTION"}:
        reasons.append(f"license {repository.license_name}")

    return RankedRepository(
        repository=repository,
        score=round(score, 1),
        components=components,
        reasons=tuple(reasons),
        star_delta=star_delta,
    )

