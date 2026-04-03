CREATE OR REPLACE TABLE analytics.ticker_overview AS
SELECT
    ticker,
    COUNT(*) AS trading_days,
    SUM(total_mentions) AS total_mentions,
    SUM(stocktwits_mentions) AS stocktwits_mentions,
    SUM(reddit_posts) AS reddit_posts,
    SUM(reddit_comments) AS reddit_comments,
    ROUND(AVG(avg_sentiment), 6) AS avg_daily_sentiment,
    ROUND(AVG(daily_return), 6) AS avg_daily_return,
    ROUND(CORR(avg_sentiment, daily_return), 6) AS sentiment_same_day_corr,
    ROUND(CORR(avg_sentiment, next_day_return), 6) AS sentiment_next_day_corr
FROM analytics.daily_market_social
GROUP BY 1
ORDER BY ticker;
