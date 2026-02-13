-- ============================================================================
-- Table: brand_daily_sales
-- Purpose: 앳홈 브랜드별/채널별 일일 매출 데이터
-- Brands: minix(미닉스), thome(톰), protione(프로티원)
-- Channels: own_mall, coupang, naver, gs_home, oliveyoung
-- Created: 2026-02-13
-- ============================================================================

-- 기존 테이블 삭제 (재생성 시)
DROP TABLE IF EXISTS brand_daily_sales CASCADE;

-- 브랜드별 일일 매출 테이블
CREATE TABLE brand_daily_sales (
    id SERIAL PRIMARY KEY,
    sale_date DATE NOT NULL,
    brand VARCHAR(20) NOT NULL CHECK (brand IN ('minix', 'thome', 'protione')),
    channel VARCHAR(20) NOT NULL CHECK (channel IN ('own_mall', 'coupang', 'naver', 'gs_home', 'oliveyoung')),

    -- 매출 지표
    revenue DECIMAL(14, 2) NOT NULL DEFAULT 0,
    orders INTEGER NOT NULL DEFAULT 0,
    quantity_sold INTEGER NOT NULL DEFAULT 0,

    -- 트래픽 지표
    visitors INTEGER NOT NULL DEFAULT 0,
    conversion_rate DECIMAL(5, 2) NOT NULL DEFAULT 0.00,

    -- 광고 지표
    ad_spend DECIMAL(12, 2) NOT NULL DEFAULT 0,
    roas DECIMAL(8, 2) NOT NULL DEFAULT 0.00,

    -- 메타데이터
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- 유니크 제약조건: 날짜+브랜드+채널 조합은 유일
    UNIQUE(sale_date, brand, channel)
);

-- ============================================================================
-- 인덱스 생성
-- ============================================================================

CREATE INDEX idx_brand_daily_sales_date_brand ON brand_daily_sales(sale_date, brand);
CREATE INDEX idx_brand_daily_sales_date_channel ON brand_daily_sales(sale_date, channel);
CREATE INDEX idx_brand_daily_sales_date_desc ON brand_daily_sales(sale_date DESC);

-- ============================================================================
-- 트리거: updated_at 자동 갱신
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_brand_daily_sales_updated_at
    BEFORE UPDATE ON brand_daily_sales
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 샘플 데이터: 어제 (2026-02-12) - 브랜드 x 채널
-- ============================================================================

-- 미닉스 (minix) - 소형가전 브랜드
INSERT INTO brand_daily_sales (sale_date, brand, channel, revenue, orders, quantity_sold, visitors, conversion_rate, ad_spend, roas) VALUES
('2026-02-12', 'minix', 'own_mall',     2850000,  38, 42,  4200, 0.90, 320000, 8.91),
('2026-02-12', 'minix', 'coupang',      4120000,  55, 61,  8500, 0.65, 580000, 7.10),
('2026-02-12', 'minix', 'naver',        1960000,  26, 29,  5100, 0.51, 410000, 4.78),
('2026-02-12', 'minix', 'gs_home',      3500000,  12, 15,  0,    0.00, 0,      0.00),
('2026-02-12', 'minix', 'oliveyoung',   0,        0,  0,   0,    0.00, 0,      0.00);

-- 톰 (thome) - 뷰티디바이스 브랜드
INSERT INTO brand_daily_sales (sale_date, brand, channel, revenue, orders, quantity_sold, visitors, conversion_rate, ad_spend, roas) VALUES
('2026-02-12', 'thome', 'own_mall',     1680000,  24, 26,  3100, 0.77, 220000, 7.64),
('2026-02-12', 'thome', 'coupang',      2340000,  33, 36,  6200, 0.53, 380000, 6.16),
('2026-02-12', 'thome', 'naver',        1150000,  16, 18,  3800, 0.42, 290000, 3.97),
('2026-02-12', 'thome', 'gs_home',      5200000,  18, 22,  0,    0.00, 0,      0.00),
('2026-02-12', 'thome', 'oliveyoung',   890000,   12, 14,  2100, 0.57, 150000, 5.93);

-- 프로티원 (protione) - 건강기능식품 브랜드
INSERT INTO brand_daily_sales (sale_date, brand, channel, revenue, orders, quantity_sold, visitors, conversion_rate, ad_spend, roas) VALUES
('2026-02-12', 'protione', 'own_mall',     1420000,  45, 68,  3500, 1.29, 180000, 7.89),
('2026-02-12', 'protione', 'coupang',      2180000,  72, 108, 7200, 1.00, 350000, 6.23),
('2026-02-12', 'protione', 'naver',        980000,   31, 47,  4100, 0.76, 260000, 3.77),
('2026-02-12', 'protione', 'gs_home',      0,        0,  0,   0,    0.00, 0,      0.00),
('2026-02-12', 'protione', 'oliveyoung',   1650000,  52, 79,  5800, 0.90, 280000, 5.89);

