# PDCA Plan: E-commerce KPI Daily Auto-Report System

**Feature**: ecommerce-kpi-reporter
**Version**: 1.0
**Created**: 2026-02-13
**Owner**: 택
**PDCA Phase**: Plan

---

## 1. 프로젝트 개요

### 1.1 목적

E-commerce 비즈니스 KPI를 매일 아침 08:00에 Slack으로 자동 전송하는 경량 보고 시스템.
기존 쿠팡 E-commerce Dashboard(정적 분석)를 자동화된 모니터링으로 발전시키는 프로젝트.

### 1.2 핵심 가치

| 구분 | AS-IS (정적 분석) | TO-BE (자동 리포트) |
|------|-----------------|-------------------|
| 방식 | 수동 대시보드 확인 | 자동 Slack 전송 |
| 빈도 | 필요 시 수동 | 매일 08:00 |
| 알림 | 없음 | 이상 탐지 자동 경고 |
| 접근성 | Tableau 접속 필요 | Slack에서 즉시 확인 |

### 1.3 포트폴리오 차별점

| 항목 | Marketing ROI 프로젝트 | Finance Close Pack | **본 프로젝트** |
|------|----------------------|-------------------|-----------------|
| 도메인 | 외부 광고 플랫폼 | 월간 재무 KPI | **내부 커머스 KPI** |
| 빈도 | 일일 | 월간 | **일일** |
| 도구 | Google Apps Script | Airflow | **n8n (경량)** |
| 데이터 | 광고 API | MySQL | **PostgreSQL** |

---

## 2. 기술 아키텍처

### 2.1 시스템 구성

```
┌─────────────────────────────────────────────────────────┐
│                    n8n Workflow                           │
│                                                          │
│  ┌──────────┐   ┌──────────────┐   ┌────────┐   ┌─────┐│
│  │  Cron    │──▶│ PostgreSQL   │──▶│  JS    │──▶│Slack││
│  │ 08:00   │   │ (3 queries)  │   │Transform│  │ Send ││
│  └──────────┘   └──────────────┘   └────────┘   └─────┘│
└─────────────────────────────────────────────────────────┘
         │                                         │
         ▼                                         ▼
┌──────────────────┐                       ┌─────────────┐
│   PostgreSQL     │                       │    Slack     │
│   (Supabase)     │                       │ #business-   │
│  • orders        │                       │  kpis        │
│  • daily_summary │                       └─────────────┘
└──────────────────┘
```

### 2.2 기술 스택

| 계층 | 기술 | 용도 |
|------|------|------|
| Database | PostgreSQL (Supabase) | KPI 원천 데이터 |
| Workflow | n8n | 스케줄링, 오케스트레이션 |
| Transform | JavaScript (n8n Function Node) | WoW 계산, 이상 탐지, 포맷팅 |
| Messaging | Slack API (Incoming Webhooks) | 리포트 전송 |
| Query | SQL (CTE, Window Functions) | 데이터 집계 |

### 2.3 데이터 플로우

```
1. Cron Trigger (08:00 KST)
   │
2. PostgreSQL Query (3개 병렬 실행)
   ├─ kpis_yesterday.sql   → 어제 KPI
   ├─ kpis_last_week.sql   → 지난주 동일 요일 KPI
   └─ top_products.sql     → 매출 상위 3개 제품
   │
3. JavaScript Transform (transform.js)
   ├─ WoW 변화율 계산
   ├─ 이상 탐지 (임계값 기반)
   └─ Slack 메시지 포맷팅
   │
4. Slack Send Message
   └─ #business-kpis 채널로 전송
```

---

## 3. 기능 명세

### 3.1 핵심 KPI 메트릭 (5개)

| # | 메트릭 | 계산 방법 | 단위 |
|---|--------|----------|------|
| 1 | 총 매출 | SUM(order_amount) | ₩ |
| 2 | 총 주문 수 | COUNT(DISTINCT order_id) | 건 |
| 3 | 평균 주문 금액 (AOV) | revenue / orders | ₩ |
| 4 | 전환율 | orders / visitors * 100 | % |
| 5 | WoW 변화율 | ((current - prev) / prev) * 100 | % |

### 3.2 이상 탐지 규칙

| 조건 | 임계값 | 심각도 | 아이콘 |
|------|--------|--------|--------|
| 매출 WoW 감소 | > 20% | Critical | 🚨 |
| 주문 수 WoW 감소 | > 15% | Warning | ⚠️ |
| 전환율 WoW 감소 | > 10%p | Warning | ⚠️ |

