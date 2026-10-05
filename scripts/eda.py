#!/usr/bin/env python3
"""
Exploratory Data Analysis (EDA) script for the ApexPlanet Data Analytics project.

This script:
1. Loads the cleaned dataset from data/processed/cleaned_dataset.csv
2. Computes descriptive statistics for every column
3. Calculates business KPIs (revenue, AOV, order count, top products, etc.)
4. Generates professional visualizations and saves them to visualizations/
5. Computes the correlation matrix and detects outliers (IQR method)
6. Produces data-driven business insights
7. Writes a machine-readable JSON summary (reports/kpi_data.json) that the
   report generator (scripts/generate_report.py) uses to build the PDF and PPTX

The script is meant to be run from the project root:

    python scripts/eda.py

All file paths are computed relative to this file, so it works on any machine
and any operating system without hardcoded absolute paths.
"""

import os
import json
import warnings

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")  # non-interactive backend, safe for terminal / CI
import matplotlib.pyplot as plt
import seaborn as sns

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Project layout (relative, portable)
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_PATH = os.path.join(PROJECT_ROOT, "data", "raw", "dataset.csv")
CLEAN_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "cleaned_dataset.csv")
VIZ_DIR = os.path.join(PROJECT_ROOT, "visualizations")
REPORT_DIR = os.path.join(PROJECT_ROOT, "reports")
KPI_JSON = os.path.join(REPORT_DIR, "kpi_data.json")

# Numerical / categorical column classification (used throughout the script)
NUMERIC_COLS = ["Age", "Quantity", "Unit_Price", "Total_Sales", "Discount", "Customer_Rating"]
CATEGORICAL_COLS = ["Gender", "City", "Product_Category", "Product", "Payment_Method"]


# ---------------------------------------------------------------------------
# Styling helpers
# ---------------------------------------------------------------------------
def apply_style():
    """Apply a clean, professional matplotlib + seaborn theme."""
    sns.set_theme(style="whitegrid")
    palette = {
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
        "axes.titlesize": 15,
        "axes.titleweight": "bold",
        "axes.labelsize": 12,
        "axes.labelweight": "bold",
        "figure.facecolor": "white",
        "axes.facecolor": "#fbfbfd",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.dpi": 100,
        "savefig.dpi": 150,
        "savefig.bbox": "tight",
    }
    plt.rcParams.update(palette)


ACCENT = "#3A56A3"      # deep blue
ACCENT2 = "#E36414"     # orange
GOOD = "#2E8B57"        # green
PALETTE = ["#3A56A3", "#E36414", "#2E8B57", "#9B59B6", "#C0392B", "#16A085", "#F39C12", "#7F8C8D"]


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
def load_data():
    """Load both the raw and the cleaned dataset."""
    raw = pd.read_csv(RAW_PATH)
    clean = pd.read_csv(CLEAN_PATH, parse_dates=["Order_Date"])
    return raw, clean


# ---------------------------------------------------------------------------
# KPIs
# ---------------------------------------------------------------------------
def compute_kpis(df):
    """Compute the key performance indicators supported by the dataset."""
    total_revenue = float(df["Total_Sales"].sum())
    total_orders = int(len(df))
    total_quantity = int(df["Quantity"].sum())
    aov = float(df["Total_Sales"].mean())
    avg_rating = float(df["Customer_Rating"].mean())
    avg_discount = float(df["Discount"].mean())
    n_customers = int(df["Customer_ID"].nunique())
    n_products = int(df["Product"].nunique())

    top_cat = df.groupby("Product_Category")["Total_Sales"].sum()
    top_prod = df.groupby(["Product_Category", "Product"])["Total_Sales"].sum().sort_values(ascending=False)
    top_city = df.groupby("City")["Total_Sales"].sum()
    top_pay = df["Payment_Method"].value_counts()

    kpis = {
        "total_revenue": round(total_revenue, 2),
        "total_orders": total_orders,
        "total_quantity": total_quantity,
        "average_order_value": round(aov, 2),
        "average_customer_rating": round(avg_rating, 2),
        "average_discount_pct": round(avg_discount, 2),
        "number_of_customers": n_customers,
        "number_of_products": n_products,
        "top_category": {
            "name": str(top_cat.idxmax()),
            "revenue": round(float(top_cat.max()), 2),
        },
        "top_product": {
            "name": str(top_prod.index[0][1]),
            "category": str(top_prod.index[0][0]),
            "revenue": round(float(top_prod.iloc[0]), 2),
        },
        "top_city": {
            "name": str(top_city.idxmax()),
            "revenue": round(float(top_city.max()), 2),
        },
        "top_payment": {
            "name": str(top_pay.idxmax()),
            "orders": int(top_pay.iloc[0]),
        },
        "date_range": [
            str(df["Order_Date"].min().date()),
            str(df["Order_Date"].max().date()),
        ],
        "rows": int(len(df)),
        "columns": int(df.shape[1]),
    }
    return kpis

