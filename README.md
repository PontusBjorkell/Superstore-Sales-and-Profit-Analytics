# Superstore Sales and Profit Analytics

> **Status:** 🚧 Work in Progress (temporary README). Screenshots,
> deployment link and final polishing will be added in the next
> revision.

## Overview

This repository is an end-to-end **Business Intelligence and Data
Analytics** project built around the Sample Superstore dataset. The
objective is to demonstrate a production-inspired analytics workflow
rather than only exploratory analysis.

The project covers the complete lifecycle from raw data ingestion
through database construction and SQL analytics to an interactive
Streamlit dashboard.

## Highlights

-   Automated preprocessing and validation
-   Feature engineering
-   Normalized SQLite database
-   Analytical SQL views
-   30 reusable SQL analyses
-   Automated CSV exports
-   Interactive multi-page Streamlit dashboard
-   Comprehensive unit tests
-   Professional project structure

## Dataset

The dataset contains approximately:

-   9,994 order line items
-   5,009 orders
-   793 customers
-   1,894 normalized product records
-   632 locations

Business variables include sales, profit, discounts, quantities,
products, customers, categories, geography and shipping.

## Repository Structure

``` text
app/
data/
reports/
scripts/
sql/
src/
tests/
images/
```

## Major Components

### Data Pipeline

-   Raw data validation
-   Cleaning and preprocessing
-   Feature engineering
-   Data quality reporting

### SQLite Warehouse

Normalized schema consisting of:

-   Customers
-   Products
-   Locations
-   Orders
-   Order Items

Includes foreign keys, indexes, analytical views and integrity
validation.

### SQL Analytics

Thirty named SQL analyses covering:

-   Executive KPIs
-   Time trends
-   Categories
-   Products
-   Discounts
-   Customers
-   Geography
-   Shipping
-   Pareto analysis
-   Management summaries

### Streamlit Dashboard

Pages include:

-   Executive Overview
-   Sales & Profit Explorer
-   Products & Discounts
-   Customers & Geography
-   SQL Analytics Browser

## Technologies

Python • Pandas • NumPy • SQLite • SQL • Streamlit • Plotly • Pytest

## Running

``` bash
pip install -r requirements.txt
python scripts/prepare_data.py
python scripts/build_database.py
python scripts/run_analysis.py
streamlit run app/app.py
```

## Current Status

Current implementation includes:

-   Clean preprocessing pipeline
-   Normalized relational database
-   Passing validation checks
-   Passing automated tests
-   SQL analytics catalogue
-   Interactive dashboard

## Planned Improvements

-   Dashboard screenshots
-   Live Streamlit deployment
-   Architecture diagram
-   GitHub Actions CI
-   Additional dashboard enhancements

## License

Educational and portfolio use.
