-- ============================================================================
-- ApexPlanet Data Analytics - Task 2: Advanced SQL
-- ============================================================================
-- Common Table Expressions (CTEs), Subqueries, and Window Functions
--
-- These queries solve real business problems using advanced SQL features:
-- - WITH clauses (CTEs) for readable, modular queries
-- - Subqueries for intermediate calculations
-- - Window functions: ROW_NUMBER, RANK, LAG, LEAD, SUM OVER, AVG OVER
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. Monthly sales/revenue trend using CTE
-- ----------------------------------------------------------------------------
-- What it does: Calculates monthly revenue trend using a CTE to cleanly
--   separate date extraction from aggregation.
-- Why it matters: CTEs make complex queries readable by breaking them into
--   logical steps. This is the foundation of maintainable SQL.
-- Business question: "What is the monthly revenue trend over the dataset period?"
WITH monthly_data AS (
    SELECT
        strftime('%Y-%m', Order_Date) AS year_month,
        Total_Sales
    FROM sales
)
SELECT
    year_month,
    SUM(Total_Sales)       AS monthly_revenue,
    COUNT(*)               AS order_count,
    AVG(Total_Sales)       AS avg_order_value
FROM monthly_data
GROUP BY year_month
ORDER BY year_month;

-- ----------------------------------------------------------------------------
-- 2. Top 10 customers by revenue using ROW_NUMBER()
-- ----------------------------------------------------------------------------
-- What it does: Ranks customers by total revenue and returns only the top 10.
-- Why it matters: ROW_NUMBER() assigns a unique rank to each row, making
--   top-N queries simple and performant.
-- Business question: "Who are our top 10 customers by total spend?"
WITH customer_revenue AS (
    SELECT
        Customer_ID,
        SUM(Total_Sales)        AS total_revenue,
        COUNT(*)                AS order_count,
        AVG(Total_Sales)        AS avg_order_value
    FROM sales
    GROUP BY Customer_ID
)
-- SQL order of operations: window functions are computed after WHERE, so
-- revenue_rank (a window alias) cannot be filtered in the same query level.
-- We wrap the windowed query in a subquery and filter at the outer level.
SELECT *
FROM (
    SELECT
        Customer_ID,
        total_revenue,
        order_count,
        avg_order_value,
        ROW_NUMBER() OVER (ORDER BY total_revenue DESC) AS revenue_rank
    FROM customer_revenue
) ranked
WHERE revenue_rank <= 10
ORDER BY revenue_rank;

-- ----------------------------------------------------------------------------
-- 3. Customer retention analysis using LAG (month-over-month customer count)
-- ----------------------------------------------------------------------------
-- What it does: Uses LAG to compare this month's customer count to last month's,
--   calculating month-over-month growth rate.
-- Why it matters: LAG gives access to previous row values, enabling period-over-
--   period comparisons without self-joins.
-- Business question: "What is the month-over-month customer growth rate?"
WITH monthly_customers AS (
    SELECT
        strftime('%Y-%m', Order_Date) AS year_month,
        COUNT(DISTINCT Customer_ID)   AS unique_customers
    FROM sales
    GROUP BY year_month
),
customer_growth AS (
    SELECT
        year_month,
        unique_customers,
        LAG(unique_customers) OVER (ORDER BY year_month) AS prev_month_customers
    FROM monthly_customers
)
SELECT
    year_month,
    unique_customers,
    prev_month_customers,
    CASE
        WHEN prev_month_customers IS NULL THEN NULL
        ELSE ROUND(100.0 * (unique_customers - prev_month_customers) / prev_month_customers, 2)
    END AS mom_growth_percent
FROM customer_growth
ORDER BY year_month;

-- ----------------------------------------------------------------------------
-- 4. Product category performance with running total
-- ----------------------------------------------------------------------------
-- What it does: Uses SUM() OVER to calculate cumulative revenue by product
--   category ordered by category name (for demonstration).
-- Why it matters: Window aggregates let us compute running totals, moving
--   averages, etc., without collapsing rows.
-- Business question: "What is the cumulative revenue by product category?"
SELECT
    Product_Category,
    SUM(Total_Sales) AS category_revenue,
    SUM(SUM(Total_Sales)) OVER (ORDER BY Product_Category) AS cumulative_revenue
FROM sales
GROUP BY Product_Category
ORDER BY category_revenue DESC;

