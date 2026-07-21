"""Tests for the SQL analytics catalogue."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd
import pytest

from superstore_analytics.analysis import (
    SQLAnalysis,
    export_analysis_results,
    parse_analysis_catalogue,
    run_analysis,
)


@pytest.fixture
def sample_catalogue(tmp_path: Path) -> Path:
    """Create a small valid named SQL catalogue."""

    path = tmp_path / "analysis.sql"
    path.write_text(
        """
-- name: 01_total
-- title: Total Value
-- description: Calculates the total value.
SELECT SUM(value) AS total_value
FROM metrics;

-- name: 02_by_group
-- title: Value by Group
-- description: Aggregates values by category.
SELECT category, SUM(value) AS total_value
FROM metrics
GROUP BY category
ORDER BY category;
""".strip(),
        encoding="utf-8",
    )

    return path


@pytest.fixture
def sample_database(tmp_path: Path) -> Path:
    """Create a tiny SQLite database for query tests."""

    path = tmp_path / "sample.db"
    connection = sqlite3.connect(path)

    try:
        connection.execute(
            """
            CREATE TABLE metrics (
                category TEXT NOT NULL,
                value REAL NOT NULL
            )
            """
        )

        connection.executemany(
            """
            INSERT INTO metrics (category, value)
            VALUES (?, ?)
            """,
            [
                ("A", 10.0),
                ("A", 15.0),
                ("B", 20.0),
            ],
        )

        connection.commit()
    finally:
        connection.close()

    return path


def test_parse_analysis_catalogue(
    sample_catalogue: Path,
) -> None:
    analyses = parse_analysis_catalogue(sample_catalogue)

    assert len(analyses) == 2
    assert analyses[0].name == "01_total"
    assert analyses[0].title == "Total Value"
    assert "SUM(value)" in analyses[0].sql


def test_missing_title_raises_error(
    tmp_path: Path,
) -> None:
    path = tmp_path / "invalid.sql"
    path.write_text(
        """
-- name: 01_invalid
-- description: Missing title.
SELECT 1;
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="missing a -- title"):
        parse_analysis_catalogue(path)


def test_duplicate_names_raise_error(
    tmp_path: Path,
) -> None:
    path = tmp_path / "duplicates.sql"
    path.write_text(
        """
-- name: duplicate
-- title: First
-- description: First query.
SELECT 1;

-- name: duplicate
-- title: Second
-- description: Second query.
SELECT 2;
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Duplicate analysis names"):
        parse_analysis_catalogue(path)


def test_run_analysis_returns_dataframe(
    sample_database: Path,
) -> None:
    connection = sqlite3.connect(sample_database)

    analysis = SQLAnalysis(
        name="total",
        title="Total",
        description="Total value.",
        sql="SELECT SUM(value) AS total_value FROM metrics;",
    )

    try:
        result = run_analysis(connection, analysis)
    finally:
        connection.close()

    assert isinstance(result, pd.DataFrame)
    assert result.loc[0, "total_value"] == pytest.approx(45.0)


def test_export_analysis_results(
    sample_database: Path,
    sample_catalogue: Path,
    tmp_path: Path,
) -> None:
    output_directory = tmp_path / "reports"
    manifest_path = output_directory / "manifest.csv"

    manifest = export_analysis_results(
        database_path=sample_database,
        catalogue_path=sample_catalogue,
        output_directory=output_directory,
        manifest_path=manifest_path,
    )

    assert len(manifest) == 2
    assert (output_directory / "01_total.csv").exists()
    assert (output_directory / "02_by_group.csv").exists()
    assert manifest_path.exists()

    total_result = pd.read_csv(
        output_directory / "01_total.csv"
    )

    assert total_result.loc[0, "total_value"] == pytest.approx(45.0)


def test_real_catalogue_contains_thirty_queries() -> None:
    project_root = Path(__file__).resolve().parents[1]
    catalogue_path = project_root / "sql" / "analysis_queries.sql"

    analyses = parse_analysis_catalogue(catalogue_path)

    assert len(analyses) == 30
    assert analyses[0].name == "01_executive_kpi_summary"
    assert analyses[-1].name == "30_management_attention_summary"
