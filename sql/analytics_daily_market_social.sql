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
        ROUND((close / NULLIF(open, 0)) - 1, 6) AS intraday_return,
        ROUND((high - low) / NULLIF(open, 0), 6) AS intraday_range_pct,
        ROUND(
            (close / NULLIF(LAG(close) OVER (PARTITION BY ticker ORDER BY trade_date), 0)) - 1,
            6
        ) AS daily_return,
        ROUND(
            (volume / NULLIF(LAG(volume) OVER (PARTITION BY ticker ORDER BY trade_date), 0)) - 1,
            6
        ) AS volume_change,
        ROUND(
            (LEAD(close) OVER (PARTITION BY ticker ORDER BY trade_date) / NULLIF(close, 0)) - 1,
            6
        ) AS next_day_return
    FROM prepared_data.market_daily_prices
),
joined AS (
    SELECT
        market_features.ticker,
        market_features.trade_date,
        market_features.open,
        market_features.high,
        market_features.low,
        market_features.close,
        market_features.volume,
        market_features.bars_15m,
        market_features.intraday_return,
        market_features.intraday_range_pct,
        market_features.daily_return,
        market_features.volume_change,
        market_features.next_day_return,
        COALESCE(daily_social_signals.total_mentions, 0) AS total_mentions,
        COALESCE(daily_social_signals.stocktwits_mentions, 0) AS stocktwits_mentions,
        COALESCE(daily_social_signals.reddit_posts, 0) AS reddit_posts,
        COALESCE(daily_social_signals.reddit_comments, 0) AS reddit_comments,
        COALESCE(daily_social_signals.unique_authors, 0) AS unique_authors,
        COALESCE(daily_social_signals.active_platforms, 0) AS active_platforms,
        COALESCE(daily_social_signals.avg_sentiment, 0) AS avg_sentiment,
        COALESCE(daily_social_signals.median_sentiment, 0) AS median_sentiment,
        COALESCE(daily_social_signals.engagement_weighted_sentiment, 0) AS engagement_weighted_sentiment,
        COALESCE(daily_social_signals.total_engagement, 0) AS total_engagement,
        COALESCE(daily_social_signals.avg_engagement, 0) AS avg_engagement,
        COALESCE(daily_social_signals.sentiment_volatility, 0) AS sentiment_volatility,
        COALESCE(daily_social_signals.positive_mentions, 0) AS positive_mentions,
        COALESCE(daily_social_signals.negative_mentions, 0) AS negative_mentions,
        COALESCE(daily_social_signals.neutral_mentions, 0) AS neutral_mentions,
        COALESCE(daily_social_signals.positive_share, 0) AS positive_share,
        COALESCE(daily_social_signals.negative_share, 0) AS negative_share,
        COALESCE(daily_social_signals.net_sentiment_balance, 0) AS net_sentiment_balance,
        COALESCE(daily_social_signals.stocktwits_share, 0) AS stocktwits_share,
        COALESCE(daily_social_signals.reddit_share, 0) AS reddit_share
    FROM market_features
    LEFT JOIN analytics.daily_social_signals AS daily_social_signals
        ON market_features.ticker = daily_social_signals.ticker
       AND market_features.trade_date = daily_social_signals.trade_date
)
SELECT
    ticker,
    trade_date,
    open,
    high,
    low,
    close,
    volume,
    bars_15m,
    intraday_return,
    intraday_range_pct,
    daily_return,
    volume_change,
    next_day_return,
    total_mentions,
    stocktwits_mentions,
    reddit_posts,
    reddit_comments,
    unique_authors,
    active_platforms,
    avg_sentiment,
    median_sentiment,
    engagement_weighted_sentiment,
    total_engagement,
    avg_engagement,
    sentiment_volatility,
    positive_mentions,
    negative_mentions,
    neutral_mentions,
    positive_share,
    negative_share,
    net_sentiment_balance,
    stocktwits_share,
    reddit_share,
    ROUND(
        AVG(avg_sentiment) OVER (
            PARTITION BY ticker
            ORDER BY trade_date
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ),
        6
    ) AS sentiment_7d_avg,
    ROUND(
        AVG(engagement_weighted_sentiment) OVER (
            PARTITION BY ticker
            ORDER BY trade_date
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ),
        6
    ) AS weighted_sentiment_7d_avg,
    ROUND(
        AVG(total_mentions) OVER (
            PARTITION BY ticker
            ORDER BY trade_date
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ),
        6
    ) AS mentions_7d_avg,
    ROUND(
        AVG(total_engagement) OVER (
            PARTITION BY ticker
            ORDER BY trade_date
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ),
        6
    ) AS engagement_7d_avg,
    ROUND(
        STDDEV_SAMP(daily_return) OVER (
            PARTITION BY ticker
            ORDER BY trade_date
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ),
        6
    ) AS return_7d_volatility,
    ROUND(avg_sentiment - LAG(avg_sentiment, 3) OVER (PARTITION BY ticker ORDER BY trade_date), 6) AS sentiment_momentum_3d,
    ROUND(total_mentions - LAG(total_mentions) OVER (PARTITION BY ticker ORDER BY trade_date), 6) AS mention_change_1d,
    ROUND(
        total_mentions - AVG(total_mentions) OVER (
            PARTITION BY ticker
            ORDER BY trade_date
            ROWS BETWEEN 13 PRECEDING AND CURRENT ROW
        ),
        6
    ) AS mention_delta_vs_14d_avg,
    ROUND(
        (
            total_mentions - AVG(total_mentions) OVER (
                PARTITION BY ticker
                ORDER BY trade_date
                ROWS BETWEEN 13 PRECEDING AND CURRENT ROW
            )
        ) / NULLIF(
            STDDEV_SAMP(total_mentions) OVER (
                PARTITION BY ticker
                ORDER BY trade_date
                ROWS BETWEEN 13 PRECEDING AND CURRENT ROW
            ),
            0
        ),
        6
    ) AS mention_zscore_14d,
    ROUND(engagement_weighted_sentiment - avg_sentiment, 6) AS weighted_sentiment_gap
FROM joined
ORDER BY ticker, trade_date;
