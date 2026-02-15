-- ============================================================================
-- Table: search_trends
-- Purpose: 검색 트렌드 데이터 (Google Trends + Naver DataLab)
-- 외부 검색 지수와 내부 매출 상관 분석용
-- Created: 2026-02-15
-- ============================================================================

DROP TABLE IF EXISTS search_trends CASCADE;

CREATE TABLE search_trends (
    id SERIAL PRIMARY KEY,
    trend_date DATE NOT NULL,
    brand VARCHAR(20) NOT NULL CHECK (brand IN ('minix', 'thome', 'protione')),
    product_group VARCHAR(50) NOT NULL,
    keyword VARCHAR(100) NOT NULL,
    source VARCHAR(20) NOT NULL CHECK (source IN ('google_trends', 'naver_datalab')),
    trend_value DECIMAL(6, 2) NOT NULL DEFAULT 0,  -- 상대 지수 0-100

    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(trend_date, brand, product_group, keyword, source)
);

-- ============================================================================
-- 인덱스
-- ============================================================================

CREATE INDEX idx_search_trends_date ON search_trends(trend_date DESC);
CREATE INDEX idx_search_trends_brand ON search_trends(trend_date, brand);
CREATE INDEX idx_search_trends_source ON search_trends(trend_date, source);

-- ============================================================================
-- 샘플 데이터: 30일 (2026-01-14 ~ 2026-02-12)
-- 8 product_groups x 2 sources = ~480행
-- 패턴: 주말 딥, 성수기 스파이크, Google/Naver 상관(r>0.7)
-- ============================================================================

-- 날짜 생성 + 트렌드 값 삽입 함수
DO $$
DECLARE
    d DATE;
    dow INTEGER;
    base_val DECIMAL;
    google_val DECIMAL;
    naver_val DECIMAL;
    noise DECIMAL;
    weekend_factor DECIMAL;
    spike_factor DECIMAL;
