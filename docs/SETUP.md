# 설치 및 설정 가이드

## 📋 목차

1. [사전 요구사항](#사전-요구사항)
2. [Supabase 설정](#supabase-설정)
3. [n8n 설치 (Docker Compose)](#n8n-설치-docker-compose)
4. [Slack 연동](#slack-연동)
5. [워크플로우 설정](#워크플로우-설정)
6. [테스트 실행](#테스트-실행)

---

## 🔧 사전 요구사항

### 필수 도구

- **Docker & Docker Compose**: n8n 컨테이너 실행
- **Supabase 프로젝트**: PostgreSQL 데이터베이스 + REST API
- **Slack Workspace**: Incoming Webhook으로 알림 수신

### 권장 환경

- **OS**: macOS, Linux, Windows (WSL)
- **메모리**: 최소 4GB RAM
- **디스크**: 최소 2GB 여유 공간

---

## 🗄️ Supabase 설정

### 1. Supabase 프로젝트 생성

1. https://supabase.com 접속하여 새 프로젝트 생성
2. **Project URL** 복사 (예: `https://xxxxx.supabase.co`)
3. **anon key** 복사 (Settings → API → anon public)

### 2. 테이블 생성

Supabase SQL Editor에서 데이터 테이블을 생성합니다.

실제 사용 테이블:
- `daily_sales`: 일별 매출/주문/방문자 집계
- `product_sales`: 제품별 매출 데이터
- `products`: 제품 마스터

참고: `schema/daily_summary.sql`은 성능 최적화용 선택 스키마입니다.

### 3. RPC 함수 생성

Supabase SQL Editor에서 3개의 RPC 함수를 생성합니다:

```sql
-- 어제 KPI 조회 (queries/kpis_yesterday.sql 기반)
CREATE OR REPLACE FUNCTION get_kpis_yesterday()
RETURNS TABLE(...) AS $$ ... $$;

-- 전주 동일 요일 KPI (queries/kpis_last_week.sql 기반)
CREATE OR REPLACE FUNCTION get_kpis_last_week()
RETURNS TABLE(...) AS $$ ... $$;

-- 매출 상위 제품 (queries/top_products.sql 기반)
CREATE OR REPLACE FUNCTION get_top_products()
RETURNS TABLE(...) AS $$ ... $$;
```

SQL 원본은 `queries/` 폴더를 참조하세요.

---

## 🤖 n8n 설치 (Docker Compose)

### 1. 환경변수 설정

```bash
cp .env.example .env
# .env 파일을 열어서 Supabase, Slack 정보 입력
```

### 2. Docker Compose 실행

```bash
docker-compose up -d
```

### 3. n8n 접속

브라우저에서 `http://localhost:5678` 접속 (포트는 `.env`의 `N8N_PORT`에 따라 변경 가능)

첫 접속 시 이메일/비밀번호로 계정 생성

### Docker Compose 구성

`docker-compose.yml` 주요 설정:
- **포트**: `${N8N_PORT:-5678}:5678`
- **타임존**: `Asia/Seoul`
- **DNS**: Google DNS (8.8.8.8) — 외부 API 호출 안정성
- **IPv6**: 활성화 — Supabase 연결 지원
- **볼륨**: `n8n_data` — 워크플로우/실행 기록 영속화

---

## 💬 Slack 연동

### 1. Incoming Webhook 생성

1. **Slack App 생성**
   - https://api.slack.com/apps 접속
   - "Create New App" → "From scratch"
   - App Name: `KPI Reporter`, Workspace 선택

2. **Incoming Webhooks 활성화**
   - Features → Incoming Webhooks → Activate
   - "Add New Webhook to Workspace"
   - 채널 선택 (예: `#business-kpis`)
   - Webhook URL 복사 (예: `https://hooks.slack.com/services/T00/B00/XXX`)

### 2. 테스트 메시지 전송

```bash
curl -X POST https://hooks.slack.com/services/YOUR/WEBHOOK/URL \
  -H 'Content-Type: application/json' \
  -d '{"text": "🎉 n8n 연동 테스트 성공!"}'
```

---

## ⚙️ 워크플로우 설정

### 1. 워크플로우 Import

1. n8n UI에서 "Workflows" → "Import from File"
2. `n8n/workflow.json` 파일 선택

### 2. Code Node 설정

워크플로우에는 2개의 Code 노드가 있습니다:

1. **"WoW Analysis & Anomaly Detection"** 노드
   - `n8n/transform.js` 내용을 Code 에디터에 붙여넣기
   - 역할: WoW 변화율 계산, 이상 탐지, Slack 메시지 포맷팅

2. **"Slack: Send KPI Alert"** 노드
   - `n8n/slack_send.js` 내용을 Code 에디터에 붙여넣기
   - `SLACK_WEBHOOK_URL`을 실제 Webhook URL로 교체
   - 역할: `this.helpers.httpRequest()`로 Slack Webhook 전송

### 3. 워크플로우 구조 (7개 노드)

```
Schedule: Daily 08:00
  ├─► Supabase: Yesterday KPIs      (HTTP Request → RPC)
  ├─► Supabase: Last Week KPIs      (HTTP Request → RPC)
  └─► Supabase: Top Products        (HTTP Request → RPC)
          │              │              │
          └──────┬───────┴──────────────┘
                 ▼
        Merge: Collect All Data      (Append, 3 inputs)
                 ▼
        WoW Analysis & Anomaly       (Code Node → transform.js)
                 ▼
        Slack: Send KPI Alert        (Code Node → slack_send.js)
```

### 4. 수동 실행 테스트

1. **"Execute Workflow"** 버튼 클릭
2. 각 노드 결과 확인:
   - HTTP Request 노드 3개: Supabase RPC 응답 데이터
   - Merge 노드: 3개 데이터 소스 합치기
   - WoW Analysis 노드: 포맷된 Slack 메시지
   - Slack Send 노드: 전송 성공 여부
3. Slack 채널에서 메시지 확인

### 5. Cron 스케줄 설정

1. Schedule Trigger 노드 클릭
2. 매일 08:00 실행 설정
3. **Activate** 토글 활성화

---

## 🧪 테스트 실행

### 1. Supabase RPC 함수 테스트

Supabase SQL Editor에서 직접 실행:

```sql
SELECT * FROM get_kpis_yesterday();
SELECT * FROM get_kpis_last_week();
SELECT * FROM get_top_products();
```

### 2. End-to-End 테스트

1. **워크플로우 수동 실행**: "Execute Workflow" 클릭
2. **Slack 메시지 확인**: 채널에 리포트 도착 확인
3. **실행 시간 확인**: Executions → 실행 시간 < 2분 확인

---

## 🛠️ 문제 해결

### Supabase RPC 호출 실패

1. **API Key 확인**: workflow.json의 `apikey` 헤더가 올바른지 확인
2. **RPC 함수 존재 여부**: Supabase SQL Editor에서 함수 직접 호출 테스트
3. **네트워크**: Docker 컨테이너에서 외부 접근 가능한지 확인

### n8n 워크플로우 실행 안됨

1. **Docker 상태**: `docker-compose ps` 로 컨테이너 상태 확인
2. **로그 확인**: `docker-compose logs n8n` 또는 n8n UI → Executions → Error Details
3. **재시작**: `docker-compose restart n8n`

### Slack 메시지 전송 실패

1. **Webhook URL 확인**: `slack_send.js`의 URL이 올바른지 확인
2. **curl 테스트**: Webhook URL로 직접 테스트 메시지 전송
3. **Code Node 에러**: n8n UI에서 Slack Send 노드의 에러 메시지 확인

### n8n Code Node 제한사항

- `process.env` 사용 불가 (sandboxed 환경)
- `$env` 접근 제한적 (설정에 따라 차단될 수 있음)
- `$('Node Name').all()` Merge 노드 통과 시 동작 안함 → `$input.all()` 사용

---

## 📚 다음 단계

- [SQL 쿼리 상세 설명](SQL_GUIDE.md)
- [Slack 메시지 커스터마이징](SLACK_INTEGRATION.md)
- [테스트 결과](../tests/TEST_RESULTS.md)

---

**문제 발생 시**: GitHub Issues에 문의하거나 문서를 참조하세요.
