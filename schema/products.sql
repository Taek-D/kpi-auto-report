-- ============================================================================
-- Tables: products + product_daily_sales
-- Purpose: 앳홈 제품 마스터 및 제품별 일일 매출 데이터
-- Brands: minix(미닉스), thome(톰), protione(프로티원)
-- Created: 2026-02-13
-- ============================================================================

-- 기존 테이블 삭제 (재생성 시)
DROP TABLE IF EXISTS product_daily_sales CASCADE;
DROP TABLE IF EXISTS products CASCADE;

-- ============================================================================
-- 제품 마스터 테이블
-- ============================================================================

CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    brand VARCHAR(20) NOT NULL CHECK (brand IN ('minix', 'thome', 'protione')),
    product_name VARCHAR(100) NOT NULL,
    sku VARCHAR(50) UNIQUE NOT NULL,
    category VARCHAR(50) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 미닉스 (minix) 제품
INSERT INTO products (brand, product_name, sku, category, price) VALUES
('minix', '미닉스 더플렌더',       'MNX-BLD-001', '소형가전',   89000),
('minix', '미닉스 미니건조기',     'MNX-DRY-001', '소형가전',   349000),
('minix', '미닉스 식기세척기',     'MNX-DSH-001', '소형가전',   459000),
('minix', '미닉스 에어프라이어',   'MNX-AFR-001', '소형가전',   129000),
('minix', '미닉스 음식물처리기',   'MNX-FDP-001', '소형가전',   690000);

-- 톰 (thome) 제품
INSERT INTO products (brand, product_name, sku, category, price) VALUES
('thome', '톰 더글로우 프로',     'THM-GLP-001', '뷰티디바이스', 298000),
('thome', '톰 더글로우',          'THM-GLW-001', '뷰티디바이스', 198000),
('thome', '톰 LED 마스크',        'THM-LED-001', '뷰티디바이스', 178000),
('thome', '톰 클렌저',            'THM-CLN-001', '뷰티디바이스', 89000);

-- 프로티원 (protione) 제품
INSERT INTO products (brand, product_name, sku, category, price) VALUES
('protione', '프로티원 바 초코',       'PRT-BAR-001', '건강기능식품', 32000),
('protione', '프로티원 바 피넛버터',   'PRT-BAR-002', '건강기능식품', 32000),
('protione', '프로티원 쉐이크 바닐라', 'PRT-SHK-001', '건강기능식품', 45000),
('protione', '프로티원 쉐이크 초코',   'PRT-SHK-002', '건강기능식품', 45000),
('protione', '프로티원 비타민 멀티',   'PRT-VIT-001', '건강기능식품', 28000);

-- ============================================================================
-- 제품별 일일 매출 테이블
-- ============================================================================

CREATE TABLE product_daily_sales (
    id SERIAL PRIMARY KEY,
    sale_date DATE NOT NULL,
    product_id INTEGER NOT NULL REFERENCES products(product_id),
    revenue DECIMAL(14, 2) NOT NULL DEFAULT 0,
    quantity_sold INTEGER NOT NULL DEFAULT 0,
    orders INTEGER NOT NULL DEFAULT 0,
    avg_rating DECIMAL(3, 2) DEFAULT NULL,
    review_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(sale_date, product_id)
);

-- 인덱스
CREATE INDEX idx_product_daily_sales_date ON product_daily_sales(sale_date DESC);
CREATE INDEX idx_product_daily_sales_product ON product_daily_sales(product_id);

-- ============================================================================
-- 샘플 데이터: 어제 (2026-02-12) 제품별 매출
-- ============================================================================

-- 미닉스 제품 매출
INSERT INTO product_daily_sales (sale_date, product_id, revenue, quantity_sold, orders, avg_rating, review_count) VALUES
('2026-02-12', 1,  2670000,  30, 28, 4.7, 12),   -- 미닉스 더플렌더
('2026-02-12', 2,  3490000,  10, 10, 4.8, 5),    -- 미닉스 미니건조기
('2026-02-12', 3,  4590000,  10, 10, 4.6, 3),    -- 미닉스 식기세척기
('2026-02-12', 4,  1290000,  10, 9,  4.5, 8),    -- 미닉스 에어프라이어
('2026-02-12', 5,  690000,   1,  1,  4.9, 1);    -- 미닉스 음식물처리기

-- 톰 제품 매출
INSERT INTO product_daily_sales (sale_date, product_id, revenue, quantity_sold, orders, avg_rating, review_count) VALUES
('2026-02-12', 6,  5960000,  20, 18, 4.8, 15),   -- 톰 더글로우 프로
('2026-02-12', 7,  2376000,  12, 11, 4.6, 9),    -- 톰 더글로우
('2026-02-12', 8,  1424000,  8,  7,  4.4, 6),    -- 톰 LED 마스크
('2026-02-12', 9,  534000,   6,  5,  4.3, 4);    -- 톰 클렌저