BEGIN
    FOR d IN SELECT generate_series('2026-01-14'::date, '2026-02-12'::date, '1 day'::interval)::date
    LOOP
        dow := EXTRACT(DOW FROM d);  -- 0=Sun, 6=Sat

        -- 주말 딥 팩터 (토일 20~30% 하락)
        IF dow IN (0, 6) THEN
            weekend_factor := 0.70 + random() * 0.10;
        ELSE
            weekend_factor := 1.0;
        END IF;

        -- 성수기 스파이크 (2월 초 설 연휴 효과)
        IF d BETWEEN '2026-02-01' AND '2026-02-05' THEN
            spike_factor := 1.25 + random() * 0.15;
        ELSE
            spike_factor := 1.0;
        END IF;

        -- minix: 미니건조기
        base_val := 55 + random() * 15;
        google_val := ROUND((base_val * weekend_factor * spike_factor + (random() - 0.5) * 8)::numeric, 2);
        naver_val := ROUND((base_val * weekend_factor * spike_factor * (0.85 + random() * 0.30) + (random() - 0.5) * 6)::numeric, 2);
        INSERT INTO search_trends (trend_date, brand, product_group, keyword, source, trend_value) VALUES
            (d, 'minix', '미니건조기', '미니건조기', 'google_trends', GREATEST(0, LEAST(100, google_val))),
            (d, 'minix', '미니건조기', '미니건조기', 'naver_datalab', GREATEST(0, LEAST(100, naver_val)));

        -- minix: 식기세척기
        base_val := 62 + random() * 12;
        google_val := ROUND((base_val * weekend_factor * spike_factor + (random() - 0.5) * 7)::numeric, 2);
        naver_val := ROUND((base_val * weekend_factor * spike_factor * (0.88 + random() * 0.24) + (random() - 0.5) * 5)::numeric, 2);
        INSERT INTO search_trends (trend_date, brand, product_group, keyword, source, trend_value) VALUES
            (d, 'minix', '식기세척기', '식기세척기', 'google_trends', GREATEST(0, LEAST(100, google_val))),
            (d, 'minix', '식기세척기', '식기세척기', 'naver_datalab', GREATEST(0, LEAST(100, naver_val)));

        -- minix: 에어프라이어
        base_val := 72 + random() * 10;
        google_val := ROUND((base_val * weekend_factor + (random() - 0.5) * 6)::numeric, 2);
        naver_val := ROUND((base_val * weekend_factor * (0.90 + random() * 0.20) + (random() - 0.5) * 5)::numeric, 2);
        INSERT INTO search_trends (trend_date, brand, product_group, keyword, source, trend_value) VALUES
            (d, 'minix', '에어프라이어', '에어프라이어', 'google_trends', GREATEST(0, LEAST(100, google_val))),
            (d, 'minix', '에어프라이어', '에어프라이어', 'naver_datalab', GREATEST(0, LEAST(100, naver_val)));

        -- minix: 음식물처리기
        base_val := 48 + random() * 18;
        google_val := ROUND((base_val * weekend_factor * spike_factor + (random() - 0.5) * 10)::numeric, 2);
        naver_val := ROUND((base_val * weekend_factor * spike_factor * (0.82 + random() * 0.36) + (random() - 0.5) * 8)::numeric, 2);
        INSERT INTO search_trends (trend_date, brand, product_group, keyword, source, trend_value) VALUES
            (d, 'minix', '음식물처리기', '음식물처리기', 'google_trends', GREATEST(0, LEAST(100, google_val))),
            (d, 'minix', '음식물처리기', '음식물처리기', 'naver_datalab', GREATEST(0, LEAST(100, naver_val)));

        -- thome: 뷰티디바이스
        base_val := 45 + random() * 20;
        google_val := ROUND((base_val * weekend_factor + (random() - 0.5) * 9)::numeric, 2);
        naver_val := ROUND((base_val * weekend_factor * (0.80 + random() * 0.40) + (random() - 0.5) * 7)::numeric, 2);
        INSERT INTO search_trends (trend_date, brand, product_group, keyword, source, trend_value) VALUES
            (d, 'thome', '뷰티디바이스', '뷰티디바이스', 'google_trends', GREATEST(0, LEAST(100, google_val))),
            (d, 'thome', '뷰티디바이스', '뷰티디바이스', 'naver_datalab', GREATEST(0, LEAST(100, naver_val)));

        -- thome: LED마스크
        base_val := 38 + random() * 22;
        google_val := ROUND((base_val * weekend_factor + (random() - 0.5) * 10)::numeric, 2);
        naver_val := ROUND((base_val * weekend_factor * (0.85 + random() * 0.30) + (random() - 0.5) * 8)::numeric, 2);
        INSERT INTO search_trends (trend_date, brand, product_group, keyword, source, trend_value) VALUES
            (d, 'thome', 'LED마스크', 'LED마스크', 'google_trends', GREATEST(0, LEAST(100, google_val))),
            (d, 'thome', 'LED마스크', 'LED마스크', 'naver_datalab', GREATEST(0, LEAST(100, naver_val)));

        -- protione: 프로틴바
        base_val := 58 + random() * 14;
        google_val := ROUND((base_val * weekend_factor + (random() - 0.5) * 7)::numeric, 2);
        naver_val := ROUND((base_val * weekend_factor * (0.87 + random() * 0.26) + (random() - 0.5) * 6)::numeric, 2);
        INSERT INTO search_trends (trend_date, brand, product_group, keyword, source, trend_value) VALUES
            (d, 'protione', '프로틴바', '프로틴바', 'google_trends', GREATEST(0, LEAST(100, google_val))),
            (d, 'protione', '프로틴바', '프로틴바', 'naver_datalab', GREATEST(0, LEAST(100, naver_val)));

        -- protione: 프로틴쉐이크
        base_val := 42 + random() * 16;
        google_val := ROUND((base_val * weekend_factor + (random() - 0.5) * 8)::numeric, 2);
        naver_val := ROUND((base_val * weekend_factor * (0.83 + random() * 0.34) + (random() - 0.5) * 7)::numeric, 2);
        INSERT INTO search_trends (trend_date, brand, product_group, keyword, source, trend_value) VALUES
            (d, 'protione', '프로틴쉐이크', '프로틴쉐이크', 'google_trends', GREATEST(0, LEAST(100, google_val))),
            (d, 'protione', '프로틴쉐이크', '프로틴쉐이크', 'naver_datalab', GREATEST(0, LEAST(100, naver_val)));
    END LOOP;
END $$;

-- ============================================================================
-- RPC: get_trend_sales_correlation(p_days INTEGER)
-- 검색 트렌드 집계 + 매출 JOIN → 브랜드x소스별 상관 분석용 데이터
-- ============================================================================

CREATE OR REPLACE FUNCTION get_trend_sales_correlation(p_days INTEGER DEFAULT 30)
RETURNS TABLE(
    brand TEXT,
    trend_date DATE,
    source TEXT,
    avg_trend_value DECIMAL,
    total_revenue DECIMAL,
    total_orders INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        t.brand::TEXT AS brand,
        t.trend_date,
        t.source::TEXT AS source,
        ROUND(AVG(t.trend_value), 2) AS avg_trend_value,
        COALESCE(SUM(b.revenue), 0) AS total_revenue,
        COALESCE(SUM(b.orders), 0)::INTEGER AS total_orders
    FROM search_trends t
    LEFT JOIN brand_daily_sales b
        ON t.brand = b.brand AND t.trend_date = b.sale_date
    WHERE t.trend_date >= CURRENT_DATE - (p_days || ' days')::INTERVAL
    GROUP BY t.brand, t.trend_date, t.source
    ORDER BY t.brand, t.trend_date, t.source;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 데이터 검증
-- ============================================================================

SELECT brand, source, COUNT(*) AS cnt, ROUND(AVG(trend_value), 1) AS avg_val
FROM search_trends
GROUP BY brand, source
ORDER BY brand, source;
