CREATE OR REPLACE TABLE analytics.ticker_overview AS
SELECT
    ticker,
    COUNT(*) AS trading_days,
    SUM(CASE WHEN total_mentions > 0 THEN 1 ELSE 0 END) AS active_social_days,
    SUM(total_mentions) AS total_mentions,
    SUM(stocktwits_mentions) AS stocktwits_mentions,
    SUM(reddit_posts) AS reddit_posts,
    SUM(reddit_comments) AS reddit_comments,
    ROUND(SUM(total_engagement), 6) AS total_engagement,
    ROUND(AVG(avg_sentiment), 6) AS avg_daily_sentiment,
    ROUND(AVG(engagement_weighted_sentiment), 6) AS avg_weighted_sentiment,
    ROUND(AVG(positive_share), 6) AS avg_positive_share,
    ROUND(AVG(negative_share), 6) AS avg_negative_share,
    ROUND(AVG(total_mentions), 6) AS avg_mentions_per_day,
    ROUND(AVG(CASE WHEN total_mentions > 0 THEN total_mentions END), 6) AS avg_mentions_per_active_day,
    ROUND(AVG(daily_return), 6) AS avg_daily_return,
    ROUND(AVG(return_7d_volatility), 6) AS avg_return_volatility_7d,
    ROUND(CORR(avg_sentiment, daily_return), 6) AS sentiment_same_day_corr,
    ROUND(CORR(engagement_weighted_sentiment, daily_return), 6) AS weighted_sentiment_same_day_corr,
    ROUND(CORR(avg_sentiment, next_day_return), 6) AS sentiment_next_day_corr,
    ROUND(CORR(engagement_weighted_sentiment, next_day_return), 6) AS weighted_sentiment_next_day_corr,
    ROUND(MAX(mention_zscore_14d), 6) AS peak_attention_zscore,
    MAX(total_mentions) AS peak_day_mentions,
    ARG_MAX(trade_date, total_mentions) AS peak_attention_date,
    ARG_MAX(trade_date, avg_sentiment) AS most_bullish_date,
    ARG_MIN(trade_date, avg_sentiment) AS most_bearish_date
FROM analytics.daily_market_social
GROUP BY 1
ORDER BY ticker;
