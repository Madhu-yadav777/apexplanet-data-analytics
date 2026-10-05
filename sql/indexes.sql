-- ============================================================================
-- ApexPlanet Data Analytics - Task 2: Query Optimization & Indexing
-- ============================================================================
-- This file demonstrates SQLite query optimization using EXPLAIN QUERY PLAN
-- and practical index creation for the most common query patterns in this
-- project.
--
-- IMPORTANT NOTES ON SQLITE INDEXING:
-- - SQLite automatically creates an index on the primary key (rowid).
-- - The sales table has NO declared PRIMARY KEY, so adding one is optional.
-- - In SQLite, indexes on VARCHAR columns work fine for equality and range
--   searches. Date stored as TEXT (YYYY-MM-DD) sorts correctly lexicographically.
-- - Indexes help SELECT queries but slow down INSERT/UPDATE/DELETE.
--   Our dataset is small (~2,000 rows), so the practical performance gain is
--   modest here; the real value is: (a) documented query patterns,
--   (b) scalability when the data grows, and (c) learning the technique.
-- ============================================================================

-- ============================================================================
-- STEP 1: EXPLAIN QUERY PLAN (before indexing)
-- ============================================================================
-- EXPLAIN QUERY PLAN shows SQLite's chosen execution strategy:
--   SCAN  -> full table scan (reads every row; unavoidable for tiny tables
--            or when SQLite decides the index isn't worth it)
--   SEARCH -> index-based lookup (uses an index)
--
-- Below we run explain queries on the most common access patterns in this
-- project. In a small database all paths may show SCAN — that is normal for
-- SQLite. The index creation below is still valid best practice.

-- 1.1 Query pattern: filter orders by date range (monthly reporting).
-- EXPLAIN QUERY PLAN
-- SELECT * FROM sales
-- WHERE Order_Date BETWEEN '2023-01-01' AND '2023-12-31';
--
-- 1.2 Query pattern: group sales by product category (KPI dashboards).
-- EXPLAIN QUERY PLAN
-- SELECT Product_Category, SUM(Total_Sales) FROM sales GROUP BY Product_Category;
--
-- 1.3 Query pattern: find a specific customer's orders (customer lookup).
-- EXPLAIN QUERY PLAN
-- SELECT * FROM sales WHERE Customer_ID = 'CUST_000001';
--
-- 1.4 Query pattern: filter by payment method (operational report).
-- EXPLAIN QUERY PLAN
-- SELECT * FROM sales WHERE Payment_Method = 'Credit Card';
--
-- 1.5 Query pattern: aggregate by date (time-series analysis).
-- EXPLAIN QUERY PLAN
-- SELECT strftime('%Y-%m', Order_Date), SUM(Total_Sales)
--   FROM sales GROUP BY strftime('%Y-%m', Order_Date);

-- ============================================================================
-- STEP 2: CREATE INDEXES
-- ============================================================================

-- Index 1: sales Order_Date
-- Why: Every time-series query (monthly trend, YoY comparison, moving average)
--   filters or groups by Order_Date. An index makes the date filter and the
--   date-based GROUP BY dramatically faster as data grows.
-- Query that benefits: 1.1 and 1.5 above (monthly revenue trend queries).
CREATE INDEX IF NOT EXISTS idx_sales_order_date ON sales(Order_Date);

-- Index 2: sales Product_Category
-- Why: Category performance is a core KPI queried repeatedly (dashboards,
--   category_performance view). Grouping/joining on this column becomes
--   index-driven.
-- Query that benefits: 1.2 above and the category_performance view.
CREATE INDEX IF NOT EXISTS idx_sales_product_category ON sales(Product_Category);

-- Index 3: sales Customer_ID
-- Why: Customer-level lookups (customer_revenue_summary view, CRM reports,
--   personalization) benefit from direct lookup instead of scanning all rows.
-- Query that benefits: 1.3 above.
CREATE INDEX IF NOT EXISTS idx_sales_customer_id ON sales(Customer_ID);

-- Index 4: sales Payment_Method
-- Why: Payment method analysis is a routine operational query.
-- Query that benefits: 1.4 above and payment_method_summary view.
CREATE INDEX IF NOT EXISTS idx_sales_payment_method ON sales(Payment_Method);

-- Index 5: sales City (geographic analysis)
-- Why: City-level reporting and the city-to-region JOIN in reports.
-- Query that benefits: city_region_revenue view.
CREATE INDEX IF NOT EXISTS idx_sales_city ON sales(City);

-- Index 6: city_regions (primary lookup key, kept for reference-table hygiene)
-- Note: This is a reference table used in JOINs. The primary key on City
--   is auto-created by SQLite for the INTEGER PRIMARY KEY. Keeping an explicit
--   index documents intent and helps if the table gains columns later.
CREATE INDEX IF NOT EXISTS idx_city_regions_city ON city_regions(City);

-- ============================================================================
-- STEP 3: EXPLAIN QUERY PLAN (after indexing)
-- ============================================================================
-- Re-run the same patterns to observe improved execution strategies.
-- Expected improvement: date-filter and customer-lookup queries transition
-- from full SCAN to index SEARCH operations (when the dataset is large enough
-- for SQLite to prefer the index over a sequential scan).

-- 3.1 Post-index: date range filter
-- EXPLAIN QUERY PLAN
-- SELECT * FROM sales
-- WHERE Order_Date BETWEEN '2023-01-01' AND '2023-12-31';

-- 3.2 Post-index: category grouping
-- EXPLAIN QUERY PLAN
-- SELECT Product_Category, SUM(Total_Sales) FROM sales GROUP BY Product_Category;

-- 3.3 Post-index: customer lookup
-- EXPLAIN QUERY PLAN
-- SELECT * FROM sales WHERE Customer_ID = 'CUST_000001';

-- 3.4 Post-index: payment method filter
-- EXPLAIN QUERY PLAN
-- SELECT * FROM sales WHERE Payment_Method = 'Credit Card';

-- ============================================================================
-- STEP 4: VERIFY INDEXES EXISTS & CLEANUP HELPERS
-- ============================================================================
-- Show all indexes on the sales table (what SQLite will actually use).
-- SELECT name, sql FROM sqlite_master
-- WHERE type = 'index' AND tbl_name = 'sales';
--
-- Optional: remove unused indexes to reduce write overhead.
-- DROP INDEX IF EXISTS idx_sales_payment_method;
-- DROP INDEX IF EXISTS idx_city_regions_city;
--
-- IMPORTANT RULES FOR FUTURE INDEXING (apply these, don't add blindly):
-- 1. Only index columns used in WHERE / JOIN / ORDER BY / GROUP BY
--    with real query volume.
-- 2. Put the most selective (distinct-value-rich) filter first in a
--    composite index.
-- 3. Index selectivity > 20% (i.e., many distinct values) is a good rule of
--    thumb; indexes on low-cardinality columns rarely help.
-- 4. Re-check EXPLAIN QUERY PLAN after schema growth.
-- 5. Never index columns used only for display in a SELECT list.
-- ============================================================================
