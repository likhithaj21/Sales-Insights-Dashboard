-- ══════════════════════════════════════════════════════════════════════
-- SalesPulse Pro — SQL Analytics Queries
-- Dataset: Superstore Sales
-- Compatible: SQLite / PostgreSQL / MySQL
-- ══════════════════════════════════════════════════════════════════════


-- ── 1. OVERALL KPIs ───────────────────────────────────────────────────
SELECT
    ROUND(SUM(sales), 2)                          AS total_sales,
    ROUND(SUM(profit), 2)                         AS total_profit,
    COUNT(DISTINCT order_id)                       AS total_orders,
    COUNT(DISTINCT customer_id)                    AS unique_customers,
    ROUND(SUM(profit) / SUM(sales) * 100, 2)      AS overall_profit_margin_pct,
    ROUND(SUM(sales) / COUNT(DISTINCT order_id), 2) AS avg_order_value,
    SUM(quantity)                                  AS total_units_sold
FROM superstore
WHERE sales > 0;


-- ── 2. MONTHLY SALES TREND WITH MoM GROWTH ───────────────────────────
WITH monthly AS (
    SELECT
        strftime('%Y', order_date)           AS yr,
        strftime('%m', order_date)           AS mo,
        strftime('%Y-%m', order_date)        AS period,
        ROUND(SUM(sales), 2)                 AS monthly_sales,
        ROUND(SUM(profit), 2)                AS monthly_profit,
        COUNT(DISTINCT order_id)             AS orders
    FROM superstore
    GROUP BY 1, 2, 3
)
SELECT
    period,
    monthly_sales,
    monthly_profit,
    orders,
    ROUND(monthly_profit / monthly_sales * 100, 2) AS profit_margin_pct,
    ROUND(
        (monthly_sales - LAG(monthly_sales) OVER (ORDER BY period))
        / LAG(monthly_sales) OVER (ORDER BY period) * 100, 1
    )                                              AS mom_growth_pct
FROM monthly
ORDER BY period;


-- ── 3. TOP 10 PRODUCTS BY SALES ──────────────────────────────────────
SELECT
    product_name,
    category,
    sub_category,
    COUNT(DISTINCT order_id)               AS total_orders,
    ROUND(SUM(sales), 2)                   AS total_sales,
    ROUND(SUM(profit), 2)                  AS total_profit,
    ROUND(SUM(profit)/SUM(sales)*100, 2)   AS profit_margin_pct,
    SUM(quantity)                          AS units_sold
FROM superstore
GROUP BY product_name, category, sub_category
ORDER BY total_sales DESC
LIMIT 10;


-- ── 4. TOP 10 LOSS-MAKING PRODUCTS (watch list) ───────────────────────
SELECT
    product_name,
    category,
    sub_category,
    ROUND(SUM(sales), 2)                   AS total_sales,
    ROUND(SUM(profit), 2)                  AS total_loss,
    ROUND(SUM(profit)/SUM(sales)*100, 2)   AS profit_margin_pct,
    COUNT(DISTINCT order_id)               AS order_count
FROM superstore
GROUP BY product_name, category, sub_category
HAVING total_loss < 0
ORDER BY total_loss ASC
LIMIT 10;


-- ── 5. REGION-WISE PERFORMANCE ────────────────────────────────────────
SELECT
    region,
    COUNT(DISTINCT order_id)               AS total_orders,
    COUNT(DISTINCT customer_id)            AS unique_customers,
    ROUND(SUM(sales), 2)                   AS total_sales,
    ROUND(SUM(profit), 2)                  AS total_profit,
    ROUND(SUM(profit)/SUM(sales)*100, 2)   AS profit_margin_pct,
    ROUND(SUM(sales)/COUNT(DISTINCT order_id), 2) AS avg_order_value,
    ROUND(AVG(
        julianday(ship_date) - julianday(order_date)
    ), 1)                                  AS avg_ship_days
FROM superstore
GROUP BY region
ORDER BY total_sales DESC;


-- ── 6. CATEGORY & SUB-CATEGORY BREAKDOWN ─────────────────────────────
SELECT
    category,
    sub_category,
    ROUND(SUM(sales), 2)                            AS total_sales,
    ROUND(SUM(profit), 2)                           AS total_profit,
    ROUND(SUM(profit)/SUM(sales)*100, 2)            AS profit_margin_pct,
    SUM(quantity)                                   AS units_sold,
    ROUND(SUM(sales)*100.0/SUM(SUM(sales)) OVER (), 2) AS sales_share_pct
FROM superstore
GROUP BY category, sub_category
ORDER BY total_sales DESC;


