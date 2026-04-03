# Raw Storage And Refined Storage Design

## 1. Raw storage strategy

The project treats the collected CSV/XLSX files as the source-of-truth raw layer. Instead of moving them into the repo, we store their locations in a manifest file:

- [raw_sources.json](C:/Users/dings/OneDrive/Documents/New%20project/config/raw_sources.json)

This gives two benefits:

1. Large raw files stay in their existing folder structure.
2. The ETL remains reproducible because the paths are explicitly documented.

## 2. Source inventory

### Market data

- file: `stocks_250101-260319_15m_RAW.csv`
- columns: `timestamp`, `Ticker`, `Open`, `High`, `Low`, `Close`, `Volume`
- row count observed: `151,852`

### StockTwits

- pattern: `*_posts.xlsx`
- workbook shape: one sheet per file
- columns: `post_id`, `user`, `time`, `content`
- row count observed: `1,310,301`

### Reddit

- pattern: `reddit_*.xlsx`
- workbook sheets: `Posts`, `Comments`, `Summary`
- posts columns: `subreddit`, `id`, `title`, `author`, `score`, `upvote_ratio`, `num_comments`, `permalink`, `selftext`, `flair`, `created_utc`, `matched_keywords`
- comments columns: `subreddit`, `comment_id`, `post_id`, `author`, `body`, `score`, `depth`, `parent_id`, `created_utc`, `is_submitter`, `awards`, `matched_keywords`
- summary columns: subreddit-level counts

## 3. Bronze design

Bronze tables preserve source structure with only light metadata:

- source file name
- source month for Reddit
- source ticker for StockTwits

No sentiment logic or business aggregation happens here.

## 4. Silver design

Silver is the refined storage layer.

### Market refinements

- parse `timestamp` into `event_timestamp`
- standardize ticker casing
- aggregate 15-minute bars into daily OHLCV

### Social refinements

- standardize text and author fields
- parse timestamps from Excel or string format
- compute sentiment score and label
- infer tracked tickers from file context or matched keywords
- build one normalized `social_mentions` table

## 5. Gold design

Gold tables are built for analytics and the final application.

### `gold.daily_social_signals`

Daily social features by ticker:

- total mentions
- source breakdown
- average sentiment
- positive and negative counts
- distinct author counts

### `gold.daily_market_sentiment`

Joined daily market and social features:

- OHLCV
- daily return
- next-day return
- daily social features

### `gold.ticker_summary`

Ticker-level KPIs and correlations.

### `gold.top_social_content`

Most bullish and bearish content per ticker for the app demo.

## 6. Why this design works for the course

- raw collection is already done
- the project still demonstrates ingestion, transformation, warehousing, and serving
- bronze/silver/gold is easy to explain during presentation
- the final dashboard consumes curated data instead of raw spreadsheets

