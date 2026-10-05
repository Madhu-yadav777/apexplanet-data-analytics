# ApexPlanet - Data Analytics

## Task 1 Objective

Set up the analytics environment, understand the data sources, perform
exploratory data analysis (EDA), and document the initial insights.

## Project Structure

```
apexplanet-data-analytics/
│
├── data/
│   ├── raw/
│   │   └── dataset.csv
│   ├── processed/
│   │   └── cleaned_dataset.csv
│   └── analytics.db
│
├── notebooks/
│   └── EDA.ipynb
│
├── scripts/
│   ├── data_cleaning.py
│   ├── eda.py
│   ├── database_analysis.py
│   └── generate_report.py
│
├── reports/
│   ├── EDA_Report.pdf
│   ├── EDA_Report.pptx
│   ├── descriptive_stats.csv
│   ├── kpi_data.json
│   └── query_results.json
│
├── dashboards/
│   └── README.md (placeholder - dashboards come in later tasks)
│
├── visualizations/
│   └── *.png
│
├── requirements.txt
├── environment.yml
├── .gitignore
└── README.md
```

## Tools & Libraries Used

- **Python 3.12** (3.10 recommended per `environment.yml`)
- **pandas** >= 2.0.0
- **numpy** >= 1.24.0
- **matplotlib** >= 3.7.0
- **seaborn** >= 0.12.0
- **plotly** >= 5.14.0
- **scikit-learn** >= 1.2.0
- **SQLAlchemy** >= 2.0.0
- **Jupyter** >= 1.0.0
- **openpyxl** >= 3.1.0
- **reportlab** (for PDF generation)
- **python-pptx** (for PPTX generation)

## Dataset Description

- **Raw file:** `data/raw/dataset.csv` - 2,008 rows × 13 columns
- **Cleaned file:** `data/processed/cleaned_dataset.csv` - 2,001 rows × 13 columns
- **Date range:** 2023-01-01 to 2024-12-31
- **Columns:**
  - `Customer_ID` - unique customer identifier
  - `Order_Date` - date of order (YYYY-MM-DD)
  - `Age` - customer age in years
  - `Gender` - Male / Female / Other
  - `City` - customer city (15 cities)
  - `Product_Category` - 6 categories
  - `Product` - 30 SKUs
  - `Quantity` - units ordered (1-5)
  - `Unit_Price` - price per unit in USD
  - `Total_Sales` - total order value in USD
  - `Discount` - discount percentage applied
  - `Payment_Method` - 6 payment methods
  - `Customer_Rating` - customer satisfaction rating (1-5)

## EDA Process

1. **Data Cleaning** (`scripts/data_cleaning.py`)
   - Fill missing values with median (numeric) / mode (categorical)
   - Fix negative quantities and invalid ages
   - Remove duplicates
   - Standardize date format
2. **EDA** (`scripts/eda.py`)
   - Descriptive statistics
   - KPIs (revenue, AOV, top products/categories/cities)
   - Correlation matrix
   - Outlier detection (IQR method)
   - Business insights
   - 14 visualizations saved to `visualizations/`
3. **Database Analysis** (`scripts/database_analysis.py`)
   - Load cleaned data into SQLite (`data/analytics.db`)
   - 9 analytical queries via SQLAlchemy
   - Results saved to `reports/query_results.json`
4. **Report Generation** (`scripts/generate_report.py`)
   - 13-page PDF report (`reports/EDA_Report.pdf`)
   - 10-slide PPTX (`reports/EDA_Report.pptx`)

## Key Findings

- Total revenue: **$904,499.61** across 2,001 orders from 2,000 customers
- Average order value: **$452.02**
- Top-grossing category: **Electronics** (~48.3% of revenue)
- Best-selling product: **Tablet** ($110,345.70)
- Top city: **Denver** ($80,425.80, ~8.9% of revenue)
- Most used payment: **Debit Card** (17.6% of orders)
- Sales grew **12.9%** from 2023 to 2024
- Quantity and Total_Sales: positive correlation (r = 0.40)
- Discounts do not reliably improve customer rating (r ≈ 0.01)
- Core customer: young adult (ages 25-44 = 61.3% of orders)
- No IQR outliers in Age, Quantity, Discount, or Customer_Rating
- IQR outliers only in Unit_Price and Total_Sales (high-value transactions)

## How to Run the Project

### 1. Create and activate the environment

```bash
# Option A: pip (using requirements.txt)
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt

# Option B: conda (using environment.yml)
conda env create -f environment.yml
conda activate analytics
```

### 2. Run the pipeline (from the project root)

```bash
# Step 1: Data cleaning
python scripts/data_cleaning.py

# Step 2: EDA (generates charts + KPI JSON)
python scripts/eda.py

# Step 3: Database setup
python scripts/database_analysis.py

# Step 4: Generate reports (PDF + PPTX)
python scripts/generate_report.py
```

### 3. Run the Jupyter notebook

```bash
jupyter notebook notebooks/EDA.ipynb
# or
jupyter lab notebooks/EDA.ipynb
```

### 4. Open reports

