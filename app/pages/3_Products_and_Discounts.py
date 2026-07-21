"""Product and discount analytics page."""

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
    page_title="Products and Discounts",
    page_icon="🏷️",
)

render_app_header(
    title="Products and Discounts",
    subtitle=(
        "Assess product portfolio strength, margin risk, discount "
        "sensitivity, and cumulative revenue concentration."
    ),
)

render_sidebar_status()

discount = run_query(
    """
    SELECT
        discount_band,
        COUNT(*) AS line_count,
        AVG(discount) * 100 AS average_discount_pct,
        SUM(sales) AS total_sales,
        SUM(profit) AS total_profit,
        100.0 * SUM(profit) / NULLIF(SUM(sales), 0)
            AS profit_margin_pct,
        100.0 * SUM(is_loss) / COUNT(*)
            AS loss_making_line_rate_pct
    FROM vw_order_item_details
    GROUP BY discount_band
    ORDER BY MIN(discount)
    """
)

sub_category = run_query(
    """
    SELECT
        category,
        sub_category,
        SUM(sales) AS total_sales,
        SUM(profit) AS total_profit,
        100.0 * SUM(profit) / NULLIF(SUM(sales), 0)
            AS profit_margin_pct
    FROM vw_order_item_details
    GROUP BY
        category,
        sub_category
    ORDER BY total_profit DESC
    """
)

chart_columns = st.columns(2)

with chart_columns[0]:
    render_bar_chart(
        discount,
        x="discount_band",
        y="profit_margin_pct",
        title="Profit margin by discount band",
        hover_data=[
            "total_sales",
            "total_profit",
            "loss_making_line_rate_pct",
        ],
    )

with chart_columns[1]:
    render_bar_chart(
        sub_category,
        x="sub_category",
        y="total_profit",
        title="Profit by sub-category",
        hover_data=[
            "category",
            "total_sales",
            "profit_margin_pct",
        ],
    )

products = run_query(
    """
    SELECT
        product_key,
        product_id,
        product_name,
        category,
        sub_category,
        total_sales,
        total_profit,
        100.0 * profit_margin AS profit_margin_pct,
        order_count,
        average_discount * 100 AS average_discount_pct,
        loss_making_lines
    FROM vw_product_summary
    ORDER BY total_sales DESC
    """
)

sales_benchmark = products["total_sales"].mean()
profit_benchmark = products["total_profit"].mean()

products["portfolio_quadrant"] = "Low sales / low profit"
products.loc[
    (products["total_sales"] >= sales_benchmark)
    & (products["total_profit"] >= profit_benchmark),
    "portfolio_quadrant",
] = "High sales / high profit"
products.loc[
    (products["total_sales"] >= sales_benchmark)
    & (products["total_profit"] < profit_benchmark),
    "portfolio_quadrant",
] = "High sales / low profit"
products.loc[
    (products["total_sales"] < sales_benchmark)
    & (products["total_profit"] >= profit_benchmark),
    "portfolio_quadrant",
] = "Low sales / high profit"

st.subheader("Product portfolio map")

scatter = px.scatter(
    products,
    x="total_sales",
    y="total_profit",
    color="portfolio_quadrant",
    hover_name="product_name",
    hover_data=[
        "category",
        "sub_category",
        "profit_margin_pct",
        "average_discount_pct",
    ],
    title="Product sales versus profit",
)

scatter.add_vline(
    x=sales_benchmark,
    line_dash="dash",
)

scatter.add_hline(
    y=profit_benchmark,
    line_dash="dash",
)

st.plotly_chart(
    scatter,
    use_container_width=True,
)

tab_top_sales, tab_top_profit, tab_losses = st.tabs(
    [
        "Top by sales",
        "Top by profit",
        "Largest losses",
    ]
)

with tab_top_sales:
    top_sales = products.nlargest(25, "total_sales")
    st.dataframe(
        format_dataframe(top_sales),
        use_container_width=True,
        hide_index=True,
    )
    dataframe_download_button(
        top_sales,
        "top_products_by_sales.csv",
    )

with tab_top_profit:
    top_profit = products.nlargest(25, "total_profit")
    st.dataframe(
        format_dataframe(top_profit),
        use_container_width=True,
        hide_index=True,
    )
    dataframe_download_button(
        top_profit,
        "top_products_by_profit.csv",
    )

with tab_losses:
    losses = products.loc[
        products["total_profit"] < 0
    ].nsmallest(25, "total_profit")

    st.dataframe(
        format_dataframe(losses),
        use_container_width=True,
        hide_index=True,
    )
    dataframe_download_button(
        losses,
        "largest_product_losses.csv",
    )
