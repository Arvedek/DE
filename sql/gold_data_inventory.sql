CREATE OR REPLACE TABLE gold.data_inventory AS
SELECT 'bronze.stock_prices_raw' AS table_name, COUNT(*) AS row_count FROM bronze.stock_prices_raw
UNION ALL
SELECT 'bronze.stocktwits_posts_raw' AS table_name, COUNT(*) AS row_count FROM bronze.stocktwits_posts_raw
UNION ALL
SELECT 'bronze.reddit_posts_raw' AS table_name, COUNT(*) AS row_count FROM bronze.reddit_posts_raw
UNION ALL
SELECT 'bronze.reddit_comments_raw' AS table_name, COUNT(*) AS row_count FROM bronze.reddit_comments_raw
UNION ALL
SELECT 'bronze.reddit_summary_raw' AS table_name, COUNT(*) AS row_count FROM bronze.reddit_summary_raw
UNION ALL
SELECT 'silver.stock_prices_daily' AS table_name, COUNT(*) AS row_count FROM silver.stock_prices_daily
UNION ALL
SELECT 'silver.social_mentions' AS table_name, COUNT(*) AS row_count FROM silver.social_mentions
UNION ALL
SELECT 'gold.daily_market_sentiment' AS table_name, COUNT(*) AS row_count FROM gold.daily_market_sentiment
UNION ALL
SELECT 'gold.ticker_summary' AS table_name, COUNT(*) AS row_count FROM gold.ticker_summary;
