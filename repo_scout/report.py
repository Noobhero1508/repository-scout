from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from repo_scout.models import JobResult


def _escape_table(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


def _short_description(value: str, limit: int = 120) -> str:
    value = " ".join(value.split())
    return value if len(value) <= limit else value[: limit - 1].rstrip() + "…"


def _date_only(value: str) -> str:
    return value[:10] if value else "—"


def render_markdown(results: list[JobResult], generated_at: datetime) -> str:
    generated_utc = generated_at.astimezone(timezone.utc)
    lines = [
        "# Repository Scout — báo cáo mới nhất",
        "",
        f"> Tạo tự động lúc {generated_utc.strftime('%Y-%m-%d %H:%M UTC')}.",
        "",
        "Điểm tổng hợp độ liên quan, đà tăng trưởng, hoạt động gần đây, độ phổ biến, "
        "độ mới và tín hiệu tin cậy. Hãy kiểm tra README và license trước khi sử dụng.",
        "",
    ]

    for result in results:
        lines.extend(
            [
                f"## {result.title}",
                "",
                result.description,
                "",
                f"Tìm thấy **{result.discovered_count}** ứng viên hợp lệ; hiển thị "
                f"**{len(result.repositories)}** repository tốt nhất.",
                "",
            ]
        )
        if not result.repositories:
            lines.extend(["Chưa tìm thấy kết quả phù hợp trong lần chạy này.", ""])
            continue

        lines.extend(
            [
                "| # | Repository | Điểm | Stars | Δ stars | Ngôn ngữ | Push gần nhất | Lý do |",
                "|---:|---|---:|---:|---:|---|---|---|",
            ]
        )
        for index, ranked in enumerate(result.repositories, start=1):
            repo = ranked.repository
            delta = "—" if ranked.star_delta is None else f"+{ranked.star_delta}"
            reason = _escape_table("; ".join(ranked.reasons[:4]))
            lines.append(
                f"| {index} | [{repo.full_name}]({repo.html_url})<br>"
                f"{_escape_table(_short_description(repo.description))} | "
                f"**{ranked.score:.1f}** | {repo.stars:,} | {delta} | "
                f"{_escape_table(repo.language)} | {_date_only(repo.pushed_at)} | {reason} |"
            )
        lines.append("")

    lines.extend(
        [
            "---",
            "",
            "Báo cáo do Repository Scout tạo. Cấu hình truy vấn nằm trong `config/jobs.json`.",
            "",
        ]
    )
    return "\n".join(lines)


def render_json(results: list[JobResult], generated_at: datetime) -> dict[str, Any]:
    return {
        "generated_at": generated_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "jobs": [
            {
                "id": result.job_id,
                "title": result.title,
                "description": result.description,
                "queries": list(result.queries),
                "discovered_count": result.discovered_count,
                "repositories": [repository.to_dict() for repository in result.repositories],
            }
            for result in results
        ],
    }

