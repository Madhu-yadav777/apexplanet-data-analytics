#!/usr/bin/env python3
"""
setup_database.py
==================
Task 2 - SQL & Data Extraction
Database setup script for the ApexPlanet Data Analytics project.

This script:
1. Inspects the cleaned Task 1 dataset (data/processed/cleaned_dataset.csv)
2. Creates the Task 2 database at database/apexplanet_sales.db
3. Imports the cleaned dataset into a properly typed `sales` table
4. Runs a comprehensive data validation suite

IMPORTANT: This script does NOT modify the original cleaned dataset.
It only reads from it and writes to the database.

Run from the project root:
    python scripts/setup_database.py

Requirements:
    - Python 3.8+
    - pandas
    - SQLAlchemy (optional; SQLite3 is built into Python stdlib)
"""

import os
import warnings
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text, inspect

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Project paths (portable, relative)
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CLEANED_DATASET = PROJECT_ROOT / "data" / "processed" / "cleaned_dataset.csv"
DATABASE_DIR = PROJECT_ROOT / "database"
DATABASE_PATH = DATABASE_DIR / "apexplanet_sales.db"

# Existing Task 1 database (kept separate for compatibility)
EXISTING_DB = PROJECT_ROOT / "data" / "analytics.db"

# US city -> region mapping used for geographic analysis
# (The cleaned Task 1 dataset contains City, not Region; the region
# mapping is stored as a reference table so it can be joined in SQL.)
CITY_REGION_MAP = [
    ("Boston", "Northeast"),
    ("New York", "Northeast"),
    ("Philadelphia", "Northeast"),
    ("Atlanta", "Southeast"),
    ("Austin", "Southeast"),
    ("Dallas", "Southeast"),
    ("Houston", "Southeast"),
    ("Miami", "Southeast"),
    ("San Antonio", "South Central"),
    ("Chicago", "Midwest"),
    ("Denver", "Midwest"),
    ("Los Angeles", "West"),
    ("Phoenix", "West"),
    ("San Diego", "West"),
    ("Seattle", "West"),
]

print("=" * 70)
print("TASK 2 - DATABASE SETUP")
print("=" * 70)
print(f"Project root     : {PROJECT_ROOT}")
print(f"Cleaned dataset  : {CLEANED_DATASET}")
print(f"Output database  : {DATABASE_PATH}")
print("=" * 70)


# ---------------------------------------------------------------------------
# STEP 1: Inspect the cleaned dataset
# ---------------------------------------------------------------------------
def inspect_dataset(path: Path) -> None:
    """Inspect the cleaned Task 1 dataset before importing."""
    print("\n--- STEP 1: Dataset inspection ---")
    df = pd.read_csv(path)
    print(f"Shape (rows, columns): {df.shape}")
    print("\nColumns and inferred dtypes:")
    for col, dtype in df.dtypes.items():
        print(f"  {col:20s} {dtype}")
    print(f"\nDate range (Order_Date): {df['Order_Date'].min()} to {df['Order_Date'].max()}")
    print("\nMissing values per column:")
    missing = df.isna().sum()
    total_rows = len(df)
    for col, cnt in missing.items():
        pct = (cnt / total_rows * 100) if total_rows else 0
        marker = " <-- NULLS PRESENT" if cnt > 0 else ""
        print(f"  {col:20s} {cnt:5d} ({pct:5.2f}%) {marker}")
    print(f"\nUnique Product Categories: {sorted(df['Product_Category'].unique())}")
    print(f"Unique Payment Methods: {sorted(df['Payment_Method'].unique())}")
    print(f"Unique Genders: {sorted(df['Gender'].unique())}")
    print(f"Unique Cities: {sorted(df['City'].unique())}")
    print(f"Unique customers (Customer_ID): {df['Customer_ID'].nunique()}")
    print(f"Duplicate Customer_ID rows: {(df['Customer_ID'].duplicated().sum())}")
    return df


