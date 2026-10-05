-- ============================================================================
-- ApexPlanet Data Analytics - Task 2: Business Questions Answered with SQL
-- ============================================================================
-- Over 20 real business questions answered using SQL against the ACTUAL
-- Task 1 dataset (database/apexplanet_sales.db, table: sales).
-- Each query is complete, valid, and directly runnable.
-- ============================================================================

-- ============================================================================
-- SECTION A: OVERVIEW & KPIs
-- ============================================================================

-- Q1. What is the total revenue?
SELECT SUM(Total_Sales) AS total_revenue FROM sales;

-- Q2. How many orders were placed?
SELECT COUNT(*) AS total_orders FROM sales;

-- Q3. What is the total quantity sold?
SELECT SUM(Quantity) AS total_quantity_sold FROM sales;

-- Q4. What is the average order value?
SELECT ROUND(AVG(Total_Sales), 2) AS average_order_value FROM sales;

-- Q5. What is the average customer rating?
SELECT ROUND(AVG(Customer_Rating), 2) AS avg_customer_rating FROM sales;

-- Q6. How many unique customers made purchases?
SELECT COUNT(DISTINCT Customer_ID) AS unique_customers FROM sales;

-- Q7. What is the largest and smallest order value?
SELECT
    MAX(Total_Sales)  AS max_order_value,
    MIN(Total_Sales)  AS min_order_value
FROM sales;

-- ============================================================================
-- SECTION B: PRODUCT PERFORMANCE
-- ============================================================================

-- Q8. Which product category generates the highest revenue?
SELECT
    Product_Category,
    SUM(Total_Sales) AS revenue,
    COUNT(*)         AS orders
FROM sales
GROUP BY Product_Category
ORDER BY revenue DESC
LIMIT 1;

-- Q9. What is the total revenue by product category?
SELECT
    Product_Category,
    SUM(Total_Sales) AS total_revenue,
    SUM(Quantity)    AS total_quantity,
    COUNT(*)         AS order_count
FROM sales
GROUP BY Product_Category
ORDER BY total_revenue DESC;

-- Q10. Which product has the highest revenue?
SELECT
    Product,
    SUM(Total_Sales) AS revenue,
    COUNT(*)         AS orders
FROM sales
GROUP BY Product
ORDER BY revenue DESC
LIMIT 1;

-- Q11. Top 10 products by revenue (with category).
SELECT
    Product,
    Product_Category,
    SUM(Total_Sales) AS revenue,
    SUM(Quantity)    AS quantity_sold
FROM sales
GROUP BY Product, Product_Category
ORDER BY revenue DESC
LIMIT 10;

-- Q12. Which category has the highest quantity sold?
SELECT
    Product_Category,
    SUM(Quantity) AS total_quantity
FROM sales
GROUP BY Product_Category
ORDER BY total_quantity DESC
LIMIT 1;

-- Q13. Which products have a discount applied on every order?
-- (products where every order row has Discount > 0)
SELECT
    Product,
    COUNT(*)            AS order_count,
    COUNT(CASE WHEN Discount > 0 THEN 1 END) AS discounted_orders,
    COUNT(CASE WHEN Discount > 0 THEN 1 END) * 100.0 / COUNT(*) AS discount_rate
FROM sales
GROUP BY Product
HAVING discount_rate = 100
ORDER BY discount_rate DESC;

-- ============================================================================
-- SECTION C: CUSTOMER ANALYSIS
-- ============================================================================

-- Q14. Who are the top 10 customers by revenue?
SELECT
    Customer_ID,
    SUM(Total_Sales)        AS lifetime_value,
    COUNT(*)                AS order_count,
    ROUND(AVG(Total_Sales), 2) AS avg_order_value,
    COUNT(DISTINCT Product_Category) AS categories_purchased
FROM sales
GROUP BY Customer_ID
ORDER BY lifetime_value DESC
LIMIT 10;

