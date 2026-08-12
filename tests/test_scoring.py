import unittest
from datetime import datetime, timezone

from repo_scout.config import Job
from repo_scout.models import Repository
from repo_scout.scoring import rank_repository


NOW = datetime(2026, 8, 10, tzinfo=timezone.utc)


def make_repository(**overrides: object) -> Repository:
    values = {
        "full_name": "example/repo",
        "html_url": "https://github.com/example/repo",
        "description": "GitHub Actions workflow automation toolkit",
        "language": "Python",
        "topics": ("automation", "github-actions"),
        "stars": 500,
        "forks": 30,
        "open_issues": 5,
        "created_at": "2026-07-01T00:00:00Z",
        "pushed_at": "2026-08-09T00:00:00Z",
        "updated_at": "2026-08-09T00:00:00Z",
        "license_name": "MIT",
        "archived": False,
        "fork": False,
    }
    values.update(overrides)
    return Repository(**values)  # type: ignore[arg-type]


JOB = Job(
    id="automation",
    title="Automation",
    description="",
    queries=("automation",),
    keywords=("github actions", "automation"),
    preferred_languages=("Python",),
)


class ScoringTests(unittest.TestCase):
    def test_recent_relevant_repository_scores_above_stale_one(self) -> None:
        recent = rank_repository(make_repository(), JOB, None, NOW)
        stale = rank_repository(
            make_repository(
                description="Unrelated project",
                topics=(),
                language="Unknown",
                created_at="2018-01-01T00:00:00Z",
                pushed_at="2020-01-01T00:00:00Z",
                license_name="Unknown",
            ),
            JOB,
            None,
            NOW,
        )
        self.assertGreater(recent.score, stale.score)

    def test_star_delta_uses_previous_snapshot(self) -> None:
        ranked = rank_repository(
            make_repository(stars=550),
            JOB,
            {"stars": 500, "last_seen_at": "2026-08-09T00:00:00Z"},
            NOW,
        )
        self.assertEqual(ranked.star_delta, 50)
        self.assertIn("+50 sao", " ".join(ranked.reasons))


if __name__ == "__main__":
    unittest.main()