-- ============================================================================
-- 샘플 데이터: 지난주 동일 요일 (2026-02-05) - 브랜드 x 채널
-- ============================================================================

-- 미닉스 (minix)
INSERT INTO brand_daily_sales (sale_date, brand, channel, revenue, orders, quantity_sold, visitors, conversion_rate, ad_spend, roas) VALUES
('2026-02-05', 'minix', 'own_mall',     2620000,  35, 39,  4000, 0.88, 300000, 8.73),
('2026-02-05', 'minix', 'coupang',      3780000,  50, 56,  8100, 0.62, 550000, 6.87),
('2026-02-05', 'minix', 'naver',        1850000,  24, 27,  4900, 0.49, 400000, 4.63),
('2026-02-05', 'minix', 'gs_home',      0,        0,  0,   0,    0.00, 0,      0.00),
('2026-02-05', 'minix', 'oliveyoung',   0,        0,  0,   0,    0.00, 0,      0.00);

-- 톰 (thome)
INSERT INTO brand_daily_sales (sale_date, brand, channel, revenue, orders, quantity_sold, visitors, conversion_rate, ad_spend, roas) VALUES
('2026-02-05', 'thome', 'own_mall',     1520000,  22, 24,  2900, 0.76, 200000, 7.60),
('2026-02-05', 'thome', 'coupang',      2150000,  30, 33,  5800, 0.52, 360000, 5.97),
('2026-02-05', 'thome', 'naver',        1080000,  15, 17,  3600, 0.42, 280000, 3.86),
('2026-02-05', 'thome', 'gs_home',      0,        0,  0,   0,    0.00, 0,      0.00),
('2026-02-05', 'thome', 'oliveyoung',   820000,   11, 13,  1950, 0.56, 140000, 5.86);

-- 프로티원 (protione)
INSERT INTO brand_daily_sales (sale_date, brand, channel, revenue, orders, quantity_sold, visitors, conversion_rate, ad_spend, roas) VALUES
('2026-02-05', 'protione', 'own_mall',     1350000,  42, 64,  3300, 1.27, 170000, 7.94),
('2026-02-05', 'protione', 'coupang',      1980000,  65, 98,  6800, 0.96, 330000, 6.00),
('2026-02-05', 'protione', 'naver',        920000,   29, 44,  3900, 0.74, 250000, 3.68),
('2026-02-05', 'protione', 'gs_home',      0,        0,  0,   0,    0.00, 0,      0.00),
('2026-02-05', 'protione', 'oliveyoung',   1520000,  48, 73,  5500, 0.87, 260000, 5.85);

-- ============================================================================
-- RPC 함수: get_brand_kpis_yesterday()
-- 브랜드별 집계 + 전체 합계 + 채널별 매출 비중
-- ============================================================================

CREATE OR REPLACE FUNCTION get_brand_kpis_yesterday()
RETURNS TABLE(
    brand TEXT,
    total_revenue DECIMAL,
    total_orders INTEGER,
    total_quantity INTEGER,
    total_visitors INTEGER,
    avg_conversion_rate DECIMAL,
    total_ad_spend DECIMAL,
    avg_roas DECIMAL,
    channel_breakdown JSONB
) AS $$
BEGIN
    RETURN QUERY
    WITH brand_totals AS (
        SELECT
            b.brand::TEXT AS brand,
            SUM(b.revenue) AS total_revenue,
            SUM(b.orders)::INTEGER AS total_orders,
            SUM(b.quantity_sold)::INTEGER AS total_quantity,
            SUM(b.visitors)::INTEGER AS total_visitors,
            CASE
                WHEN SUM(b.visitors) > 0
                THEN ROUND((SUM(b.orders)::DECIMAL / SUM(b.visitors)) * 100, 2)
                ELSE 0
            END AS avg_conversion_rate,
            SUM(b.ad_spend) AS total_ad_spend,
            CASE
                WHEN SUM(b.ad_spend) > 0
                THEN ROUND(SUM(b.revenue) / SUM(b.ad_spend), 2)
                ELSE 0
            END AS avg_roas
        FROM brand_daily_sales b
        WHERE b.sale_date = CURRENT_DATE - INTERVAL '1 day'
        GROUP BY b.brand
    ),
    channel_shares AS (
        SELECT
            sub.brand,
            jsonb_agg(
                jsonb_build_object(
                    'channel', sub.channel,
                    'revenue', sub.revenue,
                    'orders', sub.orders,
                    'share_pct', sub.share_pct
                ) ORDER BY sub.revenue DESC
            ) AS channel_breakdown
        FROM (
            SELECT
                b.brand::TEXT AS brand,
                b.channel,
                b.revenue,
                b.orders,
                ROUND(
                    (b.revenue / NULLIF(SUM(b.revenue) OVER (PARTITION BY b.brand), 0)) * 100, 1
                ) AS share_pct
            FROM brand_daily_sales b
            WHERE b.sale_date = CURRENT_DATE - INTERVAL '1 day'
              AND b.revenue > 0
        ) sub
        GROUP BY sub.brand
    )
    SELECT
        bt.brand,
        bt.total_revenue,
        bt.total_orders,
        bt.total_quantity,
        bt.total_visitors,
        bt.avg_conversion_rate,
        bt.total_ad_spend,
        bt.avg_roas,
        COALESCE(cs.channel_breakdown, '[]'::JSONB) AS channel_breakdown
    FROM brand_totals bt
    LEFT JOIN channel_shares cs ON bt.brand = cs.brand
    ORDER BY bt.total_revenue DESC;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- RPC 함수: get_brand_kpis_last_week()
