CREATE OR REPLACE TABLE gold.daily_social_signals AS
SELECT
    ticker,
    event_date AS trade_date,
    COUNT(*) AS total_mentions,
    SUM(CASE WHEN platform = 'stocktwits' THEN 1 ELSE 0 END) AS stocktwits_mentions,
    SUM(CASE WHEN platform = 'reddit' AND content_type = 'post' THEN 1 ELSE 0 END) AS reddit_posts,
    SUM(CASE WHEN platform = 'reddit' AND content_type = 'comment' THEN 1 ELSE 0 END) AS reddit_comments,
    COUNT(DISTINCT author) AS unique_authors,
    ROUND(AVG(sentiment_score), 6) AS avg_sentiment,
    SUM(CASE WHEN sentiment_label = 'positive' THEN 1 ELSE 0 END) AS positive_mentions,
    SUM(CASE WHEN sentiment_label = 'negative' THEN 1 ELSE 0 END) AS negative_mentions
FROM silver.social_mentions
GROUP BY 1, 2
ORDER BY ticker, trade_date;

