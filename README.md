# MarketMood DE Project

MarketMood is now configured around your collected raw data instead of sample APIs. The project treats your local stock price CSV, StockTwits workbooks, and Reddit monthly workbooks as the raw source layer, then builds a DuckDB bronze/silver/gold warehouse and a Streamlit app on top.

## Project objective

Build a reproducible data engineering pipeline that answers:

1. How does daily social sentiment compare with stock movement for selected tickers?
2. Which tickers attract the most Reddit and StockTwits attention?
3. Does daily sentiment show any relationship with same-day or next-day return?

## Raw sources used

Configured in [config/raw_sources.json](C:/Users/dings/OneDrive/Documents/New%20project/config/raw_sources.json):

- 15-minute stock bars CSV
- 8 StockTwits ticker workbooks
- 8 monthly Reddit workbooks with `Posts`, `Comments`, and `Summary` sheets

## Data model

### Raw source layer

- External CSV and XLSX files stay where you collected them
- The project references them through a manifest file instead of copying everything into the repo

### Bronze layer in DuckDB

- `bronze.stock_prices_raw`
- `bronze.stocktwits_posts_raw`
- `bronze.reddit_posts_raw`
- `bronze.reddit_comments_raw`
- `bronze.reddit_summary_raw`

### Silver layer in DuckDB

- `silver.stock_prices_15m`
- `silver.stock_prices_daily`
- `silver.stocktwits_posts`
- `silver.reddit_posts`
- `silver.reddit_comments`
- `silver.social_mentions`

### Gold layer in DuckDB

- `gold.daily_social_signals`
- `gold.daily_market_sentiment`
- `gold.ticker_summary`
- `gold.top_social_content`
- `gold.data_inventory`

## What the final app shows

- price trend by ticker
- daily social volume
- average sentiment over time
- sentiment vs next-day return
- top bullish and bearish Reddit or StockTwits content
- source inventory counts for the report/demo

## Current source inventory

From the raw files you provided:

- stock 15-minute bars: `151,852`
- StockTwits posts: `1,310,301`
- Reddit posts: `14,658`
- Reddit comments: `518,592`

This is a strong course-project scale because it justifies layered storage, incremental ETL, and a curated serving model.

## Repository layout

```text
.
|-- config/
|   `-- raw_sources.json
|-- dashboard/
|   `-- app.py
|-- docs/
|   |-- presentation_outline.md
|   |-- project_design.md
|   `-- raw_storage_design.md
|-- sql/
|   |-- gold_daily_market_sentiment.sql
|   |-- gold_daily_social_signals.sql
|   |-- gold_data_inventory.sql
|   |-- gold_ticker_summary.sql
|   |-- gold_top_social_content.sql
|   `-- silver_stock_prices_daily.sql
|-- src/
|   `-- market_sentiment_pipeline/
|       |-- __init__.py
|       |-- config.py
|       |-- ingest.py
|       |-- pipeline.py
|       `-- warehouse.py
|-- tests/
|   `-- test_pipeline.py
|-- requirements.txt
`-- run_pipeline.py
```

## Setup

### 1. Create a virtual environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Check the raw source manifest

Open [config/raw_sources.json](C:/Users/dings/OneDrive/Documents/New%20project/config/raw_sources.json) and confirm the file paths still match your machine.

### 3. Run the pipeline

Default run:

```powershell
python run_pipeline.py
```

If you want Reddit comments included in the final social signal table:

```powershell
python run_pipeline.py --include-reddit-comments
```

Outputs:

- DuckDB warehouse: `warehouse/market_sentiment.duckdb`
- report/demo exports: `data/exports/*.csv`

### 4. Launch the dashboard

```powershell
streamlit run dashboard/app.py
```

## Design choices

- External raw files stay untouched so the collected data remains your system of record
- DuckDB acts as the analytical warehouse and refined storage
- Bronze tables preserve source-specific structure
- Silver tables standardize schema and derive timestamps, tickers, and sentiment
- Gold tables power the dashboard and final report

## Suggested report structure

Use [docs/project_design.md](C:/Users/dings/OneDrive/Documents/New%20project/docs/project_design.md) for the report body and [docs/raw_storage_design.md](C:/Users/dings/OneDrive/Documents/New%20project/docs/raw_storage_design.md) for the architecture and storage section.

