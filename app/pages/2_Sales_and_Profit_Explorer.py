"""Interactive sales and profit explorer."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from utils import (
    build_where_clause,
    configure_page,
    dataframe_download_button,
    format_dataframe,
    load_filter_options,
    render_app_header,
    render_sidebar_status,
    run_query,
)


configure_page(
    page_title="Sales and Profit Explorer",
    page_icon="🔎",
)

render_app_header(
    title="Sales and Profit Explorer",
    subtitle=(
        "Interactively filter transactions and inspect revenue, "
        "profitability, customer, and product patterns."
    ),
)

render_sidebar_status()

date_bounds = run_query(
    """
    SELECT
        MIN(order_date) AS minimum_date,
        MAX(order_date) AS maximum_date
    FROM vw_order_item_details
    """
).iloc[0]

minimum_date = pd.to_datetime(date_bounds["minimum_date"]).date()
maximum_date = pd.to_datetime(date_bounds["maximum_date"]).date()

options = load_filter_options()

with st.sidebar:
    st.markdown("### Filters")

    selected_dates = st.date_input(
        "Order date range",
        value=(minimum_date, maximum_date),
        min_value=minimum_date,
        max_value=maximum_date,
    )

    selected_regions = st.multiselect(
        "Region",
        options["regions"],
    )

    selected_segments = st.multiselect(
        "Segment",
        options["segments"],
    )

    selected_categories = st.multiselect(
        "Category",
        options["categories"],
    )

    selected_sub_categories = st.multiselect(
        "Sub-category",
        options["sub_categories"],
    )

if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
    start_date, end_date = selected_dates
else:
    start_date = end_date = selected_dates

where_clause, params = build_where_clause(
    start_date=str(start_date),
    end_date=str(end_date),
    regions=selected_regions,
    segments=selected_segments,
    categories=selected_categories,
    sub_categories=selected_sub_categories,
)

summary = run_query(
    f"""
    SELECT
        SUM(sales) AS total_sales,
        SUM(profit) AS total_profit,
        100.0 * SUM(profit) / NULLIF(SUM(sales), 0)
            AS profit_margin_pct,
        COUNT(DISTINCT order_id) AS total_orders,
        COUNT(*) AS line_count
    FROM vw_order_item_details
    {where_clause}
    """,
    tuple(params),
).iloc[0]

metric_columns = st.columns(5)

metric_columns[0].metric(
    "Filtered sales",
    f"${summary['total_sales']:,.0f}",
)

metric_columns[1].metric(
    "Filtered profit",
    f"${summary['total_profit']:,.0f}",
)

metric_columns[2].metric(
    "Margin",
    f"{summary['profit_margin_pct']:.2f}%",
)

metric_columns[3].metric(
    "Orders",
    f"{int(summary['total_orders']):,}",
)

metric_columns[4].metric(
    "Line items",
    f"{int(summary['line_count']):,}",
)

monthly = run_query(
    f"""
    SELECT
        order_year_month,
        SUM(sales) AS total_sales,
        SUM(profit) AS total_profit
    FROM vw_order_item_details
    {where_clause}
    GROUP BY order_year_month
    ORDER BY order_year_month
    """,
    tuple(params),
)

category = run_query(
    f"""
    SELECT
        category,
        sub_category,
        SUM(sales) AS total_sales,
        SUM(profit) AS total_profit
    FROM vw_order_item_details
    {where_clause}
    GROUP BY
        category,
        sub_category
    ORDER BY total_sales DESC
    """,
    tuple(params),
)

chart_columns = st.columns(2)

with chart_columns[0]:
    line_figure = px.line(
        monthly,
        x="order_year_month",
        y=["total_sales", "total_profit"],
        markers=True,
        title="Filtered monthly performance",
    )
    st.plotly_chart(
        line_figure,
        use_container_width=True,
    )

with chart_columns[1]:
    bar_figure = px.bar(
        category.head(20),
        x="sub_category",
        y="total_sales",
        color="category",
        title="Sub-category sales",
        hover_data=["total_profit"],
    )
    st.plotly_chart(
        bar_figure,
        use_container_width=True,
    )

st.subheader("Transaction records")

transactions = run_query(
    f"""
    SELECT
        order_date,
        order_id,
        customer_name,
        segment,
        region,
        state,
        category,
        sub_category,
        product_name,
        sales,
        quantity,
        discount,
        profit,
        profit_margin
    FROM vw_order_item_details
    {where_clause}
    ORDER BY order_date DESC, row_id DESC
    LIMIT 5000
    """,
    tuple(params),
)

st.caption(
    "The table is limited to the first 5,000 matching rows for browser performance."
)

st.dataframe(
    format_dataframe(transactions),
    use_container_width=True,
    hide_index=True,
)

dataframe_download_button(
    transactions,
    "filtered_superstore_transactions.csv",
)