# ---------------------------------------------------------------------------
# STEP 2: Create the database and table with proper types
# ---------------------------------------------------------------------------
def create_database(engine, df: pd.DataFrame) -> None:
    """Create the `sales` table with explicit SQLite types and import data."""
    print("\n--- STEP 2: Create database and table ---")

    # Explicit mapping of column -> SQLite type for full control
    # Note: datetime64[ns] columns must be converted to TEXT/ISO for SQLite.
    column_types = {
        "Customer_ID": "TEXT",      # customer identifier
        "Order_Date": "DATE",       # order date (stored as ISO TEXT in SQLite)
        "Age": "REAL",              # customer age
        "Gender": "TEXT",           # customer gender
        "City": "TEXT",             # city of delivery
        "Product_Category": "TEXT", # product category
        "Product": "TEXT",          # specific product name
        "Quantity": "INTEGER",      # units sold in order
        "Unit_Price": "REAL",       # price per unit
        "Total_Sales": "REAL",      # quantity * unit_price
        "Discount": "REAL",         # discount percentage
        "Payment_Method": "TEXT",   # payment method used
        "Customer_Rating": "REAL",  # product/customer rating 1-5
    }

    # Drop existing table so we start clean (idempotent)
    if inspect(engine).has_table("sales"):
        print("Dropping existing 'sales' table for clean re-import...")
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE sales"))
            conn.commit()

    # Convert date column to ISO date strings for SQLite storage
    df_import = df.copy()
    df_import["Order_Date"] = pd.to_datetime(df_import["Order_Date"]).dt.strftime(
        "%Y-%m-%d"
    )
    # Ensure numeric columns are truly numeric
    for col in ["Quantity", "Unit_Price", "Total_Sales", "Discount", "Customer_Rating"]:
        df_import[col] = pd.to_numeric(df_import[col], errors="coerce")

    # Build table with typed schema (SQLAlchemy will infer, but we declare types)
    df_import.to_sql("sales", engine, if_exists="replace", index=False)

    print(f"Table 'sales' created with {len(df_import)} rows")
    print(f"Columns: {list(df_import.columns)}")

    # Verify types after import
    print("\nSQLite types after import:")
    inspector = inspect(engine)
    col_defs = {c["name"]: c for c in inspector.get_columns("sales")}
    for col_name in df_import.columns:
        col = col_defs[col_name]
        print(f"  {col_name:20s} -> {col['type']}")

    # -----------------------------------------------------------------------
    # Create the city_regions reference table (geographic lookup)
    # -----------------------------------------------------------------------
    print("\n--- Creating city_regions reference table ---")
    with engine.connect() as conn:
        conn.execute(text(
            "CREATE TABLE IF NOT EXISTS city_regions ("
            "City TEXT PRIMARY KEY, Region TEXT NOT NULL)"
        ))
        conn.execute(text("DELETE FROM city_regions"))
        conn.execute(text(
            "INSERT INTO city_regions (City, Region) VALUES (:city, :region)"
        ), [{"city": city, "region": region} for city, region in CITY_REGION_MAP])
        conn.commit()
        n_rows = conn.execute(text("SELECT COUNT(*) FROM city_regions")).scalar()
        print(f"Inserted {n_rows} city -> region mappings.")

    # -----------------------------------------------------------------------
    # Create performance indexes
    # -----------------------------------------------------------------------
    print("\n--- Creating performance indexes ---")
    index_statements = [
        "CREATE INDEX IF NOT EXISTS idx_sales_order_date ON sales(Order_Date)",
        "CREATE INDEX IF NOT EXISTS idx_sales_product_category ON sales(Product_Category)",
        "CREATE INDEX IF NOT EXISTS idx_sales_customer_id ON sales(Customer_ID)",
        "CREATE INDEX IF NOT EXISTS idx_sales_payment_method ON sales(Payment_Method)",
        "CREATE INDEX IF NOT EXISTS idx_sales_city ON sales(City)",
        "CREATE INDEX IF NOT EXISTS idx_city_regions_city ON city_regions(City)",
    ]
    with engine.connect() as conn:
        for sql in index_statements:
            conn.execute(text(sql))
        conn.commit()
        created = conn.execute(text(
            "SELECT name FROM sqlite_master WHERE type='index'"
        )).mappings().fetchall()
        print("Indexes created:")
        for row in created:
            print(f"  - {row['name']}")

    # -----------------------------------------------------------------------
    # Apply views from sql/views.sql
    # -----------------------------------------------------------------------
    print("\n--- Applying SQL views from sql/views.sql ---")
    views_path = PROJECT_ROOT / "sql" / "views.sql"
    if views_path.exists():
        with open(views_path, "r", encoding="utf-8") as f:
            views_content = f.read()
        view_statements = [s.strip() for s in views_content.split(";") if s.strip()]
        with engine.connect() as conn:
            for stmt in view_statements:
                conn.execute(text(stmt))
            conn.commit()
            view_list = conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='view'"
            )).mappings().fetchall()
            print(f"Views applied: {len(view_list)}")
            for row in view_list:
                print(f"  - {row['name']}")
    else:
        print(f"WARNING: {views_path} not found; skipping view creation.")


