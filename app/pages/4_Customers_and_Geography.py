"""Customer and geographic analytics page."""

from __future__ import annotations

import plotly.express as px
import streamlit as st

from utils import (
    configure_page,
    dataframe_download_button,
    format_dataframe,
    render_app_header,
    render_bar_chart,
    render_sidebar_status,
    run_query,
)


configure_page(
    page_title="Customers and Geography",
    page_icon="🌎",
)

render_app_header(
    title="Customers and Geography",
    subtitle=(
        "Compare customer segments, customer value, repeat activity, "
        "regional performance, and state-level profitability."
    ),
)

render_sidebar_status()

segment = run_query(
    """
    SELECT
        segment,
        COUNT(DISTINCT customer_id) AS total_customers,
        COUNT(DISTINCT order_id) AS total_orders,
        SUM(sales) AS total_sales,
        SUM(profit) AS total_profit,
        100.0 * SUM(profit) / NULLIF(SUM(sales), 0)
            AS profit_margin_pct,
        SUM(sales) / COUNT(DISTINCT order_id)
            AS average_order_value
    FROM vw_order_item_details
    GROUP BY segment
    ORDER BY total_sales DESC
    """
)

region = run_query(
    """
    SELECT
        region,
        COUNT(DISTINCT customer_id) AS total_customers,
        COUNT(DISTINCT order_id) AS total_orders,
        SUM(sales) AS total_sales,
        SUM(profit) AS total_profit,
        100.0 * SUM(profit) / NULLIF(SUM(sales), 0)
            AS profit_margin_pct
    FROM vw_order_item_details
    GROUP BY region
    ORDER BY total_sales DESC
    """
)

chart_columns = st.columns(2)

with chart_columns[0]:
    render_bar_chart(
        segment,
        x="segment",
        y="total_profit",
        title="Profit by customer segment",
        hover_data=[
            "total_sales",
            "profit_margin_pct",
            "average_order_value",
        ],
    )

with chart_columns[1]:
    render_bar_chart(
        region,
        x="region",
        y="total_profit",
        title="Profit by region",
        hover_data=[
            "total_sales",
            "profit_margin_pct",
            "total_customers",
        ],
    )

state = run_query(
    """
    SELECT
        state,
        region,
        COUNT(DISTINCT customer_id) AS total_customers,
        COUNT(DISTINCT order_id) AS total_orders,
        SUM(sales) AS total_sales,
        SUM(profit) AS total_profit,
        100.0 * SUM(profit) / NULLIF(SUM(sales), 0)
            AS profit_margin_pct,
        AVG(discount) * 100 AS average_discount_pct
    FROM vw_order_item_details
    GROUP BY
        state,
        region
    ORDER BY total_profit DESC
    """
)

st.subheader("State profitability")

state_figure = px.bar(
    state.sort_values("total_profit"),
    x="total_profit",
    y="state",
    color="region",
    orientation="h",
    title="Profit by state",
    hover_data=[
        "total_sales",
        "profit_margin_pct",
        "average_discount_pct",
    ],
    height=900,
)

st.plotly_chart(
    state_figure,
    use_container_width=True,
)

customers = run_query(
    """
    SELECT
        customer_id,
        customer_name,
        segment,
        order_count,
        total_sales,
        total_profit,
        100.0 * profit_margin AS profit_margin_pct,
        average_order_value,
        first_order_date,
        last_order_date
    FROM vw_customer_summary
    ORDER BY total_sales DESC
    """
)

tab_sales, tab_profit, tab_risk = st.tabs(
    [
        "Top customers by sales",
        "Top customers by profit",
        "High-value loss customers",
    ]
)

with tab_sales:
    top_sales = customers.nlargest(25, "total_sales")
    st.dataframe(
        format_dataframe(top_sales),
        use_container_width=True,
        hide_index=True,
    )
    dataframe_download_button(
        top_sales,
        "top_customers_by_sales.csv",
    )

with tab_profit:
    top_profit = customers.nlargest(25, "total_profit")
    st.dataframe(
        format_dataframe(top_profit),
        use_container_width=True,
        hide_index=True,
    )
    dataframe_download_button(
        top_profit,
        "top_customers_by_profit.csv",
    )

with tab_risk:
    average_sales = customers["total_sales"].mean()
    risk = customers.loc[
        (customers["total_sales"] >= average_sales)
        & (customers["total_profit"] < 0)
    ].sort_values("total_sales", ascending=False)

    st.dataframe(
        format_dataframe(risk),
        use_container_width=True,
        hide_index=True,
    )
    dataframe_download_button(
        risk,
        "unprofitable_high_value_customers.csv",
    )
