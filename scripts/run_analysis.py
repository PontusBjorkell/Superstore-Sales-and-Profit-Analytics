"""Run and export the complete Superstore SQL analytics catalogue."""

from __future__ import annotations

from superstore_analytics.analysis import export_analysis_results
from superstore_analytics.config import (
    ANALYSIS_MANIFEST_PATH,
    ANALYSIS_SQL_PATH,
    DATABASE_PATH,
    SQL_REPORTS_DIR,
    create_output_directories,
)


def main() -> None:
    """Execute all named SQL analyses and export their result tables."""

    create_output_directories()

    print("=" * 78)
    print("SUPERSTORE SQL ANALYTICS")
    print("=" * 78)

    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DATABASE_PATH}\n"
            "Run python scripts/build_database.py first."
        )

    if not ANALYSIS_SQL_PATH.exists():
        raise FileNotFoundError(
            f"Analysis catalogue not found: {ANALYSIS_SQL_PATH}"
        )

    print(f"\nDatabase:\n{DATABASE_PATH}")
    print(f"\nSQL catalogue:\n{ANALYSIS_SQL_PATH}")
    print(f"\nExport directory:\n{SQL_REPORTS_DIR}")

    manifest = export_analysis_results(
        database_path=DATABASE_PATH,
        catalogue_path=ANALYSIS_SQL_PATH,
        output_directory=SQL_REPORTS_DIR,
        manifest_path=ANALYSIS_MANIFEST_PATH,
    )

    print("\nCompleted analyses")
    print("-" * 78)
    print(
        manifest[
            [
                "name",
                "title",
                "row_count",
                "column_count",
            ]
        ].to_string(index=False)
    )

    print(f"\nAnalyses completed: {len(manifest)}")
    print(f"Manifest saved to:\n{ANALYSIS_MANIFEST_PATH}")
    print("=" * 78)


if __name__ == "__main__":
    main()
