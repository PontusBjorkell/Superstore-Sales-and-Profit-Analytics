"""Data loading, validation, cleaning, and feature engineering."""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd


REQUIRED_COLUMNS = {
    "Row ID",
    "Order ID",
    "Order Date",
    "Ship Date",
    "Ship Mode",
    "Customer ID",
    "Customer Name",
    "Segment",
    "Country",
    "City",
    "State",
    "Postal Code",
    "Region",
    "Product ID",
    "Category",
    "Sub-Category",
    "Product Name",
    "Sales",
    "Quantity",
    "Discount",
    "Profit",
}


def to_snake_case(column_name: str) -> str:
    """
    Convert a source column name to snake_case.

    Examples
    --------
    >>> to_snake_case("Order Date")
    'order_date'
    >>> to_snake_case("Sub-Category")
    'sub_category'
    """

    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", column_name.strip())
    cleaned = re.sub(r"_+", "_", cleaned)
    return cleaned.strip("_").lower()


def load_raw_data(path: Path | str) -> pd.DataFrame:
    """
    Load the raw Superstore CSV.

    Parameters
    ----------
    path:
        Location of the raw CSV.

    Returns
    -------
    pandas.DataFrame
        Unmodified source data.
    """

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(
            f"Raw data file was not found: {path}\n"
            "Place the source CSV at data/raw/superstore.csv."
        )

    try:
        return pd.read_csv(path, encoding="utf-8")
    except UnicodeDecodeError:
        return pd.read_csv(path, encoding="latin-1")


def validate_required_columns(df: pd.DataFrame) -> None:
    """
    Verify that all expected source columns are present.

    Raises
    ------
    ValueError
        If required columns are missing.
    """

    missing_columns = sorted(REQUIRED_COLUMNS.difference(df.columns))

    if missing_columns:
        raise ValueError(
            "The raw dataset is missing required columns: "
            + ", ".join(missing_columns)
        )


def validate_source_data(df: pd.DataFrame) -> None:
    """
    Validate important structural and numeric assumptions.

    The checks are intentionally conservative. They identify values that
    would make the analytical dataset unreliable rather than rejecting
    legitimate loss-making transactions.
    """

    if df.empty:
        raise ValueError("The raw dataset contains no rows.")

    if df["Row ID"].isna().any():
        raise ValueError("Row ID contains missing values.")

    if df["Row ID"].duplicated().any():
        duplicate_count = int(df["Row ID"].duplicated().sum())
        raise ValueError(
            f"Row ID must be unique. Found {duplicate_count} duplicate IDs."
        )

    numeric_columns = ["Sales", "Quantity", "Discount", "Profit"]

    for column in numeric_columns:
        converted = pd.to_numeric(df[column], errors="coerce")

        if converted.isna().any():
            invalid_count = int(converted.isna().sum())
            raise ValueError(
                f"{column} contains {invalid_count} non-numeric or missing values."
            )

    if (pd.to_numeric(df["Sales"]) < 0).any():
        raise ValueError("Sales contains negative values.")

    if (pd.to_numeric(df["Quantity"]) <= 0).any():
        raise ValueError("Quantity must be greater than zero.")

    discount = pd.to_numeric(df["Discount"])

    if ((discount < 0) | (discount > 1)).any():
        raise ValueError("Discount must be between 0 and 1.")


