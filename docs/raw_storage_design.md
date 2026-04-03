# Raw Storage and Refined Storage Design

## 1. Raw storage strategy

The project treats the collected CSV and Excel files as the source-of-truth raw layer. They are stored inside the repository and referenced through a manifest file:

- [raw_sources.json](C:/Users/dings/OneDrive/Documents/New%20project/config/raw_sources.json)

This helps in two ways:

1. Everyone on the team works from the same files.
2. The ETL stays reproducible because the paths are explicitly documented.

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

## 3. `source_data` design

`source_data` tables keep the original source structure with only light metadata:

- source file name
- source month for Reddit
- source ticker for StockTwits

No sentiment logic or business aggregation happens at this stage.

## 4. `prepared_data` design

`prepared_data` is the cleaned and refined layer.

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

## 5. `analytics` design

`analytics` tables are the ones we actually use for analysis, reporting, and the final dashboard.

### `analytics.daily_social_signals`

Daily social features by ticker:

- total mentions
- source breakdown
- average sentiment
- positive and negative counts
- distinct author counts

### `analytics.daily_market_social`

Joined daily market and social features:

- OHLCV
- daily return
- next-day return
- daily social features

### `analytics.ticker_overview`

Ticker-level KPIs and correlations.

### `analytics.top_social_posts`

Most bullish and bearish content per ticker for the app demo.

## 6. Why this design works for the course

- the raw collection work is already done
- the project still clearly demonstrates ingestion, transformation, warehousing, and serving
- the `source_data -> prepared_data -> analytics` flow is easy to explain during presentation
- the final dashboard reads curated tables instead of messy spreadsheets