-- Q15. Which customer is the most frequent buyer (most orders)?
SELECT
    Customer_ID,
    COUNT(*) AS order_count,
    SUM(Total_Sales) AS total_spent
FROM sales
GROUP BY Customer_ID
ORDER BY order_count DESC
LIMIT 1;

-- Q16. How much did customers spend on average vs total?
SELECT
    COUNT(DISTINCT Customer_ID) AS customers,
    SUM(Total_Sales)            AS total_customer_revenue,
    ROUND(AVG(Total_Sales), 2)  AS avg_spending_per_customer
FROM sales;

-- ============================================================================
-- SECTION D: GEOGRAPHIC & REGIONAL PERFORMANCE
-- ============================================================================

-- Q17. Which cities generate the highest revenue?
SELECT
    City,
    SUM(Total_Sales) AS revenue,
    COUNT(*)         AS orders,
    COUNT(DISTINCT Customer_ID) AS customers
FROM sales
GROUP BY City
ORDER BY revenue DESC
LIMIT 10;

-- Q18. Which city has the highest average order value?
SELECT
    City,
    ROUND(AVG(Total_Sales), 2) AS avg_order_value,
    SUM(Total_Sales)           AS total_revenue
FROM sales
GROUP BY City
ORDER BY avg_order_value DESC
LIMIT 1;

-- Q19. Revenue by US region (uses city_regions reference table).
SELECT
    cr.Region,
    SUM(s.Total_Sales) AS revenue,
    COUNT(*)           AS orders
FROM sales s
JOIN city_regions cr ON s.City = cr.City
GROUP BY cr.Region
ORDER BY revenue DESC;

-- Q20. Which region has the highest total revenue?
SELECT
    cr.Region,
    SUM(s.Total_Sales) AS revenue,
    COUNT(*)           AS orders
FROM sales s
JOIN city_regions cr ON s.City = cr.City
GROUP BY cr.Region
ORDER BY revenue DESC
LIMIT 1;

-- ============================================================================
-- SECTION E: PAYMENT METHODS
-- ============================================================================

-- Q21. Which payment method generates the highest revenue?
SELECT
    Payment_Method,
    COUNT(*)         AS transactions,
    SUM(Total_Sales) AS revenue,
    ROUND(AVG(Total_Sales), 2) AS avg_transaction_value
FROM sales
GROUP BY Payment_Method
ORDER BY revenue DESC
LIMIT 1;

-- Q22. Which payment method is most commonly used?
SELECT
    Payment_Method,
    COUNT(*) AS transaction_count
FROM sales
GROUP BY Payment_Method
ORDER BY transaction_count DESC
LIMIT 1;

-- Q23. Payment method distribution as percentages.
SELECT
    Payment_Method,
    COUNT(*) AS transactions,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS share_of_transactions_percent
FROM sales
GROUP BY Payment_Method
ORDER BY transactions DESC;

-- ============================================================================
-- SECTION F: TEMPORAL ANALYSIS (MONTHLY / QUARTERLY / YEARLY)
-- ============================================================================

-- Q24. What are the monthly revenue trends?
SELECT
    strftime('%Y-%m', Order_Date) AS year_month,
    SUM(Total_Sales)              AS monthly_revenue,
    COUNT(*)                      AS order_count,
    COUNT(DISTINCT Customer_ID)   AS active_customers
FROM sales
GROUP BY strftime('%Y-%m', Order_Date)
ORDER BY year_month;

-- Q25. Which month has the highest revenue?
SELECT
    strftime('%Y-%m', Order_Date) AS year_month,
    SUM(Total_Sales) AS monthly_revenue
FROM sales
GROUP BY strftime('%Y-%m', Order_Date)
ORDER BY monthly_revenue DESC
LIMIT 1;

-- Q26. Which month has the lowest revenue?
SELECT
    strftime('%Y-%m', Order_Date) AS year_month,
    SUM(Total_Sales) AS monthly_revenue
