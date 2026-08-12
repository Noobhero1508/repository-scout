import unittest
from datetime import datetime, timezone

from repo_scout.models import JobResult, RankedRepository
from repo_scout.report import render_markdown
from tests.test_scoring import make_repository


class ReportTests(unittest.TestCase):
    def test_markdown_contains_repository_and_score(self) -> None:
        repository = make_repository()
        ranked = RankedRepository(
            repository=repository,
            score=88.4,
            components={"relevance": 90.0},
            reasons=("khớp: automation",),
            star_delta=12,
        )
        result = JobResult(
            job_id="automation",
            title="Automation",
            description="Useful tools",
            queries=("automation",),
            discovered_count=1,
            repositories=(ranked,),
        )
        output = render_markdown([result], datetime(2026, 8, 10, tzinfo=timezone.utc))
        self.assertIn("[example/repo](https://github.com/example/repo)", output)
        self.assertIn("**88.4**", output)
        self.assertIn("+12", output)


if __name__ == "__main__":
    unittest.main()

