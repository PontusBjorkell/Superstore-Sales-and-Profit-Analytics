"""Tests for Superstore data preparation."""

import pandas as pd
import pytest

from superstore_analytics.data import (
    clean_superstore_data,
    create_data_quality_summary,
    to_snake_case,
)


@pytest.fixture
def sample_raw_data() -> pd.DataFrame:
    """Create a small valid source-format dataset."""

    return pd.DataFrame(
        {
            "Row ID": [1, 2],
            "Order ID": ["CA-2017-100001", "CA-2017-100002"],
            "Order Date": ["1/1/2017", "1/2/2017"],
            "Ship Date": ["1/4/2017", "1/5/2017"],
            "Ship Mode": ["Second Class", "Standard Class"],
            "Customer ID": ["AB-10001", "CD-10002"],
            "Customer Name": ["Alice Brown", "Chris Doe"],
            "Segment": ["Consumer", "Corporate"],
            "Country": ["United States", "United States"],
            "City": ["New York City", "Chicago"],
            "State": ["New York", "Illinois"],
            "Postal Code": [10001, 60601],
            "Region": ["East", "Central"],
            "Product ID": ["OFF-PA-100001", "TEC-PH-100002"],
            "Category": ["Office Supplies", "Technology"],
            "Sub-Category": ["Paper", "Phones"],
            "Product Name": ["Paper Product", "Phone Product"],
            "Sales": [100.0, 200.0],
            "Quantity": [2, 1],
            "Discount": [0.0, 0.2],
            "Profit": [20.0, -10.0],
        }
    )


def test_to_snake_case() -> None:
    assert to_snake_case("Order Date") == "order_date"
    assert to_snake_case("Sub-Category") == "sub_category"
    assert to_snake_case(" Customer Name ") == "customer_name"


def test_clean_data_preserves_row_count(sample_raw_data: pd.DataFrame) -> None:
    result = clean_superstore_data(sample_raw_data)

    assert len(result) == len(sample_raw_data)


def test_clean_data_creates_expected_features(
    sample_raw_data: pd.DataFrame,
) -> None:
    result = clean_superstore_data(sample_raw_data)

    expected_columns = {
        "shipping_days",
        "order_year",
        "order_quarter",
        "order_month",
        "order_month_name",
        "order_year_month",
        "order_day_of_week",
        "profit_margin",
        "unit_sales",
        "unit_profit",
        "is_profitable",
        "is_loss",
        "is_discounted",
        "discount_band",
    }

    assert expected_columns.issubset(result.columns)


def test_shipping_days_are_calculated_correctly(
    sample_raw_data: pd.DataFrame,
) -> None:
    result = clean_superstore_data(sample_raw_data)

    assert result["shipping_days"].tolist() == [3, 3]


def test_profitability_flags(
    sample_raw_data: pd.DataFrame,
) -> None:
    result = clean_superstore_data(sample_raw_data)

    assert result["is_profitable"].tolist() == [True, False]
    assert result["is_loss"].tolist() == [False, True]


def test_profit_margin_is_calculated_correctly(
    sample_raw_data: pd.DataFrame,
) -> None:
    result = clean_superstore_data(sample_raw_data)

    assert result.loc[0, "profit_margin"] == pytest.approx(0.20)
    assert result.loc[1, "profit_margin"] == pytest.approx(-0.05)


def test_invalid_discount_raises_error(
    sample_raw_data: pd.DataFrame,
) -> None:
    sample_raw_data.loc[0, "Discount"] = 1.5

    with pytest.raises(ValueError, match="Discount must be between 0 and 1"):
        clean_superstore_data(sample_raw_data)


def test_duplicate_row_id_raises_error(
    sample_raw_data: pd.DataFrame,
) -> None:
    sample_raw_data.loc[1, "Row ID"] = 1

    with pytest.raises(ValueError, match="Row ID must be unique"):
        clean_superstore_data(sample_raw_data)


def test_quality_summary_contains_core_metrics(
    sample_raw_data: pd.DataFrame,
) -> None:
    clean = clean_superstore_data(sample_raw_data)
    summary = create_data_quality_summary(sample_raw_data, clean)

    metric_names = set(summary["metric"])

    assert "raw_rows" in metric_names
    assert "unique_orders" in metric_names
    assert "loss_making_lines" in metric_names