-- 프로티원 제품 매출
INSERT INTO product_daily_sales (sale_date, product_id, revenue, quantity_sold, orders, avg_rating, review_count) VALUES
('2026-02-12', 10, 1920000,  60, 45, 4.6, 22),   -- 프로티원 바 초코
('2026-02-12', 11, 1280000,  40, 30, 4.5, 18),   -- 프로티원 바 피넛버터
('2026-02-12', 12, 1350000,  30, 25, 4.7, 14),   -- 프로티원 쉐이크 바닐라
('2026-02-12', 13, 1125000,  25, 20, 4.6, 11),   -- 프로티원 쉐이크 초코
('2026-02-12', 14, 560000,   20, 18, 4.4, 8);    -- 프로티원 비타민 멀티

-- ============================================================================
-- 샘플 데이터: 지난주 (2026-02-05) 제품별 매출
-- ============================================================================

-- 미닉스 제품 매출
INSERT INTO product_daily_sales (sale_date, product_id, revenue, quantity_sold, orders, avg_rating, review_count) VALUES
('2026-02-05', 1,  2403000,  27, 25, 4.7, 10),
('2026-02-05', 2,  3141000,  9,  9,  4.8, 4),
('2026-02-05', 3,  4131000,  9,  9,  4.6, 2),
('2026-02-05', 4,  1161000,  9,  8,  4.5, 7),
('2026-02-05', 5,  0,        0,  0,  NULL, 0);

-- 톰 제품 매출
INSERT INTO product_daily_sales (sale_date, product_id, revenue, quantity_sold, orders, avg_rating, review_count) VALUES
('2026-02-05', 6,  4470000,  15, 14, 4.8, 12),
('2026-02-05', 7,  1980000,  10, 9,  4.6, 7),
('2026-02-05', 8,  1246000,  7,  6,  4.4, 5),
('2026-02-05', 9,  445000,   5,  4,  4.3, 3);

-- 프로티원 제품 매출
INSERT INTO product_daily_sales (sale_date, product_id, revenue, quantity_sold, orders, avg_rating, review_count) VALUES
('2026-02-05', 10, 1760000,  55, 42, 4.6, 20),
('2026-02-05', 11, 1152000,  36, 27, 4.5, 16),
('2026-02-05', 12, 1215000,  27, 22, 4.7, 12),
('2026-02-05', 13, 990000,   22, 18, 4.6, 9),
('2026-02-05', 14, 504000,   18, 16, 4.4, 7);

-- ============================================================================
-- RPC 함수: get_top_products()
-- 브랜드별 상위 제품 + 전체 상위 3개
-- ============================================================================

CREATE OR REPLACE FUNCTION get_top_products()
RETURNS TABLE(
    revenue_rank BIGINT,
    brand TEXT,
    product_name TEXT,
    total_revenue DECIMAL,
    units_sold INTEGER,
    order_count INTEGER,
    avg_rating DECIMAL,
    review_count INTEGER,
    revenue_share_pct DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    WITH ranked AS (
        SELECT
            RANK() OVER (ORDER BY pds.revenue DESC) AS revenue_rank,
            p.brand::TEXT AS brand,
            p.product_name::TEXT AS product_name,
            pds.revenue AS total_revenue,
            pds.quantity_sold::INTEGER AS units_sold,
            pds.orders::INTEGER AS order_count,
            pds.avg_rating,
            pds.review_count::INTEGER AS review_count,
            ROUND(
                (pds.revenue / NULLIF(SUM(pds.revenue) OVER (), 0)) * 100, 1
            ) AS revenue_share_pct
        FROM product_daily_sales pds
        JOIN products p ON p.product_id = pds.product_id
        WHERE pds.sale_date = CURRENT_DATE - INTERVAL '1 day'
          AND pds.revenue > 0
    )
    SELECT * FROM ranked
    WHERE ranked.revenue_rank <= 5
    ORDER BY ranked.revenue_rank;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 데이터 검증 쿼리
-- ============================================================================

-- 브랜드별 상위 제품
SELECT
    p.brand,
    p.product_name,
    pds.revenue,
    RANK() OVER (PARTITION BY p.brand ORDER BY pds.revenue DESC) AS brand_rank,
    RANK() OVER (ORDER BY pds.revenue DESC) AS overall_rank
FROM product_daily_sales pds
JOIN products p ON p.product_id = pds.product_id
WHERE pds.sale_date = CURRENT_DATE - INTERVAL '1 day'
  AND pds.revenue > 0
ORDER BY pds.revenue DESC;
