"""Searchable SQL analytics catalogue page."""

from __future__ import annotations

import streamlit as st

from utils import (
    configure_page,
    dataframe_download_button,
    format_dataframe,
    load_analysis_catalogue,
    render_app_header,
    render_sidebar_status,
    run_query,
)


configure_page(
    page_title="SQL Analytics",
    page_icon="🗄️",
)

render_app_header(
    title="SQL Analytics",
    subtitle=(
        "Browse the complete catalogue of named SQL analyses, inspect "
        "their query text, view result tables, and download outputs."
    ),
)

render_sidebar_status()

analyses = load_analysis_catalogue()

search_term = st.text_input(
    "Search analyses",
    placeholder="Search by title, description, or identifier",
).strip().lower()

filtered = [
    analysis
    for analysis in analyses
    if not search_term
    or search_term in analysis.name.lower()
    or search_term in analysis.title.lower()
    or search_term in analysis.description.lower()
]

if not filtered:
    st.warning("No analyses matched the search term.")
    st.stop()

labels = {
    f"{analysis.name} — {analysis.title}": analysis
    for analysis in filtered
}

selected_label = st.selectbox(
    "Choose an analysis",
    options=list(labels),
)

selected = labels[selected_label]

st.markdown(f"### {selected.title}")
st.caption(selected.description)

with st.expander("View SQL query"):
    st.code(
        selected.sql,
        language="sql",
    )

result = run_query(selected.sql)

metric_columns = st.columns(2)

metric_columns[0].metric(
    "Rows",
    f"{len(result):,}",
)

metric_columns[1].metric(
    "Columns",
    f"{result.shape[1]:,}",
)

st.dataframe(
    format_dataframe(result),
    use_container_width=True,
    hide_index=True,
)

dataframe_download_button(
    result,
    f"{selected.name}.csv",
    label="Download analysis result",
)
