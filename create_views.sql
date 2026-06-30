-- ============================================
-- VIEW 1: Monthly Revenue Trends
-- ============================================
CREATE OR REPLACE VIEW vw_monthly_revenue AS
SELECT
    DATE_TRUNC('month', o.order_date)::date AS month,
    COUNT(DISTINCT o.order_id) AS total_orders,
    ROUND(SUM(oi.quantity * oi.price_at_order), 2) AS total_revenue,
    ROUND(SUM(oi.quantity * oi.price_at_order) / COUNT(DISTINCT o.order_id), 2) AS avg_order_value
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.order_status != 'cancelled'
GROUP BY month
ORDER BY month;

-- ============================================
-- VIEW 2: Top Products
-- ============================================
CREATE OR REPLACE VIEW vw_top_products AS
SELECT
    p.product_id,
    p.product_name,
    p.category,
    SUM(oi.quantity) AS total_quantity_sold,
    ROUND(SUM(oi.quantity * oi.price_at_order), 2) AS total_revenue
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id
JOIN products p ON oi.product_id = p.product_id
WHERE o.order_status != 'cancelled'
GROUP BY p.product_id, p.product_name, p.category
ORDER BY total_revenue DESC;

-- ============================================
-- VIEW 3: Category Performance
-- ============================================
CREATE OR REPLACE VIEW vw_category_performance AS
SELECT
    p.category,
    COUNT(DISTINCT o.order_id) AS total_orders,
    SUM(oi.quantity) AS total_units_sold,
    ROUND(SUM(oi.quantity * oi.price_at_order), 2) AS total_revenue,
    ROUND(SUM(oi.quantity * oi.price_at_order) * 100.0 / SUM(SUM(oi.quantity * oi.price_at_order)) OVER (), 2) AS revenue_share_pct
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id
JOIN products p ON oi.product_id = p.product_id
WHERE o.order_status != 'cancelled'
GROUP BY p.category
ORDER BY total_revenue DESC;

-- ============================================
-- VIEW 4: Customer Segmentation
-- ============================================
CREATE OR REPLACE VIEW vw_customer_segments AS
WITH customer_stats AS (
    SELECT
        c.customer_id,
        c.name,
        COUNT(DISTINCT o.order_id) AS order_count,
        ROUND(SUM(oi.quantity * oi.price_at_order), 2) AS total_spent
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.order_status != 'cancelled'
    GROUP BY c.customer_id, c.name
)
SELECT
    customer_id,
    name,
    order_count,
    total_spent,
    CASE WHEN order_count = 1 THEN 'New (1 order)' ELSE 'Repeat (2+ orders)' END AS customer_type,
    CASE
        WHEN total_spent >= 50000 THEN 'High Value'
        WHEN total_spent >= 20000 THEN 'Medium Value'
        ELSE 'Low Value'
    END AS spend_tier
FROM customer_stats;

-- ============================================
-- VIEW 5: Order Status Breakdown
-- ============================================
CREATE OR REPLACE VIEW vw_order_status_breakdown AS
SELECT
    o.order_status,
    COUNT(DISTINCT o.order_id) AS num_orders,
    ROUND(COUNT(DISTINCT o.order_id) * 100.0 / SUM(COUNT(DISTINCT o.order_id)) OVER (), 2) AS pct_of_orders,
    ROUND(COALESCE(SUM(oi.quantity * oi.price_at_order), 0), 2) AS associated_revenue
FROM orders o
LEFT JOIN order_items oi ON o.order_id = oi.order_id
GROUP BY o.order_status
ORDER BY num_orders DESC;