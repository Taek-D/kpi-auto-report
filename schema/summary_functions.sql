-- ============================================================================
-- Summary Report RPC Functions
-- get_weekly_summary(p_end_date): 주간 브랜드별 매출 합계 + WoW + 채널 비중
-- get_monthly_summary(p_year, p_month): 월간 브랜드별 합계 + MoM
-- ============================================================================

-- ============================================================================
-- RPC: get_weekly_summary(p_end_date DATE)
-- 해당 주(7일) 브랜드별 매출/주문/ROAS 합계 + 전주 대비 WoW 변화율
-- ============================================================================

CREATE OR REPLACE FUNCTION get_weekly_summary(p_end_date DATE DEFAULT CURRENT_DATE - INTERVAL '1 day')
RETURNS TABLE(
    brand TEXT,
    week_revenue DECIMAL,
    week_orders INTEGER,
    week_ad_spend DECIMAL,
    week_roas DECIMAL,
    prev_week_revenue DECIMAL,
    prev_week_orders INTEGER,
    revenue_wow_pct DECIMAL,
    orders_wow_pct DECIMAL,
    best_channel TEXT,
    worst_channel TEXT,
    channel_breakdown JSONB
) AS $$
BEGIN
    RETURN QUERY
    WITH current_week AS (
        SELECT
            b.brand::TEXT AS brand,
            SUM(b.revenue) AS week_revenue,
            SUM(b.orders)::INTEGER AS week_orders,
            SUM(b.ad_spend) AS week_ad_spend,
            CASE
                WHEN SUM(b.ad_spend) > 0
                THEN ROUND(SUM(b.revenue) / SUM(b.ad_spend), 2)
                ELSE 0
            END AS week_roas
        FROM brand_daily_sales b
        WHERE b.sale_date BETWEEN (p_end_date - INTERVAL '6 days') AND p_end_date
        GROUP BY b.brand
    ),
    prev_week AS (
        SELECT
            b.brand::TEXT AS brand,
            SUM(b.revenue) AS prev_revenue,
            SUM(b.orders)::INTEGER AS prev_orders
        FROM brand_daily_sales b
        WHERE b.sale_date BETWEEN (p_end_date - INTERVAL '13 days') AND (p_end_date - INTERVAL '7 days')
        GROUP BY b.brand
    ),
    channel_totals AS (
        SELECT
            sub.brand,
            sub.channel,
            sub.ch_revenue,
            sub.share_pct
        FROM (
            SELECT
                b.brand::TEXT AS brand,
                b.channel::TEXT AS channel,
                SUM(b.revenue) AS ch_revenue,
                ROUND(
                    (SUM(b.revenue) / NULLIF(SUM(SUM(b.revenue)) OVER (PARTITION BY b.brand), 0)) * 100, 1
                ) AS share_pct
            FROM brand_daily_sales b
            WHERE b.sale_date BETWEEN (p_end_date - INTERVAL '6 days') AND p_end_date
              AND b.revenue > 0
            GROUP BY b.brand, b.channel
        ) sub
    ),
    channel_agg AS (
        SELECT
            ct.brand,
            jsonb_agg(
                jsonb_build_object(
                    'channel', ct.channel,
                    'revenue', ct.ch_revenue,
                    'share_pct', ct.share_pct
                ) ORDER BY ct.ch_revenue DESC
            ) AS channel_breakdown
        FROM channel_totals ct
        GROUP BY ct.brand
    ),
    best_worst AS (
        SELECT DISTINCT ON (ct.brand)
            ct.brand,
            FIRST_VALUE(ct.channel) OVER (PARTITION BY ct.brand ORDER BY ct.ch_revenue DESC) AS best_channel,
            FIRST_VALUE(ct.channel) OVER (PARTITION BY ct.brand ORDER BY ct.ch_revenue ASC) AS worst_channel
        FROM channel_totals ct
    )
    SELECT
        cw.brand,
        cw.week_revenue,
        cw.week_orders,
        cw.week_ad_spend,
        cw.week_roas,
        COALESCE(pw.prev_revenue, 0) AS prev_week_revenue,
        COALESCE(pw.prev_orders, 0) AS prev_week_orders,
        CASE
            WHEN COALESCE(pw.prev_revenue, 0) > 0
            THEN ROUND(((cw.week_revenue - pw.prev_revenue) / pw.prev_revenue) * 100, 1)
            ELSE 0
        END AS revenue_wow_pct,
        CASE
            WHEN COALESCE(pw.prev_orders, 0) > 0
            THEN ROUND(((cw.week_orders - pw.prev_orders)::DECIMAL / pw.prev_orders) * 100, 1)
            ELSE 0
        END AS orders_wow_pct,
        COALESCE(bw.best_channel, '') AS best_channel,
        COALESCE(bw.worst_channel, '') AS worst_channel,
        COALESCE(ca.channel_breakdown, '[]'::JSONB) AS channel_breakdown
    FROM current_week cw
    LEFT JOIN prev_week pw ON cw.brand = pw.brand
    LEFT JOIN channel_agg ca ON cw.brand = ca.brand
    LEFT JOIN best_worst bw ON cw.brand = bw.brand
    ORDER BY cw.week_revenue DESC;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- RPC: get_monthly_summary(p_year INT, p_month INT)
