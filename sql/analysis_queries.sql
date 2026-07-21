-- name: 01_executive_kpi_summary
-- title: Executive KPI Summary
-- description: Overall revenue, profit, margin, order, customer, product, quantity, and discount performance.
SELECT
    ROUND(SUM(sales), 2) AS total_sales,
    ROUND(SUM(profit), 2) AS total_profit,
    ROUND(
        100.0 * SUM(profit) / NULLIF(SUM(sales), 0),
        2
    ) AS profit_margin_pct,
    COUNT(DISTINCT order_id) AS total_orders,
    COUNT(DISTINCT customer_id) AS total_customers,
    COUNT(DISTINCT product_key) AS total_products,
    SUM(quantity) AS units_sold,
    ROUND(
        SUM(sales) / COUNT(DISTINCT order_id),
        2
    ) AS average_order_value,
    ROUND(AVG(discount) * 100, 2) AS average_line_discount_pct,
    ROUND(
        100.0 * SUM(is_loss) / COUNT(*),
        2
    ) AS loss_making_line_rate_pct
FROM vw_order_item_details;


-- name: 02_annual_performance
-- title: Annual Sales and Profit Performance
-- description: Annual revenue, profit, margin, order volume, customer reach, and year-over-year growth.
WITH annual AS (
    SELECT
        order_year,
        SUM(sales) AS total_sales,
        SUM(profit) AS total_profit,
        COUNT(DISTINCT order_id) AS total_orders,
        COUNT(DISTINCT customer_id) AS total_customers
    FROM vw_order_item_details
    GROUP BY order_year
),
with_prior AS (
    SELECT
        *,
        LAG(total_sales) OVER (ORDER BY order_year) AS prior_sales,
        LAG(total_profit) OVER (ORDER BY order_year) AS prior_profit
    FROM annual
)
SELECT
    order_year,
    ROUND(total_sales, 2) AS total_sales,
    ROUND(total_profit, 2) AS total_profit,
    ROUND(
        100.0 * total_profit / NULLIF(total_sales, 0),
        2
    ) AS profit_margin_pct,
    total_orders,
    total_customers,
    ROUND(
        100.0 * (total_sales - prior_sales) / NULLIF(prior_sales, 0),
        2
    ) AS sales_yoy_growth_pct,
    ROUND(
        100.0 * (total_profit - prior_profit) / NULLIF(ABS(prior_profit), 0),
        2
    ) AS profit_yoy_growth_pct
FROM with_prior
ORDER BY order_year;


-- name: 03_monthly_performance_trend
-- title: Monthly Sales and Profit Trend
-- description: Monthly business performance with revenue, profit, margin, orders, and a three-month moving average.
WITH monthly AS (
    SELECT
        order_year_month,
        SUM(sales) AS total_sales,
        SUM(profit) AS total_profit,
        COUNT(DISTINCT order_id) AS total_orders
    FROM vw_order_item_details
    GROUP BY order_year_month
)
SELECT
    order_year_month,
    ROUND(total_sales, 2) AS total_sales,
    ROUND(total_profit, 2) AS total_profit,
    ROUND(
        100.0 * total_profit / NULLIF(total_sales, 0),
        2
    ) AS profit_margin_pct,
    total_orders,
    ROUND(
        AVG(total_sales) OVER (
            ORDER BY order_year_month
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ),
        2
    ) AS sales_3_month_moving_average
FROM monthly
ORDER BY order_year_month;


-- name: 04_quarterly_performance
-- title: Quarterly Performance
-- description: Sales, profit, margin, and order volume for every year-quarter combination.
SELECT
    order_year,
    order_quarter,
    ROUND(SUM(sales), 2) AS total_sales,
    ROUND(SUM(profit), 2) AS total_profit,
    ROUND(
        100.0 * SUM(profit) / NULLIF(SUM(sales), 0),
        2
    ) AS profit_margin_pct,
    COUNT(DISTINCT order_id) AS total_orders,
    SUM(quantity) AS units_sold
