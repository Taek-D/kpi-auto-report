-- ============================================================================
-- Table: daily_summary
-- Purpose: 일일 집계 데이터를 저장하여 쿼리 성능 최적화
-- Created: 2026-02-13
-- ============================================================================

-- 기존 테이블 삭제 (재생성 시)
DROP TABLE IF EXISTS daily_summary CASCADE;

-- 일일 요약 테이블 생성
CREATE TABLE daily_summary (
    -- 기본 키
    summary_date DATE PRIMARY KEY,
    
    -- 핵심 KPI 메트릭
    total_revenue DECIMAL(14, 2) NOT NULL DEFAULT 0,
    total_orders INTEGER NOT NULL DEFAULT 0,
    total_visitors INTEGER NOT NULL DEFAULT 0,
    avg_order_value DECIMAL(10, 2) GENERATED ALWAYS AS (
        CASE 
            WHEN total_orders > 0 THEN total_revenue / total_orders 
            ELSE 0 
        END
    ) STORED,
    conversion_rate DECIMAL(5, 2) GENERATED ALWAYS AS (
        CASE 
            WHEN total_visitors > 0 THEN (total_orders::DECIMAL / total_visitors) * 100 
            ELSE 0 
        END
    ) STORED,
    
    -- 메타데이터
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- 인덱스 생성
-- ============================================================================

-- 날짜 기반 조회 최적화
CREATE INDEX idx_daily_summary_date ON daily_summary(summary_date DESC);

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

CREATE TRIGGER update_daily_summary_updated_at
    BEFORE UPDATE ON daily_summary
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 샘플 데이터 (개발/테스트용)
-- ============================================================================

-- 지난주 데이터 (2026-02-05)
INSERT INTO daily_summary (summary_date, total_revenue, total_orders, total_visitors)
VALUES ('2026-02-05', 15000000, 450, 12000);

-- 어제 데이터 (2026-02-12)
INSERT INTO daily_summary (summary_date, total_revenue, total_orders, total_visitors)
VALUES ('2026-02-12', 18750000, 520, 13500);

-- ============================================================================
-- 데이터 검증 쿼리
-- ============================================================================

-- 테이블 구조 확인
-- \d daily_summary

-- 샘플 데이터 조회
SELECT 
    summary_date,
    total_revenue,
    total_orders,
    avg_order_value,
    conversion_rate,
    created_at
FROM daily_summary
ORDER BY summary_date DESC
LIMIT 10;

-- WoW 변화율 계산 예제
SELECT 
    summary_date,
    total_revenue,
    LAG(total_revenue) OVER (ORDER BY summary_date) AS prev_week_revenue,
    ROUND(
        ((total_revenue - LAG(total_revenue) OVER (ORDER BY summary_date)) 
        / NULLIF(LAG(total_revenue) OVER (ORDER BY summary_date), 0)) * 100, 
        2
    ) AS wow_change_pct
FROM daily_summary
WHERE summary_date >= CURRENT_DATE - INTERVAL '14 days'
ORDER BY summary_date DESC;
