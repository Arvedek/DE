# MarketMood DE Project

MarketMood is now configured around your collected raw data instead of sample APIs. The repository now includes the stock price CSV, StockTwits workbooks, and Reddit monthly workbooks under `data/raw/source_files/`, then builds a DuckDB `source_data -> prepared_data -> analytics` warehouse and a Streamlit app on top.

## Project objective

Build a reproducible data engineering pipeline that answers:

1. How does daily social sentiment compare with stock movement for selected tickers?
2. Which tickers attract the most Reddit and StockTwits attention?
3. Does daily sentiment show any relationship with same-day or next-day return?

## Raw sources used

Configured in [raw_sources.json](C:/Users/dings/OneDrive/Documents/New%20project/config/raw_sources.json):

- 15-minute stock bars CSV in `data/raw/source_files/stocks/`
- 8 StockTwits ticker workbooks in `data/raw/source_files/stocktwits/`
- 8 monthly Reddit workbooks with `Posts`, `Comments`, and `Summary` sheets in `data/raw/source_files/reddit/`

## Data model

### Raw source layer

- External CSV and XLSX files stay where you collected them
- The project references them through a manifest file instead of copying everything into the repo

### `source_data` schema in DuckDB

- `source_data.stock_prices_raw`
- `source_data.stocktwits_posts_raw`
- `source_data.reddit_posts_raw`
- `source_data.reddit_comments_raw`
- `source_data.reddit_summary_raw`

### `prepared_data` schema in DuckDB

- `prepared_data.stock_prices_15m`
- `prepared_data.market_daily_prices`
- `prepared_data.stocktwits_posts`
- `prepared_data.reddit_posts`
- `prepared_data.reddit_comments`
- `prepared_data.social_mentions`

### `analytics` schema in DuckDB

- `analytics.daily_social_signals`
- `analytics.daily_market_social`
- `analytics.ticker_overview`
- `analytics.top_social_posts`
- `analytics.dataset_inventory`

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
|   |-- raw_storage_design.md
|   `-- team_run_guide.md
|-- data/
|   `-- raw/
|       `-- source_files/
|           |-- stocks/
|           |-- stocktwits/
|           `-- reddit/
|-- sql/
|   |-- analytics_daily_market_social.sql
|   |-- analytics_daily_social_signals.sql
|   |-- analytics_dataset_inventory.sql
|   |-- analytics_ticker_overview.sql
|   |-- analytics_top_social_posts.sql
|   `-- prepared_market_daily_prices.sql
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

For a teammate-friendly step-by-step run guide, use [team_run_guide.md](C:/Users/dings/OneDrive/Documents/New%20project/docs/team_run_guide.md).

### 1. Create a virtual environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Check the raw source manifest

Open [raw_sources.json](C:/Users/dings/OneDrive/Documents/New%20project/config/raw_sources.json) and confirm the relative paths still point to the in-repo raw files.

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

- Raw source files are versioned inside the repository under `data/raw/source_files/`
- DuckDB acts as the analytical warehouse and refined storage
- `source_data` tables preserve source-specific structure
- `prepared_data` tables standardize schema and derive timestamps, tickers, and sentiment
- `analytics` tables power the dashboard and final report

## Suggested report structure

Use [docs/project_design.md](C:/Users/dings/OneDrive/Documents/New%20project/docs/project_design.md) for the report body and [docs/raw_storage_design.md](C:/Users/dings/OneDrive/Documents/New%20project/docs/raw_storage_design.md) for the architecture and storage section.
