# 설치 및 설정 가이드

## 📋 목차

1. [사전 요구사항](#사전-요구사항)
2. [PostgreSQL 설정](#postgresql-설정)
3. [n8n 설치](#n8n-설치)
4. [Slack 연동](#slack-연동)
5. [워크플로우 설정](#워크플로우-설정)
6. [테스트 실행](#테스트-실행)

---

## 🔧 사전 요구사항

### 필수 도구

- **PostgreSQL**: Supabase 또는 로컬 PostgreSQL (v14 이상 권장)
- **n8n**: 워크플로우 자동화 도구
- **Slack Workspace**: 알림 수신용
- **Node.js**: v18 이상 (n8n 실행 시 필요)

### 권장 환경

- **OS**: macOS, Linux, Windows (WSL)
- **메모리**: 최소 4GB RAM
- **디스크**: 최소 2GB 여유 공간

---

## 🗄️ PostgreSQL 설정

### Option 1: Supabase 사용 (권장)

1. **Supabase 프로젝트 생성**
   ```bash
   # https://supabase.com에 접속하여 새 프로젝트 생성
   # Connection String 복사 (예: postgresql://user:pass@db.supabase.co:5432/postgres)
   ```

2. **스키마 생성**
   ```bash
   psql "postgresql://user:pass@db.supabase.co:5432/postgres" \
     -f schema/daily_summary.sql
   ```

3. **기존 orders 테이블 확인**
   ```sql
   SELECT COUNT(*) FROM orders;
   -- 데이터가 있어야 함 (Phase 1에서 생성)
   ```

### Option 2: 로컬 PostgreSQL

1. **PostgreSQL 설치**
   ```bash
   # macOS
   brew install postgresql@14
   brew services start postgresql@14
   
   # Ubuntu
   sudo apt update
   sudo apt install postgresql postgresql-contrib
   sudo systemctl start postgresql
   ```

2. **데이터베이스 생성**
   ```bash
   createdb ecommerce_kpi
   psql ecommerce_kpi -f schema/daily_summary.sql
   ```

---

## 🤖 n8n 설치

### Option 1: Docker (권장)

```bash
# n8n 이미지 다운로드 및 실행
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  n8nio/n8n

# 브라우저에서 http://localhost:5678 접속
```

### Option 2: npm

```bash
# 전역 설치
npm install n8n -g

# 실행
n8n

# 브라우저에서 http://localhost:5678 접속
```

### n8n 초기 설정

1. **계정 생성**: 첫 접속 시 이메일/비밀번호 입력
2. **Credentials 설정**:
   - Settings → Credentials → Add Credential
   - PostgreSQL, Slack Webhook 추가

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

3. **n8n에 Webhook 등록**
   - n8n Credentials → Add Credential → Slack
   - Webhook URL 붙여넣기

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
3. Credentials 연결:
   - PostgreSQL Node → 본인의 DB Credentials 선택
   - Slack Node → 본인의 Webhook Credentials 선택

### 2. 수동 실행 테스트

1. **Test Workflow** 버튼 클릭
2. 각 노드 결과 확인:
   - PostgreSQL Node 1: 어제 KPI 데이터
   - PostgreSQL Node 2: 지난주 KPI 데이터
   - PostgreSQL Node 3: 상위 제품 데이터
   - Function Node: 변환된 메시지
   - Slack Node: 전송 성공 여부

3. Slack 채널에서 메시지 확인

### 3. Cron 스케줄 설정

1. Cron Trigger Node 클릭
2. 설정 변경:
   ```
   Mode: Every Day
   Hour: 8
   Minute: 0
   Timezone: Asia/Seoul
   ```
3. **Activate** 토글 활성화

---

## 🧪 테스트 실행

### 1. SQL 쿼리 개별 테스트

```bash
# 어제 KPI 조회
psql YOUR_DATABASE_URL -f queries/kpis_yesterday.sql

# 지난주 KPI 조회
psql YOUR_DATABASE_URL -f queries/kpis_last_week.sql

# 상위 제품 조회
psql YOUR_DATABASE_URL -f queries/top_products.sql
```

### 2. n8n Transform Logic 테스트

n8n Function Node에 다음 테스트 데이터 입력:

```javascript
// Test Input
[
  { json: { total_orders: 520, total_revenue: 18750000, avg_order_value: 36057.69, conversion_rate: 3.85 } },
  { json: { total_orders: 450, total_revenue: 15000000, avg_order_value: 33333.33, conversion_rate: 3.75 } },
  { json: [
      { rank: 1, product_name: "무선 이어폰", total_revenue: 4500000, units_sold: 150 },
      { rank: 2, product_name: "스마트워치", total_revenue: 3200000, units_sold: 80 },
      { rank: 3, product_name: "블루투스 스피커", total_revenue: 2100000, units_sold: 210 }
    ]
  }
]
```

예상 출력:
```
매출: ₩18,750,000 (+25.0% ↑)
주문 수: 520건 (+15.6% ↑)
```

### 3. End-to-End 테스트

1. **워크플로우 수동 실행**: "Execute Workflow" 클릭
2. **Slack 메시지 확인**: 채널에 리포트 도착 확인
3. **실행 시간 확인**: Executions → 실행 시간 \< 2분 확인
4. **에러 처리 테스트**:
   - DB 연결 끊기 → 에러 알림 확인
   - 잘못된 SQL 실행 → Graceful degradation 확인

---

## 🛠️ 문제 해결

### PostgreSQL 연결 실패

```bash
# 연결 테스트
psql YOUR_DATABASE_URL -c "SELECT 1;"

# 방화벽 확인
# Supabase: Settings → Database → Connection Pooling 확인
```

### n8n 워크플로우 실행 안됨

1. **Credentials 재설정**: Settings → Credentials → Test Connection
2. **로그 확인**: Executions → Error Details
3. **재시작**: `docker restart n8n` 또는 `n8n restart`

### Slack 메시지 전송 실패

1. **Webhook URL 확인**: 유효한지 curl로 테스트
2. **Rate Limit**: Slack API limits 확인 (일반적으로 문제 없음)

---

## 📚 다음 단계

- [SQL 쿼리 상세 설명](SQL_GUIDE.md)
- [Slack 메시지 커스터마이징](SLACK_INTEGRATION.md)
- [테스트 결과](../tests/TEST_RESULTS.md)

---

**문제 발생 시**: GitHub Issues에 문의하거나 문서를 참조하세요.
