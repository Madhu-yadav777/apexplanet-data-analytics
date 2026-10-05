#!/usr/bin/env python3
"""
ApexPlanet Retail Sales Dashboard

Interactive Streamlit + Plotly dashboard for the ApexPlanet data analytics project.
Uses the cleaned dataset from Task 1 (data/processed/cleaned_dataset.csv).

Run with:
    streamlit run dashboards/app.py
"""

import os
import warnings

import numpy as np
import pandas as pd

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="ApexPlanet - Interactive Sales Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Project paths (relative to this file)
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "processed", "cleaned_dataset.csv")

# ---------------------------------------------------------------------------
# Colors & styling
# ---------------------------------------------------------------------------
ACCENT = "#3A56A3"       # deep blue
ACCENT2 = "#E36414"      # orange
DARK = "#1F2937"
LIGHT = "#F3F6FA"
GOOD = "#2E8B57"
PALETTE = [ACCENT, ACCENT2, GOOD, "#9B59B6", "#C0392B", "#16A085", "#F39C12", "#7F8C8D"]

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
@st.cache_data(ttl=300)
def load_data():
    """Load the cleaned Task 1 dataset."""
    df = pd.read_csv(DATA_PATH, parse_dates=["Order_Date"])
    df = df.copy()
    df["Order_Year"] = df["Order_Date"].dt.year
    df["Order_Month"] = df["Order_Date"].dt.strftime("%Y-%m")
    df["Discount_Value"] = df["Unit_Price"] * df["Quantity"] * (df["Discount"] / 100.0)
    df["Potential_Revenue"] = df["Unit_Price"] * df["Quantity"]

    # City -> Region mapping (15 US cities, 5 regions)
    REGION_MAP = {
        "Boston": "Northeast",
        "New York": "Northeast",
        "Philadelphia": "Northeast",
        "Atlanta": "Southeast",
        "Austin": "Southeast",
        "Dallas": "Southeast",
        "Houston": "Southeast",
        "Miami": "Southeast",
        "San Antonio": "South Central",
        "Chicago": "Midwest",
        "Denver": "Midwest",
        "Los Angeles": "West",
        "Phoenix": "West",
        "San Diego": "West",
        "Seattle": "West",
    }
    df["Region"] = df["City"].map(REGION_MAP)

    # Age group segmentation
    def age_group(age):
        if pd.isna(age):
            return "Unknown"
        if age < 25:
            return "18-24 (Young Adult)"
        if age < 45:
            return "25-44 (Adult)"
        if age < 60:
            return "45-59 (Middle-aged)"
        return "60+ (Senior)"

    df["Age_Group"] = df["Age"].apply(age_group)
    return df


def filter_data(df, start_date, end_date, region, cities, category, payment, gender, age):
    """Apply all sidebar filters to the dataset."""
    mask = (df["Order_Date"].dt.date >= start_date) & (df["Order_Date"].dt.date <= end_date)
    if region != "All":
        mask &= df["Region"] == region
    if cities and "All" not in cities:
        mask &= df["City"].isin(cities)
    if category != "All":
        mask &= df["Product_Category"] == category
    if payment != "All":
        mask &= df["Payment_Method"] == payment
    if gender != "All":
        mask &= df["Gender"] == gender
    if age != "All":
        mask &= df["Age_Group"] == age
    return df[mask].copy()


# ---------------------------------------------------------------------------
# Load data once
# ---------------------------------------------------------------------------
df = load_data()

# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------
st.sidebar.title("🔍 Filters")

min_date = df["Order_Date"].min().date()
max_date = df["Order_Date"].max().date()
start_date, end_date = st.sidebar.date_input(
    "Date Range",
    value=[min_date, max_date],
    min_value=min_date,
    max_value=max_date,
)

regions = ["All"] + sorted(df["Region"].dropna().unique().tolist())
selected_region = st.sidebar.selectbox("Region", regions)

cities = ["All"] + sorted(df["City"].unique().tolist())
selected_cities = st.sidebar.multiselect("City", cities, default=["All"])