FROM sales
GROUP BY strftime('%Y-%m', Order_Date)
ORDER BY monthly_revenue
LIMIT 1;

-- Q27. Monthly revenue trend with growth over previous month.
WITH monthly_rev AS (
    SELECT
        strftime('%Y-%m', Order_Date) AS year_month,
        SUM(Total_Sales) AS monthly_revenue
    FROM sales
    GROUP BY strftime('%Y-%m', Order_Date)
)
SELECT
    year_month,
    monthly_revenue,
    LAG(monthly_revenue) OVER (ORDER BY year_month) AS prev_month_revenue,
    ROUND(100.0 * (monthly_revenue - LAG(monthly_revenue) OVER (ORDER BY year_month))
          / LAG(monthly_revenue) OVER (ORDER BY year_month), 2) AS mom_growth_pct
FROM monthly_rev
ORDER BY year_month;

-- Q28. Year-over-year comparison (2023 vs 2024).
SELECT
    strftime('%Y', Order_Date) AS year,
    SUM(Total_Sales)           AS total_revenue,
    COUNT(*)                   AS order_count,
    ROUND(AVG(Total_Sales), 2) AS avg_order_value
FROM sales
GROUP BY strftime('%Y', Order_Date)
ORDER BY year;

-- ============================================================================
-- SECTION G: DISCOUNT ANALYSIS
-- ============================================================================

-- Q29. How much discount revenue is being given away (total discount amount)?
SELECT
    ROUND(SUM(Unit_Price * Quantity * Discount / 100), 2) AS total_discount_given
FROM sales;

-- Q30. Orders by discount tier (0% / 1-10% / 11-20% / 21-30% / 30%+).
SELECT
    CASE
        WHEN Discount = 0 THEN 'No Discount'
        WHEN Discount <= 10 THEN '1-10%'
        WHEN Discount <= 20 THEN '11-20%'
        WHEN Discount <= 30 THEN '21-30%'
    END AS discount_tier,
    COUNT(*) AS order_count,
    SUM(Total_Sales) AS revenue
FROM sales
GROUP BY discount_tier
ORDER BY order_count DESC;

-- ============================================================================
-- SECTION H: CUSTOMER SATISFACTION
-- ============================================================================

-- Q31. Which product category has the highest customer rating?
SELECT
    Product_Category,
    ROUND(AVG(Customer_Rating), 2) AS avg_rating,
    COUNT(*) AS review_count
FROM sales
GROUP BY Product_Category
ORDER BY avg_rating DESC
LIMIT 1;

-- Q32. Correlation between discount and customer rating (average rating per discount tier).
SELECT
    CASE
        WHEN Discount = 0 THEN 'No Discount'
        WHEN Discount <= 10 THEN '1-10%'
        WHEN Discount <= 20 THEN '11-20%'
        WHEN Discount <= 30 THEN '21-30%'
    END AS discount_tier,
    ROUND(AVG(Customer_Rating), 2) AS avg_rating,
    COUNT(*) AS order_count
FROM sales
GROUP BY discount_tier
ORDER BY avg_rating DESC;

-- Q33. Average customer rating overall.
SELECT
    ROUND(AVG(Customer_Rating), 2) AS avg_customer_rating,
    MIN(Customer_Rating) AS min_rating,
    MAX(Customer_Rating) AS max_rating
FROM sales;

-- ============================================================================
-- SECTION I: DEMOGRAPHIC SEGMENTATION
-- ============================================================================

-- Q34. How does revenue vary by customer gender?
SELECT
    Gender,
    COUNT(*)         AS order_count,
    SUM(Total_Sales) AS total_revenue,
    ROUND(AVG(Total_Sales), 2) AS avg_order_value,
    COUNT(DISTINCT Customer_ID) AS customers
FROM sales
GROUP BY Gender
ORDER BY total_revenue DESC;

