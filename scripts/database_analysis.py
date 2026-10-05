#!/usr/bin/env python3
"""
SQLAlchemy + SQLite integration for the ApexPlanet Data Analytics project.

This script:
1. Creates an in-memory SQLite database (or a file-backed one at data/analytics.db)
2. Loads the cleaned dataset into a table named `sales`
3. Exposes a SQLAlchemy engine and a declarative ORM model
4. Runs a handful of analytical queries through both ORM and raw SQL
5. Persists the query results into reports/query_results.json so the
   report generator (scripts/generate_report.py) can embed them in the PDF/PPTX

Run from the project root:
    python scripts/database_analysis.py
"""

import os
import json
import warnings

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Project layout (relative, portable)
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEAN_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "cleaned_dataset.csv")
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
REPORT_DIR = os.path.join(PROJECT_ROOT, "reports")
DB_PATH = os.path.join(DATA_DIR, "analytics.db")
QUERY_JSON = os.path.join(REPORT_DIR, "query_results.json")

Base = declarative_base()


def get_engine(db_path: str = DB_PATH):
    """Create (or reuse) a SQLAlchemy engine backed by SQLite."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    engine = create_engine(f"sqlite:///{db_path}", echo=False, future=True)
    return engine


def load_data_to_db(engine):
    """Load the cleaned dataset into the `sales` table (replace if exists)."""
    df = pd.read_csv(CLEAN_PATH)
    df.to_sql("sales", engine, if_exists="replace", index=False)
    print(f"Loaded {len(df)} rows into 'sales' table (columns: {list(df.columns)})")
    return df


def run_queries(engine):
    """Run a set of analytical queries and return structured results."""
    results = {}

    with engine.connect() as conn:
        # 1. Total revenue & orders
        row = conn.execute(text(
            "SELECT COUNT(*) AS total_orders, "
            "SUM(Total_Sales) AS total_revenue, "
            "AVG(Total_Sales) AS avg_order_value "
            "FROM sales"
        )).mappings().first()
        results["overview"] = {
            "total_orders": int(row["total_orders"]),
            "total_revenue": round(float(row["total_revenue"]), 2),
            "avg_order_value": round(float(row["avg_order_value"]), 2),
        }

        # 2. Revenue by product category
        rows = conn.execute(text(
            "SELECT Product_Category, SUM(Total_Sales) AS revenue, COUNT(*) AS orders "
            "FROM sales GROUP BY Product_Category ORDER BY revenue DESC"
        )).mappings().all()
        results["revenue_by_category"] = [
            {"category": r["Product_Category"], "revenue": round(float(r["revenue"]), 2),
             "orders": int(r["orders"])}
            for r in rows
        ]

        # 3. Top 5 products by revenue
        rows = conn.execute(text(
            "SELECT Product, Product_Category, SUM(Total_Sales) AS revenue, COUNT(*) AS orders "
            "FROM sales GROUP BY Product ORDER BY revenue DESC LIMIT 5"
        )).mappings().all()
        results["top_products"] = [
            {"product": r["Product"], "category": r["Product_Category"],
             "revenue": round(float(r["revenue"]), 2), "orders": int(r["orders"])}
            for r in rows
        ]

        # 4. Revenue by city (top 5)
        rows = conn.execute(text(
            "SELECT City, SUM(Total_Sales) AS revenue, COUNT(*) AS orders "
            "FROM sales GROUP BY City ORDER BY revenue DESC LIMIT 5"
        )).mappings().all()
        results["top_cities"] = [
            {"city": r["City"], "revenue": round(float(r["revenue"]), 2), "orders": int(r["orders"])}
            for r in rows
        ]

        # 5. Payment method distribution
        rows = conn.execute(text(
            "SELECT Payment_Method, COUNT(*) AS orders, SUM(Total_Sales) AS revenue "
            "FROM sales GROUP BY Payment_Method ORDER BY orders DESC"
        )).mappings().all()
        results["payment_methods"] = [
            {"method": r["Payment_Method"], "orders": int(r["orders"]),
             "revenue": round(float(r["revenue"]), 2)}
            for r in rows
        ]

        # 6. Gender distribution
        rows = conn.execute(text(
            "SELECT Gender, COUNT(*) AS orders, AVG(Total_Sales) AS avg_order_value "
            "FROM sales GROUP BY Gender ORDER BY orders DESC"
        )).mappings().all()
        results["gender"] = [
            {"gender": r["Gender"], "orders": int(r["orders"]),
             "avg_order_value": round(float(r["avg_order_value"]), 2)}
            for r in rows
        ]

        # 7. Monthly revenue trend
        rows = conn.execute(text(
            "SELECT strftime('%Y-%m', Order_Date) AS month, "
            "SUM(Total_Sales) AS revenue, COUNT(*) AS orders "
            "FROM sales GROUP BY month ORDER BY month"
        )).mappings().all()
        results["monthly_trend"] = [
            {"month": r["month"], "revenue": round(float(r["revenue"]), 2), "orders": int(r["orders"])}
            for r in rows
        ]

        # 8. Average rating by category
        rows = conn.execute(text(
            "SELECT Product_Category, AVG(Customer_Rating) AS avg_rating, COUNT(*) AS orders "
            "FROM sales GROUP BY Product_Category ORDER BY avg_rating DESC"
        )).mappings().all()
        results["rating_by_category"] = [
            {"category": r["Product_Category"], "avg_rating": round(float(r["avg_rating"]), 2),
             "orders": int(r["orders"])}
            for r in rows
        ]

        # 9. Correlation-style query: quantity vs total_sales
        rows = conn.execute(text(
            "SELECT AVG(Quantity) AS avg_qty, AVG(Total_Sales) AS avg_sales, COUNT(*) AS n "
            "FROM sales"
        )).mappings().first()
        results["quantity_sales"] = {
            "avg_qty": round(float(rows["avg_qty"]), 2),
            "avg_sales": round(float(rows["avg_sales"]), 2),
            "n": int(rows["n"]),
        }

    return results


def main():
    print("=" * 60)
    print("APEXPLANET DATA ANALYTICS - DATABASE INTEGRATION")
    print("=" * 60)

    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(REPORT_DIR, exist_ok=True)

    engine = get_engine(DB_PATH)
    df = load_data_to_db(engine)
    query_results = run_queries(engine)

    with open(QUERY_JSON, "w") as f:
        json.dump(query_results, f, indent=2, default=str)
    print(f"\nQuery results saved to {QUERY_JSON}")
    print("\nDatabase integration finished successfully.")
    return query_results


if __name__ == "__main__":
    main()