# ---------------------------------------------------------------------------
# STEP 3: Data validation
# ---------------------------------------------------------------------------
def validate_database(engine, expected_rows: int) -> dict:
    """Validate the imported database thoroughly."""
    print("\n--- STEP 3: Data validation ---")
    results = {}

    with engine.connect() as conn:
        # 1. Verify table exists
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        results["table_exists"] = "sales" in tables
        print(f"[OK] Table exists: {results['table_exists']}")

        # 2. Verify row count matches source dataset
        row_count = conn.execute(text("SELECT COUNT(*) FROM sales")).scalar()
        results["row_count"] = row_count
        results["row_count_matches"] = row_count == expected_rows
        print(f"[OK] Row count: {row_count} (expected {expected_rows}) -> matches: {results['row_count_matches']}")

        # 3. Verify key columns present
        columns = [c["name"] for c in inspector.get_columns("sales")]
        expected_columns = list(pd.read_csv(CLEANED_DATASET).columns)
        results["columns_present"] = set(expected_columns) <= set(columns)
        missing = set(expected_columns) - set(columns)
        print(f"[OK] All expected columns present: {results['columns_present']}" + (f" (missing: {missing})" if missing else ""))

        # 4. Check NULL values
        null_counts = {}
        for col in ["Order_Date", "Quantity", "Unit_Price", "Total_Sales", "Discount", "Customer_Rating"]:
            cnt = conn.execute(text(f"SELECT COUNT(*) FROM sales WHERE {col} IS NULL")).scalar()
            null_counts[col] = cnt
        results["nulls"] = null_counts
        max_nulls = max(null_counts.values())
        results["no_nulls_in_key_numeric_cols"] = max_nulls == 0
        print(f"[OK] Nulls in key numeric columns: {max_nulls} -> clean: {results['no_nulls_in_key_numeric_cols']}")

        # 5. Check for EXACT duplicate rows (all 13 columns identical)
        # NOTE: grouping by Customer_ID alone would flag repeat customers —
        # that is normal business behavior, not a data error. We check the
        # full row instead to find accidental duplicate records.
        distinct_rows = conn.execute(text(
            "SELECT COUNT(*) FROM (SELECT DISTINCT * FROM sales)"
        )).scalar()
        dup_count = int(row_count) - int(distinct_rows)
        results["duplicate_customers"] = dup_count == 0
        print(f"[OK] Exact duplicate rows: {dup_count} -> clean: {results['duplicate_customers']}")

        # 6. Verify numeric sums are reasonable (no accidental corruption)
        total_sales = conn.execute(text("SELECT SUM(Total_Sales) FROM sales")).scalar()
        total_quantity = conn.execute(text("SELECT SUM(Quantity) FROM sales")).scalar()
        results["total_revenue"] = float(total_sales) if total_sales is not None else 0.0
        results["total_quantity"] = int(total_quantity) if total_quantity is not None else 0
        results["positive_revenue"] = results["total_revenue"] > 0
        print(f"[OK] Total revenue: ${results['total_revenue']:,.2f} | Total quantity: {results['total_quantity']:,}")

        # 7. Verify category and payment method coverage
        cat_count = conn.execute(text("SELECT COUNT(DISTINCT Product_Category) FROM sales")).scalar()
        pay_count = conn.execute(text("SELECT COUNT(DISTINCT Payment_Method) FROM sales")).scalar()
        results["categories"] = int(cat_count)
        results["payment_methods"] = int(pay_count)
        print(f"[OK] Distinct categories: {cat_count} | Distinct payment methods: {pay_count}")

        # 8. Verify date range
        min_date = conn.execute(text("SELECT MIN(Order_Date) FROM sales")).scalar()
        max_date = conn.execute(text("SELECT MAX(Order_Date) FROM sales")).scalar()
        results["date_range"] = (str(min_date), str(max_date))
        print(f"[OK] Date range: {min_date} to {max_date}")

        # 9. Verify city_regions reference table exists
        tables = inspector.get_table_names()
        results["city_regions_exists"] = "city_regions" in tables
        print(f"[OK] city_regions table exists: {results['city_regions_exists']}")

        # 10. Verify indexes exist on the sales table
        idx_count = conn.execute(text(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND tbl_name='sales'"
        )).scalar()
        results["index_count"] = int(idx_count)
        print(f"[OK] Indexes on sales table: {idx_count}")

    return results


# ---------------------------------------------------------------------------
# STEP 4: Report and save
# ---------------------------------------------------------------------------
def main():
    try:
        df = inspect_dataset(CLEANED_DATASET)
        expected_rows = len(df)

        # Create engine pointing to the new database location
        os.makedirs(DATABASE_DIR, exist_ok=True)
        engine = create_engine(f"sqlite:///{DATABASE_PATH}", future=True)

        create_database(engine, df)
        validation = validate_database(engine, expected_rows)

        # Print validation summary
        print("\n" + "=" * 70)
        print("VALIDATION SUMMARY")
        print("=" * 70)
        all_pass = True
        for key, value in validation.items():
            status = "PASS" if (value is True or value is False) else "INFO"
            if isinstance(value, bool) and not value:
                all_pass = False
            print(f"[{'PASS' if value else 'FAIL'}] {key}: {value}")
        print("=" * 70)

        if all_pass and validation["row_count_matches"]:
            print("\nSUCCESS: Database created and validated at")
            print(f"  {DATABASE_PATH}")
            return True
        else:
            print("\nWARNING: Some validation checks did not pass. Please review.")
            return False

    except Exception as e:
        print(f"\nERROR: {type(e).__name__}: {e}")
        raise


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
