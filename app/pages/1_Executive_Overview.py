"""Executive overview page."""

from __future__ import annotations

import streamlit as st

from utils import (
    configure_page,
    dataframe_download_button,
    format_dataframe,
    load_executive_kpis,
    render_app_header,
    render_bar_chart,
    render_line_chart,
    render_sidebar_status,
    run_query,
)


configure_page(
    page_title="Executive Overview",
    page_icon="📈",
)

render_app_header(
    title="Executive Overview",
    subtitle=(
        "High-level view of commercial performance, growth, "
        "profitability, seasonality, and management priorities."
    ),
)

render_sidebar_status()

kpis = load_executive_kpis()

kpi_columns = st.columns(5)

kpi_columns[0].metric(
    "Total sales",
    f"${kpis['total_sales']:,.0f}",
)

kpi_columns[1].metric(
    "Total profit",
    f"${kpis['total_profit']:,.0f}",
)

kpi_columns[2].metric(
    "Profit margin",
    f"{kpis['profit_margin_pct']:.2f}%",
)

kpi_columns[3].metric(
    "Orders",
    f"{int(kpis['total_orders']):,}",
)

kpi_columns[4].metric(
    "Customers",
    f"{int(kpis['total_customers']):,}",
)

st.markdown("---")

annual = run_query(
    """
    SELECT
        order_year,
        ROUND(SUM(sales), 2) AS total_sales,
        ROUND(SUM(profit), 2) AS total_profit,
        ROUND(
            100.0 * SUM(profit) / NULLIF(SUM(sales), 0),
            2
        ) AS profit_margin_pct
    FROM vw_order_item_details
    GROUP BY order_year
    ORDER BY order_year
    """
)

monthly = run_query(
    """
    SELECT
        order_year_month,
        ROUND(SUM(sales), 2) AS total_sales,
        ROUND(SUM(profit), 2) AS total_profit
    FROM vw_order_item_details
    GROUP BY order_year_month
    ORDER BY order_year_month
    """
)

chart_columns = st.columns(2)

with chart_columns[0]:
    render_line_chart(
        annual,
        x="order_year",
        y=["total_sales", "total_profit"],
        title="Annual sales and profit",
    )

with chart_columns[1]:
    render_line_chart(
        monthly,
        x="order_year_month",
        y="total_sales",
        title="Monthly sales trend",
    )

category = run_query(
    """
    SELECT
        category,
        ROUND(SUM(sales), 2) AS total_sales,
        ROUND(SUM(profit), 2) AS total_profit,
        ROUND(
            100.0 * SUM(profit) / NULLIF(SUM(sales), 0),
            2
        ) AS profit_margin_pct
    FROM vw_order_item_details
    GROUP BY category
    ORDER BY total_sales DESC
    """
)

region = run_query(
    """
    SELECT
        region,
        ROUND(SUM(sales), 2) AS total_sales,
        ROUND(SUM(profit), 2) AS total_profit,
        ROUND(
            100.0 * SUM(profit) / NULLIF(SUM(sales), 0),
            2
        ) AS profit_margin_pct
    FROM vw_order_item_details
    GROUP BY region
    ORDER BY total_sales DESC
    """
)

chart_columns = st.columns(2)

with chart_columns[0]:
    render_bar_chart(
        category,
        x="category",
        y="total_profit",
        title="Profit by category",
        hover_data=["total_sales", "profit_margin_pct"],
    )

with chart_columns[1]:
    render_bar_chart(
        region,
        x="region",
        y="total_profit",
        title="Profit by region",
        hover_data=["total_sales", "profit_margin_pct"],
    )

st.subheader("Management attention summary")

attention = run_query(
    """
    WITH highest_sales_category AS (
        SELECT
            'Highest-sales category' AS indicator,
            category AS finding,
            ROUND(SUM(sales), 2) AS metric_value,
            'USD sales' AS metric_unit
        FROM vw_order_item_details
        GROUP BY category
        ORDER BY SUM(sales) DESC
        LIMIT 1
    ),
    most_profitable_sub_category AS (
        SELECT
            'Most-profitable sub-category' AS indicator,
            sub_category AS finding,
            ROUND(SUM(profit), 2) AS metric_value,
            'USD profit' AS metric_unit
        FROM vw_order_item_details
        GROUP BY sub_category
        ORDER BY SUM(profit) DESC
        LIMIT 1
    ),
    largest_loss_sub_category AS (
        SELECT
            'Largest-loss sub-category' AS indicator,
            sub_category AS finding,
            ROUND(SUM(profit), 2) AS metric_value,
            'USD profit' AS metric_unit
        FROM vw_order_item_details
        GROUP BY sub_category
        ORDER BY SUM(profit) ASC
        LIMIT 1
    ),
    strongest_region AS (
        SELECT
            'Most-profitable region' AS indicator,
            region AS finding,
            ROUND(SUM(profit), 2) AS metric_value,
            'USD profit' AS metric_unit
        FROM vw_order_item_details
        GROUP BY region
        ORDER BY SUM(profit) DESC
        LIMIT 1
    )
    SELECT * FROM highest_sales_category
    UNION ALL
    SELECT * FROM most_profitable_sub_category
    UNION ALL
    SELECT * FROM largest_loss_sub_category
    UNION ALL
    SELECT * FROM strongest_region
    """
)

st.dataframe(
    format_dataframe(attention),
    use_container_width=True,
    hide_index=True,
)

dataframe_download_button(
    attention,
    "management_attention_summary.csv",
)