FROM vw_order_item_details
GROUP BY
    order_year,
    order_quarter
ORDER BY
    order_year,
    order_quarter;


-- name: 05_month_of_year_seasonality
-- title: Month-of-Year Seasonality
-- description: Aggregated seasonal performance across all years for each calendar month.
SELECT
    order_month,
    CASE order_month
        WHEN 1 THEN 'January'
        WHEN 2 THEN 'February'
        WHEN 3 THEN 'March'
        WHEN 4 THEN 'April'
        WHEN 5 THEN 'May'
        WHEN 6 THEN 'June'
        WHEN 7 THEN 'July'
        WHEN 8 THEN 'August'
        WHEN 9 THEN 'September'
        WHEN 10 THEN 'October'
        WHEN 11 THEN 'November'
        WHEN 12 THEN 'December'
    END AS month_name,
    ROUND(SUM(sales), 2) AS total_sales,
    ROUND(SUM(profit), 2) AS total_profit,
    ROUND(
        100.0 * SUM(profit) / NULLIF(SUM(sales), 0),
        2
    ) AS profit_margin_pct,
    COUNT(DISTINCT order_id) AS total_orders
FROM vw_order_item_details
GROUP BY order_month
ORDER BY order_month;


-- name: 06_category_performance
-- title: Category Performance
-- description: Revenue, profit, margin, order penetration, quantity, and discount performance by category.
SELECT
    category,
    ROUND(SUM(sales), 2) AS total_sales,
    ROUND(SUM(profit), 2) AS total_profit,
    ROUND(
        100.0 * SUM(profit) / NULLIF(SUM(sales), 0),
        2
    ) AS profit_margin_pct,
    COUNT(DISTINCT order_id) AS total_orders,
    SUM(quantity) AS units_sold,
    ROUND(AVG(discount) * 100, 2) AS average_discount_pct,
    ROUND(
        100.0 * SUM(is_loss) / COUNT(*),
        2
    ) AS loss_making_line_rate_pct
FROM vw_order_item_details
GROUP BY category
ORDER BY total_sales DESC;


-- name: 07_sub_category_performance
-- title: Sub-Category Performance
-- description: Detailed ranking of sub-categories by sales, profit, margin, order count, and loss frequency.
SELECT
    category,
    sub_category,
    ROUND(SUM(sales), 2) AS total_sales,
    ROUND(SUM(profit), 2) AS total_profit,
    ROUND(
        100.0 * SUM(profit) / NULLIF(SUM(sales), 0),
        2
    ) AS profit_margin_pct,
    COUNT(DISTINCT order_id) AS total_orders,
    SUM(quantity) AS units_sold,
    ROUND(AVG(discount) * 100, 2) AS average_discount_pct,
    SUM(is_loss) AS loss_making_lines,
    ROUND(
        100.0 * SUM(is_loss) / COUNT(*),
        2
    ) AS loss_making_line_rate_pct
FROM vw_order_item_details
GROUP BY
    category,
    sub_category
ORDER BY total_profit DESC;


-- name: 08_product_portfolio_quadrants
-- title: Product Portfolio Quadrants
-- description: Classifies product records into high or low sales and profit groups relative to portfolio averages.
WITH product_metrics AS (
    SELECT
        product_key,
        product_id,
        product_name,
        category,
        sub_category,
        total_sales,
        total_profit,
        profit_margin,
        order_count
    FROM vw_product_summary
),
benchmarks AS (
    SELECT
        AVG(total_sales) AS average_product_sales,
        AVG(total_profit) AS average_product_profit
    FROM product_metrics
)
SELECT
    pm.product_key,
    pm.product_id,
    pm.product_name,
    pm.category,
    pm.sub_category,
    pm.total_sales,
    pm.total_profit,
    ROUND(pm.profit_margin * 100, 2) AS profit_margin_pct,
    pm.order_count,
    CASE
        WHEN pm.total_sales >= b.average_product_sales
         AND pm.total_profit >= b.average_product_profit
            THEN 'High sales / high profit'
        WHEN pm.total_sales >= b.average_product_sales
         AND pm.total_profit < b.average_product_profit
            THEN 'High sales / low profit'
        WHEN pm.total_sales < b.average_product_sales
         AND pm.total_profit >= b.average_product_profit
            THEN 'Low sales / high profit'
        ELSE 'Low sales / low profit'
    END AS portfolio_quadrant