def clean_superstore_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the source dataset and create reusable analytical features.

    Returns
    -------
    pandas.DataFrame
        A line-item-level analytical table with standardized column names,
        parsed dates, and derived business metrics.
    """

    validate_required_columns(df)
    validate_source_data(df)

    clean = df.copy()

    clean.columns = [to_snake_case(column) for column in clean.columns]

    text_columns = [
        "order_id",
        "ship_mode",
        "customer_id",
        "customer_name",
        "segment",
        "country",
        "city",
        "state",
        "region",
        "product_id",
        "category",
        "sub_category",
        "product_name",
    ]

    for column in text_columns:
        clean[column] = clean[column].astype("string").str.strip()

    clean["order_date"] = pd.to_datetime(
        clean["order_date"],
        errors="raise",
    )

    clean["ship_date"] = pd.to_datetime(
        clean["ship_date"],
        errors="raise",
    )

    clean["row_id"] = pd.to_numeric(clean["row_id"], errors="raise").astype("int64")
    clean["quantity"] = (
        pd.to_numeric(clean["quantity"], errors="raise").astype("int64")
    )
    clean["sales"] = pd.to_numeric(clean["sales"], errors="raise").astype("float64")
    clean["discount"] = (
        pd.to_numeric(clean["discount"], errors="raise").astype("float64")
    )
    clean["profit"] = pd.to_numeric(clean["profit"], errors="raise").astype("float64")

    # Postal codes are identifiers rather than quantities.
    clean["postal_code"] = (
        pd.to_numeric(clean["postal_code"], errors="coerce")
        .astype("Int64")
        .astype("string")
        .str.zfill(5)
    )

    # Operational features
    clean["shipping_days"] = (
        clean["ship_date"] - clean["order_date"]
    ).dt.days.astype("int64")

    if (clean["shipping_days"] < 0).any():
        raise ValueError("Ship Date occurs before Order Date for one or more rows.")

    # Calendar features
    clean["order_year"] = clean["order_date"].dt.year.astype("int64")
    clean["order_quarter"] = (
        "Q" + clean["order_date"].dt.quarter.astype("string")
    )
    clean["order_month"] = clean["order_date"].dt.month.astype("int64")
    clean["order_month_name"] = clean["order_date"].dt.month_name()
    clean["order_year_month"] = clean["order_date"].dt.to_period("M").astype("string")
    clean["order_day_of_week"] = clean["order_date"].dt.day_name()

    # Commercial features
    clean["profit_margin"] = np.where(
        clean["sales"].ne(0),
        clean["profit"] / clean["sales"],
        np.nan,
    )

    clean["unit_sales"] = np.where(
        clean["quantity"].ne(0),
        clean["sales"] / clean["quantity"],
        np.nan,
    )

    clean["unit_profit"] = np.where(
        clean["quantity"].ne(0),
        clean["profit"] / clean["quantity"],
        np.nan,
    )

    clean["is_profitable"] = clean["profit"] > 0
    clean["is_loss"] = clean["profit"] < 0
    clean["is_discounted"] = clean["discount"] > 0

    discount_bins = [-0.001, 0, 0.10, 0.20, 0.30, 0.50, 1.00]
    discount_labels = [
        "No discount",
        "Up to 10%",
        "11–20%",
        "21–30%",
        "31–50%",
        "Over 50%",
    ]

    clean["discount_band"] = pd.cut(
        clean["discount"],
        bins=discount_bins,
        labels=discount_labels,
        include_lowest=True,
    )

    # Preserve the source line-item grain and produce deterministic ordering.
    clean = clean.sort_values("row_id").reset_index(drop=True)

    return clean


def create_data_quality_summary(
    raw_df: pd.DataFrame,
    clean_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Produce a compact data-quality and coverage report.
    """

    metrics = [
        ("raw_rows", len(raw_df)),
        ("clean_rows", len(clean_df)),
        ("raw_columns", raw_df.shape[1]),
        ("clean_columns", clean_df.shape[1]),
        ("duplicate_source_rows", int(raw_df.duplicated().sum())),
        ("missing_source_values", int(raw_df.isna().sum().sum())),
        ("unique_orders", int(clean_df["order_id"].nunique())),
        ("unique_customers", int(clean_df["customer_id"].nunique())),
        ("unique_products", int(clean_df["product_id"].nunique())),
        ("unique_states", int(clean_df["state"].nunique())),
        ("unique_cities", int(clean_df["city"].nunique())),
        ("loss_making_lines", int(clean_df["is_loss"].sum())),
        ("discounted_lines", int(clean_df["is_discounted"].sum())),
        ("minimum_order_date", clean_df["order_date"].min().date().isoformat()),
        ("maximum_order_date", clean_df["order_date"].max().date().isoformat()),
        ("minimum_ship_date", clean_df["ship_date"].min().date().isoformat()),
        ("maximum_ship_date", clean_df["ship_date"].max().date().isoformat()),
    ]

    return pd.DataFrame(metrics, columns=["metric", "value"])


def save_processed_data(
    df: pd.DataFrame,
    output_path: Path | str,
) -> None:
    """Save the cleaned analytical dataset."""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(
        output_path,
        index=False,
        date_format="%Y-%m-%d",
    )