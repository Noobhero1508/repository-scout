from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class Repository:
    full_name: str
    html_url: str
    description: str
    language: str
    topics: tuple[str, ...]
    stars: int
    forks: int
    open_issues: int
    created_at: str
    pushed_at: str
    updated_at: str
    license_name: str
    archived: bool
    fork: bool

    @classmethod
    def from_api(cls, item: dict[str, Any]) -> "Repository":
        license_data = item.get("license") or {}
        return cls(
            full_name=str(item.get("full_name", "")),
            html_url=str(item.get("html_url", "")),
            description=str(item.get("description") or ""),
            language=str(item.get("language") or "Unknown"),
            topics=tuple(str(topic) for topic in item.get("topics", []) or []),
            stars=int(item.get("stargazers_count", 0) or 0),
            forks=int(item.get("forks_count", 0) or 0),
            open_issues=int(item.get("open_issues_count", 0) or 0),
            created_at=str(item.get("created_at", "")),
            pushed_at=str(item.get("pushed_at", "")),
            updated_at=str(item.get("updated_at", "")),
            license_name=str(license_data.get("spdx_id") or license_data.get("name") or "Unknown"),
            archived=bool(item.get("archived", False)),
            fork=bool(item.get("fork", False)),
        )


@dataclass(frozen=True)
class RankedRepository:
    repository: Repository
    score: float
    components: dict[str, float]
    reasons: tuple[str, ...]
    star_delta: int | None

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self.repository)
        result["topics"] = list(self.repository.topics)
        result.update(
            {
                "score": self.score,
                "components": self.components,
                "reasons": list(self.reasons),
                "star_delta": self.star_delta,
            }
        )
        return result


@dataclass(frozen=True)
class JobResult:
    job_id: str
    title: str
    description: str
    queries: tuple[str, ...]
    discovered_count: int
    repositories: tuple[RankedRepository, ...]