FROM product_metrics AS pm
CROSS JOIN benchmarks AS b
ORDER BY
    pm.total_sales DESC;


-- name: 09_top_products_by_sales
-- title: Top Products by Sales
-- description: The twenty product records generating the most revenue, with corresponding profit and margin.
SELECT
    product_key,
    product_id,
    product_name,
    category,
    sub_category,
    total_sales,
    total_profit,
    ROUND(profit_margin * 100, 2) AS profit_margin_pct,
    order_count,
    total_quantity
FROM vw_product_summary
ORDER BY total_sales DESC
LIMIT 20;


-- name: 10_top_products_by_profit
-- title: Top Products by Profit
-- description: The twenty product records generating the highest total profit.
SELECT
    product_key,
    product_id,
    product_name,
    category,
    sub_category,
    total_sales,
    total_profit,
    ROUND(profit_margin * 100, 2) AS profit_margin_pct,
    order_count,
    total_quantity
FROM vw_product_summary
ORDER BY total_profit DESC
LIMIT 20;


-- name: 11_largest_product_losses
-- title: Largest Product Losses
-- description: The twenty product records with the most negative cumulative profit.
SELECT
    product_key,
    product_id,
    product_name,
    category,
    sub_category,
    total_sales,
    total_profit,
    ROUND(profit_margin * 100, 2) AS profit_margin_pct,
    average_discount,
    loss_making_lines
FROM vw_product_summary
WHERE total_profit < 0
ORDER BY total_profit ASC
LIMIT 20;


