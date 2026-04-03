CREATE OR REPLACE TABLE analytics.top_social_posts AS
WITH ranked_content AS (
    SELECT
        ticker,
        platform,
        content_type,
        event_date,
        author,
        text_content,
        engagement_score,
        sentiment_score,
        sentiment_label,
        ROW_NUMBER() OVER (
            PARTITION BY ticker, sentiment_label
            ORDER BY ABS(sentiment_score) DESC, engagement_score DESC, event_date DESC
        ) AS rank_in_label
    FROM prepared_data.social_mentions
    WHERE sentiment_label IN ('positive', 'negative')
      AND text_content IS NOT NULL
      AND LENGTH(TRIM(text_content)) > 0
)
SELECT
    ticker,
    platform,
    content_type,
    event_date,
    author,
    text_content,
    engagement_score,
    sentiment_score,
    sentiment_label,
    rank_in_label
FROM ranked_content
WHERE rank_in_label <= 25
ORDER BY ticker, sentiment_label, rank_in_label;
