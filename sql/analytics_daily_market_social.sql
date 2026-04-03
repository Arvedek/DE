CREATE OR REPLACE TABLE analytics.daily_market_social AS
WITH market_features AS (
    SELECT
        ticker,
        trade_date,
        open,
        high,
        low,
        close,
        volume,
        bars_15m,
        ROUND(
            (close / NULLIF(LAG(close) OVER (PARTITION BY ticker ORDER BY trade_date), 0)) - 1,
            6
        ) AS daily_return,
        ROUND(
            (LEAD(close) OVER (PARTITION BY ticker ORDER BY trade_date) / NULLIF(close, 0)) - 1,
            6
        ) AS next_day_return
    FROM prepared_data.market_daily_prices
)
SELECT
    market_features.ticker,
    market_features.trade_date,
    market_features.open,
    market_features.high,
    market_features.low,
    market_features.close,
    market_features.volume,
    market_features.bars_15m,
    market_features.daily_return,
    market_features.next_day_return,
    COALESCE(daily_social_signals.total_mentions, 0) AS total_mentions,
    COALESCE(daily_social_signals.stocktwits_mentions, 0) AS stocktwits_mentions,
    COALESCE(daily_social_signals.reddit_posts, 0) AS reddit_posts,
    COALESCE(daily_social_signals.reddit_comments, 0) AS reddit_comments,
    COALESCE(daily_social_signals.unique_authors, 0) AS unique_authors,
    COALESCE(daily_social_signals.avg_sentiment, 0) AS avg_sentiment,
    COALESCE(daily_social_signals.positive_mentions, 0) AS positive_mentions,
    COALESCE(daily_social_signals.negative_mentions, 0) AS negative_mentions
FROM market_features
LEFT JOIN analytics.daily_social_signals AS daily_social_signals
    ON market_features.ticker = daily_social_signals.ticker
   AND market_features.trade_date = daily_social_signals.trade_date
ORDER BY market_features.ticker, market_features.trade_date;
