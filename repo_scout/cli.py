from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from repo_scout.config import Config, load_config
from repo_scout.github_client import GitHubAPIError, GitHubClient
from repo_scout.models import JobResult, Repository
from repo_scout.report import render_json, render_markdown
from repo_scout.scoring import rank_repository
from repo_scout.state import load_state, previous_snapshot, update_state, write_json


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Tìm và xếp hạng GitHub repository theo các nhóm công việc."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/jobs.json"),
        help="Đường dẫn tới file cấu hình JSON.",
    )
    parser.add_argument(
        "--check-config",
        action="store_true",
        help="Chỉ kiểm tra cấu hình, không gọi GitHub API.",
    )
    return parser


def _configure_stdio() -> None:
    """Keep Vietnamese output readable on Windows terminals and redirected logs."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8", errors="replace")


def _discover(config: Config, client: GitHubClient, now: datetime) -> tuple[list[JobResult], list[Repository]]:
    state_path = Path(config.settings.state_path)
    state = load_state(state_path)
    since = (now - timedelta(days=config.settings.lookback_days)).date().isoformat()
    results: list[JobResult] = []
    all_repositories: dict[str, Repository] = {}

    for job in config.jobs:
        candidates: dict[str, Repository] = {}
        expanded_queries: list[str] = []
        print(f"\n[{job.title}]", flush=True)
        for query_template in job.queries:
            query = query_template.format(since=since)
            expanded_queries.append(query)
            print(f"  Tìm: {query}", flush=True)
            for repository in client.search_repositories(
                query,
                limit=config.settings.max_results_per_query,
            ):
                candidates[repository.full_name] = repository

        filtered = [
            repository
            for repository in candidates.values()
            if not (config.settings.exclude_archived and repository.archived)
            and not (config.settings.exclude_forks and repository.fork)
        ]
        ranked = [
            rank_repository(
                repository,
                job,
                previous_snapshot(state, repository.full_name),
                now,
            )
            for repository in filtered
        ]
        ranked.sort(key=lambda item: (item.score, item.repository.stars), reverse=True)
        top_n = job.top_n or config.settings.report_top_n
        results.append(
            JobResult(
                job_id=job.id,
                title=job.title,
                description=job.description,
                queries=tuple(expanded_queries),
                discovered_count=len(filtered),
                repositories=tuple(ranked[:top_n]),
            )
        )
        all_repositories.update({repo.full_name: repo for repo in filtered})
        print(f"  {len(filtered)} ứng viên hợp lệ, chọn {min(top_n, len(ranked))}.", flush=True)

    update_state(state, list(all_repositories.values()), now)
    write_json(state_path, state)
    return results, list(all_repositories.values())


def _write_reports(config: Config, results: list[JobResult], now: datetime) -> None:
    markdown_path = Path(config.settings.report_path)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown = render_markdown(results, now)
    markdown_path.write_text(markdown, encoding="utf-8")

    json_payload = render_json(results, now)
    write_json(Path(config.settings.json_report_path), json_payload)

    history_path = Path(config.settings.history_dir) / f"{now.date().isoformat()}.md"
    history_path.parent.mkdir(parents=True, exist_ok=True)
    history_path.write_text(markdown, encoding="utf-8")
    print(f"\nĐã tạo {markdown_path}, {config.settings.json_report_path} và {history_path}.")


def main(argv: list[str] | None = None) -> int:
    _configure_stdio()
    args = build_parser().parse_args(argv)
    try:
        config = load_config(args.config)
        if args.check_config:
            print(f"Cấu hình hợp lệ: {len(config.jobs)} nhóm công việc.")
            return 0

        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        if not token:
            print(
                "Cảnh báo: chưa có GITHUB_TOKEN/GH_TOKEN; GitHub API sẽ giới hạn request thấp hơn.",
                file=sys.stderr,
            )

        now = datetime.now(timezone.utc)
        client = GitHubClient(
            token=token,
            timeout_seconds=config.settings.request_timeout_seconds,
        )
        results, _ = _discover(config, client, now)
        _write_reports(config, results, now)
        return 0
    except (ValueError, GitHubAPIError, OSError) as exc:
        print(f"Lỗi: {exc}", file=sys.stderr)
        return 1