categories = ["All"] + sorted(df["Product_Category"].unique().tolist())
selected_category = st.sidebar.selectbox("Product Category", categories)

payments = ["All"] + sorted(df["Payment_Method"].unique().tolist())
selected_payment = st.sidebar.selectbox("Payment Method", payments)

genders = ["All"] + sorted(df["Gender"].dropna().unique().tolist())
selected_gender = st.sidebar.selectbox("Customer Gender", genders)

age_groups = ["All"] + sorted(df["Age_Group"].dropna().unique().tolist())
selected_age = st.sidebar.selectbox("Age Group", age_groups)

filtered_df = filter_data(
    df, start_date, end_date, selected_region, selected_cities,
    selected_category, selected_payment, selected_gender, selected_age,
)

# ---------------------------------------------------------------------------
# KPI computation
# ---------------------------------------------------------------------------
def compute_kpis(d):
    if d.empty:
        return None
    total_revenue = float(d["Total_Sales"].sum())
    total_orders = int(len(d))
    total_quantity = int(d["Quantity"].sum())
    aov = float(d["Total_Sales"].mean())
    avg_rating = float(d["Customer_Rating"].mean()) if d["Customer_Rating"].notna().any() else 0.0
    discount_value = float(d["Discount_Value"].sum())
    return dict(
        total_revenue=total_revenue,
        total_orders=total_orders,
        total_quantity=total_quantity,
        aov=aov,
        avg_rating=avg_rating,
        discount_value=discount_value,
    )


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("🛒 ApexPlanet - Retail Sales Dashboard")
st.markdown(
    "Interactive analytics for the ApexPlanet retail dataset. Explore revenue, "
    "orders, customer behavior, and product performance. Use the filters in the "
    "sidebar to refine the view and drive every chart below."
)

# ---------------------------------------------------------------------------
# KPI cards
# ---------------------------------------------------------------------------
kpi = compute_kpis(filtered_df)

if kpi and kpi["total_orders"] > 0:
    st.markdown(f"**{kpi['total_orders']:,} orders**  |  "
                f"**{kpi['total_quantity']:,} units sold**  |  "
                f"**{len(filtered_df['Customer_ID'].unique()):,} customers**  |  "
                f"**{start_date} → {end_date}**")

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    kpi_items = [
        ("Total Revenue", f"${kpi['total_revenue']:,.2f}", ACCENT),
        ("Total Orders", f"{kpi['total_orders']:,}", ACCENT2),
        ("Total Quantity", f"{kpi['total_quantity']:,}", GOOD),
        ("Average Order Value", f"${kpi['aov']:,.2f}", "#9B59B6"),
        ("Avg Customer Rating", f"{kpi['avg_rating']:.2f} / 5", "#F39C12"),
        ("Discounts Given", f"${kpi['discount_value']:,.2f}", "#7F8C8D"),
    ]
    for (label, value, color), col in zip(kpi_items, [col1, col2, col3, col4, col5, col6]):
        col.metric(label=label, value=value, delta=None, delta_color="off")
else:
    st.warning("No data matches the current filters. Adjust the filters to see results.")

# ---------------------------------------------------------------------------
# 1. Revenue by Category
# ---------------------------------------------------------------------------
st.subheader("Revenue by Product Category")

if not filtered_df.empty:
    cat_rev = filtered_df.groupby("Product_Category")["Total_Sales"].sum().sort_values(ascending=False).reset_index()
    fig_cat = px.bar(
        cat_rev, x="Product_Category", y="Total_Sales",
        text_auto=".2s",
        title="Total Revenue by Category",
    )
    fig_cat.update_traces(marker_color=ACCENT)
    fig_cat.update_layout(height=400, template="plotly_white",
                          xaxis_title="Category", yaxis_title="Revenue ($)")
    st.plotly_chart(fig_cat, use_container_width=True)

    fig_donut = px.pie(
        cat_rev, names="Product_Category", values="Total_Sales",
        hole=0.4, title="Revenue Share by Category",
    )
    fig_donut.update_layout(height=400, template="plotly_white")
    st.plotly_chart(fig_donut, use_container_width=True)
