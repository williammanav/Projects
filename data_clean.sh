#!/bin/bash

INPUT="Auto_Sales_dirty.csv"
OUTPUT="Auto_Sales_clean.csv"
TEMP="temp_clean.csv"

echo "🧹 Cleaning Auto Sales Dataset..."

# 1️⃣ Remove leading/trailing spaces, normalize NULLs
awk -F',' '
BEGIN { OFS="," }
NR==1 { print; next }
{
  for (i=1; i<=NF; i++) {
    gsub(/^ +| +$/, "", $i)
    if ($i == "" || tolower($i) == "na" || tolower($i) == "null") {
      $i = "UNKNOWN"
    }
  }
  print
}
' "$INPUT" > "$TEMP"

# 2️⃣ Remove invalid numeric values
awk -F',' '
BEGIN { OFS="," }
NR==1 { print; next }
{
  for (i=1; i<=NF; i++) {
    if ($i ~ /^-999$|^-1$/) {
      $i = "UNKNOWN"
    }
  }
  print
}
' "$TEMP" > "$OUTPUT"

# 3️⃣ Remove duplicates (excluding header)
awk '!seen[$0]++' "$OUTPUT" > "$TEMP"
head -n 1 "$OUTPUT" > "$OUTPUT"
tail -n +2 "$TEMP" >> "$OUTPUT"

rm "$TEMP"

echo "✅ Cleaning completed"
echo "📁 Output file: $OUTPUT"