-- 지난주 동일 요일 브랜드별 집계
-- ============================================================================

CREATE OR REPLACE FUNCTION get_brand_kpis_last_week()
RETURNS TABLE(
    brand TEXT,
    total_revenue DECIMAL,
    total_orders INTEGER,
    total_quantity INTEGER,
    total_visitors INTEGER,
    avg_conversion_rate DECIMAL,
    total_ad_spend DECIMAL,
    avg_roas DECIMAL,
    channel_breakdown JSONB
) AS $$
BEGIN
    RETURN QUERY
    WITH brand_totals AS (
        SELECT
            b.brand::TEXT AS brand,
            SUM(b.revenue) AS total_revenue,
            SUM(b.orders)::INTEGER AS total_orders,
            SUM(b.quantity_sold)::INTEGER AS total_quantity,
            SUM(b.visitors)::INTEGER AS total_visitors,
            CASE
                WHEN SUM(b.visitors) > 0
                THEN ROUND((SUM(b.orders)::DECIMAL / SUM(b.visitors)) * 100, 2)
                ELSE 0
            END AS avg_conversion_rate,
            SUM(b.ad_spend) AS total_ad_spend,
            CASE
                WHEN SUM(b.ad_spend) > 0
                THEN ROUND(SUM(b.revenue) / SUM(b.ad_spend), 2)
                ELSE 0
            END AS avg_roas
        FROM brand_daily_sales b
        WHERE b.sale_date = CURRENT_DATE - INTERVAL '8 days'
        GROUP BY b.brand
    ),
    channel_shares AS (
        SELECT
            sub.brand,
            jsonb_agg(
                jsonb_build_object(
                    'channel', sub.channel,
                    'revenue', sub.revenue,
                    'orders', sub.orders,
                    'share_pct', sub.share_pct
                ) ORDER BY sub.revenue DESC
            ) AS channel_breakdown
        FROM (
            SELECT
                b.brand::TEXT AS brand,
                b.channel,
                b.revenue,
                b.orders,
                ROUND(
                    (b.revenue / NULLIF(SUM(b.revenue) OVER (PARTITION BY b.brand), 0)) * 100, 1
                ) AS share_pct
            FROM brand_daily_sales b
            WHERE b.sale_date = CURRENT_DATE - INTERVAL '8 days'
              AND b.revenue > 0
        ) sub
        GROUP BY sub.brand
    )
    SELECT
        bt.brand,
        bt.total_revenue,
        bt.total_orders,
        bt.total_quantity,
        bt.total_visitors,
        bt.avg_conversion_rate,
        bt.total_ad_spend,
        bt.avg_roas,
        COALESCE(cs.channel_breakdown, '[]'::JSONB) AS channel_breakdown
    FROM brand_totals bt
    LEFT JOIN channel_shares cs ON bt.brand = cs.brand
    ORDER BY bt.total_revenue DESC;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 데이터 검증 쿼리
-- ============================================================================

-- 어제 브랜드별 매출 확인
SELECT brand, SUM(revenue) AS total_revenue, SUM(orders) AS total_orders
FROM brand_daily_sales
WHERE sale_date = CURRENT_DATE - INTERVAL '1 day'
GROUP BY brand
ORDER BY total_revenue DESC;

-- 채널별 매출 비중 (Window Function)
SELECT
    brand,
    channel,
    revenue,
    ROUND(
        (revenue / NULLIF(SUM(revenue) OVER (PARTITION BY brand), 0)) * 100, 1
    ) AS share_pct
FROM brand_daily_sales
WHERE sale_date = CURRENT_DATE - INTERVAL '1 day'
  AND revenue > 0
ORDER BY brand, revenue DESC;
