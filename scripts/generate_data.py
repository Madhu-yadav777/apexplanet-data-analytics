#!/usr/bin/env python3
"""
Generate a realistic sample e-commerce sales dataset for the EDA internship task.

Because no real company dataset was provided with this project, this script
creates a synthetic-but-realistic dataset of retail orders. The data is clearly
labeled as sample data in the README and is NOT claimed to come from a real company.

The generated file is saved to data/raw/dataset.csv.
Run from the project root:
    python scripts/generate_data.py
"""

import os
import random
import numpy as np
import pandas as pd

random.seed(42)
np.random.seed(42)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
OUTPUT_FILE = os.path.join(RAW_DIR, "dataset.csv")


def build_dataset(n_orders: int = 2000) -> pd.DataFrame:
    cities = [
        "New York", "Los Angeles", "Chicago", "Houston", "Phoenix",
        "Philadelphia", "San Antonio", "San Diego", "Dallas", "Austin",
        "Seattle", "Denver", "Miami", "Atlanta", "Boston",
    ]
    genders = ["Male", "Female", "Other"]
    categories = {
        "Electronics": ["Smartphone", "Laptop", "Tablet", "Headphones", "Smart Watch"],
        "Apparel": ["T-Shirt", "Jeans", "Jacket", "Sneakers", "Dress"],
        "Home & Kitchen": ["Blender", "Coffee Maker", "Air Fryer", "Kettle", "Toaster"],
        "Sports": ["Yoga Mat", "Dumbbells", "Running Shoes", "Cycling Helmet", "Golf Club"],
        "Books & Media": ["Novel", "Cookbook", "Board Game", "Vinyl Record", "Magazine"],
        "Beauty": ["Skincare Set", "Perfume", "Makeup Kit", "Hair Dryer", "Serum"],
    }
    products = {cat: prods for cat, prods in categories.items()}

    # Category-based price ranges (USD)
    category_price = {
        "Electronics": (20, 1500),
        "Apparel": (10, 250),
        "Home & Kitchen": (15, 500),
        "Sports": (8, 400),
        "Books & Media": (5, 120),
        "Beauty": (12, 300),
    }
    payment_methods = ["Credit Card", "Debit Card", "PayPal", "Cash", "Bank Transfer", "Gift Card"]
    order_dates = pd.date_range(start="2023-01-01", end="2024-12-31", freq="D")

    records = []
    for i in range(n_orders):
        category = random.choice(list(categories.keys()))
        product = random.choice(products[category])
        lo, hi = category_price[category]
        # Base unit price with some variance
        unit_price = round(random.uniform(lo, hi), 2)
        quantity = random.choices([1, 2, 3, 4, 5], weights=[45, 30, 15, 7, 3])[0]
        discount = round(random.choice([0, 0, 0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30]) * 100, 0)
        total = round(unit_price * quantity * (1 - discount / 100), 2)
        age = int(random.triangular(18, 68, 38))
        gender = random.choice(genders)
        city = random.choice(cities)
        payment = random.choice(payment_methods)
        order_date = random.choice(order_dates)
        # Rating: weighted toward higher values, occasionally missing
        if random.random() < 0.05:
            rating = None
        else:
            rating = round(random.triangular(1.0, 5.0, 4.2), 1)

        records.append({
            "Customer_ID": f"CUST_{i:06d}",
            "Order_Date": order_date.strftime("%Y-%m-%d"),
            "Age": age,
            "Gender": gender,
            "City": city,
            "Product_Category": category,
            "Product": product,
            "Quantity": quantity,
            "Unit_Price": unit_price,
            "Total_Sales": total,
            "Discount": discount,
            "Payment_Method": payment,
            "Customer_Rating": rating,
        })

    df = pd.DataFrame(records)
    return df


def inject_quality_issues(df: pd.DataFrame) -> pd.DataFrame:
    """Introduce realistic data-quality problems for the cleaning step to handle.

    These are intentionally seeded so the EDA/cleaning workflow has meaningful
    work: a few missing values, a handful of duplicated rows, a couple of
    negative quantities, some whitespace in text columns, and inconsistent
    date formats.
    """
    n = len(df)

    # 1. Missing values in Rating (already some) - add a few more
    missing_rating_idx = np.random.choice(n, 12, replace=False)
    df.loc[missing_rating_idx, "Customer_Rating"] = np.nan

    # 2. A few duplicate rows
    dup_idx = np.random.choice(n, 8, replace=False)
    df = pd.concat([df, df.iloc[dup_idx]], ignore_index=True)

    # 3. Negative quantity for a few rows (invalid)
    neg_qty_idx = np.random.choice(len(df), 5, replace=False)
    df.loc[neg_qty_idx, "Quantity"] = -1

    # 4. Whitespace in City and Gender
    ws_idx = np.random.choice(len(df), 20, replace=False)
    for idx in ws_idx:
        city = df.at[idx, "City"]
        df.at[idx, "City"] = f"  {city} "
        gender = df.at[idx, "Gender"]
        df.at[idx, "Gender"] = f" {gender}"

    # 5. Inconsistent date format for a slice (MM/DD/YYYY)
    date_idx = np.random.choice(len(df), 40, replace=False)
    for idx in date_idx:
        d = pd.to_datetime(df.at[idx, "Order_Date"])
        df.at[idx, "Order_Date"] = d.strftime("%m/%d/%Y")

    # 6. A few missing Age values
    age_idx = np.random.choice(len(df), 6, replace=False)
    df.loc[age_idx, "Age"] = np.nan

    # 7. Two rows with an impossible future/high age (invalid)
    bad_age_idx = np.random.choice(len(df), 3, replace=False)
    df.loc[bad_age_idx, "Age"] = 150

    return df


def main():
    os.makedirs(RAW_DIR, exist_ok=True)
    df = build_dataset(n_orders=2000)
    df = inject_quality_issues(df)
    # Shuffle to interleave the quality issues
    df = df.sample(frac=1, random_state=7).reset_index(drop=True)
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"Generated dataset with {len(df)} rows x {len(df.columns)} columns")
    print(f"Saved to: {OUTPUT_FILE}")
    print("\nColumn dtypes:")
    print(df.dtypes)
    print("\nFirst 5 rows:")
    print(df.head())


if __name__ == "__main__":
    main()
