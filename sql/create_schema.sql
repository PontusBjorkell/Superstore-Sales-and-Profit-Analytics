PRAGMA foreign_keys = ON;

DROP VIEW IF EXISTS vw_order_item_details;
DROP VIEW IF EXISTS vw_order_summary;
DROP VIEW IF EXISTS vw_customer_summary;
DROP VIEW IF EXISTS vw_product_summary;

DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS locations;

CREATE TABLE customers (
    customer_id TEXT PRIMARY KEY,
    customer_name TEXT NOT NULL,
    segment TEXT NOT NULL
        CHECK (segment IN ('Consumer', 'Corporate', 'Home Office'))
);

CREATE TABLE products (
    product_key INTEGER PRIMARY KEY,
    product_id TEXT NOT NULL,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,
    sub_category TEXT NOT NULL,
    UNIQUE (
        product_id,
        product_name,
        category,
        sub_category
    )
);

CREATE TABLE locations (
    location_id INTEGER PRIMARY KEY,
    country TEXT NOT NULL,
    city TEXT NOT NULL,
    state TEXT NOT NULL,
    postal_code TEXT,
    region TEXT NOT NULL,
    UNIQUE (
        country,
        city,
        state,
        postal_code,
        region
    )
);

CREATE TABLE orders (
    order_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    location_id INTEGER NOT NULL,
    order_date TEXT NOT NULL,
    ship_date TEXT NOT NULL,
    ship_mode TEXT NOT NULL,
    shipping_days INTEGER NOT NULL
        CHECK (shipping_days >= 0),

    FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id),

    FOREIGN KEY (location_id)
        REFERENCES locations(location_id)
);

CREATE TABLE order_items (
    row_id INTEGER PRIMARY KEY,
    order_id TEXT NOT NULL,
    product_key INTEGER NOT NULL,
    sales REAL NOT NULL
        CHECK (sales >= 0),
    quantity INTEGER NOT NULL
        CHECK (quantity > 0),
    discount REAL NOT NULL
        CHECK (discount >= 0 AND discount <= 1),
    profit REAL NOT NULL,
    profit_margin REAL,
    unit_sales REAL,
    unit_profit REAL,
    is_profitable INTEGER NOT NULL
        CHECK (is_profitable IN (0, 1)),
    is_loss INTEGER NOT NULL
        CHECK (is_loss IN (0, 1)),
    is_discounted INTEGER NOT NULL
        CHECK (is_discounted IN (0, 1)),
    discount_band TEXT NOT NULL,

    FOREIGN KEY (order_id)
        REFERENCES orders(order_id),

    FOREIGN KEY (product_key)
        REFERENCES products(product_key)
);

CREATE INDEX idx_orders_customer_id
    ON orders(customer_id);

CREATE INDEX idx_orders_location_id
    ON orders(location_id);

CREATE INDEX idx_orders_order_date
    ON orders(order_date);

CREATE INDEX idx_order_items_order_id
    ON order_items(order_id);

CREATE INDEX idx_order_items_product_key
    ON order_items(product_key);

CREATE INDEX idx_order_items_discount
    ON order_items(discount);

CREATE INDEX idx_order_items_profit
    ON order_items(profit);

CREATE INDEX idx_products_product_id
    ON products(product_id);

CREATE INDEX idx_products_category
    ON products(category);

CREATE INDEX idx_products_sub_category
    ON products(sub_category);

CREATE INDEX idx_locations_region
    ON locations(region);

CREATE INDEX idx_locations_state
    ON locations(state);
