#!/usr/bin/env python3
"""
Data cleaning script for the ApexPlanet Data Analytics EDA project.

This script:
1. Loads the raw dataset from data/raw/dataset.csv
2. Performs data cleaning operations:
   - Handles missing values
   - Removes duplicates
   - Corrects data types
   - Fixes invalid values (negative quantities, impossible ages)
   - Standardizes date formats
   - Cleans whitespace in categorical columns
3. Saves the cleaned dataset to data/processed/cleaned_dataset.csv

Run from the project root:
    python scripts/data_cleaning.py
"""

import os
import pandas as pd
import numpy as np

def main():
    # Set up paths
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw_path = os.path.join(project_root, "data", "raw", "dataset.csv")
    processed_dir = os.path.join(project_root, "data", "processed")
    output_path = os.path.join(processed_dir, "cleaned_dataset.csv")
    
    # Ensure processed directory exists
    os.makedirs(processed_dir, exist_ok=True)
    
    print("Loading raw dataset...")
    df = pd.read_csv(raw_path)
    print(f"Raw dataset shape: {df.shape}")
    
    # Create a copy for cleaning
    df_clean = df.copy()
    
    # 1. Standardize column names (remove whitespace)
    df_clean.columns = df_clean.columns.str.strip()
    
    # 2. Handle missing values
    print("\nHandling missing values...")
    missing_before = df_clean.isnull().sum()
    print(f"Missing values per column:\n{missing_before[missing_before > 0]}")
    
    # Fill numerical columns with median
    numeric_cols = ['Age', 'Unit_Price', 'Total_Sales', 'Discount', 'Customer_Rating']
    for col in numeric_cols:
        if col in df_clean.columns:
            median_val = df_clean[col].median()
            df_clean[col].fillna(median_val, inplace=True)
            print(f"Filled missing {col} with median: {median_val:.2f}")
    
    # Fill categorical columns with mode
    categorical_cols = ['Gender', 'City', 'Product_Category', 'Product', 'Payment_Method']
    for col in categorical_cols:
        if col in df_clean.columns:
            mode_val = df_clean[col].mode()[0] if not df_clean[col].mode().empty else 'Unknown'
            df_clean[col].fillna(mode_val, inplace=True)
            print(f"Filled missing {col} with mode: '{mode_val}'")
    
    # Order_Date: fill with most common date
    if 'Order_Date' in df_clean.columns:
        mode_date = df_clean['Order_Date'].mode()[0]
        df_clean['Order_Date'].fillna(mode_date, inplace=True)
        print(f"Filled missing Order_Date with mode: {mode_date}")
    
    print(f"Missing values after handling: {df_clean.isnull().sum().sum()}")
    
    # 3. Fix data types
    print("\nFixing data types...")
    # Convert Order_Date to datetime (handling both formats)
    df_clean['Order_Date'] = pd.to_datetime(df_clean['Order_Date'], errors='coerce')
    # Fill any conversion errors with the most common date
    if df_clean['Order_Date'].isnull().any():
        mode_date = df_clean['Order_Date'].mode()[0]
        df_clean['Order_Date'].fillna(mode_date, inplace=True)
    
    # Ensure numeric columns are proper types
    df_clean['Quantity'] = pd.to_numeric(df_clean['Quantity'], errors='coerce')
    df_clean['Age'] = pd.to_numeric(df_clean['Age'], errors='coerce')
    
    # 4. Handle invalid values
    print("\nHandling invalid values...")
    
    # Fix negative quantities (set to 1 as minimum reasonable value)
    neg_qty_count = (df_clean['Quantity'] < 0).sum()
    if neg_qty_count > 0:
        df_clean.loc[df_clean['Quantity'] < 0, 'Quantity'] = 1
        print(f"Fixed {neg_qty_count} negative quantity values (set to 1)")
    
    # Fix impossible ages (<0 or >100)
    invalid_age_count = ((df_clean['Age'] < 0) | (df_clean['Age'] > 100)).sum()
    if invalid_age_count > 0:
        # Set to median age
        median_age = df_clean['Age'].median()
        df_clean.loc[(df_clean['Age'] < 0) | (df_clean['Age'] > 100), 'Age'] = median_age
        print(f"Fixed {invalid_age_count} invalid age values (set to median: {median_age:.1f})")
    
    # Ensure Total_Sales is non-negative
    neg_sales_count = (df_clean['Total_Sales'] < 0).sum()
    if neg_sales_count > 0:
        df_clean.loc[df_clean['Total_Sales'] < 0, 'Total_Sales'] = 0
        print(f"Fixed {neg_sales_count} negative Total_Sales values (set to 0)")
    
    # Ensure Discount is between 0 and 100
    invalid_discount_count = ((df_clean['Discount'] < 0) | (df_clean['Discount'] > 100)).sum()
    if invalid_discount_count > 0:
        df_clean['Discount'] = df_clean['Discount'].clip(0, 100)
        print(f"Fixed {invalid_discount_count} invalid Discount values (clipped to 0-100)")
    
    # 5. Remove duplicates
    print("\nRemoving duplicate records...")
    initial_count = len(df_clean)
    df_clean = df_clean.drop_duplicates()
    duplicates_removed = initial_count - len(df_clean)
    print(f"Removed {duplicates_removed} duplicate rows")
    
    # 6. Clean whitespace in string columns
    print("\nCleaning whitespace in categorical columns...")
    str_cols = df_clean.select_dtypes(include=['object']).columns
    for col in str_cols:
        df_clean[col] = df_clean[col].astype(str).str.strip()
    
    # Final check
    print(f"\nCleaned dataset shape: {df_clean.shape}")
    print(f"Final missing values: {df_clean.isnull().sum().sum()}")
    
    # Save cleaned dataset
    df_clean.to_csv(output_path, index=False)
    print(f"\nCleaned dataset saved to: {output_path}")
    
    # Show basic info about cleaned data
    print("\nCleaned dataset info:")
    print(df_clean.info())
    
    return df_clean

if __name__ == "__main__":
    main()