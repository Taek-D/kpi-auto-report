# 테스트 결과

## 테스트 개요

**테스트 날짜**: 2026-02-13 (v2 앳홈 도메인 전환)
**테스트 환경**: 로컬 Docker (n8n) + Supabase (PostgreSQL)
**테스트 범위**: Supabase RPC, n8n 워크플로우, Slack 연동

**v2 변경사항**: Generic E-commerce -> 앳홈(미닉스/톰/프로티원) 도메인 전환

---

## 테스트 케이스

### TC-1: Supabase RPC 함수 정확성

**목적**: 각 RPC 함수가 올바른 결과를 반환하는지 확인

| RPC 함수 | 예상 결과 | 상태 |
|----------|---------|------|
| get_brand_kpis_yesterday() | 브랜드별 어제 KPI (3행) | -- Supabase 실행 대기 |
| get_brand_kpis_last_week() | 브랜드별 지난주 KPI (3행) | -- Supabase 실행 대기 |
| get_top_products() | 매출 상위 5개 제품 | -- Supabase 실행 대기 |
| get_competitor_changes() | 경쟁사 순위/가격 변동 | -- Supabase 실행 대기 |

### TC-2: 브랜드별 WoW 계산 로직

**목적**: 브랜드별 Week-over-Week 변화율이 정확히 계산되는지 확인

| 브랜드 | 어제 매출 | 지난주 매출 | 예상 WoW | 상태 |
|--------|----------|-----------|---------|------|
| 미닉스 | ₩12,430,000 | ₩8,250,000 | +50.7% | -- 실행 대기 |
| 톰 | ₩11,260,000 | ₩5,570,000 | +102.2% | -- 실행 대기 |
| 프로티원 | ₩6,230,000 | ₩5,770,000 | +8.0% | -- 실행 대기 |

### TC-3: 이상 탐지 (브랜드별 임계값)

**목적**: 브랜드별 차별화된 임계값이 정상 작동하는지 확인

| 시나리오 | 브랜드 | 조건 | 예상 결과 | 상태 |
|---------|--------|------|----------|------|
| 매출 급락 (일반) | 미닉스 | WoW -25% | Critical 알림 | -- 실행 대기 |
| 매출 급락 (톰 완화) | 톰 | WoW -25% | 알림 없음 (임계값 -30%) | -- 실행 대기 |
| 주문 감소 | 프로티원 | WoW -18% | Warning 알림 | -- 실행 대기 |

### TC-4: n8n 워크플로우 실행

**목적**: 8노드 전체 파이프라인이 정상 작동하는지 확인

**실행 단계**:
1. Schedule Trigger (수동 실행)
2. HTTP Request 4개 (Supabase RPC, 병렬 실행)
3. Merge: Collect All Data (Append, 4 inputs)
4. Code Node: WoW Analysis & Anomaly Detection (transform.js)
5. Code Node: Slack Send KPI Alert (slack_send.js)

**결과**: -- Supabase 테이블/RPC 생성 후 실행 대기

### TC-5: Slack 메시지 포맷

**목적**: 앳홈 맞춤 Slack 메시지가 올바르게 포맷되는지 확인

**확인 항목**:
- [ ] 리포트 제목: "앳홈 Daily KPI 리포트"
- [ ] 브랜드별 이모지 (미닉스: 🏠, 톰: 💆, 프로티원: 💪)
- [ ] 브랜드별 매출/주문/ROAS 표시
- [ ] 채널 비중 요약 (상위 2개 채널)
- [ ] 매출 Top 5 제품 (브랜드 태그 포함)
- [ ] 경쟁사 모니터링 (순위/가격 변동)
- [ ] 숫자 천 단위 구분 (₩12,430,000)

---

## 에러 시나리오 테스트

### TC-6: 데이터 없음 처리

**시나리오**: 어제 날짜에 주문 데이터 없음

**예상 동작**:
- Slack 메시지: "어제 날짜에 대한 데이터가 없습니다"
- 에러 아님 (정상 처리)

**결과**: -- 실행 대기

### TC-7: 경쟁사 데이터 없음

**시나리오**: market_competitors 테이블에 어제 데이터 없음

**예상 동작**:
- 경쟁사 모니터링 섹션 생략
- 나머지 리포트 정상 표시

**결과**: -- 실행 대기

---

## 실행 전 체크리스트

1. [ ] Supabase SQL Editor에서 `schema/products.sql` 실행
2. [ ] Supabase SQL Editor에서 `schema/brand_daily_sales.sql` 실행
3. [ ] Supabase SQL Editor에서 `schema/market_competitors.sql` 실행
4. [ ] RPC 함수 4개 호출 테스트
5. [ ] n8n workflow.json import
6. [ ] transform.js / slack_send.js Code Node에 붙여넣기
7. [ ] Slack Webhook URL 설정
8. [ ] Execute Workflow 수동 실행

---

**업데이트 날짜**: 2026-02-13 (v2 앳홈 전환)