-- name: 12_product_sales_pareto
-- title: Product Sales Pareto Analysis
-- description: Ranks products by revenue and calculates cumulative contribution to total sales.
WITH ranked AS (
    SELECT
        product_key,
        product_id,
        product_name,
        category,
        sub_category,
        total_sales,
        total_profit,
        ROW_NUMBER() OVER (
            ORDER BY total_sales DESC
        ) AS sales_rank,
        SUM(total_sales) OVER (
            ORDER BY total_sales DESC
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS cumulative_sales,
        SUM(total_sales) OVER () AS portfolio_sales
    FROM vw_product_summary
)
SELECT
    product_key,
    product_id,
    product_name,
    category,
    sub_category,
    sales_rank,
    total_sales,
    total_profit,
    ROUND(
        100.0 * total_sales / NULLIF(portfolio_sales, 0),
        3
    ) AS sales_share_pct,
    ROUND(
        100.0 * cumulative_sales / NULLIF(portfolio_sales, 0),
        2
    ) AS cumulative_sales_share_pct,
    CASE
        WHEN cumulative_sales <= portfolio_sales * 0.80
            THEN 'Core revenue products'
        ELSE 'Long-tail products'
    END AS pareto_group
FROM ranked
ORDER BY sales_rank;


-- name: 13_discount_band_performance
-- title: Discount Band Performance
-- description: Measures sales, profit, margin, and loss frequency across discount ranges.
SELECT
    discount_band,
    COUNT(*) AS line_count,
    COUNT(DISTINCT order_id) AS total_orders,
    ROUND(AVG(discount) * 100, 2) AS average_discount_pct,
    ROUND(SUM(sales), 2) AS total_sales,
    ROUND(SUM(profit), 2) AS total_profit,
    ROUND(
        100.0 * SUM(profit) / NULLIF(SUM(sales), 0),
        2
    ) AS profit_margin_pct,
    SUM(is_loss) AS loss_making_lines,
    ROUND(
        100.0 * SUM(is_loss) / COUNT(*),
        2
    ) AS loss_making_line_rate_pct
FROM vw_order_item_details
GROUP BY discount_band
ORDER BY MIN(discount);


-- name: 14_discount_performance_by_category
-- title: Discount Performance by Category
-- description: Shows how discount bands affect profitability within each product category.
SELECT
    category,
    discount_band,
    COUNT(*) AS line_count,
    ROUND(AVG(discount) * 100, 2) AS average_discount_pct,
    ROUND(SUM(sales), 2) AS total_sales,
    ROUND(SUM(profit), 2) AS total_profit,
    ROUND(
        100.0 * SUM(profit) / NULLIF(SUM(sales), 0),
        2
    ) AS profit_margin_pct,
    ROUND(
        100.0 * SUM(is_loss) / COUNT(*),
        2
    ) AS loss_making_line_rate_pct
FROM vw_order_item_details
GROUP BY
    category,
    discount_band
ORDER BY
    category,
    MIN(discount);


-- name: 15_discounted_vs_full_price
-- title: Discounted Versus Full-Price Performance
-- description: Compares commercial performance between discounted and non-discounted line items.
SELECT
    CASE
        WHEN is_discounted = 1 THEN 'Discounted'
        ELSE 'Full price'
    END AS pricing_group,
    COUNT(*) AS line_count,
    COUNT(DISTINCT order_id) AS total_orders,
    ROUND(SUM(sales), 2) AS total_sales,
    ROUND(SUM(profit), 2) AS total_profit,
    ROUND(
        100.0 * SUM(profit) / NULLIF(SUM(sales), 0),
        2
    ) AS profit_margin_pct,
    ROUND(AVG(discount) * 100, 2) AS average_discount_pct,
    ROUND(
        100.0 * SUM(is_loss) / COUNT(*),
        2
    ) AS loss_making_line_rate_pct
FROM vw_order_item_details
GROUP BY is_discounted
ORDER BY is_discounted;


-- name: 16_high_sales_loss_making_lines
-- title: High-Sales Loss-Making Lines
-- description: Identifies large revenue transactions that nevertheless generated losses.
SELECT
    row_id,
    order_id,
    order_date,
    customer_name,
    segment,
    region,
    state,
    product_name,
    category,
    sub_category,
    sales,
    quantity,
    ROUND(discount * 100, 2) AS discount_pct,
    profit,
    ROUND(profit_margin * 100, 2) AS profit_margin_pct
FROM vw_order_item_details
WHERE profit < 0
ORDER BY sales DESC
LIMIT 50;


-- name: 17_segment_performance
-- title: Customer Segment Performance
-- description: Revenue, profit, margin, customer count, order count, and average order value by customer segment.
SELECT
    segment,
    COUNT(DISTINCT customer_id) AS total_customers,
    COUNT(DISTINCT order_id) AS total_orders,
    ROUND(SUM(sales), 2) AS total_sales,
    ROUND(SUM(profit), 2) AS total_profit,
    ROUND(
        100.0 * SUM(profit) / NULLIF(SUM(sales), 0),
        2
    ) AS profit_margin_pct,
    ROUND(
        SUM(sales) / COUNT(DISTINCT order_id),
        2
    ) AS average_order_value,
    ROUND(AVG(discount) * 100, 2) AS average_discount_pct
FROM vw_order_item_details
GROUP BY segment
ORDER BY total_sales DESC;


-- name: 18_top_customers_by_sales
-- title: Top Customers by Sales
-- description: The twenty customers with the greatest cumulative revenue and their profitability.
SELECT
    customer_id,
    customer_name,
    segment,
    order_count,
    total_sales,
    total_profit,
    ROUND(profit_margin * 100, 2) AS profit_margin_pct,
    average_order_value,
    first_order_date,
    last_order_date
FROM vw_customer_summary
ORDER BY total_sales DESC
LIMIT 20;


-- name: 19_top_customers_by_profit
-- title: Top Customers by Profit
-- description: The twenty customers generating the highest total profit.
SELECT
    customer_id,
    customer_name,
    segment,
    order_count,
    total_sales,
    total_profit,
    ROUND(profit_margin * 100, 2) AS profit_margin_pct,
    average_order_value,
    first_order_date,
    last_order_date
FROM vw_customer_summary
ORDER BY total_profit DESC
LIMIT 20;


-- name: 20_unprofitable_high_value_customers
-- title: Unprofitable High-Value Customers
-- description: Customers with above-average sales but negative cumulative profit.
WITH benchmark AS (
    SELECT AVG(total_sales) AS average_customer_sales
    FROM vw_customer_summary
)
SELECT
    cs.customer_id,
    cs.customer_name,
    cs.segment,
    cs.order_count,
    cs.total_sales,
    cs.total_profit,
    ROUND(cs.profit_margin * 100, 2) AS profit_margin_pct,
    cs.average_order_value,
    cs.first_order_date,
    cs.last_order_date
FROM vw_customer_summary AS cs
CROSS JOIN benchmark AS b
WHERE cs.total_sales >= b.average_customer_sales
  AND cs.total_profit < 0
ORDER BY cs.total_sales DESC;


-- name: 21_customer_frequency_groups
-- title: Customer Purchase Frequency Groups
-- description: Segments customers by lifetime order frequency and summarizes value and profitability.
WITH grouped AS (
    SELECT
        *,
        CASE
            WHEN order_count = 1 THEN 'One-time'
            WHEN order_count BETWEEN 2 AND 4 THEN 'Occasional'
            WHEN order_count BETWEEN 5 AND 8 THEN 'Repeat'
            ELSE 'Frequent'
        END AS frequency_group
    FROM vw_customer_summary
)
SELECT
    frequency_group,
    COUNT(*) AS total_customers,
    ROUND(AVG(order_count), 2) AS average_orders_per_customer,
    ROUND(SUM(total_sales), 2) AS total_sales,
    ROUND(SUM(total_profit), 2) AS total_profit,
    ROUND(
        100.0 * SUM(total_profit) / NULLIF(SUM(total_sales), 0),
        2
    ) AS profit_margin_pct,
    ROUND(AVG(average_order_value), 2) AS average_order_value
FROM grouped
GROUP BY frequency_group
ORDER BY
    CASE frequency_group
        WHEN 'One-time' THEN 1
        WHEN 'Occasional' THEN 2
        WHEN 'Repeat' THEN 3
        WHEN 'Frequent' THEN 4
    END;


-- name: 22_regional_performance
-- title: Regional Performance
-- description: Revenue, profit, margin, order activity, customer reach, and discounting by region.
SELECT
    region,
    COUNT(DISTINCT state) AS total_states,
    COUNT(DISTINCT customer_id) AS total_customers,
    COUNT(DISTINCT order_id) AS total_orders,
    ROUND(SUM(sales), 2) AS total_sales,
    ROUND(SUM(profit), 2) AS total_profit,
    ROUND(
        100.0 * SUM(profit) / NULLIF(SUM(sales), 0),
        2
    ) AS profit_margin_pct,
    ROUND(AVG(discount) * 100, 2) AS average_discount_pct,
    ROUND(
        SUM(sales) / COUNT(DISTINCT order_id),
        2
    ) AS average_order_value
FROM vw_order_item_details
GROUP BY region
ORDER BY total_sales DESC;


-- name: 23_state_performance
-- title: State Performance Ranking
-- description: State-level sales, profit, margin, customers, orders, and loss frequency.
SELECT
    state,
    region,
    COUNT(DISTINCT customer_id) AS total_customers,
    COUNT(DISTINCT order_id) AS total_orders,
    ROUND(SUM(sales), 2) AS total_sales,
    ROUND(SUM(profit), 2) AS total_profit,
    ROUND(
        100.0 * SUM(profit) / NULLIF(SUM(sales), 0),
        2
    ) AS profit_margin_pct,
    ROUND(AVG(discount) * 100, 2) AS average_discount_pct,
    ROUND(
        100.0 * SUM(is_loss) / COUNT(*),
        2
    ) AS loss_making_line_rate_pct
FROM vw_order_item_details
GROUP BY
    state,
    region
ORDER BY total_profit DESC;


-- name: 24_loss_making_states
-- title: Loss-Making States
-- description: Geographic markets with negative cumulative profit, ranked from largest loss upward.
SELECT
    state,
    region,
    COUNT(DISTINCT customer_id) AS total_customers,
    COUNT(DISTINCT order_id) AS total_orders,
    ROUND(SUM(sales), 2) AS total_sales,
    ROUND(SUM(profit), 2) AS total_profit,
    ROUND(
        100.0 * SUM(profit) / NULLIF(SUM(sales), 0),
        2
    ) AS profit_margin_pct,
    ROUND(AVG(discount) * 100, 2) AS average_discount_pct
FROM vw_order_item_details
GROUP BY
    state,
    region
HAVING SUM(profit) < 0
ORDER BY total_profit ASC;


-- name: 25_city_performance
-- title: Top Cities by Sales
-- description: The thirty largest city markets by revenue with profitability and customer activity.
SELECT
    city,
    state,
    region,
    COUNT(DISTINCT customer_id) AS total_customers,
    COUNT(DISTINCT order_id) AS total_orders,
    ROUND(SUM(sales), 2) AS total_sales,
    ROUND(SUM(profit), 2) AS total_profit,
    ROUND(
        100.0 * SUM(profit) / NULLIF(SUM(sales), 0),
        2
    ) AS profit_margin_pct
FROM vw_order_item_details
GROUP BY
    city,
    state,
    region
ORDER BY total_sales DESC
LIMIT 30;


-- name: 26_ship_mode_performance
-- title: Ship Mode Performance
-- description: Compares shipping modes by order volume, delivery time, sales, profit, and margin.
SELECT
    ship_mode,
    COUNT(DISTINCT order_id) AS total_orders,
    ROUND(AVG(shipping_days), 2) AS average_shipping_days,
    MIN(shipping_days) AS minimum_shipping_days,
    MAX(shipping_days) AS maximum_shipping_days,
    ROUND(SUM(sales), 2) AS total_sales,
    ROUND(SUM(profit), 2) AS total_profit,
    ROUND(
        100.0 * SUM(profit) / NULLIF(SUM(sales), 0),
        2
    ) AS profit_margin_pct,
    ROUND(
        SUM(sales) / COUNT(DISTINCT order_id),
        2
    ) AS average_order_value
FROM vw_order_item_details
GROUP BY ship_mode
ORDER BY total_orders DESC;


-- name: 27_shipping_days_distribution
-- title: Shipping Time Distribution
-- description: Distribution of orders by number of elapsed shipping days.
SELECT
    shipping_days,
    COUNT(DISTINCT order_id) AS total_orders,
    ROUND(
        100.0 * COUNT(DISTINCT order_id)
        / SUM(COUNT(DISTINCT order_id)) OVER (),
        2
    ) AS order_share_pct,
    ROUND(SUM(sales), 2) AS total_sales,
    ROUND(SUM(profit), 2) AS total_profit
FROM vw_order_item_details
GROUP BY shipping_days
ORDER BY shipping_days;


-- name: 28_order_value_distribution
-- title: Order Value Distribution
-- description: Groups complete orders into commercial value bands and summarizes profitability.
WITH grouped AS (
    SELECT
        *,
        CASE
            WHEN total_sales < 50 THEN 'Under $50'
            WHEN total_sales < 200 THEN '$50–$199'
            WHEN total_sales < 500 THEN '$200–$499'
            WHEN total_sales < 1000 THEN '$500–$999'
            ELSE '$1,000+'
        END AS order_value_band
    FROM vw_order_summary
)
SELECT
    order_value_band,
    COUNT(*) AS total_orders,
    ROUND(SUM(total_sales), 2) AS total_sales,
    ROUND(SUM(total_profit), 2) AS total_profit,
    ROUND(AVG(total_sales), 2) AS average_order_value,
    ROUND(
        100.0 * SUM(total_profit) / NULLIF(SUM(total_sales), 0),
        2
    ) AS profit_margin_pct,
    ROUND(
        100.0 * SUM(
            CASE WHEN total_profit < 0 THEN 1 ELSE 0 END
        ) / COUNT(*),
        2
    ) AS loss_making_order_rate_pct
FROM grouped
GROUP BY order_value_band
ORDER BY
    CASE order_value_band
        WHEN 'Under $50' THEN 1
        WHEN '$50–$199' THEN 2
        WHEN '$200–$499' THEN 3
        WHEN '$500–$999' THEN 4
        WHEN '$1,000+' THEN 5
    END;


-- name: 29_profit_concentration_by_sub_category
-- title: Profit Concentration by Sub-Category
-- description: Ranks sub-categories by profit and shows cumulative contribution to total positive profit.
WITH sub_category_profit AS (
    SELECT
        category,
        sub_category,
        SUM(sales) AS total_sales,
        SUM(profit) AS total_profit
    FROM vw_order_item_details
    GROUP BY
        category,
        sub_category
),
ranked AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            ORDER BY total_profit DESC
        ) AS profit_rank,
        SUM(
            CASE WHEN total_profit > 0 THEN total_profit ELSE 0 END
        ) OVER (
            ORDER BY total_profit DESC
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS cumulative_positive_profit,
        SUM(
            CASE WHEN total_profit > 0 THEN total_profit ELSE 0 END
        ) OVER () AS total_positive_profit
    FROM sub_category_profit
)
SELECT
    category,
    sub_category,
    profit_rank,
    ROUND(total_sales, 2) AS total_sales,
    ROUND(total_profit, 2) AS total_profit,
    ROUND(
        100.0 * total_profit / NULLIF(total_sales, 0),
        2
    ) AS profit_margin_pct,
    ROUND(
        100.0 * cumulative_positive_profit
        / NULLIF(total_positive_profit, 0),
        2
    ) AS cumulative_positive_profit_share_pct
