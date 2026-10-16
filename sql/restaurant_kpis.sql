-- SQLite demonstration against the four CSV-derived tables.
-- Run: python -m src.load_sqlite; then open data/restaurant_demo.sqlite in SQLite.
-- Grain: aggregate item lines to order before applying order-level discounts.

-- 1. Sales by channel (correct discount grain)
WITH gross_by_order AS (
    SELECT order_id, SUM(quantity * unit_price) AS gross_sales
    FROM order_items GROUP BY order_id
)
SELECT o.channel,
       COUNT(*) AS transactions,
       ROUND(SUM(g.gross_sales), 2) AS gross_sales,
       ROUND(SUM(o.discount_amount), 2) AS discounts,
       ROUND(SUM(g.gross_sales - o.discount_amount), 2) AS net_sales
FROM orders o
JOIN gross_by_order g ON o.order_id = g.order_id
GROUP BY o.channel ORDER BY net_sales DESC;

-- 2. Daily net sales
WITH gross_by_order AS (
    SELECT order_id, SUM(quantity * unit_price) AS gross_sales
    FROM order_items GROUP BY order_id
)
SELECT o.order_date,
       COUNT(*) AS transactions,
       ROUND(SUM(g.gross_sales - o.discount_amount), 2) AS net_sales
FROM orders o JOIN gross_by_order g ON o.order_id = g.order_id
GROUP BY o.order_date ORDER BY o.order_date;

-- 3. Direct wage cost by role; excludes payroll taxes, tips and benefits
SELECT role, ROUND(SUM(paid_hours), 1) AS paid_hours,
       ROUND(SUM(paid_hours * hourly_rate), 2) AS direct_hourly_wages
FROM labor_shifts GROUP BY role ORDER BY direct_hourly_wages DESC;

-- 4. Missing menu recipe cost coverage: investigate before reporting profit
SELECT m.sku, m.item_name,
       SUM(i.quantity) AS units_sold,
       ROUND(SUM(i.quantity * i.unit_price), 2) AS affected_gross_sales
FROM order_items i JOIN menu_costs m ON m.sku = i.sku
WHERE m.unit_cost IS NULL
GROUP BY m.sku, m.item_name ORDER BY affected_gross_sales DESC;
