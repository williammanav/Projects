#!/bin/bash

# ==============================================================================
# CONFIGURATION
# ==============================================================================
CSV_FILE="Auto_Sales_clean.csv"
DB_FILE="analytics.db"
TABLE_NAME="auto_sales"

# Check if CSV exists
if [[ ! -f "$CSV_FILE" ]]; then
    echo "❌ Error: $CSV_FILE not found."
    exit 1
fi

echo "======================================"
echo "📊 AUTO SALES – UNIFIED ANALYTICS"
echo "======================================"

# ==============================================================================
# PHASE 1: DATA INGESTION (Load CSV into SQLite)
# ==============================================================================
echo "⚙️  Loading data into $DB_FILE..."
rm -f "$DB_FILE"

sqlite3 "$DB_FILE" <<EOF
.mode csv
.import '$CSV_FILE' $TABLE_NAME
EOF

# ==============================================================================
# PHASE 2: COMPUTE AGGREGATIONS (Create Summary Tables)
# ==============================================================================
# We create tables for these analytics so they are saved for later use (e.g. Python/BI tools)
# while also being available for immediate display below.

sqlite3 "$DB_FILE" <<EOF
-- 1. Time Series
DROP TABLE IF EXISTS analytics_time;
CREATE TABLE analytics_time AS
SELECT 
    substr(ORDERDATE,1,4) as year,
    substr(ORDERDATE,1,7) as year_month,
    count(*) as orders,
    ROUND(sum(SALES),2) as total_sales
FROM $TABLE_NAME GROUP BY year, year_month;

-- 2. Product Analytics
DROP TABLE IF EXISTS analytics_product;
CREATE TABLE analytics_product AS
SELECT 
    PRODUCTLINE, 
    ROUND(SUM(SALES),2) as total_sales,
    SUM(QUANTITYORDERED) as total_qty
FROM $TABLE_NAME GROUP BY PRODUCTLINE;

-- 3. Geography
DROP TABLE IF EXISTS analytics_geo;
CREATE TABLE analytics_geo AS
SELECT COUNTRY, CITY, ROUND(SUM(SALES),2) as sales FROM $TABLE_NAME GROUP BY COUNTRY, CITY;
EOF

# ==============================================================================
# PHASE 3: REPORTING (Query DB and Display to Console)
# ==============================================================================

# Helper function to run a single value query
run_query() {
    sqlite3 "$DB_FILE" "SELECT $1;"
}

echo -e "\n--- 🔢 HIGH LEVEL METRICS ---"

echo -n "1. Total Rows: "
run_query "COUNT(*) FROM $TABLE_NAME"

echo -n "2. Total Columns: "
run_query "COUNT(*) FROM pragma_table_info('$TABLE_NAME')"

echo -n "3. Total Unique Orders: "
run_query "COUNT(DISTINCT ORDERNUMBER) FROM $TABLE_NAME"

echo -n "4. Total Unique Customers: "
run_query "COUNT(DISTINCT CUSTOMERNAME) FROM $TABLE_NAME"

echo -n "5. Total Unique Products: "
run_query "COUNT(DISTINCT PRODUCTCODE) FROM $TABLE_NAME"

echo -n "6. Total Sales: $"
run_query "ROUND(SUM(SALES),2) FROM $TABLE_NAME"

echo -n "7. Avg Sales per Order: $"
run_query "ROUND(SUM(SALES) / COUNT(DISTINCT ORDERNUMBER),2) FROM $TABLE_NAME"

echo -n "8. Sales Range: "
run_query "'Min: $' || MIN(SALES) || ' - Max: $' || MAX(SALES) FROM $TABLE_NAME"

echo -n "9. Total Quantity Sold: "
run_query "SUM(QUANTITYORDERED) FROM $TABLE_NAME"


echo -e "\n--- 📅 TIME ANALYSIS ---"

echo "10. Sales by Year:"
sqlite3 -header -column "$DB_FILE" "SELECT year, SUM(total_sales) as sales FROM analytics_time GROUP BY year ORDER BY year;"

echo -e "\n11. Top 5 Months by Sales:"
sqlite3 -header -column "$DB_FILE" "SELECT year_month, total_sales FROM analytics_time ORDER BY total_sales DESC LIMIT 5;"


echo -e "\n--- 📦 PRODUCT ANALYSIS ---"

echo "12. Sales & Qty by Product Line:"
sqlite3 -header -column "$DB_FILE" "SELECT * FROM analytics_product ORDER BY total_sales DESC;"

echo -e "\n13. Top 5 Specific Products (by Revenue):"
sqlite3 -header -column "$DB_FILE" "SELECT PRODUCTCODE, ROUND(SUM(SALES),2) as revenue FROM $TABLE_NAME GROUP BY PRODUCTCODE ORDER BY revenue DESC LIMIT 5;"


echo -e "\n--- 🌍 GEOGRAPHY & CUSTOMERS ---"

echo "14. Sales by Country (Top 5):"
sqlite3 -header -column "$DB_FILE" "SELECT COUNTRY, SUM(sales) as tot FROM analytics_geo GROUP BY COUNTRY ORDER BY tot DESC LIMIT 5;"

echo -e "\n15. Top 5 Cities:"
sqlite3 -header -column "$DB_FILE" "SELECT CITY, SUM(sales) as tot FROM analytics_geo GROUP BY CITY ORDER BY tot DESC LIMIT 5;"

echo -e "\n16. Order Status Distribution:"
sqlite3 -header -column "$DB_FILE" "SELECT STATUS, COUNT(*) as count FROM $TABLE_NAME GROUP BY STATUS ORDER BY count DESC;"

echo -e "\n17. Top 5 Customers:"
sqlite3 -header -column "$DB_FILE" "SELECT CUSTOMERNAME, ROUND(SUM(SALES),2) as rev FROM $TABLE_NAME GROUP BY CUSTOMERNAME ORDER BY rev DESC LIMIT 5;"

echo -e "\n======================================"
echo "✅ Analytics Complete."
echo "💾 Database saved to: $DB_FILE"
echo "======================================"