FROM ranked
ORDER BY profit_rank;


-- name: 30_management_attention_summary
-- title: Management Attention Summary
-- description: A compact collection of business risks and opportunities suitable for an executive dashboard.
WITH metrics AS (
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
best_profit AS (
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
largest_loss AS (
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
best_region AS (
    SELECT
        'Most-profitable region' AS indicator,
        region AS finding,
        ROUND(SUM(profit), 2) AS metric_value,
        'USD profit' AS metric_unit
    FROM vw_order_item_details
    GROUP BY region
    ORDER BY SUM(profit) DESC
    LIMIT 1
),
worst_discount_band AS (
    SELECT
        'Lowest-margin discount band' AS indicator,
        discount_band AS finding,
        ROUND(
            100.0 * SUM(profit) / NULLIF(SUM(sales), 0),
            2
        ) AS metric_value,
        'Percent margin' AS metric_unit
    FROM vw_order_item_details
    GROUP BY discount_band
    ORDER BY
        SUM(profit) / NULLIF(SUM(sales), 0) ASC
    LIMIT 1
)
SELECT * FROM metrics
UNION ALL
SELECT * FROM best_profit
UNION ALL
SELECT * FROM largest_loss
UNION ALL
SELECT * FROM best_region
UNION ALL
SELECT * FROM worst_discount_band;
