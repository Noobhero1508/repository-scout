import json
import tempfile
import unittest
from pathlib import Path

from repo_scout.config import load_config


class ConfigTests(unittest.TestCase):
    def test_loads_project_config(self) -> None:
        config = load_config(Path("config/jobs.json"))
        self.assertGreaterEqual(len(config.jobs), 3)
        self.assertEqual(config.jobs[0].id, "new_and_interesting")

    def test_rejects_duplicate_job_ids(self) -> None:
        payload = {
            "jobs": [
                {"id": "same", "title": "One", "queries": ["stars:>1"]},
                {"id": "same", "title": "Two", "queries": ["stars:>2"]},
            ]
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "bị trùng"):
                load_config(path)


if __name__ == "__main__":
    unittest.main()