else:
    st.info("No data to display.")

# ---------------------------------------------------------------------------
# 2. Monthly Sales Trend
# ---------------------------------------------------------------------------
st.subheader("Monthly Sales Trend")

if not filtered_df.empty:
    monthly = filtered_df.groupby("Order_Month").agg(
        revenue=("Total_Sales", "sum"),
        orders=("Total_Sales", "count"),
        quantity=("Quantity", "sum"),
    ).reset_index()
    fig_month = px.line(
        monthly, x="Order_Month", y="revenue",
        title="Monthly Revenue Trend",
        labels={"Order_Month": "Month", "revenue": "Revenue ($)"},
    )
    fig_month.update_layout(height=400, template="plotly_white")
    st.plotly_chart(fig_month, use_container_width=True)

    fig_orders = px.bar(
        monthly, x="Order_Month", y="orders",
        title="Monthly Order Count",
        labels={"Order_Month": "Month", "orders": "Orders"},
    )
    fig_orders.update_traces(marker_color=ACCENT2)
    fig_orders.update_layout(height=300, template="plotly_white")
    st.plotly_chart(fig_orders, use_container_width=True)
else:
    st.info("No data to display.")

# ---------------------------------------------------------------------------
# 3. Customer Demographics
# ---------------------------------------------------------------------------
st.subheader("Customer Demographics")

if not filtered_df.empty:
    gender_counts = filtered_df["Gender"].value_counts().dropna().reset_index().rename(columns={"count": "Gender_Count"})
    age_counts = filtered_df["Age_Group"].value_counts().dropna().reset_index().rename(columns={"count": "Age_Count"})

    fig_gender = px.pie(
        gender_counts, names="Gender", values="Gender_Count",
        hole=0.4, title="Customer Gender Distribution",
    )
    fig_gender.update_layout(height=350, template="plotly_white")

    fig_age = px.pie(
        age_counts, names="Age_Group", values="Age_Count",
        hole=0.4, title="Customer Age Group Distribution",
        color_discrete_sequence=PALETTE,
    )
    fig_age.update_layout(height=350, template="plotly_white")

    gcol1, gcol2 = st.columns(2)
    gcol1.plotly_chart(fig_gender, use_container_width=True)
    gcol2.plotly_chart(fig_age, use_container_width=True)
else:
    st.info("No data to display.")

# ---------------------------------------------------------------------------
# 4. Payment Method Analysis
# ---------------------------------------------------------------------------
st.subheader("Payment Method Analysis")

if not filtered_df.empty:
    pay_rev = filtered_df.groupby("Payment_Method")["Total_Sales"].sum().sort_values(ascending=False).reset_index()
    pay_count = filtered_df["Payment_Method"].value_counts().reset_index().rename(columns={"count": "Transaction_Count"})

    fig_pay_rev = px.bar(
        pay_rev, x="Payment_Method", y="Total_Sales",
        text_auto=".2s", title="Revenue by Payment Method",
    )
    fig_pay_rev.update_traces(marker_color=GOOD)
    fig_pay_rev.update_layout(height=380, template="plotly_white")

    fig_pay_count = px.bar(
        pay_count, x="Payment_Method", y="Transaction_Count",
        title="Transaction Count by Payment Method",
    )
    fig_pay_count.update_traces(marker_color="#F39C12")
    fig_pay_count.update_layout(height=380, template="plotly_white")

    pcol1, pcol2 = st.columns(2)
    pcol1.plotly_chart(fig_pay_rev, use_container_width=True)
    pcol2.plotly_chart(fig_pay_count, use_container_width=True)
else:
    st.info("No data to display.")

# ---------------------------------------------------------------------------
# 5. Geographic Sales
# ---------------------------------------------------------------------------
st.subheader("Geographic Sales Performance")

