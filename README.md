# SBCL Quarterly Data Extractor

This repository includes a small script to extract the most recent quarterly results
for SBCL (consolidated) from Screener.in and save them as a CSV.

## Usage

```bash
python scripts/extract_quarterly.py \
  --url "https://www.screener.in/company/SBCL/consolidated/" \
  --limit 20 \
  --output data/sbcl_last_20_quarters.csv
```

The CSV will include the quarter label and all metrics reported in the quarterly
results table.