-- Q35. How does revenue vary by age group?
-- We derive age groups from the Age column (no dedicated age_group column exists).
SELECT
    CASE
        WHEN Age < 25 THEN '18-24 (Young Adult)'
        WHEN Age < 45 THEN '25-44 (Adult)'
        WHEN Age < 60 THEN '45-59 (Middle-aged)'
        ELSE '60+ (Senior)'
    END AS age_group,
    COUNT(*)         AS order_count,
    SUM(Total_Sales) AS total_revenue,
    ROUND(AVG(Total_Sales), 2) AS avg_order_value
FROM sales
GROUP BY age_group
ORDER BY total_revenue DESC;

-- Q36. Which gender spends more on average?
SELECT
    Gender,
    ROUND(AVG(Total_Sales), 2) AS avg_order_value
FROM sales
GROUP BY Gender
ORDER BY avg_order_value DESC;

-- ============================================================================
-- SECTION J: PRODUCT & QUANTITY INSIGHTS
-- ============================================================================

-- Q37. Which products are high-value but low-volume vs low-value high-volume?
-- (reveals premium vs mass-market product positioning)
SELECT
    Product,
    SUM(Total_Sales)            AS revenue,
    SUM(Quantity)               AS total_units,
    ROUND(AVG(Total_Sales), 2)  AS avg_order_value,
    COUNT(*)                    AS order_count,
    CASE
        WHEN COUNT(*) > AVG(COUNT(*)) OVER () THEN 'High-volume'
        ELSE 'Low-volume'
    END AS volume_category
FROM sales
GROUP BY Product
ORDER BY revenue DESC
LIMIT 10;

-- Q38. Total revenue by product category and payment method cross-tab.
SELECT
    Product_Category,
    Payment_Method,
    SUM(Total_Sales) AS revenue,
    COUNT(*) AS orders
FROM sales
GROUP BY Product_Category, Payment_Method
ORDER BY Product_Category, revenue DESC;

-- ============================================================================
-- SECTION K: VALUE-BASED BUSINESS INSIGHTS
-- ============================================================================

-- Q39. What share of revenue comes from the top 10% of customers (Pareto analysis)?
WITH customer_revenue AS (
    SELECT
        Customer_ID,
        SUM(Total_Sales) AS customer_revenue
    FROM sales
    GROUP BY Customer_ID
),
ranked AS (
    SELECT
        Customer_ID,
        customer_revenue,
        PERCENT_RANK() OVER (ORDER BY customer_revenue ASC) AS revenue_percentile
    FROM customer_revenue
)
SELECT
    ROUND(SUM(customer_revenue), 2) AS top_10_percent_revenue,
    ROUND(SUM(customer_revenue) * 100.0 / (SELECT SUM(customer_revenue) FROM ranked), 2) AS share_of_total_revenue_pct
FROM ranked
WHERE revenue_percentile >= 0.90;

-- Q40. Which category combines highest revenue AND highest quantity (sweet spot)?
SELECT
    Product_Category,
    SUM(Total_Sales)   AS total_revenue,
    SUM(Quantity)      AS total_quantity,
    ROUND(SUM(Total_Sales) / SUM(Quantity), 2) AS avg_value_per_unit
FROM sales
GROUP BY Product_Category
ORDER BY total_revenue DESC, total_quantity DESC
LIMIT 3;

-- Q41. Repeat purchase potential: customers who ordered more than once.
SELECT
    COUNT(DISTINCT Customer_ID)                 AS repeat_customers,
    COUNT(DISTINCT CASE WHEN cnt > 1 THEN Customer_ID END) AS actually_repeated,
    ROUND(COUNT(DISTINCT CASE WHEN cnt > 1 THEN Customer_ID END) * 100.0
          / COUNT(*), 2) AS repeat_rate_pct
FROM (
    SELECT Customer_ID, COUNT(*) AS cnt FROM sales GROUP BY Customer_ID
);
