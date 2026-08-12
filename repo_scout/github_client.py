from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from repo_scout.models import Repository


class GitHubAPIError(RuntimeError):
    """Raised when the GitHub API cannot complete a request."""


class GitHubClient:
    def __init__(self, token: str | None, timeout_seconds: int = 30) -> None:
        self.token = token
        self.timeout_seconds = timeout_seconds
        self.base_url = "https://api.github.com"

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "repository-scout/0.1",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _get_json(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        query_string = urllib.parse.urlencode(params)
        request = urllib.request.Request(
            f"{self.base_url}{path}?{query_string}",
            headers=self._headers(),
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            remaining = exc.headers.get("x-ratelimit-remaining", "unknown")
            reset = exc.headers.get("x-ratelimit-reset", "unknown")
            try:
                detail = json.loads(exc.read().decode("utf-8")).get("message", str(exc))
            except (json.JSONDecodeError, UnicodeDecodeError):
                detail = str(exc)
            raise GitHubAPIError(
                f"GitHub API trả về HTTP {exc.code}: {detail}. "
                f"Rate limit còn {remaining}, reset={reset}."
            ) from exc
        except urllib.error.URLError as exc:
            raise GitHubAPIError(f"Không kết nối được GitHub API: {exc.reason}") from exc

    def search_repositories(self, query: str, limit: int = 50) -> list[Repository]:
        limit = max(1, min(limit, 1000))
        repositories: list[Repository] = []
        page = 1

        while len(repositories) < limit:
            per_page = min(100, limit - len(repositories))
            payload = self._get_json(
                "/search/repositories",
                {
                    "q": query,
                    "sort": "stars",
                    "order": "desc",
                    "per_page": per_page,
                    "page": page,
                },
            )
            items = payload.get("items", [])
            if not isinstance(items, list):
                raise GitHubAPIError("GitHub API trả về dữ liệu tìm kiếm không hợp lệ")

            repositories.extend(
                Repository.from_api(item) for item in items if isinstance(item, dict)
            )
            if len(items) < per_page:
                break
            page += 1
            if len(repositories) < limit:
                time.sleep(1.1)

        return repositories[:limit]

