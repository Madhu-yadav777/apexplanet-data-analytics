-- ============================================================================
-- ApexPlanet Data Analytics - Task 2: SQL Fundamentals
-- ============================================================================
-- Database : database/apexplanet_sales.db
-- Table    : sales (imported from data/processed/cleaned_dataset.csv)
-- Reference: city_regions (City -> Region mapping)
--
-- Each query below demonstrates one SQL concept using the ACTUAL Task 1
-- dataset. Every query is valid, executable, and annotated with the
-- business question it answers.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. SELECT - Retrieve specific columns
-- ----------------------------------------------------------------------------
-- What it does: Fetches order details for every sale.
-- Why it matters: SELECT is the foundation of every SQL query. It lets us
--   pick only the columns we care about instead of dumping the whole row.
-- Business question: "Show me customer, product, and revenue for each order."
SELECT
    Customer_ID,
    Order_Date,
    Product,
    Product_Category,
    Quantity,
    Total_Sales
FROM
    sales;

-- ----------------------------------------------------------------------------
-- 2. WHERE - Filter rows with a condition
-- ----------------------------------------------------------------------------
-- What it does: Returns only orders where the discount exceeds 10%.
-- Why it matters: WHERE lets us narrow results to a meaningful subset, which
--   is critical for targeted business analysis.
-- Business question: "Which orders had a discount greater than 10%?"
SELECT
    Customer_ID,
    Product,
    Discount,
    Total_Sales
FROM
    sales
WHERE
    Discount > 10;

-- ----------------------------------------------------------------------------
-- 3. ORDER BY - Sort results
-- ----------------------------------------------------------------------------
-- What it does: Lists all orders sorted by total sales in descending order.
-- Why it matters: Sorting helps spot top performers at a glance.
-- Business question: "Which are the highest-value orders?"
SELECT
    Customer_ID,
    Order_Date,
    Product,
    Total_Sales
FROM
    sales
ORDER BY
    Total_Sales DESC;

-- ----------------------------------------------------------------------------
-- 4. LIMIT - Restrict the number of rows
-- ----------------------------------------------------------------------------
-- What it does: Returns only the top 5 orders by revenue.
-- Why it matters: LIMIT keeps results manageable and focuses on the leaders.
-- Business question: "What are the 5 highest-revenue orders?"
SELECT
    Customer_ID,
    Order_Date,
    Product,
    Total_Sales
FROM
    sales
ORDER BY
    Total_Sales DESC
LIMIT 5;

-- ----------------------------------------------------------------------------
-- 5. INNER JOIN - Combine two tables on matching keys
-- ----------------------------------------------------------------------------
-- What it does: Joins the sales table with the city_regions reference table
--   to enrich each order with its US region.
-- Why it matters: INNER JOIN lets us pull in dimensional data (like region)
--   that lives in a separate reference table.
-- Business question: "What region does each order belong to?"
SELECT
    s.Customer_ID,
    s.City,
    cr.Region,
    s.Product,
    s.Total_Sales
FROM
    sales s
INNER JOIN
    city_regions cr ON s.City = cr.City;

-- ----------------------------------------------------------------------------
-- 6. LEFT JOIN - Keep all rows from the left table
-- ----------------------------------------------------------------------------
-- What it does: Returns every sale, and if a city has no region mapping,
--   the Region column will be NULL instead of dropping the row.
-- Why it matters: LEFT JOIN guarantees no data loss when the right table
--   may not have a matching row for every key.
-- Business question: "Show all orders with region, even if some cities
--   don't have a region mapping yet."
SELECT
    s.Customer_ID,
    s.City,
    COALESCE(cr.Region, 'Unmapped') AS Region,
    s.Total_Sales
FROM
    sales s
LEFT JOIN
    city_regions cr ON s.City = cr.City;

-- ----------------------------------------------------------------------------
-- 7. RIGHT JOIN - Not supported in SQLite
-- ----------------------------------------------------------------------------
-- SQLite does NOT support RIGHT JOIN directly. The standard workaround is
-- to rewrite the query with a LEFT JOIN and swap the tables.
--
-- A RIGHT JOIN of sales and city_regions is equivalent to a LEFT JOIN of
-- city_regions and sales:
--
-- Business question: "Which regions have NO sales recorded? (NULL city = no match)"
SELECT
    cr.Region,
    s.Customer_ID,
    s.City,
    s.Total_Sales
FROM
    city_regions cr
LEFT JOIN
    sales s ON cr.City = s.City;
-- Note: every region row is kept; unmatched sales rows appear as NULL.

