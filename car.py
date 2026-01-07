import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

# --------------------------------
# PAGE CONFIG
# --------------------------------
st.set_page_config(
    page_title="Auto Sales Analytics Dashboard",
    layout="wide"
)

st.title("🚗 Auto Sales Analytics Dashboard")
st.subheader("Name: Manav Williams")
st.subheader("UID: 2509037")
st.subheader("Roll Number: 37")
st.divider()

CSV_PATH = "Auto_Sales_clean.csv"
DB_PATH = "analytics.db"

# --------------------------------
# LOAD RAW CSV (FOR INTERACTIVITY)
# --------------------------------
@st.cache_data
def load_raw():
    df = pd.read_csv(CSV_PATH)
    df["ORDERDATE"] = pd.to_datetime(df["ORDERDATE"])
    df["YEAR"] = df["ORDERDATE"].dt.year
    df["MONTH"] = df["ORDERDATE"].dt.month
    df["YEAR_MONTH"] = df["ORDERDATE"].dt.to_period("M").astype(str)
    return df

# --------------------------------
# LOAD SQLITE KPIs
# --------------------------------
@st.cache_data
def load_kpi():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM kpi_metrics", conn)
    conn.close()
    return df

raw = load_raw()
kpi = load_kpi()

# --------------------------------
# SIDEBAR FILTERS
# --------------------------------
st.sidebar.header("🔍 Filters")