### 3.3 상위 제품 분석

- 매출 기준 Top 3 제품 순위
- RANK() Window Function 사용
- 제품명, 매출액, 판매수량, 매출비중(%) 표시

### 3.4 Slack 메시지 포맷

```
📊 일일 E-commerce KPI 리포트 | 2026-02-13

핵심 지표 (어제 기준)
━━━━━━━━━━━━━━━━━━━━━
💰 매출: ₩18,750,000 (+25.0% ↑)
📦 주문 수: 520건 (+15.6% ↑)
🛒 평균 주문 금액: ₩36,058 (+8.2% ↑)
📈 전환율: 3.85% (+0.1%p ↑)

🏆 매출 상위 3개 제품
1. 무선 이어폰 Pro: ₩4,500,000 (150개 판매)
2. 스마트워치 Ultra: ₩3,200,000 (80개 판매)
3. 블루투스 스피커: ₩2,100,000 (210개 판매)

📊 대시보드 바로가기 | ⏰ 리포트 생성: 08:00:15
```

---

## 4. 파일 구조 및 현황

### 4.1 프로젝트 구조

```
KPI_Auto_Report(Athome)/
├── CLAUDE.md                    # Claude Code 프로젝트 컨텍스트
├── KPI_Auto_Report_PRD.md       # PRD (상세 기획서)
├── README.md                    # 프로젝트 소개
├── schema/
│   └── daily_summary.sql        # DDL + 샘플 데이터 + 트리거
├── queries/
│   ├── kpis_yesterday.sql       # 어제 KPI 조회
│   ├── kpis_last_week.sql       # 지난주 동일 요일 KPI
│   └── top_products.sql         # 매출 Top 3 제품
├── n8n/
│   ├── workflow.json            # n8n 워크플로우 정의
│   └── transform.js             # 변환 로직 (WoW, 이상 탐지, 포맷팅)
├── docs/
│   ├── SETUP.md                 # 설치 가이드
│   ├── SQL_GUIDE.md             # SQL 쿼리 상세 설명
│   ├── SLACK_INTEGRATION.md     # Slack 연동 가이드
│   └── pdca/                    # PDCA 문서
│       └── PLAN.md              # (이 문서)
└── tests/
    └── TEST_RESULTS.md          # 테스트 케이스 (미실행)
```

### 4.2 구현 현황