# ---------------------------------------------------------------------------
# Insights (all numbers are computed from the dataset)
# ---------------------------------------------------------------------------
def compute_insights(df, kpis):
    """Return a list of data-driven, human-readable business insights."""
    insights = []

    cat_sales = df.groupby("Product_Category")["Total_Sales"].sum().sort_values(ascending=False)
    top_cat, top_cat_rev = cat_sales.index[0], cat_sales.iloc[0]
    low_cat, low_cat_rev = cat_sales.index[-1], cat_sales.iloc[-1]

    prod_sales = df.groupby("Product")["Total_Sales"].sum().sort_values(ascending=False)
    top_prod, top_prod_rev = prod_sales.index[0], prod_sales.iloc[0]

    city_sales = df.groupby("City")["Total_Sales"].sum().sort_values(ascending=False)
    top_city, top_city_rev = city_sales.index[0], city_sales.iloc[0]

    pay = df["Payment_Method"].value_counts()
    top_pay, top_pay_n = pay.index[0], int(pay.iloc[0])

    # Year over year growth
    df = df.copy()
    df["Year"] = df["Order_Date"].dt.year
    yearly = df.groupby("Year")["Total_Sales"].sum()
    y0, y1 = sorted(yearly.index)
    growth = (yearly[y1] - yearly[y0]) / yearly[y0] * 100

    # Discount vs rating relationship
    disc_rating_corr = df["Discount"].corr(df["Customer_Rating"])

    # Best rated category
    rating_by_cat = df.groupby("Product_Category")["Customer_Rating"].mean().sort_values(ascending=False)
    best_rated_cat, best_rated_val = rating_by_cat.index[0], rating_by_cat.iloc[0]

    # Peak month
    peak_month = df.set_index("Order_Date")["Total_Sales"].resample("M").sum().idxmax()

    # Top customer
    cust_spend = df.groupby("Customer_ID")["Total_Sales"].sum().sort_values(ascending=False)
    top_cust, top_cust_spend = cust_spend.index[0], cust_spend.iloc[0]

    # Age band
    age_mean = df["Age"].mean()
    adults_25_44 = ((df["Age"] >= 25) & (df["Age"] <= 44)).mean() * 100

    # Quantity drivers of revenue
    qty_sales_corr = df["Quantity"].corr(df["Total_Sales"])

    insights = [
        f"Total revenue across the period ({kpis['date_range'][0]} to {kpis['date_range'][1]}) is "
        f"${kpis['total_revenue']:,.2f} from {kpis['total_orders']:,} orders by "
        f"{kpis['number_of_customers']:,} unique customers.",
        f"Average order value is ${kpis['average_order_value']:,.2f} and {kpis['total_quantity']:,} "
        f"units were sold in total.",
        f"'{top_cat}' is the highest-grossing category at ${top_cat_rev:,.2f} "
        f"({top_cat_rev / kpis['total_revenue'] * 100:.1f}% of total revenue).",
        f"'{low_cat}' is the lowest-grossing category at ${low_cat_rev:,.2f}, "
        f"a candidate for promotion, bundling or portfolio review.",
        f"'{top_prod}' is the single best-selling product with ${top_prod_rev:,.2f} in revenue.",
        f"'{top_city}' leads all regions in sales with ${top_city_rev:,.2f} "
        f"({top_city_rev / kpis['total_revenue'] * 100:.1f}% of total revenue).",
        f"'{top_pay}' is the most used payment method with {top_pay_n} "
        f"({top_pay_n / kpis['total_orders'] * 100:.1f}%) of all orders.",
        f"Sales grew by {growth:.1f}% from {y0} to {y1} "
        f"(${yearly[y0]:,.0f} to ${yearly[y1]:,.0f}), indicating a positive momentum.",
        f"'{peak_month.strftime('%B %Y')}' was the peak sales month, consistent with a post-holiday/promotional surge.",
        f"Quantity and total sales show a strong positive correlation "
        f"(r = {qty_sales_corr:.2f}); buying more units drives more revenue.",
        f"'{best_rated_cat}' earns the highest average customer rating "
        f"({best_rated_val:.2f}/5), suggesting strong product-market fit in that segment.",
        f"The average customer rating is {kpis['average_customer_rating']:.2f}/5 across "
        f"{kpis['total_orders']:,} orders.",
        f"A discount of {kpis['average_discount_pct']:.1f}% (average) has a "
        f"{'negative' if disc_rating_corr < 0 else 'positive'} relationship with customer rating "
        f"(r = {disc_rating_corr:.2f}); deeper discounts do not reliably improve satisfaction.",
        f"Customers aged 25-44 make up {adults_25_44:.1f}% of orders (average age "
        f"{age_mean:.1f}), pointing to a strong young-adult core demographic.",
        f"Customer '{top_cust}' is the top spender with ${top_cust_spend:,.2f}, a prime "
        f"candidate for loyalty / retention programs.",
    ]
    return insights

