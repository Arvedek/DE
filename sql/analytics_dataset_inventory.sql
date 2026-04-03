CREATE OR REPLACE TABLE analytics.dataset_inventory AS
SELECT 'source_data.stock_prices_raw' AS table_name, COUNT(*) AS row_count FROM source_data.stock_prices_raw
UNION ALL
SELECT 'source_data.stocktwits_posts_raw' AS table_name, COUNT(*) AS row_count FROM source_data.stocktwits_posts_raw
UNION ALL
SELECT 'source_data.reddit_posts_raw' AS table_name, COUNT(*) AS row_count FROM source_data.reddit_posts_raw
UNION ALL
SELECT 'source_data.reddit_comments_raw' AS table_name, COUNT(*) AS row_count FROM source_data.reddit_comments_raw
UNION ALL
SELECT 'source_data.reddit_summary_raw' AS table_name, COUNT(*) AS row_count FROM source_data.reddit_summary_raw
UNION ALL
SELECT 'prepared_data.market_daily_prices' AS table_name, COUNT(*) AS row_count FROM prepared_data.market_daily_prices
UNION ALL
SELECT 'prepared_data.social_mentions' AS table_name, COUNT(*) AS row_count FROM prepared_data.social_mentions
UNION ALL
SELECT 'analytics.daily_social_signals' AS table_name, COUNT(*) AS row_count FROM analytics.daily_social_signals
UNION ALL
SELECT 'analytics.daily_market_social' AS table_name, COUNT(*) AS row_count FROM analytics.daily_market_social
UNION ALL
SELECT 'analytics.daily_platform_mix' AS table_name, COUNT(*) AS row_count FROM analytics.daily_platform_mix
UNION ALL
SELECT 'analytics.ticker_overview' AS table_name, COUNT(*) AS row_count FROM analytics.ticker_overview
UNION ALL
SELECT 'analytics.pipeline_health' AS table_name, COUNT(*) AS row_count FROM analytics.pipeline_health;
