# PRD: 앳홈 KPI Daily Auto-Report System v2

**Project Code**: `athome-kpi-reporter`
**Version**: 2.0
**Last Updated**: 2026-02-13
**Owner**: 택
**Status**: In Progress (v2 도메인 전환)

---

## Executive Summary

### What We're Building
앳홈(미닉스/톰/프로티원) 3개 브랜드의 일일 KPI를 자동으로 수집, 분석하여 Slack으로 전송하는 자동화 시스템. 브랜드별/채널별 매출 분석, 경쟁사 모니터링, 이상 탐지를 포함합니다.

### Why It Matters
**비즈니스 문제**: 앳홈 AX팀에서 3개 브랜드 x 5개 채널의 KPI를 매일 수동으로 확인하며, 경쟁사 동향을 별도로 모니터링해야 함

**솔루션**: 브랜드별 일일 KPI 자동 리포트 + 경쟁사 순위/가격 변동 알림 + 이상 탐지 -- 매일 08:00 Slack 자동 전송

### v1 -> v2 변경점
| 항목 | v1 (Generic E-commerce) | v2 (앳홈 맞춤) |
|------|----------------------|---------------|
| **도메인** | 일반 이커머스 | 앳홈 3브랜드 x 5채널 |
| **테이블** | daily_sales, products | brand_daily_sales, products, market_competitors |
| **RPC 함수** | 3개 | 4개 (+경쟁사 변동) |
| **분석** | 전체 합산 WoW | 브랜드별 WoW + 채널 비중 |
| **알림** | 일반 임계값 | 브랜드별 차등 임계값 |
| **경쟁사** | 없음 | 쿠팡/네이버 순위/가격 모니터링 |
| **n8n 노드** | 7개 | 8개 (+Competitor Changes) |

### JD 키워드 매칭 (앳홈 AX팀 데이터분석가)
| JD 키워드 | 프로젝트 역량 증명 |
|-----------|------------------|
| **크롤링/스크래핑** | market_competitors 테이블 (크롤링 데이터 저장/분석) |
| **SQL** | Window Functions, CTEs, JSONB, 복합 인덱스 |
| **Python** | n8n Code Node (JavaScript, 동일 로직) |
| **Tableau** | 데이터 파이프라인 (Tableau 대시보드 연동 가능) |
| **n8n 자동화** | 8노드 워크플로우, 병렬 실행 |
| **데이터 정합성** | UNIQUE 제약조건, COALESCE, NULL 처리 |

---

## 앳홈 브랜드 구성

### 미닉스 (minix) - 소형가전
| 제품 | SKU | 가격 |
|------|-----|------|
| 미닉스 더플렌더 | MNX-BLD-001 | 89,000 |
| 미닉스 미니건조기 | MNX-DRY-001 | 349,000 |
| 미닉스 식기세척기 | MNX-DSH-001 | 459,000 |
| 미닉스 에어프라이어 | MNX-AFR-001 | 129,000 |
| 미닉스 음식물처리기 | MNX-FDP-001 | 690,000 |

### 톰 (thome) - 뷰티디바이스
| 제품 | SKU | 가격 |
|------|-----|------|
| 톰 더글로우 프로 | THM-GLP-001 | 298,000 |
| 톰 더글로우 | THM-GLW-001 | 198,000 |
| 톰 LED 마스크 | THM-LED-001 | 178,000 |
| 톰 클렌저 | THM-CLN-001 | 89,000 |

### 프로티원 (protione) - 건강기능식품
| 제품 | SKU | 가격 |
|------|-----|------|
| 프로티원 바 초코 | PRT-BAR-001 | 32,000 |
| 프로티원 바 피넛버터 | PRT-BAR-002 | 32,000 |
| 프로티원 쉐이크 바닐라 | PRT-SHK-001 | 45,000 |
| 프로티원 쉐이크 초코 | PRT-SHK-002 | 45,000 |
| 프로티원 비타민 멀티 | PRT-VIT-001 | 28,000 |

### 판매 채널
| 채널 | 코드 | 특징 |
|------|------|------|
| 자사몰 | own_mall | 높은 마진, ROAS 최고 |
| 쿠팡 | coupang | 최대 트래픽, 가격 경쟁 |
| 네이버 | naver | 검색 트래픽, 리뷰 중요 |
| GS홈쇼핑 | gs_home | 톰 핵심 채널, 방송일 매출 변동 큼 |
| 올리브영 | oliveyoung | 프로티원 핵심 채널, 오프라인 연계 |

---