# ---------------------------------------------------------------------------
# Descriptive statistics
# ---------------------------------------------------------------------------
def descriptive_stats(df):
    """Return a nicely formatted dict of per-column statistics."""
    numeric = df[NUMERIC_COLS].describe().T
    numeric["std_rounded"] = numeric["std"].round(2)
    out = {}
    for col in df.columns:
        s = df[col]
        if pd.api.types.is_numeric_dtype(s):
            out[col] = {
                "mean": round(float(s.mean()), 2),
                "std": round(float(s.std()), 2),
                "min": float(s.min()),
                "q1": round(float(s.quantile(0.25)), 2),
                "median": round(float(s.median()), 2),
                "q3": round(float(s.quantile(0.75)), 2),
                "max": float(s.max()),
                "unique": int(s.nunique()),
            }
        else:
            out[col] = {
                "unique": int(s.nunique()),
                "top": str(s.value_counts().index[0]),
            }
    return out


# ---------------------------------------------------------------------------
# Outlier detection (IQR)
# ---------------------------------------------------------------------------
def detect_outliers(df):
    """Detect outliers per numeric column using the 1.5 * IQR rule."""
    results = {}
    for col in NUMERIC_COLS:
        s = df[col]
        q1 = s.quantile(0.25)
        q3 = s.quantile(0.75)
        iqr = q3 - q1
        lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        count = int(((s < lo) | (s > hi)).sum())
        results[col] = {
            "q1": round(float(q1), 2),
            "q3": round(float(q3), 2),
            "iqr": round(float(iqr), 2),
            "lower_bound": round(float(lo), 2),
            "upper_bound": round(float(hi), 2),
            "outliers": count,
        }
    return results


# ---------------------------------------------------------------------------
# Correlation
# ---------------------------------------------------------------------------
def correlation_matrix(df):
    return df[NUMERIC_COLS].corr()

# Visualization functions
# ---------------------------------------------------------------------------
def viz_missing_values(raw, clean, path):
    """Missing-value bar chart (raw vs cleaned)."""
    raw_miss = raw.isnull().sum()
    clean_miss = clean.isnull().sum()
    fig, ax = plt.subplots(figsize=(11, 6))
    cols = raw_miss[raw_miss > 0].index.tolist() + [c for c in clean_miss.index if clean_miss[c] > 0]
    cols = list(dict.fromkeys(cols))
    raw_vals = [int(raw_miss[c]) for c in cols]
    clean_vals = [int(clean_miss[c]) for c in cols]
    x = np.arange(len(cols))
    w = 0.38
    ax.bar(x - w / 2, raw_vals, w, label="Raw", color=ACCENT)
    ax.bar(x + w / 2, clean_vals, w, label="Cleaned", color=GOOD)
    ax.set_xticks(x)
    ax.set_xticklabels(cols, rotation=25, ha="right")
    ax.set_ylabel("Missing values")
    ax.set_title("Missing Values - Raw vs Cleaned Dataset")
    ax.legend()
    for i, v in enumerate(raw_vals):
        ax.text(i - w / 2, v + 1, str(v), ha="center", fontsize=9)
    for i, v in enumerate(clean_vals):
        ax.text(i + w / 2, v + 1, str(v), ha="center", fontsize=9)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)

