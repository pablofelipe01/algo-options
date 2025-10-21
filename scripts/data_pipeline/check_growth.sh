#!/bin/bash
echo "📈 CRECIMIENTO DEL DATASET"
echo ""
for file in data/historical/*_60days.parquet; do
    ticker=$(basename "$file" _60days.parquet)
    size=$(du -h "$file" | cut -f1)
    echo "$ticker: $size"
done
echo ""
echo "Total: $(du -sh data/historical | cut -f1)"