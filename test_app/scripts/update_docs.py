from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
from typing import Iterable, List


SCRIPT_DIR = Path(__file__).resolve().parent
TEST_APP_DIR = SCRIPT_DIR.parent
DOCS_DIR = TEST_APP_DIR / "docs"
CHANGELOG_PATH = DOCS_DIR / "CHANGELOG.md"
DECISIONS_PATH = DOCS_DIR / "DECISIONS.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Append lightweight changelog and decision-log entries for Puppy Coordinator."
    )
    parser.add_argument(
        "--date",
        default=date.today().isoformat(),
        help="Entry date in YYYY-MM-DD format. Defaults to today.",
    )
    parser.add_argument(
        "--changelog",
        action="append",
        default=[],
        help="Changelog bullet to append. Repeat for multiple items.",
    )
    parser.add_argument(
        "--decision-title",
        help="Decision heading to append to DECISIONS.md.",
    )
    parser.add_argument(
        "--decision",
        action="append",
        default=[],
        help="Decision bullet. Repeat for multiple decision bullets.",
    )
    parser.add_argument(
        "--why",
        action="append",
        default=[],
        help="Why bullet. Repeat for multiple why bullets.",
    )
    parser.add_argument(
        "--follow-up",
        action="append",
        default=[],
        help="Optional follow-up bullet. Repeat for multiple items.",
    )
    return parser.parse_args()


def read_lines(path: Path) -> List[str]:
    return path.read_text(encoding="utf-8").splitlines()


def write_lines(path: Path, lines: Iterable[str]) -> None:
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def ensure_heading_section(lines: List[str], heading: str, insert_at: int) -> int:
    for index, line in enumerate(lines):
        if line == heading:
            return index
    lines[insert_at:insert_at] = [heading, ""]
    return insert_at


def section_end(lines: List[str], start_index: int) -> int:
    for index in range(start_index + 1, len(lines)):
        if lines[index].startswith("#"):
            return index
    return len(lines)


def append_changelog_entries(path: Path, entry_date: str, entries: List[str]) -> None:
    if not entries:
        return

    lines = read_lines(path)
    unreleased_index = ensure_heading_section(lines, "## Unreleased", 2)
    insert_hint = unreleased_index + 2
    date_heading = f"### {entry_date}"
    date_index = ensure_heading_section(lines, date_heading, insert_hint)
    end_index = section_end(lines, date_index)

    while end_index > date_index + 1 and lines[end_index - 1] == "":
        end_index -= 1

    block = [f"- {entry}" for entry in entries]
    if end_index > date_index + 1:
        block.insert(0, "")
    block.append("")
    lines[end_index:end_index] = block
    write_lines(path, lines)


def append_decision_entry(
    path: Path,
    entry_date: str,
    title: str,
    decision_points: List[str],
    why_points: List[str],
    follow_ups: List[str],
) -> None:
    if not title:
        return

    lines = read_lines(path)
    date_heading = f"## {entry_date}"
    date_index = ensure_heading_section(lines, date_heading, 2)
    end_index = section_end(lines, date_index)

    while end_index > date_index + 1 and lines[end_index - 1] == "":
        end_index -= 1

    block = [
        "",
        f"### {title}",
        "",
        "Decision:",
        "",
    ]
    block.extend(f"- {item}" for item in decision_points or ["No decision text provided."])
    block.extend(["", "Why:", ""])
    block.extend(f"- {item}" for item in why_points or ["No rationale provided."])

    if follow_ups:
        block.extend(["", "Follow-up:", ""])
        block.extend(f"- {item}" for item in follow_ups)

    block.append("")
    lines[end_index:end_index] = block
    write_lines(path, lines)


def main() -> int:
    args = parse_args()

    if not args.changelog and not args.decision_title:
        raise SystemExit("Nothing to do. Pass --changelog and/or --decision-title.")

    append_changelog_entries(CHANGELOG_PATH, args.date, args.changelog)
    append_decision_entry(
        DECISIONS_PATH,
        args.date,
        args.decision_title or "",
        args.decision,
        args.why,
        args.follow_up,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