def viz_distributions(clean, path):
    """Distribution of each numeric variable (histogram + KDE)."""
    cols = [c for c in NUMERIC_COLS]
    fig, axes = plt.subplots(2, 3, figsize=(15, 9))
    axes = axes.flatten()
    for i, col in enumerate(cols):
        ax = axes[i]
        sns.histplot(clean[col], kde=True, ax=ax, color=ACCENT, edgecolor="white")
        ax.set_title(f"Distribution of {col}")
        ax.set_xlabel("")
        ax.set_ylabel("Frequency")
        ax.axvline(clean[col].mean(), color=ACCENT2, linestyle="--", linewidth=1.5,
                   label=f"Mean={clean[col].mean():.2f}")
        ax.legend(fontsize=9)
    fig.suptitle("Numerical Variable Distributions", fontsize=17, fontweight="bold", y=1.02)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)

def viz_correlation(clean, path):
    """Correlation heatmap of the numeric columns."""
    corr = correlation_matrix(clean)
    fig, ax = plt.subplots(figsize=(10, 8))
    mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
    sns.heatmap(corr, mask=mask, annot=True, fmt=".2f", cmap="RdBu_r",
                center=0, vmin=-1, vmax=1, square=True, linewidths=1,
                cbar_kws={"shrink": 0.8}, ax=ax)
    ax.set_title("Correlation Heatmap - Numerical Variables")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def viz_categorical(clean, path):
    """Bar charts for the main categorical variables."""
    cols = ["Gender", "Product_Category", "Payment_Method"]
    fig, axes = plt.subplots(1, 3, figsize=(17, 5.5))
    for ax, col in zip(axes, cols):
        vc = clean[col].value_counts()
        ax.bar(vc.index, vc.values, color=PALETTE[: len(vc)])
        ax.set_title(f"Orders by {col}")
        ax.set_ylabel("Orders")
        ax.tick_params(axis="x", rotation=20, labelsize=9)
        for i, v in enumerate(vc.values):
            ax.text(i, v + max(vc.values) * 0.01, f"{v}", ha="center", fontsize=9)
    fig.suptitle("Categorical Variable Analysis", fontsize=17, fontweight="bold", y=1.02)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def viz_numerical(clean, path):
    """Box plots + scatter for the numeric variables."""
    fig, axes = plt.subplots(1, 3, figsize=(17, 5.5))
    cols = ["Age", "Quantity", "Total_Sales"]
    for ax, col in zip(axes, cols):
        sns.boxplot(x=clean[col], ax=ax, color=ACCENT, flierprops=dict(marker="o", markersize=4, alpha=0.4))
        ax.set_title(f"Box Plot of {col}")
        ax.set_ylabel("")
        ax.set_xlabel("")
    fig.suptitle("Numerical Variable Box Plots (IQR Outliers)", fontsize=17, fontweight="bold", y=1.02)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)

