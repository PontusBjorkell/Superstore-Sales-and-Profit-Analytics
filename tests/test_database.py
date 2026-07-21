"""Tests for the Superstore SQLite database layer."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd
import pytest

from superstore_analytics.database import (
    build_database,
    connect_database,
    create_dimension_tables,
    create_fact_tables,
)


@pytest.fixture
def sample_clean_data() -> pd.DataFrame:
    """Create a small processed-format dataset."""

    return pd.DataFrame(
        {
            "row_id": [1, 2, 3],
            "order_id": [
                "CA-2017-100001",
                "CA-2017-100001",
                "CA-2017-100002",
            ],
            "order_date": pd.to_datetime(
                [
                    "2017-01-01",
                    "2017-01-01",
                    "2017-01-02",
                ]
            ),
            "ship_date": pd.to_datetime(
                [
                    "2017-01-04",
                    "2017-01-04",
                    "2017-01-05",
                ]
            ),
            "ship_mode": [
                "Second Class",
                "Second Class",
                "Standard Class",
            ],
            "customer_id": [
                "AB-10001",
                "AB-10001",
                "CD-10002",
            ],
            "customer_name": [
                "Alice Brown",
                "Alice Brown",
                "Chris Doe",
            ],
            "segment": [
                "Consumer",
                "Consumer",
                "Corporate",
            ],
            "country": [
                "United States",
                "United States",
                "United States",
            ],
            "city": [
                "New York City",
                "New York City",
                "Chicago",
            ],
            "state": [
                "New York",
                "New York",
                "Illinois",
            ],
            "postal_code": [
                "10001",
                "10001",
                "60601",
            ],
            "region": [
                "East",
                "East",
                "Central",
            ],
            "product_id": [
                "OFF-PA-100001",
                "TEC-PH-100002",
                "OFF-PA-100001",
            ],
            "product_name": [
                "Paper Product",
                "Phone Product",
                "Paper Product",
            ],
            "category": [
                "Office Supplies",
                "Technology",
                "Office Supplies",
            ],
            "sub_category": [
                "Paper",
                "Phones",
                "Paper",
            ],
            "sales": [100.0, 200.0, 50.0],
            "quantity": [2, 1, 1],
            "discount": [0.0, 0.2, 0.0],
            "profit": [20.0, -10.0, 5.0],
            "profit_margin": [0.20, -0.05, 0.10],
            "unit_sales": [50.0, 200.0, 50.0],
            "unit_profit": [10.0, -10.0, 5.0],
            "is_profitable": [True, False, True],
            "is_loss": [False, True, False],
            "is_discounted": [False, True, False],
            "discount_band": [
                "No discount",
                "11–20%",
                "No discount",
            ],
            "shipping_days": [3, 3, 3],
        }
    )


@pytest.fixture
def sample_conflicting_product_ids(
    sample_clean_data: pd.DataFrame,
) -> pd.DataFrame:
    """
    Return data where one source product ID maps to two descriptions.

    This reproduces the real Superstore dataset issue and verifies that
    surrogate product keys handle it correctly.
    """

    conflicting = sample_clean_data.copy()
    conflicting.loc[2, "product_name"] = "Different Paper Product"

    return conflicting


def test_connect_database_enables_foreign_keys(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "test.db"

    connection = connect_database(database_path)

    try:
        enabled = connection.execute(
            "PRAGMA foreign_keys;"
        ).fetchone()[0]

        assert enabled == 1
    finally:
        connection.close()


def test_dimension_tables_have_expected_counts(
    sample_clean_data: pd.DataFrame,
) -> None:
    dimensions = create_dimension_tables(sample_clean_data)

    assert len(dimensions["customers"]) == 2
    assert len(dimensions["products"]) == 2
    assert len(dimensions["locations"]) == 2


def test_product_dimension_uses_surrogate_keys_for_conflicts(
    sample_conflicting_product_ids: pd.DataFrame,
) -> None:
    dimensions = create_dimension_tables(
        sample_conflicting_product_ids
    )

    products = dimensions["products"]

    assert len(products) == 3
    assert products["product_key"].is_unique
    assert products["product_id"].nunique() == 2


def test_fact_tables_have_expected_counts(
    sample_clean_data: pd.DataFrame,
) -> None:
    dimensions = create_dimension_tables(sample_clean_data)

    facts = create_fact_tables(
        clean_df=sample_clean_data,
        locations=dimensions["locations"],
        products=dimensions["products"],
    )

    assert len(facts["orders"]) == 2
    assert len(facts["order_items"]) == 3


def test_orders_reference_valid_location_ids(
    sample_clean_data: pd.DataFrame,
) -> None:
    dimensions = create_dimension_tables(sample_clean_data)

    facts = create_fact_tables(
        clean_df=sample_clean_data,
        locations=dimensions["locations"],
        products=dimensions["products"],
    )

    valid_location_ids = set(
        dimensions["locations"]["location_id"]
    )

    assert set(
        facts["orders"]["location_id"]
    ).issubset(valid_location_ids)


def test_order_items_reference_valid_product_keys(
    sample_clean_data: pd.DataFrame,
) -> None:
    dimensions = create_dimension_tables(sample_clean_data)

    facts = create_fact_tables(
        clean_df=sample_clean_data,
        locations=dimensions["locations"],
        products=dimensions["products"],
    )

    valid_product_keys = set(
        dimensions["products"]["product_key"]
    )

    assert set(
        facts["order_items"]["product_key"]
    ).issubset(valid_product_keys)


def test_conflicting_source_product_ids_build_successfully(
    sample_conflicting_product_ids: pd.DataFrame,
) -> None:
    dimensions = create_dimension_tables(
        sample_conflicting_product_ids
    )

    facts = create_fact_tables(
        clean_df=sample_conflicting_product_ids,
        locations=dimensions["locations"],
        products=dimensions["products"],
    )

    assert len(facts["order_items"]) == 3
    assert facts["order_items"]["product_key"].nunique() == 3


def test_inconsistent_order_data_raises_error(
    sample_clean_data: pd.DataFrame,
) -> None:
    sample_clean_data.loc[1, "ship_mode"] = "First Class"

    dimensions = create_dimension_tables(sample_clean_data)

    with pytest.raises(
        ValueError,
        match="inconsistent order-level information",
    ):
        create_fact_tables(
            clean_df=sample_clean_data,
            locations=dimensions["locations"],
            products=dimensions["products"],
        )


def test_build_database_creates_valid_tables_and_views(
    sample_conflicting_product_ids: pd.DataFrame,
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "test.db"

    project_root = Path(__file__).resolve().parents[1]
    schema_path = project_root / "sql" / "create_schema.sql"
    views_path = project_root / "sql" / "create_views.sql"

    validation_df = build_database(
        clean_df=sample_conflicting_product_ids,
        database_path=database_path,
        schema_path=schema_path,
        views_path=views_path,
    )

    assert validation_df["passed"].all()

    connection = sqlite3.connect(database_path)

    try:
        tables = {
            row[0]
            for row in connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                """
            )
        }

        views = {
            row[0]
            for row in connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'view'
                """
            )
        }

        assert {
            "customers",
            "products",
            "locations",
            "orders",
            "order_items",
        }.issubset(tables)

        assert {
            "vw_order_item_details",
            "vw_order_summary",
            "vw_customer_summary",
            "vw_product_summary",
        }.issubset(views)

        product_rows = connection.execute(
            "SELECT COUNT(*) FROM products"
        ).fetchone()[0]

        item_rows = connection.execute(
            "SELECT COUNT(*) FROM order_items"
        ).fetchone()[0]

        assert product_rows == 3
        assert item_rows == 3

    finally:
        connection.close()
