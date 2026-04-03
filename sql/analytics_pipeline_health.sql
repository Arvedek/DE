CREATE OR REPLACE TABLE analytics.pipeline_health AS
SELECT
    'source_data.stock_prices_raw' AS table_name,
    COUNT(*) AS row_count,
    COUNT(DISTINCT ticker) AS distinct_tickers,
    MIN(TRY_STRPTIME(timestamp, '%Y-%m-%d %H:%M:%S')) AS min_timestamp,
    MAX(TRY_STRPTIME(timestamp, '%Y-%m-%d %H:%M:%S')) AS max_timestamp,
    COUNT(*) - COUNT(TRY_STRPTIME(timestamp, '%Y-%m-%d %H:%M:%S')) AS null_timestamp_rows,
    COUNT(*) - COUNT(DISTINCT CONCAT(COALESCE(timestamp, ''), '|', COALESCE(ticker, ''))) AS duplicate_key_rows,
    COUNT(DISTINCT source_file) AS source_file_count
FROM source_data.stock_prices_raw

UNION ALL

SELECT
    'prepared_data.stock_prices_15m' AS table_name,
    COUNT(*) AS row_count,
    COUNT(DISTINCT ticker) AS distinct_tickers,
    MIN(event_timestamp) AS min_timestamp,
    MAX(event_timestamp) AS max_timestamp,
    COUNT(*) - COUNT(event_timestamp) AS null_timestamp_rows,
    COUNT(*) - COUNT(DISTINCT CONCAT(COALESCE(CAST(event_timestamp AS VARCHAR), ''), '|', COALESCE(ticker, ''))) AS duplicate_key_rows,
    COUNT(DISTINCT source_file) AS source_file_count
FROM prepared_data.stock_prices_15m

UNION ALL

SELECT
    'prepared_data.stocktwits_posts' AS table_name,
    COUNT(*) AS row_count,
    COUNT(DISTINCT ticker) AS distinct_tickers,
    MIN(event_timestamp) AS min_timestamp,
    MAX(event_timestamp) AS max_timestamp,
    COUNT(*) - COUNT(event_timestamp) AS null_timestamp_rows,
    COUNT(*) - COUNT(DISTINCT CONCAT(COALESCE(post_id, ''), '|', COALESCE(ticker, ''))) AS duplicate_key_rows,
    COUNT(DISTINCT source_file) AS source_file_count
FROM prepared_data.stocktwits_posts

UNION ALL

SELECT
    'prepared_data.reddit_posts' AS table_name,
    COUNT(*) AS row_count,
    COUNT(
        DISTINCT CASE
            WHEN matched_tickers IS NOT NULL AND LENGTH(TRIM(matched_tickers)) > 0 THEN matched_tickers
        END
    ) AS distinct_tickers,
    MIN(event_timestamp) AS min_timestamp,
    MAX(event_timestamp) AS max_timestamp,
    COUNT(*) - COUNT(event_timestamp) AS null_timestamp_rows,
    COUNT(*) - COUNT(DISTINCT id) AS duplicate_key_rows,
    COUNT(DISTINCT source_file) AS source_file_count
FROM prepared_data.reddit_posts

UNION ALL

SELECT
    'prepared_data.reddit_comments' AS table_name,
    COUNT(*) AS row_count,
    0 AS distinct_tickers,
    MIN(event_timestamp) AS min_timestamp,
    MAX(event_timestamp) AS max_timestamp,
    COUNT(*) - COUNT(event_timestamp) AS null_timestamp_rows,
    COUNT(*) - COUNT(DISTINCT comment_id) AS duplicate_key_rows,
    COUNT(DISTINCT source_file) AS source_file_count
FROM prepared_data.reddit_comments

UNION ALL

SELECT
    'prepared_data.social_mentions' AS table_name,
    COUNT(*) AS row_count,
    COUNT(DISTINCT ticker) AS distinct_tickers,
    MIN(event_timestamp) AS min_timestamp,
    MAX(event_timestamp) AS max_timestamp,
    COUNT(*) - COUNT(event_timestamp) AS null_timestamp_rows,
    COUNT(*) - COUNT(DISTINCT CONCAT(COALESCE(platform, ''), '|', COALESCE(content_id, ''), '|', COALESCE(ticker, ''))) AS duplicate_key_rows,
    COUNT(DISTINCT source_file) AS source_file_count
FROM prepared_data.social_mentions

UNION ALL

SELECT
    'analytics.daily_market_social' AS table_name,
    COUNT(*) AS row_count,
    COUNT(DISTINCT ticker) AS distinct_tickers,
    MIN(CAST(trade_date AS TIMESTAMP)) AS min_timestamp,
    MAX(CAST(trade_date AS TIMESTAMP)) AS max_timestamp,
    COUNT(*) - COUNT(trade_date) AS null_timestamp_rows,
    COUNT(*) - COUNT(DISTINCT CONCAT(COALESCE(CAST(trade_date AS VARCHAR), ''), '|', COALESCE(ticker, ''))) AS duplicate_key_rows,
    0 AS source_file_count
FROM analytics.daily_market_social;
