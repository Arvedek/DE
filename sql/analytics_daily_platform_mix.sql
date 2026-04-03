CREATE OR REPLACE TABLE analytics.daily_platform_mix AS
SELECT
    ticker,
    event_date AS trade_date,
    platform,
    COUNT(*) AS mention_count,
    COUNT(DISTINCT author) AS unique_authors,
    ROUND(AVG(sentiment_score), 6) AS avg_sentiment,
    ROUND(
        SUM(sentiment_score * GREATEST(COALESCE(engagement_score, 0), 1))
        / NULLIF(SUM(GREATEST(COALESCE(engagement_score, 0), 1)), 0),
        6
    ) AS engagement_weighted_sentiment,
    ROUND(SUM(COALESCE(engagement_score, 0)), 6) AS total_engagement
FROM prepared_data.social_mentions
GROUP BY 1, 2, 3
ORDER BY ticker, trade_date, platform;