if not filtered_df.empty:
    city_rev = filtered_df.groupby("City")["Total_Sales"].sum().sort_values(ascending=False).head(10).reset_index()
    fig_city = px.bar(
        city_rev, x="City", y="Total_Sales",
        text_auto=".2s", title="Top 10 Cities by Revenue",
    )
    fig_city.update_traces(marker_color=ACCENT)
    fig_city.update_layout(height=400, template="plotly_white",
                           xaxis_title="City", yaxis_title="Revenue ($)")

    region_rev = filtered_df.groupby("Region")["Total_Sales"].sum().reset_index()
    fig_region = px.treemap(
        region_rev, path=["Region"], values="Total_Sales",
        title="Revenue by Region",
    )
    fig_region.update_layout(height=400, template="plotly_white")

    geocol1, geocol2 = st.columns(2)
    geocol1.plotly_chart(fig_city, use_container_width=True)
    geocol2.plotly_chart(fig_region, use_container_width=True)
else:
    st.info("No data to display.")

# ---------------------------------------------------------------------------
# 6. Product Performance
# ---------------------------------------------------------------------------
st.subheader("Product Performance")

if not filtered_df.empty:
    prod = filtered_df.groupby("Product_Category").agg(
        avg_rating=("Customer_Rating", "mean"),
        total_qty=("Quantity", "sum"),
        total_rev=("Total_Sales", "sum"),
    ).reset_index()

    fig_prod = px.scatter(
        prod, x="avg_rating", y="total_rev", size="total_qty",
        color="Product_Category",
        hover_name="Product_Category",
        title="Product Category Performance (Rating vs Revenue vs Quantity)",
        labels={"avg_rating": "Avg Customer Rating",
                "total_rev": "Total Revenue ($)",
                "total_qty": "Total Quantity"},
    )
    fig_prod.update_layout(height=450, template="plotly_white")
    st.plotly_chart(fig_prod, use_container_width=True)
else:
    st.info("No data to display.")

# ---------------------------------------------------------------------------
# 7. Customer Lifetime Value
# ---------------------------------------------------------------------------
st.subheader("Top Customers by Lifetime Value")

if not filtered_df.empty:
    clv = filtered_df.groupby("Customer_ID").agg(
        total_spent=("Total_Sales", "sum"),
        order_count=("Total_Sales", "count"),
        avg_rating=("Customer_Rating", "mean"),
    ).sort_values("total_spent", ascending=False).head(20).reset_index()

    fig_clv = px.bar(
        clv, x="Customer_ID", y="total_spent",
        title="Top 20 Customers by Total Spend",
        labels={"Customer_ID": "Customer", "total_spent": "Total Spend ($)"},
    )
    fig_clv.update_traces(marker_color="#9B59B6")
    fig_clv.update_layout(height=400, template="plotly_white")
    st.plotly_chart(fig_clv, use_container_width=True)

    top_cust = clv.iloc[0]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Top Customer ID", top_cust["Customer_ID"])
    c2.metric("Top Customer Spend", f"${top_cust['total_spent']:,.2f}")
    c3.metric("Top Customer Orders", f"{int(top_cust['order_count'])}")
    c4.metric("Top Customer Avg Rating", f"{top_cust['avg_rating']:.2f} / 5")
else:
    st.info("No data to display.")

# ---------------------------------------------------------------------------
# 8. Discount vs Rating
# ---------------------------------------------------------------------------
st.subheader("Discount & Customer Rating Relationship")

if not filtered_df.empty:
    sample = filtered_df.dropna(subset=["Discount", "Customer_Rating"]).head(2000)
    fig_disc = px.scatter(
        sample, x="Discount", y="Customer_Rating",
        color="Product_Category",
        hover_data=["City", "Quantity"],
        title="Discount % vs Customer Rating",
    )
    fig_disc.update_layout(height=400, template="plotly_white",
                           xaxis_title="Discount (%)",
                           yaxis_title="Customer Rating")
    st.plotly_chart(fig_disc, use_container_width=True)
else:
    st.info("No data to display.")

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.markdown("---")
st.markdown(
    "<small>ApexPlanet Data Analytics — Task 2: Interactive Dashboard | "
    "Powered by Streamlit + Plotly</small>",
    unsafe_allow_html=True,
)