def viz_sales_category(clean, path):
    """Revenue by product category with revenue-share labels."""
    cat = clean.groupby("Product_Category")["Total_Sales"].sum().sort_values()
    total = cat.sum()
    fig, ax = plt.subplots(figsize=(10, 6.5))
    bars = ax.barh(cat.index, cat.values, color=PALETTE[: len(cat)])
    for i, (v, name) in enumerate(zip(cat.values, cat.index)):
        ax.text(v + total * 0.005, i, f"  ({v / total * 100:.1f}%)", va="center", fontsize=9)
    ax.set_title("Revenue by Product Category")
    ax.set_xlabel("Total Sales (USD)")
    ax.set_xlim(0, cat.max() * 1.18)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def viz_gender(clean, path):
    """Gender analysis: order count and average order value."""
    g = clean.groupby("Gender").agg(orders=("Total_Sales", "count"),
                                   revenue=("Total_Sales", "sum"),
                                   aov=("Total_Sales", "mean"))
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    g["orders"].plot(kind="bar", ax=axes[0], color=PALETTE)
    axes[0].set_title("Orders by Gender")
    axes[0].set_ylabel("Orders")
    axes[0].set_xlabel("")
    for i, v in enumerate(g["orders"].values):
        axes[0].text(i, v + 2, f"{int(v)}", ha="center", fontsize=10, fontweight="bold")

    g["aov"].plot(kind="bar", ax=axes[1], color=ACCENT)
    axes[1].set_title("Average Order Value by Gender")
    axes[1].set_ylabel("USD")
    axes[1].set_xlabel("")
    for i, v in enumerate(g["aov"].values):
        axes[1].text(i, v + 1, f"", ha="center", fontsize=10, fontweight="bold")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def viz_age(clean, path):
    """Age distribution as a histogram with a KDE overlay."""
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.histplot(clean["Age"], bins=25, kde=True, ax=ax, color=ACCENT, edgecolor="white")
    ax.axvline(clean["Age"].mean(), color=ACCENT2, linestyle="--", linewidth=1.8,
               label=f"Mean age = {clean['Age'].mean():.1f}")
    ax.set_title("Customer Age Distribution")
    ax.set_xlabel("Age")
    ax.set_ylabel("Number of Orders")
    ax.legend(fontsize=11)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def viz_payment(clean, path):
    """Payment method: order counts and revenue."""
    pay = clean.groupby("Payment_Method").agg(orders=("Total_Sales", "count"),
                                             revenue=("Total_Sales", "sum"))
    pay = pay.sort_values("orders")
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(pay.index, pay["orders"], color=PALETTE[: len(pay)])
    ax.set_title("Orders by Payment Method")
    ax.set_xlabel("Number of Orders")
    for i, v in enumerate(pay["orders"].values):
        ax.text(v + 2, i, f"{int(v)}", va="center", fontsize=10)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def viz_city(clean, path):
    """City-wise analysis: top cities by revenue."""
    city = clean.groupby("City")["Total_Sales"].sum().sort_values().tail(10)
    total = clean["Total_Sales"].sum()
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.barh(city.index, city.values, color=PALETTE[: len(city)][::-1])
    for i, (v, name) in enumerate(zip(city.values, city.index)):
        ax.text(v + city.max() * 0.005, i, f"", va="center", fontsize=9)
    ax.set_title("Top 10 Cities by Sales")
    ax.set_xlabel("Total Sales (USD)")
    ax.set_xlim(0, city.max() * 1.18)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def viz_product(clean, path):
    """Product performance: top 10 products by revenue."""
    prod = clean.groupby("Product")["Total_Sales"].sum().sort_values().tail(10)
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.barh(prod.index, prod.values, color=ACCENT)
    for i, v in enumerate(prod.values):
        ax.text(v + prod.max() * 0.005, i, f"", va="center", fontsize=9)
    ax.set_title("Top 10 Products by Revenue")
    ax.set_xlabel("Total Sales (USD)")
    ax.set_xlim(0, prod.max() * 1.18)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def viz_timeseries(clean, path):
    """Time-series sales trend (monthly, with 3-month moving average)."""
    monthly = clean.set_index("Order_Date")["Total_Sales"].resample("M").sum()
    rolling = monthly.rolling(window=3, min_periods=1).mean()
    fig, ax = plt.subplots(figsize=(13, 6))
    ax.plot(monthly.index, monthly.values, color=ACCENT2, alpha=0.55, linewidth=1.4, label="Monthly sales")
    ax.plot(rolling.index, rolling.values, color=ACCENT, linewidth=2.5, label="3-month moving average")
    ax.fill_between(monthly.index, monthly.values, alpha=0.10, color=ACCENT)
    ax.set_title("Monthly Sales Trend (2023 - 2024)")
    ax.set_ylabel("Total Sales (USD)")
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def viz_scatter(clean, path):
    """Scatter plots of important numeric relationships."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    # Quantity vs Unit Price
    ax = axes[0]
    sns.scatterplot(x="Quantity", y="Unit_Price", data=clean, ax=ax, color=ACCENT, alpha=0.5, s=28)
    ax.set_title("Quantity vs Unit Price")
    ax.set_xlabel("Quantity")
    ax.set_ylabel("Unit Price (USD)")
    # Discount vs Rating
    ax = axes[1]
    sns.scatterplot(x="Discount", y="Customer_Rating", data=clean, ax=ax,
                    hue="Product_Category", palette=PALETTE, alpha=0.6, s=28, legend=False)
    ax.set_title("Discount vs Customer Rating")
    ax.set_xlabel("Discount (%)")
    ax.set_ylabel("Customer Rating")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)

def viz_summary_dashboard(clean, kpis, path):
    """A single-page summary dashboard of the key KPIs and top visuals."""
    fig = plt.figure(figsize=(16, 11))
    fig.suptitle("ApexPlanet - EDA Summary Dashboard", fontsize=20, fontweight="bold", y=0.985)

    # Row 1: KPI cards (6 cards in one row)
    cards = [
        ("Total Revenue", "${:,.0f}".format(kpis["total_revenue"])),
        ("Total Orders", "{:,}".format(kpis["total_orders"])),
        ("Avg Order Value", "${:,.2f}".format(kpis["average_order_value"])),
        ("Avg Rating", "{:.2f} / 5".format(kpis["average_customer_rating"])),
        ("Customers", "{:,}".format(kpis["number_of_customers"])),
        ("Avg Discount", "{:.1f}%".format(kpis["average_discount_pct"])),
    ]
    for i, (label, value) in enumerate(cards):
        ax = fig.add_subplot(1, 6, i + 1)
        ax.axis("off")
        ax.text(0.5, 0.62, value, ha="center", va="center", fontsize=15,
                fontweight="bold", color=ACCENT,
                bbox=dict(boxstyle="round,pad=0.6", facecolor="#EEF2FA", edgecolor=ACCENT, linewidth=1.2))
        ax.text(0.5, 0.18, label, ha="center", va="center", fontsize=9.5, color="#333333")

    # Row 2: category revenue + gender split
    cat = clean.groupby("Product_Category")["Total_Sales"].sum().sort_values()
    ax = fig.add_subplot(2, 2, 3)
    ax.barh(cat.index, cat.values, color=PALETTE[: len(cat)])
    ax.set_title("Revenue by Category", fontweight="bold")
    ax.set_xlabel("USD")

    g = clean["Gender"].value_counts()
    ax = fig.add_subplot(2, 2, 4)
    ax.pie(g, labels=g.index, autopct="%1.0f%%", colors=PALETTE, startangle=90,
           wedgeprops=dict(edgecolor="white"))
    ax.set_title("Gender Split", fontweight="bold")

    # Row 3: payment methods + monthly trend (full width)
    pay = clean["Payment_Method"].value_counts()
    ax = fig.add_subplot(2, 2, 1)
    pay.plot(kind="bar", ax=ax, color=ACCENT)
    ax.set_title("Orders by Payment Method", fontweight="bold")
    ax.tick_params(axis="x", rotation=20)
    ax.set_ylabel("")

    monthly = clean.set_index("Order_Date")["Total_Sales"].resample("M").sum()
    ax = fig.add_subplot(2, 2, 2)
    ax.plot(monthly.index, monthly.values, color=ACCENT, linewidth=2)
    ax.fill_between(monthly.index, monthly.values, alpha=0.15, color=ACCENT)
    ax.set_title("Monthly Sales Trend", fontweight="bold")
    ax.grid(True, alpha=0.3)
    fig.autofmt_xdate()

    fig.tight_layout(rect=[0, 0, 1, 0.965])
    fig.savefig(path)
    plt.close(fig)

def make_all_visualizations(raw, clean, kpis):
    """Generate every required chart and save it into visualizations/."""
    os.makedirs(VIZ_DIR, exist_ok=True)
    specs = {
        "missing_values.png": lambda: viz_missing_values(raw, clean, os.path.join(VIZ_DIR, "missing_values.png")),
        "distributions.png": lambda: viz_distributions(clean, os.path.join(VIZ_DIR, "distributions.png")),
        "correlation_heatmap.png": lambda: viz_correlation(clean, os.path.join(VIZ_DIR, "correlation_heatmap.png")),
        "categorical_analysis.png": lambda: viz_categorical(clean, os.path.join(VIZ_DIR, "categorical_analysis.png")),
        "numerical_analysis.png": lambda: viz_numerical(clean, os.path.join(VIZ_DIR, "numerical_analysis.png")),
        "summary_dashboard.png": lambda: viz_summary_dashboard(clean, kpis, os.path.join(VIZ_DIR, "summary_dashboard.png")),
        "sales_by_category.png": lambda: viz_sales_category(clean, os.path.join(VIZ_DIR, "sales_by_category.png")),
        "gender_analysis.png": lambda: viz_gender(clean, os.path.join(VIZ_DIR, "gender_analysis.png")),
        "age_distribution.png": lambda: viz_age(clean, os.path.join(VIZ_DIR, "age_distribution.png")),
        "payment_method_analysis.png": lambda: viz_payment(clean, os.path.join(VIZ_DIR, "payment_method_analysis.png")),
        "city_analysis.png": lambda: viz_city(clean, os.path.join(VIZ_DIR, "city_analysis.png")),
        "product_performance.png": lambda: viz_product(clean, os.path.join(VIZ_DIR, "product_performance.png")),
        "time_series_sales.png": lambda: viz_timeseries(clean, os.path.join(VIZ_DIR, "time_series_sales.png")),
        "scatter_relationships.png": lambda: viz_scatter(clean, os.path.join(VIZ_DIR, "scatter_relationships.png")),
    }
    for name, fn in specs.items():
        print(f"  generating {name}")
        fn()
    return list(specs.keys())


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main():
    apply_style()
    print("=" * 60)
    print("APEXPLANET DATA ANALYTICS - EDA PIPELINE")
    print("=" * 60)

    raw, clean = load_data()
    print(f"Loaded raw data:   {raw.shape[0]} rows x {raw.shape[1]} cols")
    print(f"Loaded clean data: {clean.shape[0]} rows x {clean.shape[1]} cols")

    print("\n[1/5] Descriptive statistics")
    stats = descriptive_stats(clean)
    pd.DataFrame(stats).T.to_csv(os.path.join(REPORT_DIR, "descriptive_stats.csv"))
    print(pd.DataFrame(stats).T)

    print("\n[2/5] KPIs")
    kpis = compute_kpis(clean)
    for k, v in kpis.items():
        print(f"  {k}: {v}")

    print("\n[3/5] Correlations & outliers")
    corr = correlation_matrix(clean)
    print(corr.round(2))
    outliers = detect_outliers(clean)
    for k, v in outliers.items():
        print(f"  {k}: {v['outliers']} outliers "+
              f"[Q1={v['q1']}, Q3={v['q3']}, IQR={v['iqr']}, bounds=({v['lower_bound']}, {v['upper_bound']})]")

    print("\n[4/5] Business insights")
    insights = compute_insights(clean, kpis)
    for i, ins in enumerate(insights, 1):
        print(f"  {i:02d}. {ins}")

    print("\n[5/5] Generating visualizations")
    viz_files = make_all_visualizations(raw, clean, kpis)
    print(f"  {len(viz_files)} charts written to visualizations/")

    # Persist a JSON summary for the report generator
    os.makedirs(REPORT_DIR, exist_ok=True)
    payload = {
        "kpis": kpis,
        "insights": insights,
        "correlation": {a: {b: round(float(corr.loc[a, b]), 3) for b in corr.columns} for a in corr.index},
        "outliers": outliers,
        "stats": stats,
        "viz_files": viz_files,
    }
    with open(KPI_JSON, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"\nJSON summary saved to {KPI_JSON}")
    print("\nEDA pipeline finished successfully.")
    return clean, kpis, insights
if __name__ == "__main__":
    main()
