"""SQL analysis catalogue parsing, execution, and export utilities."""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class SQLAnalysis:
    """One named SQL analysis from the catalogue."""

    name: str
    title: str
    description: str
    sql: str


_HEADER_PATTERN = re.compile(
    r"^--\s*name:\s*(?P<name>[a-zA-Z0-9_\-]+)\s*$",
    flags=re.IGNORECASE,
)

_TITLE_PATTERN = re.compile(
    r"^--\s*title:\s*(?P<title>.+?)\s*$",
    flags=re.IGNORECASE,
)

_DESCRIPTION_PATTERN = re.compile(
    r"^--\s*description:\s*(?P<description>.+?)\s*$",
    flags=re.IGNORECASE,
)


def parse_analysis_catalogue(path: Path | str) -> list[SQLAnalysis]:
    """
    Parse a SQL file containing named analyses.

    Each analysis must begin with:

    -- name: 01_executive_summary
    -- title: Executive KPI Summary
    -- description: Overall business performance.

    The SQL statement follows until the next ``-- name:`` marker.
    """

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Analysis SQL file not found: {path}")

    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    analyses: list[SQLAnalysis] = []
    current_name: str | None = None
    current_title: str | None = None
    current_description: str | None = None
    sql_lines: list[str] = []

    def flush_current() -> None:
        nonlocal current_name, current_title, current_description, sql_lines

        if current_name is None:
            return

        sql = "\n".join(sql_lines).strip()

        if not current_title:
            raise ValueError(
                f"Analysis '{current_name}' is missing a -- title: line."
            )

        if not current_description:
            raise ValueError(
                f"Analysis '{current_name}' is missing a -- description: line."
            )

        if not sql:
            raise ValueError(
                f"Analysis '{current_name}' does not contain SQL."
            )

        analyses.append(
            SQLAnalysis(
                name=current_name,
                title=current_title,
                description=current_description,
                sql=sql,
            )
        )

        current_name = None
        current_title = None
        current_description = None
        sql_lines = []

    for line in lines:
        header_match = _HEADER_PATTERN.match(line)

        if header_match:
            flush_current()
            current_name = header_match.group("name")
            continue

        if current_name is None:
            continue

        title_match = _TITLE_PATTERN.match(line)
        if title_match:
            current_title = title_match.group("title")
            continue

        description_match = _DESCRIPTION_PATTERN.match(line)
        if description_match:
            current_description = description_match.group("description")
            continue

        sql_lines.append(line)

    flush_current()

    if not analyses:
        raise ValueError(
            f"No named analyses were found in {path}."
        )

    names = [analysis.name for analysis in analyses]
    duplicate_names = sorted(
        {name for name in names if names.count(name) > 1}
    )

    if duplicate_names:
        raise ValueError(
            "Duplicate analysis names found: "
            + ", ".join(duplicate_names)
        )

    return analyses


def run_analysis(
    connection: sqlite3.Connection,
    analysis: SQLAnalysis,
) -> pd.DataFrame:
    """Execute one analysis and return its result."""

    return pd.read_sql_query(analysis.sql, connection)


def run_all_analyses(
    database_path: Path | str,
    catalogue_path: Path | str,
) -> dict[str, pd.DataFrame]:
    """Execute every named analysis in the SQL catalogue."""

    database_path = Path(database_path)

    if not database_path.exists():
        raise FileNotFoundError(
            f"SQLite database not found: {database_path}"
        )

    analyses = parse_analysis_catalogue(catalogue_path)
    results: dict[str, pd.DataFrame] = {}

    connection = sqlite3.connect(database_path)

    try:
        for analysis in analyses:
            results[analysis.name] = run_analysis(
                connection,
                analysis,
            )
    finally:
        connection.close()

    return results


def export_analysis_results(
    database_path: Path | str,
    catalogue_path: Path | str,
    output_directory: Path | str,
    manifest_path: Path | str | None = None,
) -> pd.DataFrame:
    """
    Execute all analyses, save one CSV per analysis, and create a manifest.
    """

    output_directory = Path(output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)

    analyses = parse_analysis_catalogue(catalogue_path)
    connection = sqlite3.connect(database_path)

    manifest_rows: list[dict[str, object]] = []

    try:
        for analysis in analyses:
            result = run_analysis(connection, analysis)
            output_path = output_directory / f"{analysis.name}.csv"
            result.to_csv(output_path, index=False)

            manifest_rows.append(
                {
                    "name": analysis.name,
                    "title": analysis.title,
                    "description": analysis.description,
                    "row_count": len(result),
                    "column_count": result.shape[1],
                    "output_file": output_path.name,
                }
            )
    finally:
        connection.close()

    manifest = pd.DataFrame(manifest_rows)

    if manifest_path is not None:
        manifest_path = Path(manifest_path)
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest.to_csv(manifest_path, index=False)

    return manifest