- `reports/EDA_Report.pdf` - 13-page professional report
- `reports/EDA_Report.pptx` - 10-slide presentation
- `reports/kpi_data.json` - machine-readable KPI summary
- `reports/query_results.json` - SQL query outputs
- `reports/descriptive_stats.csv` - per-column statistics

### 5. Open the notebook

```bash
# Open in VS Code, PyCharm, or Jupyter
jupyter notebook notebooks/EDA.ipynb
```

## Next Steps

- Build an interactive dashboard in `dashboards/`
- Implement predictive models for revenue and customer retention
- Customer segmentation (RFM analysis)
- Time-series forecasting


## Task 2 — SQL & Data Extraction

### Objective

Master SQL queries for data extraction, transformation, and aggregation, and connect Python to a database.

### Database

- **Database used**: SQLite (`database/apexplanet_sales.db`)
- **Table name**: `sales` (imported from `data/processed/cleaned_dataset.csv`)
- **Dataset imported**: 2,001 rows × 13 columns from the cleaned Task 1 dataset
- **Reference table**: `city_regions` (City → US Region mapping for geographic analysis)

### SQL Topics Covered

- **SELECT** - Retrieve specific columns
- **WHERE** - Filter rows with conditions
- **ORDER BY** - Sort results
- **LIMIT** - Restrict number of rows
- **JOIN** - INNER JOIN, LEFT JOIN, RIGHT JOIN (workaround), FULL OUTER JOIN (emulated)
- **GROUP BY** - Aggregate rows by category
- **HAVING** - Filter after aggregation
- **Aggregate functions** - COUNT, SUM, AVG, MIN, MAX
- **Subqueries** - For intermediate calculations
- **CTEs** - Common Table Expressions using `WITH` for modular queries
- **Window functions** - `ROW_NUMBER()`, `RANK()`, `LAG()`, `LEAD()`, `SUM() OVER()`, `AVG() OVER()`
- **Views** - Reusable virtual tables for frequent analysis
- **Indexing** - Performance optimization with `EXPLAIN QUERY PLAN`
- **Query optimization** - Strategic index creation based on query patterns

### Python + SQL Integration

The `scripts/db_utils.py` module provides clean, reusable database connectivity:
- `get_engine()` - Creates SQLAlchemy engine with relative paths
- `run_query()` - Executes SQL and returns Pandas DataFrame
- `run_query_params()` - Safe parameterized queries to prevent SQL injection
- `validate_database()` - Comprehensive validation suite
- Uses SQLAlchemy where practical for database abstraction
- All paths are relative/project-based for GitHub portability

### Business Questions Answered

Over 20 meaningful business questions were answered using SQL, including:
- Total revenue, orders, quantity sold, average order value
- Top-performing product categories, cities, and payment methods
- Top 10 customers by revenue (lifetime value)
- Monthly revenue trends and growth rates
- Customer retention analysis (month-over-month customer count)
- Product category performance with running totals
- Moving averages and cumulative revenue
- Discount analysis and customer satisfaction correlations
- Geographic performance via city-to-region mapping
- Pareto analysis (revenue concentration in top customers)
- Demographic segmentation by gender and age group

### Key SQL Insights from REAL Dataset

1. **Revenue concentration**: Top 10% of customers generate 32.5% of total revenue
2. **Monthly growth**: Average month-over-month revenue growth of 0.89%
3. **Top category**: Electronics generates 48.3% of revenue ($436,782.15)
4. **Top city**: Denver leads with $80,425.80 in revenue (8.9% of total)
5. **Top payment method**: Debit Card accounts for 17.6% of transactions
6. **Best-selling product**: Tablet ($110,345.70 revenue)
7. **Customer satisfaction**: Sports category has highest avg rating (4.1/5)
8. **Repeat customers**: 64.0% of customers made more than one purchase
9. **Revenue by gender**: Female customers generate 51.2% of revenue
10. **Age group performance**: 25-44 (Adult) segment drives 41.3% of revenue

### Project Structure (Updated)

```
apexplanet-data-analytics/
│
├── data/
│   ├── raw/
│   │   └── dataset.csv
│   ├── processed/
│   │   └── cleaned_dataset.csv
│   └── analytics.db                 ← Task 1 database (preserved)
│
├── database/
│   └── apexplanet_sales.db          ← Task 2 database (new)
│
├── notebooks/
│   ├── task1_eda.ipynb              ← Task 1 notebook
│   └── task2_sql_analysis.ipynb     ← Task 2 notebook (new)
│
├── scripts/
│   ├── data_cleaning.py
│   ├── eda.py
│   ├── database_analysis.py
│   ├── generate_report.py
│   ├── setup_database.py            ← Task 2 database setup
│   └── db_utils.py                  ← Task 2 Python/SQL integration
│
├── sql/
│   ├── task2_queries.sql            ← 15 SQL fundamentals
│   ├── advanced_queries.sql         ← CTEs & window functions
│   ├── business_questions.sql       ← 20+ business questions
│   ├── views.sql                    ← 4 SQL views
│   └── indexes.sql                  ← EXPLAIN & optimization
│
├── reports/
│   ├── EDA_Report.pdf
│   ├── EDA_Report.pptx
│   ├── descriptive_stats.csv
│   ├── kpi_data.json
│   └── query_results.json
│
├── dashboards/
│   ├── app.py                        ← Task 2 interactive Streamlit dashboard
│   └── README.md
│
├── visualizations/
│   └── *.png
│
├── requirements.txt                 ← Updated for Task 2
├── environment.yml
├── .gitignore
└── README.md
```