# Date range
min_date, max_date = raw["ORDERDATE"].min(), raw["ORDERDATE"].max()
date_range = st.sidebar.date_input(
    "Order Date (From – To)",
    [min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

# Year
years = sorted(raw["YEAR"].unique())
selected_years = st.sidebar.multiselect("Year", years, default=years)

# Month
months = list(range(1, 13))
selected_months = st.sidebar.multiselect("Month", months, default=months)

# Country
countries = sorted(raw["COUNTRY"].dropna().unique())
selected_countries = st.sidebar.multiselect(
    "Country",
    countries,
    default=countries
)

# Product Line
product_lines = sorted(raw["PRODUCTLINE"].dropna().unique())
selected_products = st.sidebar.multiselect(
    "Product Line",
    product_lines,
    default=product_lines
)

# Order Status
statuses = sorted(raw["STATUS"].dropna().unique())
selected_statuses = st.sidebar.multiselect(
    "Order Status",
    statuses,
    default=statuses
)

# --------------------------------
# APPLY ALL FILTERS
# --------------------------------
filtered = raw[
    (raw["ORDERDATE"] >= pd.to_datetime(date_range[0])) &
    (raw["ORDERDATE"] <= pd.to_datetime(date_range[1])) &
    (raw["YEAR"].isin(selected_years)) &
    (raw["MONTH"].isin(selected_months)) &
    (raw["COUNTRY"].isin(selected_countries)) &
    (raw["PRODUCTLINE"].isin(selected_products)) &
    (raw["STATUS"].isin(selected_statuses))
]

# --------------------------------
# GLOBAL KPIs (NOT FILTERED)
# --------------------------------
st.subheader("📊 Dataset & Sales KPIs")

cols = st.columns(5)
for i, row in enumerate(kpi.itertuples()):
    cols[i % 5].metric(
        row.metric.replace("_", " ").title(),
        row.value
    )

st.divider()

# --------------------------------
# TIME-BASED ANALYTICS
# --------------------------------
st.subheader("📈 Time-Based Analytics")

ts = (
    filtered
    .groupby("YEAR_MONTH", as_index=False)
    .agg(
        total_sales=("SALES", "sum"),
        orders=("ORDERNUMBER", "nunique")
    )
)

col1, col2 = st.columns(2)

with col1:
    fig = px.line(ts, x="YEAR_MONTH", y="total_sales",
                  title="Sales by Month")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig = px.line(ts, x="YEAR_MONTH", y="orders",
                  title="Orders by Month")
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# --------------------------------
# PRODUCT ANALYTICS
# --------------------------------
st.subheader("🧱 Product Analytics")

product = (
    filtered
    .groupby("PRODUCTLINE", as_index=False)
    .agg(
        total_sales=("SALES", "sum"),
        total_quantity=("QUANTITYORDERED", "sum")
    )
)

col1, col2 = st.columns(2)

with col1:
    fig = px.bar(product, x="PRODUCTLINE", y="total_sales",
                 title="Sales by Product Line")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig = px.bar(product, x="PRODUCTLINE", y="total_quantity",
                 title="Quantity Sold by Product Line")
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# --------------------------------
# GEOGRAPHY ANALYTICS
# --------------------------------
st.subheader("🌍 Geography Analytics")

geo = (
    filtered
    .groupby("COUNTRY", as_index=False)
    .agg(total_sales=("SALES", "sum"))
)

fig = px.bar(geo, x="COUNTRY", y="total_sales",
             title="Sales by Country")
st.plotly_chart(fig, use_container_width=True)

st.divider()

# --------------------------------
# ORDER HEALTH
# --------------------------------
st.subheader("📦 Order Health")

order_health = (
    filtered
    .groupby("STATUS", as_index=False)
    .agg(order_count=("ORDERNUMBER", "nunique"))
)

fig = px.bar(order_health, x="STATUS", y="order_count",
             title="Order Status Distribution")
st.plotly_chart(fig, use_container_width=True)

st.divider()

# --------------------------------
# CUSTOMER ANALYTICS
# --------------------------------
st.subheader("🧑‍💼 Top Customers")

customers = (
    filtered
    .groupby("CUSTOMERNAME", as_index=False)
    .agg(total_sales=("SALES", "sum"))
    .sort_values("total_sales", ascending=False)
    .head(5)
)

fig = px.bar(
    customers.sort_values("total_sales"),
    x="total_sales",
    y="CUSTOMERNAME",
    orientation="h",
    title="Top 5 Customers by Sales"
)
st.plotly_chart(fig, use_container_width=True)

st.subheader("💼 Sales by Deal Size")

deal = (
    filtered
    .groupby("DEALSIZE", as_index=False)
    .agg(total_sales=("SALES","sum"))
)

fig = px.bar(
    deal,
    x="DEALSIZE",
    y="total_sales",
    title="Revenue by Deal Size"
)
st.plotly_chart(fig, use_container_width=True)

st.subheader("📈 Year-over-Year Sales Growth")

yoy = (
    filtered
    .groupby("YEAR", as_index=False)
    .agg(total_sales=("SALES","sum"))
    .sort_values("YEAR")
)

yoy["YoY_Growth_%"] = yoy["total_sales"].pct_change() * 100

fig = px.bar(
    yoy,
    x="YEAR",
    y="YoY_Growth_%",
    title="Year-over-Year Sales Growth (%)"
)
st.plotly_chart(fig, use_container_width=True)

st.divider()


st.subheader("📊 Sales vs Orders")

dual = (
    filtered
    .groupby("YEAR_MONTH", as_index=False)
    .agg(
        total_sales=("SALES","sum"),
        orders=("ORDERNUMBER","nunique")
    )
)

fig = px.line(
    dual,
    x="YEAR_MONTH",
    y=["total_sales", "orders"],
    title="Sales vs Orders Trend"
)
st.plotly_chart(fig, use_container_width=True)

st.subheader("📦 Top 10 Products by Quantity")

top_qty = (
    filtered
    .groupby("PRODUCTLINE", as_index=False)
    .agg(quantity=("QUANTITYORDERED","sum"))
    .sort_values("quantity", ascending=False)
    .head(10)
)

fig = px.bar(
    top_qty.sort_values("quantity"),
    x="quantity",
    y="PRODUCTLINE",
    orientation="h",
    title="Top 10 Products by Quantity Sold"
)
st.plotly_chart(fig, use_container_width=True)


st.divider()

















