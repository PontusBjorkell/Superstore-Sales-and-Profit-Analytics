"""Main entry point for the Superstore Streamlit application."""

from __future__ import annotations

import streamlit as st

from utils import (
    configure_page,
    database_exists,
    load_executive_kpis,
    render_app_header,
    render_sidebar_status,
)


configure_page(
    page_title="Superstore Sales and Profit Analytics",
    page_icon="📊",
)

render_app_header(
    title="Superstore Sales and Profit Analytics",
    subtitle=(
        "Business intelligence dashboard for revenue, profitability, "
        "customers, products, discounts, geography, and operations."
    ),
)

render_sidebar_status()

if not database_exists():
    st.error(
        "The SQLite database was not found. Run "
        "`python scripts/build_database.py` before launching the dashboard."
    )
    st.stop()

kpis = load_executive_kpis()

columns = st.columns(5)

columns[0].metric(
    "Total sales",
    f"${kpis['total_sales']:,.0f}",
)

columns[1].metric(
    "Total profit",
    f"${kpis['total_profit']:,.0f}",
)

columns[2].metric(
    "Profit margin",
    f"{kpis['profit_margin_pct']:.2f}%",
)

columns[3].metric(
    "Orders",
    f"{int(kpis['total_orders']):,}",
)

columns[4].metric(
    "Customers",
    f"{int(kpis['total_customers']):,}",
)

st.markdown("---")

st.subheader("Dashboard sections")

section_columns = st.columns(2)

with section_columns[0]:
    st.markdown(
        """
        ### Executive Overview
        Review core KPIs, long-term performance, seasonal patterns,
        category results, and management priorities.

        ### Sales and Profit Explorer
        Filter the transaction data by date, geography, segment,
        category, and sub-category.
        """
    )

with section_columns[1]:
    st.markdown(
        """
        ### Products and Discounts
        Identify profitable products, loss-making items, discount risk,
        and product portfolio quadrants.

        ### Customers and Geography
        Compare customer segments, customer value, regions, states,
        and cities.

        ### SQL Analytics
        Browse and download the complete named SQL analysis catalogue.
        """
    )

st.info(
    "Use the page navigation in the sidebar to open each analytical section."
)