-- ----------------------------------------------------------------------------
-- 8. FULL OUTER JOIN - Emulated in SQLite
-- ----------------------------------------------------------------------------
-- SQLite has no FULL OUTER JOIN. The equivalent is:
--   (LEFT JOIN) UNION (RIGHT JOIN as LEFT JOIN of the other table)
--
-- Business question: "Show all cities that appear in EITHER the sales data
--   OR the city_regions table, with matching sales where available."
SELECT
    s.Customer_ID, s.City, s.Product_Category, s.Total_Sales, cr.Region
FROM sales s
LEFT JOIN city_regions cr ON s.City = cr.City
UNION
SELECT
    s.Customer_ID, s.City, s.Product_Category, s.Total_Sales, cr.Region
FROM city_regions cr
LEFT JOIN sales s ON cr.City = s.City
WHERE s.Customer_ID IS NULL;

-- ----------------------------------------------------------------------------
-- 9. GROUP BY - Aggregate rows by category
-- ----------------------------------------------------------------------------
-- What it does: Groups sales by product category and computes total revenue
--   and order count for each.
-- Why it matters: GROUP BY is the core of summarization; it collapses many
--   rows into one per group.
-- Business question: "How much revenue does each product category generate?"
SELECT
    Product_Category,
    COUNT(*)              AS order_count,
    SUM(Total_Sales)      AS total_revenue,
    AVG(Total_Sales)      AS avg_order_value
FROM
    sales
GROUP BY
    Product_Category
ORDER BY
    total_revenue DESC;

-- ----------------------------------------------------------------------------
-- 10. HAVING - Filter after aggregation
-- ----------------------------------------------------------------------------
-- What it does: Returns only categories with total revenue above $50,000.
-- Why it matters: HAVING filters on the AGGREGATED value, unlike WHERE which
--   filters individual rows before grouping.
-- Business question: "Which categories generated more than $50,000 in total revenue?"
SELECT
    Product_Category,
    SUM(Total_Sales) AS total_revenue
FROM
    sales
GROUP BY
    Product_Category
HAVING
    SUM(Total_Sales) > 50000
ORDER BY
    total_revenue DESC;

-- ----------------------------------------------------------------------------
-- 11. COUNT - Count rows or values
-- ----------------------------------------------------------------------------
-- What it does: Counts the total number of orders and distinct customers.
-- Why it matters: COUNT is the simplest aggregation and the basis for
--   many KPIs (order volume, customer count, etc.).
-- Business question: "How many orders were placed and how many unique
--   customers made them?"
SELECT
    COUNT(*)                    AS total_orders,
    COUNT(DISTINCT Customer_ID) AS unique_customers
FROM
    sales;

-- ----------------------------------------------------------------------------
-- 12. SUM - Sum numeric values
-- ----------------------------------------------------------------------------
-- What it does: Computes total revenue and total units sold across all orders.
-- Why it matters: SUM gives the absolute scale of the business.
-- Business question: "What is the total revenue and total quantity sold?"
SELECT
    SUM(Total_Sales) AS total_revenue,
    SUM(Quantity)    AS total_quantity_sold
FROM
    sales;

-- ----------------------------------------------------------------------------
-- 13. AVG - Average of numeric values
-- ----------------------------------------------------------------------------
-- What it does: Computes the average order value and average customer rating.
-- Why it matters: AVG smooths out individual variation to reveal the norm.
-- Business question: "What is the average order value and average customer
--   satisfaction rating?"
SELECT
    AVG(Total_Sales)       AS avg_order_value,
    AVG(Customer_Rating)   AS avg_rating
FROM
    sales;

-- ----------------------------------------------------------------------------
-- 14. MIN - Minimum value
-- ----------------------------------------------------------------------------
-- What it does: Finds the smallest order value and the lowest rating.
-- Why it matters: MIN identifies the lower bound, useful for spotting
--   anomalies or understanding the smallest transactions.
-- Business question: "What is the smallest order value and the lowest
--   customer rating in the dataset?"
SELECT
    MIN(Total_Sales)       AS min_order_value,
    MIN(Customer_Rating)   AS min_rating,
    MIN(Order_Date)        AS earliest_order
FROM
    sales;

-- ----------------------------------------------------------------------------
-- 15. MAX - Maximum value
-- ----------------------------------------------------------------------------
-- What it does: Finds the largest order value and the highest rating.
-- Why it matters: MAX identifies the upper bound, useful for understanding
--   peak performance and top-tier experiences.
-- Business question: "What is the largest single order value and the highest
--   customer rating?"
SELECT
    MAX(Total_Sales)       AS max_order_value,
    MAX(Customer_Rating)   AS max_rating,
    MAX(Order_Date)        AS latest_order
FROM
    sales;
