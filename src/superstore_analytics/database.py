"""SQLite database construction and validation utilities."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


PRODUCT_NATURAL_KEY = [
    "product_id",
    "product_name",
    "category",
    "sub_category",
]

LOCATION_NATURAL_KEY = [
    "country",
    "city",
    "state",
    "postal_code",
    "region",
]


def connect_database(database_path: Path | str) -> sqlite3.Connection:
    """Open a SQLite connection with foreign-key enforcement enabled."""

    database_path = Path(database_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(database_path)
    connection.execute("PRAGMA foreign_keys = ON;")

    return connection


def execute_sql_file(
    connection: sqlite3.Connection,
    sql_path: Path | str,
) -> None:
    """Execute all SQL statements contained in a file."""

    sql_path = Path(sql_path)

    if not sql_path.exists():
        raise FileNotFoundError(f"SQL file not found: {sql_path}")

    sql_text = sql_path.read_text(encoding="utf-8")
    connection.executescript(sql_text)


def create_dimension_tables(
    clean_df: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    """Create normalized customer, product, and location dimensions."""

    customers = (
        clean_df[
            [
                "customer_id",
                "customer_name",
                "segment",
            ]
        ]
        .drop_duplicates()
        .sort_values("customer_id")
        .reset_index(drop=True)
    )

    products = (
        clean_df[PRODUCT_NATURAL_KEY]
        .drop_duplicates()
        .sort_values(PRODUCT_NATURAL_KEY)
        .reset_index(drop=True)
    )

    products.insert(
        0,
        "product_key",
        range(1, len(products) + 1),
    )

    locations = (
        clean_df[LOCATION_NATURAL_KEY]
        .drop_duplicates()
        .sort_values(
            [
                "country",
                "state",
                "city",
                "postal_code",
                "region",
            ]
        )
        .reset_index(drop=True)
    )

    locations.insert(
        0,
        "location_id",
        range(1, len(locations) + 1),
    )

    return {
        "customers": customers,
        "products": products,
        "locations": locations,
    }


def create_fact_tables(
    clean_df: pd.DataFrame,
    locations: pd.DataFrame,
    products: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    """Create normalized order and order-item fact tables."""

    order_source = clean_df[
        [
            "order_id",
            "customer_id",
            "order_date",
            "ship_date",
            "ship_mode",
            "shipping_days",
            *LOCATION_NATURAL_KEY,
        ]
    ].copy()

    order_source = order_source.merge(
        locations,
        on=LOCATION_NATURAL_KEY,
        how="left",
        validate="many_to_one",
    )

    if order_source["location_id"].isna().any():
        raise ValueError(
            "One or more orders could not be matched to a location."
        )

    order_consistency = (
        order_source.groupby("order_id")
        .agg(
            customer_count=("customer_id", "nunique"),
            order_date_count=("order_date", "nunique"),
            ship_date_count=("ship_date", "nunique"),
            ship_mode_count=("ship_mode", "nunique"),
            location_count=("location_id", "nunique"),
            shipping_days_count=("shipping_days", "nunique"),
        )
    )

    inconsistent_orders = order_consistency[
        (order_consistency > 1).any(axis=1)
    ]

    if not inconsistent_orders.empty:
        raise ValueError(
            "Some order IDs contain inconsistent order-level information: "
            f"{inconsistent_orders.index.tolist()[:5]}"
        )

    orders = (
        order_source[
            [
                "order_id",
                "customer_id",
                "location_id",
                "order_date",
                "ship_date",
                "ship_mode",
                "shipping_days",
            ]
        ]
        .drop_duplicates(subset=["order_id"])
        .sort_values("order_id")
        .reset_index(drop=True)
    )

    orders["location_id"] = orders["location_id"].astype("int64")
    orders["shipping_days"] = orders["shipping_days"].astype("int64")

    orders["order_date"] = (
        pd.to_datetime(orders["order_date"])
        .dt.strftime("%Y-%m-%d")
    )

    orders["ship_date"] = (
        pd.to_datetime(orders["ship_date"])
        .dt.strftime("%Y-%m-%d")
    )

    order_items = clean_df[
        [
            "row_id",
            "order_id",
            *PRODUCT_NATURAL_KEY,
            "sales",
            "quantity",
            "discount",
            "profit",
            "profit_margin",
            "unit_sales",
            "unit_profit",
            "is_profitable",
            "is_loss",
            "is_discounted",
            "discount_band",
        ]
    ].copy()

    order_items = order_items.merge(
        products[
            [
                "product_key",
                *PRODUCT_NATURAL_KEY,
            ]
        ],
        on=PRODUCT_NATURAL_KEY,
        how="left",
        validate="many_to_one",
    )

    if order_items["product_key"].isna().any():
        raise ValueError(
            "One or more order items could not be matched to a product."
        )

    order_items = order_items[
        [
            "row_id",
            "order_id",
            "product_key",
            "sales",
            "quantity",
            "discount",
            "profit",
            "profit_margin",
            "unit_sales",
            "unit_profit",
            "is_profitable",
            "is_loss",
            "is_discounted",
            "discount_band",
        ]
    ]

    integer_columns = [
        "row_id",
        "product_key",
        "quantity",
    ]

    for column in integer_columns:
        order_items[column] = (
            pd.to_numeric(order_items[column], errors="raise")
            .astype("int64")
        )

    boolean_columns = [
        "is_profitable",
        "is_loss",
        "is_discounted",
    ]

    for column in boolean_columns:
        order_items[column] = (
            order_items[column]
            .astype(bool)
            .astype("int64")
        )

    order_items["discount_band"] = (
        order_items["discount_band"].astype("string")
    )

    order_items = (
        order_items
        .sort_values("row_id")
        .reset_index(drop=True)
    )

    return {
        "orders": orders,
        "order_items": order_items,
    }


def insert_dataframe(
    connection: sqlite3.Connection,
    dataframe: pd.DataFrame,
    table_name: str,
) -> None:
    """Insert a dataframe into an existing SQLite table."""

    dataframe.to_sql(
        table_name,
        connection,
        if_exists="append",
        index=False,
    )


def _expected_product_count(clean_df: pd.DataFrame) -> int:
    """Return the number of unique product records in the source data."""

    return int(
        clean_df[PRODUCT_NATURAL_KEY]
        .drop_duplicates()
        .shape[0]
    )


def _expected_location_count(clean_df: pd.DataFrame) -> int:
    """Return the number of unique location records in the source data."""

    return int(
        clean_df[LOCATION_NATURAL_KEY]
        .drop_duplicates()
        .shape[0]
    )


def validate_database(
    connection: sqlite3.Connection,
    clean_df: pd.DataFrame,
) -> pd.DataFrame:
    """Compare database counts and totals with the processed dataset."""

    checks: list[tuple[str, object, object, bool]] = []

    expected_counts = {
        "customers": int(clean_df["customer_id"].nunique()),
        "products": _expected_product_count(clean_df),
        "locations": _expected_location_count(clean_df),
        "orders": int(clean_df["order_id"].nunique()),
        "order_items": int(len(clean_df)),
    }

    for table_name, expected_value in expected_counts.items():
        actual_value = connection.execute(
            f"SELECT COUNT(*) FROM {table_name}"
        ).fetchone()[0]

        checks.append(
            (
                f"{table_name}_row_count",
                expected_value,
                actual_value,
                expected_value == actual_value,
            )
        )

    database_sales, database_profit = connection.execute(
        """
        SELECT
            SUM(sales),
            SUM(profit)
        FROM order_items
        """
    ).fetchone()

    expected_sales = float(clean_df["sales"].sum())
    expected_profit = float(clean_df["profit"].sum())

    checks.append(
        (
            "total_sales",
            expected_sales,
            database_sales,
            abs(expected_sales - float(database_sales)) < 0.01,
        )
    )

    checks.append(
        (
            "total_profit",
            expected_profit,
            database_profit,
            abs(expected_profit - float(database_profit)) < 0.01,
        )
    )

    foreign_key_errors = connection.execute(
        "PRAGMA foreign_key_check;"
    ).fetchall()

    checks.append(
        (
            "foreign_key_errors",
            0,
            len(foreign_key_errors),
            len(foreign_key_errors) == 0,
        )
    )

    view_count = connection.execute(
        """
        SELECT COUNT(*)
        FROM sqlite_master
        WHERE type = 'view'
          AND name IN (
              'vw_order_item_details',
              'vw_order_summary',
              'vw_customer_summary',
              'vw_product_summary'
          )
        """
    ).fetchone()[0]

    checks.append(
        (
            "required_views",
            4,
            view_count,
            view_count == 4,
        )
    )

    return pd.DataFrame(
        checks,
        columns=[
            "check_name",
            "expected_value",
            "actual_value",
            "passed",
        ],
    )


def build_database(
    clean_df: pd.DataFrame,
    database_path: Path | str,
    schema_path: Path | str,
    views_path: Path | str,
) -> pd.DataFrame:
    """Build the complete normalized SQLite database."""

    connection = connect_database(database_path)

    try:
        execute_sql_file(connection, schema_path)

        dimensions = create_dimension_tables(clean_df)

        facts = create_fact_tables(
            clean_df=clean_df,
            locations=dimensions["locations"],
            products=dimensions["products"],
        )

        with connection:
            insert_dataframe(
                connection,
                dimensions["customers"],
                "customers",
            )

            insert_dataframe(
                connection,
                dimensions["products"],
                "products",
            )

            insert_dataframe(
                connection,
                dimensions["locations"],
                "locations",
            )

            insert_dataframe(
                connection,
                facts["orders"],
                "orders",
            )

            insert_dataframe(
                connection,
                facts["order_items"],
                "order_items",
            )

        execute_sql_file(connection, views_path)
        connection.commit()

        validation_df = validate_database(
            connection,
            clean_df,
        )

        if not validation_df["passed"].all():
            failed_checks = validation_df.loc[
                ~validation_df["passed"],
                "check_name",
            ].tolist()

            raise ValueError(
                "Database validation failed: "
                + ", ".join(failed_checks)
            )

        return validation_df

    finally:
        connection.close()