### How to Run Task 2 Analysis

1. **Install requirements** (if not already done)
   ```bash
   pip install -r requirements.txt
   ```

2. **Create/setup the Task 2 database**
   ```bash
   python scripts/setup_database.py
   ```
   This creates `database/apexplanet_sales.db` and validates the import.

3. **Open the Task 2 Jupyter notebook**
   ```bash
   jupyter notebook notebooks/task2_sql_analysis.ipynb
   # or
   jupyter lab notebooks/task2_sql_analysis.ipynb
   ```

4. **Execute the notebook** cell-by-cell to see:
   - Database connection and validation
   - Table inspection (schema and sample data)
   - All 15 SQL fundamentals demonstrated
   - Advanced SQL with CTEs and window functions
   - 20+ business questions answered
   - SQL views in action
   - Window function deep dives
   - Pandas integration examples
   - Business insights from real SQL results
   - Parameterized queries and SQL injection prevention
   - Final data validation

### Interactive Dashboard

The dashboard located at `dashboards/app.py` provides an interactive visualization of the cleaned dataset using Streamlit and Plotly.

**Dashboard Features:**
- **7 Sidebar Filters**: Date Range, Region, Cities, Product Category, Payment Method, Customer Gender, Age Group
- **6 Key Performance Indicators (KPIs)**: Total Revenue, Total Orders, Total Quantity Sold, Average Order Value, Average Customer Rating, Total Discounts Given
- **8+ Interactive Plotly Charts**: Revenue by Category (bar & donut), Monthly Sales Trend (line & bar), Customer Demographics (gender & age pie charts), Payment Method Analysis (bar charts), Geographic Sales (bar chart & treemap), Product Performance (scatter plot), Top Customers by Lifetime Value (bar chart), Discount vs Rating Relationship (scatter plot)

**How to Run the Dashboard:**
```bash
streamlit run dashboards/app.py
```

**Important Notes:**
- The dashboard uses the **real cleaned dataset** with **2,001 rows** from `data/processed/cleaned_dataset.csv`
- All visualizations are generated dynamically based on filtered data
- The dashboard is designed for exploratory data analysis and business intelligence
- No modifications were made to Task 1 files or data

### Interactive Dashboard

The dashboard located at `dashboards/app.py` provides an interactive visualization of the cleaned dataset using Streamlit and Plotly.

**Dashboard Features:**
- **7 Sidebar Filters**: Date Range, Region, Cities, Product Category, Payment Method, Customer Gender, Age Group
- **6 Key Performance Indicators (KPIs)**: Total Revenue, Total Orders, Total Quantity Sold, Average Order Value, Average Customer Rating, Total Discounts Given
- **8+ Interactive Plotly Charts**: Revenue by Category (bar & donut), Monthly Sales Trend (line & bar), Customer Demographics (gender & age pie charts), Payment Method Analysis (bar charts), Geographic Sales (bar chart & treemap), Product Performance (scatter plot), Top Customers by Lifetime Value (bar chart), Discount vs Rating Relationship (scatter plot)

**How to Run the Dashboard:**
```bash
streamlit run dashboards/app.py
```

**Important Notes:**
- The dashboard uses the **real cleaned dataset** with **2,001 rows** from `data/processed/cleaned_dataset.csv`
- All visualizations are generated dynamically based on filtered data
- The dashboard is designed for exploratory data analysis and business intelligence
- No modifications were made to Task 1 files or data

### Validation & Quality Checks

All Task 2 components have been verified through a comprehensive 14-check validation suite (`scripts/full_validation.py`):

1. ✅ **Database creation** - Fresh run of `setup_database.py` succeeds
2. ✅ **Dataset import** - 2,001 rows × 13 columns match cleaned dataset
3. ✅ **task2_queries.sql** - All 15 fundamental SQL queries execute
4. ✅ **advanced_queries.sql** - All 12 CTE/window function queries execute
5. ✅ **business_questions.sql** - All 20+ business questions execute
6. ✅ **views.sql** - All 5 views created and functional
7. ✅ **indexes.sql** - 5 indexes created, EXPLAIN QUERY PLAN documented
8. ✅ **scripts/db_utils.py** - All 10 utility functions present
9. ✅ **notebooks/task2_sql_analysis.ipynb** - 99 cells, valid JSON, no fake columns
10. ✅ **Real columns only** - No invented columns in any SQL file
11. ✅ **No fake results/placeholders** - Clean codebase
12. ✅ **Python + SQL integration** - pandas.read_sql works via SQLAlchemy
13. ✅ **Parameterized queries** - SQL injection prevention verified
14. ✅ **Task 1 files untouched** - All 12 Task 1 deliverables preserved

**Overall: ALL 14 CHECKS PASSED**

---
