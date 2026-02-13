-- ============================================================================
-- Query: brand_kpis_yesterday.sql
-- Purpose: 어제 날짜의 브랜드별 KPI 집계 + 채널별 매출 비중
-- Source: brand_daily_sales 테이블 (Supabase)
-- Usage: Supabase RPC get_brand_kpis_yesterday() 함수 원본
-- ============================================================================

-- 브랜드별 집계
WITH brand_totals AS (
    SELECT
        brand,
        SUM(revenue) AS total_revenue,
        SUM(orders) AS total_orders,
        SUM(quantity_sold) AS total_quantity,
        SUM(visitors) AS total_visitors,
        CASE
            WHEN SUM(visitors) > 0
            THEN ROUND((SUM(orders)::DECIMAL / SUM(visitors)) * 100, 2)
            ELSE 0
        END AS avg_conversion_rate,
        SUM(ad_spend) AS total_ad_spend,
        CASE
            WHEN SUM(ad_spend) > 0
            THEN ROUND(SUM(revenue) / SUM(ad_spend), 2)
            ELSE 0
        END AS avg_roas
    FROM brand_daily_sales
    WHERE sale_date = CURRENT_DATE - INTERVAL '1 day'
    GROUP BY brand
),

-- 채널별 매출 비중 (Window Function: SUM OVER PARTITION BY)
channel_shares AS (
    SELECT
        brand,
        channel,
        revenue,
        orders,
        ROUND(
            (revenue / NULLIF(SUM(revenue) OVER (PARTITION BY brand), 0)) * 100, 1
        ) AS channel_share_pct
    FROM brand_daily_sales
    WHERE sale_date = CURRENT_DATE - INTERVAL '1 day'
      AND revenue > 0
    ORDER BY brand, revenue DESC
),

-- 전체 합계
grand_total AS (
    SELECT
        'total' AS brand,
        SUM(revenue) AS total_revenue,
        SUM(orders) AS total_orders,
        SUM(quantity_sold) AS total_quantity,
        SUM(visitors) AS total_visitors,
        CASE
            WHEN SUM(visitors) > 0
            THEN ROUND((SUM(orders)::DECIMAL / SUM(visitors)) * 100, 2)
            ELSE 0
        END AS avg_conversion_rate,
        SUM(ad_spend) AS total_ad_spend,
        CASE
            WHEN SUM(ad_spend) > 0
            THEN ROUND(SUM(revenue) / SUM(ad_spend), 2)
            ELSE 0
        END AS avg_roas
    FROM brand_daily_sales
    WHERE sale_date = CURRENT_DATE - INTERVAL '1 day'
)

-- 브랜드별 결과
SELECT * FROM brand_totals
UNION ALL
SELECT * FROM grand_total
ORDER BY
    CASE brand
        WHEN 'total' THEN 'zzz'
        ELSE brand
    END;