## 경쟁사 모니터링

### 소형가전 카테고리
| 경쟁사 | 주요 제품 | 비교 대상 |
|--------|---------|----------|
| 스마트카라 | PCS-400 (음식물처리기) | 미닉스 음식물처리기 |
| 린클 | 루펜 SLW-03 (음식물처리기) | 미닉스 음식물처리기 |

### 뷰티디바이스 카테고리
| 경쟁사 | 주요 제품 | 비교 대상 |
|--------|---------|----------|
| LG | 프라엘 더마 LED 마스크 | 톰 더글로우 프로 |
| 페이스팩토리 | LED 마스크 | 톰 LED 마스크 |

---

## 시스템 아키텍처

```
┌──────────────────────────────────────────────────────────────────────────┐
│                     n8n Workflow (8 Nodes)                                │
│                                                                          │
│  ┌──────────┐   ┌───────────────────┐                                   │
│  │ Schedule │──▶│ HTTP: Yesterday   │──┐                                 │
│  │ Trigger  │   │ Brand KPIs        │  │                                 │
│  │ 08:00    │──▶│ HTTP: Last Week   │──┤  ┌──────────┐  ┌────────────┐ │
│  │          │   │ Brand KPIs        │  ├─▶│  Merge   │─▶│ WoW        │ │
│  │          │──▶│ HTTP: Top         │──┤  │ (4 input)│  │ Analysis   │ │
│  │          │   │ Products          │  │  └──────────┘  └─────┬──────┘ │
│  │          │──▶│ HTTP: Competitor  │──┘                       │        │
│  │          │   │ Changes           │                          ▼        │
│  └──────────┘   └───────────────────┘                  ┌────────────┐  │
│                                                         │ Slack Send │  │
│                                                         └────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
         │                                                  │
         ▼                                                  ▼
┌──────────────────────┐                          ┌──────────────┐
│   Supabase REST API  │                          │    Slack     │
│                      │                          │  #athome-kpis│
│  • brand_daily_sales │                          └──────────────┘
│  • products          │
│  • product_daily_sales│
│  • market_competitors│
└──────────────────────┘
```

---

## 이상 탐지 기준

| 브랜드 | 매출 Critical | 주문 Warning | 비고 |
|--------|-------------|-------------|------|
| 미닉스 | WoW -20% | WoW -15% | 기본 임계값 |
| 톰 | WoW -30% | WoW -25% | GS홈쇼핑 방송일 변동 감안 (완화) |
| 프로티원 | WoW -20% | WoW -15% | 기본 임계값 |

---

## Technical Requirements

### 테이블 구조
- `brand_daily_sales`: 브랜드(3) x 채널(5) 일일 매출 (복합 인덱스: sale_date + brand)
- `products`: 제품 마스터 14개 (앳홈 실제 제품명)
- `product_daily_sales`: 제품별 일일 매출 + 평점/리뷰
- `market_competitors`: 경쟁사 크롤링 데이터 (순위/가격/리뷰)

### RPC 함수 (Supabase)
1. `get_brand_kpis_yesterday()`: 브랜드별 어제 KPI + 채널 breakdown (JSONB)
2. `get_brand_kpis_last_week()`: 브랜드별 지난주 동요일 KPI
3. `get_top_products()`: 매출 상위 5개 제품 (RANK + revenue_share)
4. `get_competitor_changes()`: 경쟁사 순위/가격 변동

### SQL 기법
- Window Functions: RANK(), SUM() OVER (PARTITION BY), LAG()
- CTE (WITH): 복잡한 쿼리 모듈화
- JSONB: 채널별 매출 breakdown
- Self-JOIN: 전주 대비 경쟁사 변동 비교
- COALESCE/NULLIF: NULL 안전 처리

---

## Definition of Done

- [x] PRD 작성
- [x] 앳홈 도메인 스키마 (3개 테이블) 작성
- [x] SQL 쿼리 5개 작성 (브랜드별, 채널별, 경쟁사)
- [x] RPC 함수 4개 작성
- [x] n8n 워크플로우 8노드 구성
- [x] transform.js 브랜드별 분석 로직
- [x] 경쟁사 모니터링 로직
- [x] Supabase 테이블/RPC 실제 생성 (4 tables + 4 RPC functions)
- [x] n8n 워크플로우 E2E 테스트 (8노드, 2.491s, Success)
- [x] Slack 메시지 정상 수신 확인 (status: "sent", 619ms)
- [x] GitHub push (d687e07)

---

**Version**: 2.0 (앳홈 도메인 전환)
