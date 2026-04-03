CREATE OR REPLACE TABLE analytics.daily_social_signals AS
WITH base AS (
    SELECT
        ticker,
        event_date AS trade_date,
        COUNT(*) AS total_mentions,
        SUM(CASE WHEN platform = 'stocktwits' THEN 1 ELSE 0 END) AS stocktwits_mentions,
        SUM(CASE WHEN platform = 'reddit' AND content_type = 'post' THEN 1 ELSE 0 END) AS reddit_posts,
        SUM(CASE WHEN platform = 'reddit' AND content_type = 'comment' THEN 1 ELSE 0 END) AS reddit_comments,
        COUNT(DISTINCT author) AS unique_authors,
        COUNT(DISTINCT platform) AS active_platforms,
        ROUND(AVG(sentiment_score), 6) AS avg_sentiment,
        ROUND(MEDIAN(sentiment_score), 6) AS median_sentiment,
        ROUND(
            SUM(sentiment_score * GREATEST(COALESCE(engagement_score, 0), 1))
            / NULLIF(SUM(GREATEST(COALESCE(engagement_score, 0), 1)), 0),
            6
        ) AS engagement_weighted_sentiment,
        ROUND(SUM(COALESCE(engagement_score, 0)), 6) AS total_engagement,
        ROUND(AVG(COALESCE(engagement_score, 0)), 6) AS avg_engagement,
        ROUND(STDDEV_POP(sentiment_score), 6) AS sentiment_volatility,
        SUM(CASE WHEN sentiment_label = 'positive' THEN 1 ELSE 0 END) AS positive_mentions,
        SUM(CASE WHEN sentiment_label = 'negative' THEN 1 ELSE 0 END) AS negative_mentions,
        SUM(CASE WHEN sentiment_label = 'neutral' THEN 1 ELSE 0 END) AS neutral_mentions
    FROM prepared_data.social_mentions
    GROUP BY 1, 2
)
SELECT
    ticker,
    trade_date,
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
    ROUND(positive_mentions / NULLIF(total_mentions, 0), 6) AS positive_share,
    ROUND(negative_mentions / NULLIF(total_mentions, 0), 6) AS negative_share,
    ROUND((positive_mentions - negative_mentions) / NULLIF(total_mentions, 0), 6) AS net_sentiment_balance,
    ROUND(stocktwits_mentions / NULLIF(total_mentions, 0), 6) AS stocktwits_share,
    ROUND((reddit_posts + reddit_comments) / NULLIF(total_mentions, 0), 6) AS reddit_share
FROM base
ORDER BY ticker, trade_date;
