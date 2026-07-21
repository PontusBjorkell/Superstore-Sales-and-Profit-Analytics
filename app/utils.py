"""Shared Streamlit utilities for the Superstore dashboard."""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path
from typing import Iterable

import pandas as pd
import plotly.express as px
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from superstore_analytics.analysis import parse_analysis_catalogue
from superstore_analytics.config import (
    ANALYSIS_SQL_PATH,
    DATABASE_PATH,
)


CURRENCY_COLUMNS = {
    "sales",
    "profit",
    "total_sales",
    "total_profit",
    "average_order_value",
    "unit_sales",
    "unit_profit",
    "metric_value",
}

PERCENT_COLUMNS = {
    "profit_margin_pct",
    "average_discount_pct",
    "loss_making_line_rate_pct",
    "sales_yoy_growth_pct",
    "profit_yoy_growth_pct",
    "order_share_pct",
    "sales_share_pct",
    "cumulative_sales_share_pct",
    "cumulative_positive_profit_share_pct",
    "loss_making_order_rate_pct",
    "discount_pct",
}


def configure_page(
    page_title: str,
    page_icon: str = "📊",
) -> None:
    """Configure a Streamlit page consistently."""

    st.set_page_config(
        page_title=page_title,
        page_icon=page_icon,
        layout="wide",
        initial_sidebar_state="expanded",
    )


def render_app_header(
    title: str,
    subtitle: str,
) -> None:
    """Render a common dashboard header."""

    st.title(title)
    st.caption(subtitle)


def database_exists() -> bool:
    """Return whether the SQLite database exists."""

    return DATABASE_PATH.exists()


def render_sidebar_status() -> None:
    """Display project and database status in the sidebar."""

    st.sidebar.markdown("## Superstore Analytics")
    st.sidebar.caption("SQL + Streamlit business intelligence project")

    if database_exists():
        st.sidebar.success("Database available")
    else:
        st.sidebar.error("Database missing")

    st.sidebar.markdown("---")
    st.sidebar.caption(f"Project root: `{PROJECT_ROOT.name}`")


@st.cache_data(show_spinner=False)
def run_query(
    sql: str,
    params: tuple | dict | None = None,
) -> pd.DataFrame:
    """Run a read-only SQL query against the project database."""

    if not database_exists():
        raise FileNotFoundError(
            f"Database not found: {DATABASE_PATH}"
        )

    connection = sqlite3.connect(
        f"file:{DATABASE_PATH}?mode=ro",
        uri=True,
    )

    try:
        return pd.read_sql_query(
            sql,
            connection,
            params=params,
        )
    finally:
        connection.close()


@st.cache_data(show_spinner=False)
def load_executive_kpis() -> dict[str, float]:
    """Load the core executive KPI row."""

    result = run_query(
        """
        SELECT
            SUM(sales) AS total_sales,
            SUM(profit) AS total_profit,
            100.0 * SUM(profit) / NULLIF(SUM(sales), 0)
                AS profit_margin_pct,
            COUNT(DISTINCT order_id) AS total_orders,
            COUNT(DISTINCT customer_id) AS total_customers
        FROM vw_order_item_details
        """
    )

    return result.iloc[0].to_dict()


@st.cache_data(show_spinner=False)
def load_filter_options() -> dict[str, list[str]]:
    """Load reusable dashboard filter values."""

    result = run_query(
        """
        SELECT DISTINCT
            region,
            segment,
            category,
            sub_category
        FROM vw_order_item_details
        """
    )

    return {
        "regions": sorted(result["region"].dropna().unique().tolist()),
        "segments": sorted(result["segment"].dropna().unique().tolist()),
        "categories": sorted(result["category"].dropna().unique().tolist()),
        "sub_categories": sorted(
            result["sub_category"].dropna().unique().tolist()
        ),
    }


def build_where_clause(
    *,
    start_date: str | None = None,
    end_date: str | None = None,
    regions: Iterable[str] | None = None,
    segments: Iterable[str] | None = None,
    categories: Iterable[str] | None = None,
    sub_categories: Iterable[str] | None = None,
) -> tuple[str, list[object]]:
    """Build a safe SQL WHERE clause and positional parameters."""

    clauses: list[str] = []
    params: list[object] = []

    if start_date is not None:
        clauses.append("order_date >= ?")
        params.append(start_date)

    if end_date is not None:
        clauses.append("order_date <= ?")
        params.append(end_date)

    def add_in_filter(
        column: str,
        values: Iterable[str] | None,
    ) -> None:
        selected = list(values or [])

        if selected:
            placeholders = ", ".join("?" for _ in selected)
            clauses.append(f"{column} IN ({placeholders})")
            params.extend(selected)

    add_in_filter("region", regions)
    add_in_filter("segment", segments)
    add_in_filter("category", categories)
    add_in_filter("sub_category", sub_categories)

    if not clauses:
        return "", params

    return "WHERE " + " AND ".join(clauses), params


def format_dataframe(
    dataframe: pd.DataFrame,
) -> pd.io.formats.style.Styler:
    """Return a readable styled dataframe."""

    formatters: dict[str, str] = {}

    for column in dataframe.columns:
        if column in CURRENCY_COLUMNS:
            formatters[column] = "${:,.2f}"
        elif column in PERCENT_COLUMNS:
            formatters[column] = "{:,.2f}%"
        elif column.endswith("_count") or column.startswith("total_"):
            if pd.api.types.is_numeric_dtype(dataframe[column]):
                formatters[column] = "{:,.0f}"

    return dataframe.style.format(
        formatters,
        na_rep="—",
    )


def dataframe_download_button(
    dataframe: pd.DataFrame,
    filename: str,
    label: str = "Download CSV",
) -> None:
    """Render a CSV download button."""

    st.download_button(
        label=label,
        data=dataframe.to_csv(index=False).encode("utf-8"),
        file_name=filename,
        mime="text/csv",
    )


def render_bar_chart(
    dataframe: pd.DataFrame,
    *,
    x: str,
    y: str,
    title: str,
    orientation: str = "v",
    hover_data: list[str] | None = None,
) -> None:
    """Render a consistent Plotly bar chart."""

    figure = px.bar(
        dataframe,
        x=x,
        y=y,
        orientation=orientation,
        title=title,
        hover_data=hover_data,
    )

    figure.update_layout(
        margin=dict(l=20, r=20, t=60, b=20),
    )

    st.plotly_chart(
        figure,
        use_container_width=True,
    )


def render_line_chart(
    dataframe: pd.DataFrame,
    *,
    x: str,
    y: str | list[str],
    title: str,
) -> None:
    """Render a consistent Plotly line chart."""

    figure = px.line(
        dataframe,
        x=x,
        y=y,
        markers=True,
        title=title,
    )

    figure.update_layout(
        margin=dict(l=20, r=20, t=60, b=20),
    )

    st.plotly_chart(
        figure,
        use_container_width=True,
    )


@st.cache_data(show_spinner=False)
def load_analysis_catalogue():
    """Load the named SQL analytics catalogue."""

    return parse_analysis_catalogue(ANALYSIS_SQL_PATH)
