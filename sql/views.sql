-- ============================================================================
-- ApexPlanet Data Analytics - Task 2: SQL Views
-- ============================================================================
-- Views are virtual tables that encapsulate complex queries. They simplify
-- repeated analysis, improve readability, and act as an abstraction layer
-- over the base tables.
--
-- Database: database/apexplanet_sales.db
-- Base table: sales (from data/processed/cleaned_dataset.csv)
-- Reference table: city_regions
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. monthly_sales_summary
-- ----------------------------------------------------------------------------
-- What it encapsulates: Month-level revenue, order count, active customer
--   count, and month-over-month revenue growth.
-- Why it's useful: Whenever the team needs a "how did we do this month"
--   snapshot, they query this view instead of re-running the aggregation.
-- Drop first to make re-running this file idempotent.
DROP VIEW IF EXISTS monthly_sales_summary;

CREATE VIEW monthly_sales_summary AS
WITH monthly_rev AS (
    SELECT
        strftime('%Y-%m', Order_Date) AS year_month,
        SUM(Total_Sales)              AS monthly_revenue,
        COUNT(*)                      AS order_count,
        COUNT(DISTINCT Customer_ID)   AS active_customers
    FROM sales
    GROUP BY strftime('%Y-%m', Order_Date)
)
SELECT
    year_month,
    monthly_revenue,
    order_count,
    active_customers,
    LAG(monthly_revenue) OVER (ORDER BY year_month) AS prev_month_revenue,
    ROUND(
        100.0 * (monthly_revenue - LAG(monthly_revenue) OVER (ORDER BY year_month))
        / LAG(monthly_revenue) OVER (ORDER BY year_month), 2
    ) AS mom_growth_percent
FROM monthly_rev;

-- Example usage:
-- SELECT * FROM monthly_sales_summary WHERE mom_growth_percent > 0;
-- SELECT * FROM monthly_sales_summary ORDER BY year_month;

-- ----------------------------------------------------------------------------
-- 2. category_performance
-- ----------------------------------------------------------------------------
-- What it encapsulates: Per-product-category revenue, quantity, average
--   order value, average customer rating, and revenue share.
-- Why it's useful: A single query for "which category is performing best"
--   that can be reused in dashboards and reports.
DROP VIEW IF EXISTS category_performance;

CREATE VIEW category_performance AS
SELECT
    Product_Category,
    SUM(Total_Sales) AS total_revenue,
    SUM(Quantity)    AS total_quantity,
    COUNT(*)         AS order_count,
    ROUND(AVG(Total_Sales), 2) AS avg_order_value,
    ROUND(AVG(Customer_Rating), 2) AS avg_rating,
    ROUND(
        SUM(Total_Sales) * 100.0 /
        (SELECT SUM(Total_Sales) FROM sales), 2
    ) AS revenue_share_percent
FROM sales
GROUP BY Product_Category;

-- Example usage:
-- SELECT * FROM category_performance ORDER BY total_revenue DESC;
-- SELECT * FROM category_performance WHERE avg_rating >= 3.5;

-- ----------------------------------------------------------------------------
-- 3. customer_revenue_summary
-- ----------------------------------------------------------------------------
-- What it encapsulates: Per-customer lifetime value, order count, average
--   order value, first purchase date, last purchase date, and categories
--   purchased.
-- Why it's useful: Customer-level segmentation for marketing, loyalty
--   programs, and churn analysis.
DROP VIEW IF EXISTS customer_revenue_summary;

CREATE VIEW customer_revenue_summary AS
SELECT
    Customer_ID,
    SUM(Total_Sales)            AS lifetime_value,
    COUNT(*)                    AS order_count,
    ROUND(AVG(Total_Sales), 2)  AS avg_order_value,
    MIN(Order_Date)             AS first_purchase,
    MAX(Order_Date)             AS last_purchase,
    COUNT(DISTINCT Product_Category) AS categories_purchased,
    ROUND(AVG(Customer_Rating), 2) AS avg_rating
FROM sales
GROUP BY Customer_ID;

-- Example usage:
-- SELECT * FROM customer_revenue_summary WHERE order_count > 5;
-- SELECT * FROM customer_revenue_summary ORDER BY lifetime_value DESC LIMIT 20;

-- ----------------------------------------------------------------------------
-- 4. payment_method_summary
-- ----------------------------------------------------------------------------
-- What it encapsulates: Per-payment-method transaction count, revenue,
--   average transaction value, and share of total transactions.
-- Why it's useful: Payment method analysis for operations (which methods to
--   optimize for, which have friction, etc.).
DROP VIEW IF EXISTS payment_method_summary;

CREATE VIEW payment_method_summary AS
SELECT
    Payment_Method,
    COUNT(*) AS transaction_count,
    SUM(Total_Sales) AS total_revenue,
    ROUND(AVG(Total_Sales), 2) AS avg_transaction_value,
    ROUND(
        COUNT(*) * 100.0 /
        (SELECT COUNT(*) FROM sales), 2
    ) AS transaction_share_percent
FROM sales
GROUP BY Payment_Method;

-- Example usage:
-- SELECT * FROM payment_method_summary ORDER BY total_revenue DESC;
-- SELECT * FROM payment_method_summary WHERE avg_transaction_value > 100;

-- ----------------------------------------------------------------------------
-- 5. city_region_revenue
-- ----------------------------------------------------------------------------
-- What it encapsulates: City-level revenue enriched with US region.
-- Why it's useful: Geographic analysis without repeating the JOIN.
DROP VIEW IF EXISTS city_region_revenue;

CREATE VIEW city_region_revenue AS
SELECT
    s.City,
    cr.Region,
    SUM(s.Total_Sales) AS total_revenue,
    COUNT(*)           AS order_count,
    COUNT(DISTINCT s.Customer_ID) AS active_customers,
    ROUND(AVG(s.Total_Sales), 2) AS avg_order_value
FROM sales s
JOIN city_regions cr ON s.City = cr.City
GROUP BY s.City, cr.Region;

-- Example usage:
-- SELECT * FROM city_region_revenue WHERE Region = 'West';
-- SELECT * FROM city_region_revenue ORDER BY total_revenue DESC;