| 영역 | 파일 | 상태 | 비고 |
|------|------|------|------|
| DB 스키마 | schema/daily_summary.sql | ✅ 완료 | DDL, 인덱스, 트리거, 샘플 데이터 |
| SQL 쿼리 | queries/kpis_yesterday.sql | ✅ 완료 | CTE 기반, NULLIF 패턴 |
| SQL 쿼리 | queries/kpis_last_week.sql | ✅ 완료 | 8일 전 동일 요일 조회 |
| SQL 쿼리 | queries/top_products.sql | ✅ 완료 | RANK() Window Function |
| n8n 워크플로우 | n8n/workflow.json | ⚠️ 부분 | 쿼리가 실제 SQL 파일과 불일치 |
| 변환 로직 | n8n/transform.js | ✅ 완료 | WoW 계산, 이상 탐지, Slack 포맷 |
| 문서 | docs/*.md | ✅ 완료 | 설치, SQL, Slack 가이드 |
| 테스트 | tests/TEST_RESULTS.md | ❌ 미실행 | 모든 TC가 ⏳ 대기 상태 |

---

## 5. 식별된 Gap 및 개선 필요 사항

### 5.1 Critical (반드시 해결)

| # | 항목 | 상세 | 파일 |
|---|------|------|------|
| G-1 | workflow.json 쿼리 불일치 | PostgreSQL 노드의 query 필드가 실제 SQL 파일 내용과 다름. 단순 placeholder만 있음 | n8n/workflow.json:24,37,51 |
| G-2 | 전환율/방문자 Placeholder | kpis_yesterday.sql, kpis_last_week.sql 모두 `total_visitors=0`, `conversion_rate=0.00`으로 하드코딩 | queries/kpis_yesterday.sql:44-45 |
| G-3 | 테스트 미실행 | TEST_RESULTS.md의 모든 테스트 케이스(8개)가 ⏳ 대기 상태 | tests/TEST_RESULTS.md |

### 5.2 Major (해결 권장)

| # | 항목 | 상세 | 파일 |
|---|------|------|------|
| G-4 | transform.js Null 미처리 | 입력 데이터가 null/empty일 때 에러 발생 가능. `$input.all()[0]`이 undefined일 수 있음 | n8n/transform.js:14-16 |
| G-5 | topProducts 입력 구조 불일치 | transform.js는 `topProducts`를 배열로 기대하지만, n8n 노드에서 각 행이 개별 item으로 전달됨 | n8n/transform.js:16,71 |
| G-6 | 환경변수 설정 부재 | DB 자격증명, Slack Webhook URL 등의 .env 파일이 없음 | - |

### 5.3 Minor (선택적)

| # | 항목 | 상세 |
|---|------|------|
| G-7 | 에러 핸들링 없음 | Slack 전송 실패 시 재시도/알림 로직 없음 |
| G-8 | 고급 제품 순위 비교 | top_products.sql의 지난주 순위 비교 쿼리가 주석 처리 |
| G-9 | GitHub 저장소 미생성 | 코드가 로컬에만 존재 |

---

## 6. 실행 계획

### Phase 1: Gap 해결 (우선순위 높음)

| 순서 | 작업 | 관련 Gap | 예상 작업량 |
|------|------|---------|-----------|
| 1-1 | workflow.json에 실제 SQL 쿼리 반영 | G-1 | 소 |
| 1-2 | 전환율 계산 방안 결정 (visitors 테이블 or 고정값) | G-2 | 중 |
| 1-3 | transform.js에 null/empty 방어 코드 추가 | G-4 | 소 |
| 1-4 | topProducts 입력 구조 정합성 확보 | G-5 | 소 |
| 1-5 | .env.example 파일 생성 | G-6 | 소 |

### Phase 2: 테스트 실행

| 순서 | 작업 | 관련 Gap |
|------|------|---------|
| 2-1 | SQL 쿼리 개별 실행 검증 (TC-1) | G-3 |
| 2-2 | WoW 계산 로직 검증 (TC-2) | G-3 |
| 2-3 | 이상 탐지 로직 검증 (TC-3) | G-3 |
| 2-4 | End-to-End 워크플로우 테스트 (TC-4~5) | G-3 |
| 2-5 | 에러 시나리오 테스트 (TC-6~7) | G-3 |

### Phase 3: 마무리

| 순서 | 작업 |
|------|------|
| 3-1 | TEST_RESULTS.md 실제 결과로 업데이트 |
| 3-2 | GitHub 저장소 생성 및 Push |
| 3-3 | 포트폴리오 연동 (Notion 등) |

---

## 7. 비기능 요구사항

| 항목 | 목표 | 비고 |
|------|------|------|
| SQL 쿼리 실행 시간 | < 5초 | 인덱스 필수 |
| 전체 파이프라인 시간 | < 2분 | Cron → Slack |
| Slack API 응답 | < 1초 | 단일 메시지 |
| n8n 에러 재시도 | 3회 | 지수 백오프 |
| 데이터 기준 | T-1 (어제) | 실시간 아님 |

---

## 8. 위험 요소

| 위험 | 확률 | 영향 | 완화 방안 |
|------|------|------|----------|
| PostgreSQL 쿼리 타임아웃 | 중 | 높음 | 쿼리 타임아웃 10초, 인덱스 |
| Slack rate limit | 낮음 | 중 | 일 1회 전송으로 안전 |
| n8n 서버 다운타임 | 낮음 | 높음 | 클라우드 배포 (Railway/Render) |
| 방문자 데이터 부재 | 높음 | 중 | 전환율 제외 or 추정값 사용 |

---

## 9. 성공 기준

- [ ] n8n 워크플로우 수동 실행 성공
- [ ] Slack 메시지에 5개 KPI 모두 표시
- [ ] WoW 변화율 정확 계산 (수동 검증 일치)
- [ ] 이상 탐지 3개 시나리오 통과
- [ ] SQL 쿼리에 Window Functions (LAG, RANK) 활용
- [ ] GitHub 저장소 생성 + README 포함
- [ ] 8개 테스트 케이스 중 6개 이상 통과

---

## 10. PDCA 다음 단계

| 현재 | 다음 | 액션 |
|------|------|------|
| **Plan** (이 문서) | Design | 식별된 Gap(G-1~G-6) 해결 방안 상세 설계 |
| - | Do | Gap 해결 구현 + 테스트 실행 |
| - | Check | Gap Analysis (목표: 90% 이상 일치율) |
| - | Act | 보완 및 최종 보고서 |