-- ----------------------------------------------------------------------------
-- 5. Moving average of daily revenue (7-day window)
-- ----------------------------------------------------------------------------
-- What it does: Computes a 7-day moving average of daily revenue using
--   AVG() OVER with a ROWS BETWEEN window frame.
-- Why it matters: Moving averages smooth out daily volatility to reveal
--   underlying trends.
-- Business question: "What is the 7-day moving average of daily revenue?"
WITH daily_revenue AS (
    SELECT
        Order_Date       AS sales_date,
        SUM(Total_Sales) AS daily_total
    FROM sales
    GROUP BY Order_Date
)
SELECT
    sales_date,
    daily_total,
    AVG(daily_total) OVER (
        ORDER BY sales_date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS moving_avg_7day
FROM daily_revenue
ORDER BY sales_date;

-- ----------------------------------------------------------------------------
-- 6. Ranking customers within each product category using RANK()
-- ----------------------------------------------------------------------------
-- What it does: Uses RANK() to rank customers by revenue *within each*
--   product category, handling ties by giving equal ranks.
-- Why it matters: RANK() (vs ROW_NUMBER) is essential when ties should
--   share the same rank (e.g., two customers with identical revenue).
-- Business question: "Who are the top customers in each product category?"
WITH category_customer_revenue AS (
    SELECT
        Product_Category,
        Customer_ID,
        SUM(Total_Sales) AS category_revenue
    FROM sales
    GROUP BY Product_Category, Customer_ID
)
-- Same WHERE-vs-window rule as query 2: category_rank is a window alias,
-- so we filter on it in an outer query after the window has been computed.
SELECT *
FROM (
    SELECT
        Product_Category,
        Customer_ID,
        category_revenue,
        RANK() OVER (
            PARTITION BY Product_Category
            ORDER BY category_revenue DESC
        ) AS category_rank
    FROM category_customer_revenue
) ranked
WHERE category_rank <= 3  -- Top 3 per category
ORDER BY Product_Category, category_rank;

-- ----------------------------------------------------------------------------
-- 7. Period-over-period comparison: current month vs previous month revenue
-- ----------------------------------------------------------------------------
-- What it does: Uses LAG to access prior month's revenue and calculates
--   month-over-month change.
-- Why it matters: Period comparisons are fundamental to business analysis.
-- Business question: "How did this month's revenue compare to last month's?"
WITH monthly_revenue AS (
    SELECT
        strftime('%Y-%m', Order_Date) AS year_month,
        SUM(Total_Sales)              AS monthly_revenue
    FROM sales
    GROUP BY year_month
),
revenue_comparison AS (
    SELECT
        year_month,
        monthly_revenue,
        LAG(monthly_revenue) OVER (ORDER BY year_month) AS prev_month_revenue
    FROM monthly_revenue
)
SELECT
    year_month,
    monthly_revenue,
    prev_month_revenue,
    CASE
        WHEN prev_month_revenue IS NULL THEN NULL
        ELSE ROUND(100.0 * (monthly_revenue - prev_month_revenue) / prev_month_revenue, 2)
    END AS mom_change_percent
FROM revenue_comparison
ORDER BY year_month;

-- ----------------------------------------------------------------------------
-- 8. Customer lifetime value (total spent) with percentile ranking
-- ----------------------------------------------------------------------------
-- What it does: Calculates each customer's total lifetime value and uses
--   NTILE to bucket customers into quintiles (20% groups).
-- Why it matters: Percentile rankings help understand customer value
--   distribution without being skewed by outliers.
-- Business question: "How do customers distribute across lifetime value quintiles?"
WITH customer_ltv AS (
    SELECT
        Customer_ID,
        SUM(Total_Sales)   AS lifetime_value,
        COUNT(*)           AS order_count,
        AVG(Total_Sales)   AS avg_order_value
    FROM sales
    GROUP BY Customer_ID
)
SELECT
    Customer_ID,
    lifetime_value,
    order_count,
    avg_order_value,
    NTILE(5) OVER (ORDER BY lifetime_value DESC) AS value_quintile
FROM customer_ltv
ORDER BY lifetime_value DESC;

-- ----------------------------------------------------------------------------
-- 9. Product performance vs category average using AVG() OVER
-- ----------------------------------------------------------------------------
-- What it does: For each product, shows its revenue vs the average revenue
--   of its product category using AVG() OVER with PARTITION BY.
-- Why it matters: Comparing an item to its group average reveals relative
--   performance (above/below average).
-- Business question: "How does each product's revenue compare to its
--   category average?"
WITH product_revenue AS (
    SELECT
        Product,
        Product_Category,
        SUM(Total_Sales) AS product_revenue
    FROM sales
    GROUP BY Product, Product_Category
)
SELECT
    Product,
    Product_Category,
    product_revenue,
    AVG(product_revenue) OVER (
        PARTITION BY Product_Category
    ) AS category_avg_revenue,
    product_revenue - AVG(product_revenue) OVER (
        PARTITION BY Product_Category
    ) AS vs_category_avg
FROM product_revenue
ORDER BY Product_Category, product_revenue DESC;

-- ----------------------------------------------------------------------------
-- 10. Sequential order analysis using LAG and LEAD
-- ----------------------------------------------------------------------------
-- What it does: For each order, looks at the previous order's value (LAG)
--   and next order's value (LEAD) to calculate sequential differences.
-- Why it matters: LAG and LEAD enable time-series-like analysis directly
--   in SQL without complex self-joins.
-- Business question: "How does each order's value compare to the order
--   before and after it (chronologically)?"
WITH ordered_sales AS (
    SELECT
        *,
        ROW_NUMBER() OVER (ORDER BY Order_Date, Customer_ID) AS sale_sequence
    FROM sales
)
SELECT
    Order_Date,
    Customer_ID,
    Total_Sales,
    LAG(Total_Sales) OVER (ORDER BY Order_Date, Customer_ID) AS prev_order_value,
    LEAD(Total_Sales) OVER (ORDER BY Order_Date, Customer_ID) AS next_order_value,
    Total_Sales - LAG(Total_Sales) OVER (ORDER BY Order_Date, Customer_ID) AS diff_from_prev,
    LEAD(Total_Sales) OVER (ORDER BY Order_Date, Customer_ID) - Total_Sales AS diff_to_next
FROM ordered_sales
WHERE sale_sequence BETWEEN 1 AND 10  -- First 10 orders for demo
ORDER BY sale_sequence;

-- ----------------------------------------------------------------------------
-- 11. Quarterly sales performance with CTE and window functions
-- ----------------------------------------------------------------------------
-- What it does: Groups sales by quarter, calculates quarterly revenue,
--   and shows quarter-over-quarter growth.
-- Why it matters: Quarterly analysis is standard for business reporting.
-- Business question: "What is the quarterly revenue trend and growth rate?"
WITH quarterly_sales AS (
    SELECT
        strftime('%Y-Q', Order_Date) AS year_quarter,
        SUM(Total_Sales)             AS quarterly_revenue
    FROM sales
    GROUP BY strftime('%Y-Q', Order_Date)
),
quarterly_growth AS (
    SELECT
        year_quarter,
        quarterly_revenue,
        LAG(quarterly_revenue) OVER (ORDER BY year_quarter) AS prev_quarter_revenue
    FROM quarterly_sales
)
SELECT
    year_quarter,
    quarterly_revenue,
    prev_quarter_revenue,
    CASE
        WHEN prev_quarter_revenue IS NULL THEN NULL
        ELSE ROUND(100.0 * (quarterly_revenue - prev_quarter_revenue) / prev_quarter_revenue, 2)
    END AS qoq_growth_percent
FROM quarterly_growth
ORDER BY year_quarter;

-- ----------------------------------------------------------------------------
-- 12. Detecting streaks: consecutive days with sales above average
-- ----------------------------------------------------------------------------
-- What it does: Uses window functions in a clever way to flag days where
--   daily revenue exceeds the overall average, then identifies streaks.
-- Why it matters: This pattern demonstrates advanced window function usage
--   for sequence analysis.
-- Business question: "Identify streaks of consecutive days where daily
--   revenue was above the overall average."
WITH daily_stats AS (
    SELECT
        Order_Date       AS sales_date,
        SUM(Total_Sales) AS daily_revenue
    FROM sales
    GROUP BY Order_Date
),
daily_flagged AS (
    SELECT
        sales_date,
        daily_revenue,
        CASE
            WHEN daily_revenue > (SELECT AVG(daily_revenue) FROM daily_stats)
            THEN 1 ELSE 0
        END AS above_average
    FROM daily_stats
),
streak_calc AS (
    SELECT
        sales_date,
        daily_revenue,
        above_average,
        -- This creates a streak ID: changes when above_average changes
        SUM(above_average) OVER (ORDER BY sales_date
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) - above_average * SUM(1 - above_average) OVER (ORDER BY sales_date
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS streak_id
    FROM daily_flagged
)
SELECT
    MIN(sales_date) AS streak_start,
    MAX(sales_date) AS streak_end,
    COUNT(*)        AS streak_length,
    AVG(daily_revenue) AS avg_daily_revenue_during_streak
FROM streak_calc
WHERE above_average = 1
GROUP BY streak_id
HAVING COUNT(*) >= 3  -- Only streaks of 3+ days
ORDER BY streak_length DESC;