-- 해당 월 브랜드별 합계 + 전월 대비 MoM 변화율
-- ============================================================================

CREATE OR REPLACE FUNCTION get_monthly_summary(p_year INT DEFAULT EXTRACT(YEAR FROM CURRENT_DATE)::INT, p_month INT DEFAULT EXTRACT(MONTH FROM CURRENT_DATE)::INT)
RETURNS TABLE(
    brand TEXT,
    month_revenue DECIMAL,
    month_orders INTEGER,
    month_ad_spend DECIMAL,
    month_roas DECIMAL,
    prev_month_revenue DECIMAL,
    prev_month_orders INTEGER,
    revenue_mom_pct DECIMAL,
    orders_mom_pct DECIMAL,
    channel_breakdown JSONB
) AS $$
DECLARE
    v_start_date DATE;
    v_end_date DATE;
    v_prev_start DATE;
    v_prev_end DATE;
BEGIN
    v_start_date := make_date(p_year, p_month, 1);
    v_end_date := (v_start_date + INTERVAL '1 month' - INTERVAL '1 day')::DATE;
    v_prev_start := (v_start_date - INTERVAL '1 month')::DATE;
    v_prev_end := (v_start_date - INTERVAL '1 day')::DATE;

    RETURN QUERY
    WITH current_month AS (
        SELECT
            b.brand::TEXT AS brand,
            SUM(b.revenue) AS month_revenue,
            SUM(b.orders)::INTEGER AS month_orders,
            SUM(b.ad_spend) AS month_ad_spend,
            CASE
                WHEN SUM(b.ad_spend) > 0
                THEN ROUND(SUM(b.revenue) / SUM(b.ad_spend), 2)
                ELSE 0
            END AS month_roas
        FROM brand_daily_sales b
        WHERE b.sale_date BETWEEN v_start_date AND v_end_date
        GROUP BY b.brand
    ),
    prev_month AS (
        SELECT
            b.brand::TEXT AS brand,
            SUM(b.revenue) AS prev_revenue,
            SUM(b.orders)::INTEGER AS prev_orders
        FROM brand_daily_sales b
        WHERE b.sale_date BETWEEN v_prev_start AND v_prev_end
        GROUP BY b.brand
    ),
    channel_shares AS (
        SELECT
            sub.brand,
            jsonb_agg(
                jsonb_build_object(
                    'channel', sub.channel,
                    'revenue', sub.ch_revenue,
                    'share_pct', sub.share_pct
                ) ORDER BY sub.ch_revenue DESC
            ) AS channel_breakdown
        FROM (
            SELECT
                b.brand::TEXT AS brand,
                b.channel::TEXT AS channel,
                SUM(b.revenue) AS ch_revenue,
                ROUND(
                    (SUM(b.revenue) / NULLIF(SUM(SUM(b.revenue)) OVER (PARTITION BY b.brand), 0)) * 100, 1
                ) AS share_pct
            FROM brand_daily_sales b
            WHERE b.sale_date BETWEEN v_start_date AND v_end_date
              AND b.revenue > 0
            GROUP BY b.brand, b.channel
        ) sub
        GROUP BY sub.brand
    )
    SELECT
        cm.brand,
        cm.month_revenue,
        cm.month_orders,
        cm.month_ad_spend,
        cm.month_roas,
        COALESCE(pm.prev_revenue, 0) AS prev_month_revenue,
        COALESCE(pm.prev_orders, 0) AS prev_month_orders,
        CASE
            WHEN COALESCE(pm.prev_revenue, 0) > 0
            THEN ROUND(((cm.month_revenue - pm.prev_revenue) / pm.prev_revenue) * 100, 1)
            ELSE 0
        END AS revenue_mom_pct,
        CASE
            WHEN COALESCE(pm.prev_orders, 0) > 0
            THEN ROUND(((cm.month_orders - pm.prev_orders)::DECIMAL / pm.prev_orders) * 100, 1)
            ELSE 0
        END AS orders_mom_pct,
        COALESCE(cs.channel_breakdown, '[]'::JSONB) AS channel_breakdown
    FROM current_month cm
    LEFT JOIN prev_month pm ON cm.brand = pm.brand
    LEFT JOIN channel_shares cs ON cm.brand = cs.brand
    ORDER BY cm.month_revenue DESC;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 검증 쿼리
-- ============================================================================

-- 주간 요약 테스트
SELECT * FROM get_weekly_summary('2026-02-12');

-- 월간 요약 테스트 (2026년 2월)
SELECT * FROM get_monthly_summary(2026, 2);
