# 테스트 결과

## 테스트 개요

**테스트 날짜**: 2026-02-13 (v2 앳홈 도메인 전환)
**테스트 환경**: 로컬 Docker (n8n 2.x, port 5679) + Supabase (PostgreSQL, ap-northeast-2)
**테스트 범위**: Supabase RPC, n8n 워크플로우 E2E, Slack 연동
**전체 실행 시간**: 2.491s (Success)

**v2 변경사항**: Generic E-commerce -> 앳홈(미닉스/톰/프로티원) 도메인 전환

---

## 테스트 케이스

### TC-1: Supabase RPC 함수 정확성 -- PASS

**목적**: 각 RPC 함수가 올바른 결과를 반환하는지 확인

| RPC 함수 | 예상 결과 | 실제 결과 | 상태 |
|----------|---------|----------|------|
| get_brand_kpis_yesterday() | 브랜드별 어제 KPI (3행) | 3행 (minix, thome, protione) + channel_breakdown JSONB | PASS |
| get_brand_kpis_last_week() | 브랜드별 지난주 KPI (3행) | 3행 (minix, protione, thome) + channel_breakdown JSONB | PASS |
| get_top_products() | 매출 상위 5개 제품 | 5행 (톰 더글로우 프로 #1, 미닉스 식기세척기 #2, ...) | PASS |
| get_competitor_changes() | 경쟁사 순위/가격 변동 | 13행 (ranking_change, price_change 포함) | PASS |

**참고**: get_brand_kpis_yesterday/last_week에서 Window Function + jsonb_agg 중첩 오류 발견 후 수정 완료 (subquery 패턴 적용)

### TC-2: 브랜드별 WoW 계산 로직 -- PASS

**목적**: 브랜드별 Week-over-Week 변화율이 정확히 계산되는지 확인

| 브랜드 | 어제 매출 | 지난주 매출 | 예상 WoW | 실제 WoW | 상태 |
|--------|----------|-----------|---------|---------|------|
| 미닉스 | ₩12,430,000 | ₩8,250,000 | +50.7% | +50.7% ↑ | PASS |
| 톰 | ₩11,260,000 | ₩5,570,000 | +102.2% | +102.2% ↑ | PASS |
| 프로티원 | ₩6,230,000 | ₩5,770,000 | +8.0% | +8.0% ↑ | PASS |
| **전체** | **₩29,920,000** | **₩19,590,000** | **+52.7%** | **+52.7% ↑** | **PASS** |

### TC-3: 이상 탐지 (브랜드별 임계값) -- PASS

**목적**: 브랜드별 차별화된 임계값이 정상 작동하는지 확인

| 시나리오 | 브랜드 | WoW 변화 | 임계값 | 예상 결과 | 실제 결과 | 상태 |
|---------|--------|---------|--------|----------|----------|------|
| 매출 증가 | 미닉스 | +50.7% | -20% Critical | 알림 없음 | alerts_count: 0 | PASS |
| 매출 대폭 증가 | 톰 | +102.2% | -30% Critical (완화) | 알림 없음 | alerts_count: 0 | PASS |
| 매출 소폭 증가 | 프로티원 | +8.0% | -20% Critical | 알림 없음 | alerts_count: 0 | PASS |

**참고**: 현재 샘플 데이터는 모든 브랜드가 WoW 증가 상태이므로 이상 탐지 알림 0건 (정상)

### TC-4: n8n 워크플로우 E2E 실행 -- PASS

**목적**: 8노드 전체 파이프라인이 정상 작동하는지 확인

**실행 방법**: Playwright 브라우저 자동화로 n8n UI에서 "Execute workflow" 클릭

| 노드 | 입력 | 출력 | 상태 |
|------|------|------|------|
| Schedule: Daily 08:00 | (trigger) | 1 item | PASS |
| Supabase: Yesterday Brand KPIs | POST RPC | 3 items | PASS |
| Supabase: Last Week Brand KPIs | POST RPC | 3 items | PASS |
| Supabase: Top Products | POST RPC | 5 items | PASS |
| Supabase: Competitor Changes | POST RPC | 13 items | PASS |
| Merge: Collect All Data | 4 inputs (append) | 24 items | PASS |
| WoW Analysis & Anomaly Detection | 24 items | 1 item | PASS |
| Slack: Send KPI Alert | 1 item | 1 item (sent) | PASS |

**전체 실행 시간**: 2.491s (Slack 전송: 619ms)

### TC-5: Slack 메시지 포맷 -- PASS

**목적**: 앳홈 맞춤 Slack 메시지가 올바르게 포맷되는지 확인

**확인 항목**:
- [x] 리포트 제목: "앳홈 Daily KPI 리포트"
- [x] 브랜드별 이모지 (미닉스: 🏠, 톰: 💆, 프로티원: 💪)
- [x] 브랜드별 매출/주문/ROAS 표시
- [x] 채널 비중 요약 (상위 2개 채널)
- [x] 매출 Top 5 제품 (브랜드 태그 포함)
- [x] 경쟁사 모니터링 (가격 변동: 린클 루펜 SLW-03 ₩10,000 인하)
- [x] 숫자 천 단위 구분 (₩12,430,000)

**실제 Slack 메시지 출력**:
```
📊 *앳홈 Daily KPI 리포트* | 2026-02-13

*전체 실적 (어제 기준)*
━━━━━━━━━━━━━━━━━━━━━
💰 *총 매출*: ₩29,920,000 (+52.7% ↑)
📦 *총 주문*: 434건 (+17.0% ↑)

*브랜드별 실적*
━━━━━━━━━━━━━━━━━━━━━
🏠 *미닉스*
  매출: ₩12,430,000 (+50.7% ↑)
  주문: 131건 | ROAS: 9.5 (coupang 33.1%, gs_home 28.2%)

💆 *톰*
  매출: ₩11,260,000 (+102.2% ↑)
  주문: 103건 | ROAS: 10.8 (gs_home 46.2%, coupang 20.8%)

💪 *프로티원*
  매출: ₩6,230,000 (+8.0% ↑)
  주문: 200건 | ROAS: 5.8 (coupang 35%, oliveyoung 26.5%)

*🏆 매출 Top 5 제품*
1. *톰 더글로우 프로* [톰]: ₩5,960,000 ★4.8
2. *미닉스 식기세척기* [미닉스]: ₩4,590,000 ★4.6
3. *미닉스 미니건조기* [미닉스]: ₩3,490,000 ★4.8
4. *미닉스 더플렌더* [미닉스]: ₩2,670,000 ★4.7
5. *톰 더글로우* [톰]: ₩2,376,000 ★4.6

*🔍 경쟁사 모니터링*
💰 린클 루펜 SLW-03 [린클] ₩10,000 인하

⏰ 리포트 생성: 오전 6:23:29
```

**메타데이터 출력**:
```json
{
  "date": "2026-02-13",
  "total_revenue": 29920000,
  "total_orders": 434,
  "wow_revenue": 52.73,
  "wow_orders": 16.98,
  "alerts_count": 0,
  "competitor_alerts": 1,
  "has_anomaly": false,
  "has_data": true,
  "brands": ["minix", "thome", "protione"]
}
```

---

## 발견된 이슈 및 수정

### ISSUE-1: PostgreSQL Window Function + jsonb_agg 중첩 오류

**증상**: `aggregate function calls cannot contain window function calls`
**원인**: `jsonb_agg(jsonb_build_object('share_pct', SUM() OVER()))` - Window Function이 Aggregate 내부에 중첩
**수정**: subquery에서 Window Function 먼저 계산 후 외부에서 jsonb_agg() 적용
**영향**: get_brand_kpis_yesterday(), get_brand_kpis_last_week() 두 함수 모두 수정

### ISSUE-2: n8n CLI execute 제한

**증상**: `n8n execute --id=...` 실행 시 "Missing node to start execution"
**원인**: CLI execute는 Execute Workflow Trigger 노드가 있어야 작동, Schedule Trigger만으로는 불가
**우회**: Playwright 브라우저 자동화로 n8n UI에서 직접 실행

---

## 실행 전 체크리스트

1. [x] Supabase SQL Editor에서 `schema/products.sql` 실행
2. [x] Supabase SQL Editor에서 `schema/brand_daily_sales.sql` 실행
3. [x] Supabase SQL Editor에서 `schema/market_competitors.sql` 실행
4. [x] RPC 함수 4개 호출 테스트
5. [x] n8n workflow.json import (docker cp + n8n import:workflow)
6. [x] transform.js / slack_send.js 코드 워크플로우에 내장
7. [x] Slack Webhook URL 설정 (.env에서 로드)
8. [x] Execute Workflow 수동 실행 (Playwright)

---

## 테스트 결과 요약

| 테스트 | 결과 | 비고 |
|--------|------|------|
| TC-1: RPC 함수 정확성 | **PASS** | 4개 RPC 모두 정상 |
| TC-2: WoW 계산 로직 | **PASS** | 브랜드별/전체 WoW 정확 |
| TC-3: 이상 탐지 | **PASS** | 임계값 로직 정상 (현재 데이터에서 알림 0건) |
| TC-4: n8n E2E 실행 | **PASS** | 8노드 파이프라인 2.491s 완료 |
| TC-5: Slack 메시지 포맷 | **PASS** | 모든 포맷 항목 정상 |

**전체 결과**: 5/5 PASS

---

**업데이트 날짜**: 2026-02-13 15:26 KST (E2E 테스트 완료)
