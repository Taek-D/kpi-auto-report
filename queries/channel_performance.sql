-- ============================================================================
-- Query: channel_performance.sql
-- Purpose: 채널별 매출, ROAS, 전환율 비교 + WoW 변동
-- Source: brand_daily_sales 테이블 (Supabase)
-- Usage: n8n transform.js에서 참조용 (별도 RPC 없이 brand_kpis에 포함)
-- ============================================================================

-- 채널별 어제 vs 지난주 비교
WITH yesterday_channels AS (
    SELECT
        channel,
        SUM(revenue) AS revenue,
        SUM(orders) AS orders,
        SUM(visitors) AS visitors,
        CASE
            WHEN SUM(visitors) > 0
            THEN ROUND((SUM(orders)::DECIMAL / SUM(visitors)) * 100, 2)
            ELSE 0
        END AS conversion_rate,
        SUM(ad_spend) AS ad_spend,
        CASE
            WHEN SUM(ad_spend) > 0
            THEN ROUND(SUM(revenue) / SUM(ad_spend), 2)
            ELSE 0
        END AS roas
    FROM brand_daily_sales
    WHERE sale_date = CURRENT_DATE - INTERVAL '1 day'
    GROUP BY channel
),

last_week_channels AS (
    SELECT
        channel,
        SUM(revenue) AS revenue,
        SUM(orders) AS orders,
        SUM(visitors) AS visitors,
        CASE
            WHEN SUM(visitors) > 0
            THEN ROUND((SUM(orders)::DECIMAL / SUM(visitors)) * 100, 2)
            ELSE 0
        END AS conversion_rate,
        SUM(ad_spend) AS ad_spend,
        CASE
            WHEN SUM(ad_spend) > 0
            THEN ROUND(SUM(revenue) / SUM(ad_spend), 2)
            ELSE 0
        END AS roas
    FROM brand_daily_sales
    WHERE sale_date = CURRENT_DATE - INTERVAL '8 days'
    GROUP BY channel
)

SELECT
    y.channel,
    y.revenue AS current_revenue,
    lw.revenue AS prev_revenue,
    ROUND(
        ((y.revenue - COALESCE(lw.revenue, 0)) / NULLIF(lw.revenue, 0)) * 100, 1
    ) AS revenue_wow_pct,

    -- 채널 매출 순위 (WoW)
    RANK() OVER (ORDER BY y.revenue DESC) AS current_rank,

    y.roas AS current_roas,
    lw.roas AS prev_roas,
    ROUND(y.roas - COALESCE(lw.roas, 0), 2) AS roas_change,

    y.conversion_rate AS current_conv_rate,
    lw.conversion_rate AS prev_conv_rate,
    ROUND(y.conversion_rate - COALESCE(lw.conversion_rate, 0), 2) AS conv_rate_change

FROM yesterday_channels y
LEFT JOIN last_week_channels lw ON y.channel = lw.channel
WHERE y.revenue > 0
ORDER BY y.revenue DESC;