-- ── 7. CUSTOMER SEGMENT ANALYSIS ─────────────────────────────────────
SELECT
    segment,
    COUNT(DISTINCT customer_id)            AS unique_customers,
    COUNT(DISTINCT order_id)               AS total_orders,
    ROUND(SUM(sales), 2)                   AS total_sales,
    ROUND(SUM(profit), 2)                  AS total_profit,
    ROUND(SUM(profit)/SUM(sales)*100, 2)   AS profit_margin_pct,
    ROUND(SUM(sales)/COUNT(DISTINCT customer_id), 2) AS sales_per_customer
FROM superstore
GROUP BY segment
ORDER BY total_sales DESC;


-- ── 8. DISCOUNT IMPACT ON PROFIT ──────────────────────────────────────
SELECT
    CASE
        WHEN discount = 0            THEN 'No Discount'
        WHEN discount <= 0.20        THEN 'Low (0-20%)'
        WHEN discount <= 0.40        THEN 'Medium (20-40%)'
        ELSE                              'High (>40%)'
    END                                        AS discount_band,
    COUNT(DISTINCT order_id)                   AS order_count,
    ROUND(SUM(sales), 2)                       AS total_sales,
    ROUND(SUM(profit), 2)                      AS total_profit,
    ROUND(SUM(profit)/SUM(sales)*100, 2)       AS profit_margin_pct,
    ROUND(AVG(discount)*100, 1)                AS avg_discount_pct
FROM superstore
GROUP BY discount_band
ORDER BY avg_discount_pct;


-- ── 9. QUARTERLY PERFORMANCE + YoY GROWTH ────────────────────────────
WITH quarterly AS (
    SELECT
        strftime('%Y', order_date)  AS yr,
        CASE
            WHEN CAST(strftime('%m', order_date) AS INT) <= 3  THEN 'Q1'
            WHEN CAST(strftime('%m', order_date) AS INT) <= 6  THEN 'Q2'
            WHEN CAST(strftime('%m', order_date) AS INT) <= 9  THEN 'Q3'
            ELSE                                                     'Q4'
        END                         AS qtr,
        ROUND(SUM(sales), 2)        AS q_sales,
        ROUND(SUM(profit), 2)       AS q_profit
    FROM superstore
    GROUP BY yr, qtr
)
SELECT
    yr, qtr, q_sales, q_profit,
    ROUND(q_profit/q_sales*100, 2)  AS margin_pct,
    ROUND(
        (q_sales - LAG(q_sales) OVER (PARTITION BY qtr ORDER BY yr))
        / LAG(q_sales) OVER (PARTITION BY qtr ORDER BY yr) * 100, 1
    )                               AS yoy_growth_pct
FROM quarterly
ORDER BY yr, qtr;


-- ── 10. TOP 10 STATES BY SALES ────────────────────────────────────────
SELECT
    state,
    region,
    COUNT(DISTINCT order_id)               AS total_orders,
    ROUND(SUM(sales), 2)                   AS total_sales,
    ROUND(SUM(profit), 2)                  AS total_profit,
    ROUND(SUM(profit)/SUM(sales)*100, 2)   AS profit_margin_pct
FROM superstore
GROUP BY state, region
ORDER BY total_sales DESC
LIMIT 10;


-- ── 11. SHIPPING MODE ANALYSIS ────────────────────────────────────────
SELECT
    ship_mode,
    COUNT(DISTINCT order_id)               AS total_orders,
    ROUND(SUM(sales), 2)                   AS total_sales,
    ROUND(SUM(profit), 2)                  AS total_profit,
    ROUND(AVG(
        julianday(ship_date) - julianday(order_date)
    ), 1)                                  AS avg_ship_days,
    ROUND(SUM(profit)/SUM(sales)*100, 2)   AS profit_margin_pct
FROM superstore
GROUP BY ship_mode
ORDER BY total_orders DESC;


-- ── 12. RFM — CUSTOMER VALUE SCORING ─────────────────────────────────
WITH rfm AS (
    SELECT
        customer_id,
        customer_name,
        segment,
        julianday('now') - julianday(MAX(order_date)) AS recency_days,
        COUNT(DISTINCT order_id)                       AS frequency,
        ROUND(SUM(sales), 2)                           AS monetary
    FROM superstore
    GROUP BY customer_id, customer_name, segment
),
scored AS (
    SELECT *,
        NTILE(4) OVER (ORDER BY recency_days ASC)  AS r_score,
        NTILE(4) OVER (ORDER BY frequency DESC)    AS f_score,
        NTILE(4) OVER (ORDER BY monetary DESC)     AS m_score
    FROM rfm
)
SELECT *,
    (r_score + f_score + m_score) AS rfm_total,
    CASE
        WHEN r_score=4 AND f_score>=3 THEN 'Champion'
        WHEN r_score>=3 AND f_score>=2 THEN 'Loyal'
        WHEN r_score<=2 AND m_score>=3 THEN 'At Risk'
        ELSE 'Dormant'
    END AS customer_segment
FROM scored
ORDER BY rfm_total DESC;
