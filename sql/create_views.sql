DROP VIEW IF EXISTS vw_order_item_details;
DROP VIEW IF EXISTS vw_order_summary;
DROP VIEW IF EXISTS vw_customer_summary;
DROP VIEW IF EXISTS vw_product_summary;

CREATE VIEW vw_order_item_details AS
SELECT
    oi.row_id,
    o.order_id,
    o.order_date,
    o.ship_date,
    o.ship_mode,
    o.shipping_days,

    c.customer_id,
    c.customer_name,
    c.segment,

    l.country,
    l.city,
    l.state,
    l.postal_code,
    l.region,

    p.product_key,
    p.product_id,
    p.product_name,
    p.category,
    p.sub_category,

    oi.sales,
    oi.quantity,
    oi.discount,
    oi.profit,
    oi.profit_margin,
    oi.unit_sales,
    oi.unit_profit,
    oi.is_profitable,
    oi.is_loss,
    oi.is_discounted,
    oi.discount_band,

    CAST(strftime('%Y', o.order_date) AS INTEGER) AS order_year,
    CAST(strftime('%m', o.order_date) AS INTEGER) AS order_month,
    strftime('%Y-%m', o.order_date) AS order_year_month,
    'Q' || CAST(
        ((CAST(strftime('%m', o.order_date) AS INTEGER) - 1) / 3) + 1
        AS INTEGER
    ) AS order_quarter

FROM order_items AS oi

JOIN orders AS o
    ON oi.order_id = o.order_id

JOIN customers AS c
    ON o.customer_id = c.customer_id

JOIN locations AS l
    ON o.location_id = l.location_id

JOIN products AS p
    ON oi.product_key = p.product_key;


CREATE VIEW vw_order_summary AS
SELECT
    o.order_id,
    o.order_date,
    o.ship_date,
    o.ship_mode,
    o.shipping_days,

    c.customer_id,
    c.customer_name,
    c.segment,

    l.country,
    l.city,
    l.state,
    l.postal_code,
    l.region,

    COUNT(oi.row_id) AS line_count,
    COUNT(DISTINCT oi.product_key) AS distinct_products,
    SUM(oi.quantity) AS total_quantity,
    ROUND(SUM(oi.sales), 2) AS total_sales,
    ROUND(SUM(oi.profit), 2) AS total_profit,

    CASE
        WHEN SUM(oi.sales) = 0 THEN NULL
        ELSE SUM(oi.profit) / SUM(oi.sales)
    END AS order_profit_margin,

    AVG(oi.discount) AS average_discount,
    MAX(oi.discount) AS maximum_discount,

    CASE
        WHEN SUM(oi.profit) > 0 THEN 1
        ELSE 0
    END AS is_profitable_order

FROM orders AS o

JOIN customers AS c
    ON o.customer_id = c.customer_id

JOIN locations AS l
    ON o.location_id = l.location_id

JOIN order_items AS oi
    ON o.order_id = oi.order_id

GROUP BY
    o.order_id,
    o.order_date,
    o.ship_date,
    o.ship_mode,
    o.shipping_days,
    c.customer_id,
    c.customer_name,
    c.segment,
    l.country,
    l.city,
    l.state,
    l.postal_code,
    l.region;


CREATE VIEW vw_customer_summary AS
SELECT
    c.customer_id,
    c.customer_name,
    c.segment,

    COUNT(DISTINCT o.order_id) AS order_count,
    COUNT(oi.row_id) AS line_count,
    COUNT(DISTINCT oi.product_key) AS distinct_products,
    SUM(oi.quantity) AS total_quantity,
    ROUND(SUM(oi.sales), 2) AS total_sales,
    ROUND(SUM(oi.profit), 2) AS total_profit,

    CASE
        WHEN SUM(oi.sales) = 0 THEN NULL
        ELSE SUM(oi.profit) / SUM(oi.sales)
    END AS profit_margin,

    ROUND(
        SUM(oi.sales) / COUNT(DISTINCT o.order_id),
        2
    ) AS average_order_value,

    MIN(o.order_date) AS first_order_date,
    MAX(o.order_date) AS last_order_date

FROM customers AS c

JOIN orders AS o
    ON c.customer_id = o.customer_id

JOIN order_items AS oi
    ON o.order_id = oi.order_id

GROUP BY
    c.customer_id,
    c.customer_name,
    c.segment;


CREATE VIEW vw_product_summary AS
SELECT
    p.product_key,
    p.product_id,
    p.product_name,
    p.category,
    p.sub_category,

    COUNT(DISTINCT oi.order_id) AS order_count,
    COUNT(oi.row_id) AS line_count,
    SUM(oi.quantity) AS total_quantity,
    ROUND(SUM(oi.sales), 2) AS total_sales,
    ROUND(SUM(oi.profit), 2) AS total_profit,

    CASE
        WHEN SUM(oi.sales) = 0 THEN NULL
        ELSE SUM(oi.profit) / SUM(oi.sales)
    END AS profit_margin,

    AVG(oi.discount) AS average_discount,
    SUM(oi.is_loss) AS loss_making_lines

FROM products AS p

JOIN order_items AS oi
    ON p.product_key = oi.product_key

GROUP BY
    p.product_key,
    p.product_id,
    p.product_name,
    p.category,
    p.sub_category;
