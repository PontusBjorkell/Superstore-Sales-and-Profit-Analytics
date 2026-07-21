"""Build the normalized Superstore SQLite database."""

from __future__ import annotations

import pandas as pd

from superstore_analytics.config import (
    DATABASE_PATH,
    DATABASE_VALIDATION_REPORT_PATH,
    PROCESSED_DATA_PATH,
    SCHEMA_SQL_PATH,
    VIEWS_SQL_PATH,
    create_output_directories,
)
from superstore_analytics.database import build_database


def main() -> None:
    """Build and validate the project database."""

    create_output_directories()

    print("=" * 72)
    print("SUPERSTORE DATABASE BUILD")
    print("=" * 72)

    if not PROCESSED_DATA_PATH.exists():
        raise FileNotFoundError(
            f"Processed dataset not found: {PROCESSED_DATA_PATH}\n"
            "Run python scripts/prepare_data.py first."
        )

    print(f"\nLoading processed data from:\n{PROCESSED_DATA_PATH}")

    clean_df = pd.read_csv(
        PROCESSED_DATA_PATH,
        dtype={
            "postal_code": "string",
        },
        parse_dates=[
            "order_date",
            "ship_date",
        ],
    )

    print(
        f"Processed shape: "
        f"{clean_df.shape[0]:,} rows × "
        f"{clean_df.shape[1]} columns"
    )

    print(f"\nBuilding SQLite database at:\n{DATABASE_PATH}")

    validation_df = build_database(
        clean_df=clean_df,
        database_path=DATABASE_PATH,
        schema_path=SCHEMA_SQL_PATH,
        views_path=VIEWS_SQL_PATH,
    )

    DATABASE_VALIDATION_REPORT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    validation_df.to_csv(
        DATABASE_VALIDATION_REPORT_PATH,
        index=False,
    )

    print("\nDatabase validation")
    print("-" * 72)
    print(validation_df.to_string(index=False))

    print(
        f"\nValidation report saved to:\n"
        f"{DATABASE_VALIDATION_REPORT_PATH}"
    )

    print("\nDatabase created successfully.")
    print("=" * 72)


if __name__ == "__main__":
    main()
