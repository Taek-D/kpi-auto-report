# Slack 연동 가이드

## 📋 개요

이 프로젝트는 n8n Code Node에서 `this.helpers.httpRequest()`를 사용하여 Slack Incoming Webhook으로 KPI 리포트를 전송합니다.

---

## 🔧 Webhook 설정

### 1. Slack App 생성

1. https://api.slack.com/apps 접속
2. "Create New App" → "From scratch"
3. App Name: `KPI Reporter`, Workspace 선택

### 2. Incoming Webhooks 활성화

1. Features → Incoming Webhooks → Activate
2. "Add New Webhook to Workspace"
3. 채널 선택 (예: `#business-kpis`)
4. Webhook URL 복사

### 3. Webhook URL 테스트

```bash
curl -X POST https://hooks.slack.com/services/YOUR/WEBHOOK/URL \
  -H 'Content-Type: application/json' \
  -d '{"text": "🎉 연동 테스트 성공!"}'
```

---

## 🛠️ n8n에서의 구현

### 왜 Code Node인가?

n8n HTTP Request 노드의 JSON body 모드에서 줄바꿈(`\n`) 포함 문자열을 처리하지 못하는 문제가 있어, Code Node + `this.helpers.httpRequest()`를 사용합니다.

### slack_send.js 구조

```javascript
// 1. 이전 노드에서 메시지 수신
const items = $input.all();
const message = items[0].json.message;

// 2. Slack Webhook 전송
const SLACK_WEBHOOK_URL = 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL';

await this.helpers.httpRequest({
  method: 'POST',
  url: SLACK_WEBHOOK_URL,
  body: { text: message },
  json: true
});

// 3. 전송 결과 반환
return [{ json: { status: 'sent', sent_at: new Date().toISOString() } }];
```

### Webhook URL 설정 방법

1. n8n UI에서 "Slack: Send KPI Alert" 노드 클릭
2. Code 에디터에서 `SLACK_WEBHOOK_URL` 값을 실제 URL로 교체
3. GitHub에는 플레이스홀더(`YOUR/WEBHOOK/URL`)만 커밋 (보안)

---

## 📊 메시지 포맷

### 전체 메시지 구조

```
📊 일일 E-commerce KPI 리포트 | 2026-02-13

핵심 지표 (어제 기준)
━━━━━━━━━━━━━━━━━━━━━
💰 매출: ₩12,500,000 (+8.3% ↑)
📦 주문 수: 342건 (+5.2% ↑)
🛒 평균 주문 금액: ₩36,549 (+2.9% ↑)
📈 전환율: 3.2% (+0.4%p ↑)

🏆 매출 상위 3개 제품
1. 무선 이어폰 Pro: ₩2,340,000 (156개 판매)
2. 스마트워치 S3: ₩1,890,000 (63개 판매)
3. USB-C 허브 7in1: ₩1,230,000 (205개 판매)

⏰ 리포트 생성: 08:00:12
```

### 이상 탐지 알림 (조건 충족 시 추가)

```
🔔 이상 감지
🚨 Critical: 매출이 지난주 대비 25.3% 감소했습니다
⚠️ Warning: 주문 수가 지난주 대비 18.1% 감소했습니다
```

### 데이터 없음 처리

```
📊 일일 E-commerce KPI 리포트 | 2026-02-13

⚠️ 어제 날짜에 대한 데이터가 없습니다. 데이터 소스를 확인해 주세요.
```

---

## 📝 Slack 텍스트 포맷팅

| 포맷 | Slack 문법 | 예시 |
|------|-----------|------|
| 굵게 | `*텍스트*` | **텍스트** |
| 기울임 | `_텍스트_` | _텍스트_ |
| 코드 | `` `코드` `` | `코드` |

### 이모지 매핑

| 이모지 | Slack 코드 | 용도 |
|--------|-----------|------|
| 📊 | `:bar_chart:` | 리포트 헤더 |
| 💰 | `:moneybag:` | 매출 |
| 📦 | `:package:` | 주문 수 |
| 🛒 | `:shopping_cart:` | 평균 주문 금액 |
| 📈 | `:chart_with_upwards_trend:` | 전환율 |
| 🏆 | `:trophy:` | 상위 제품 |
| 🚨 | `:rotating_light:` | Critical 알림 |
| ⚠️ | `:warning:` | Warning 알림 |

---

## 🔍 문제 해결

### "Bad request - no_text" 에러

- **원인**: Slack이 `text` 필드를 찾지 못함
- **해결**: `body: { text: message }`와 `json: true` 옵션 확인

### Webhook URL 만료

- Slack Webhook URL은 만료되지 않지만, App이 삭제되면 무효화됨
- 새 URL 발급: Slack App → Incoming Webhooks → "Add New Webhook"

---

## 📚 참고 자료

- [Slack Incoming Webhooks 공식 문서](https://api.slack.com/messaging/webhooks)
- [Slack 메시지 포맷팅 가이드](https://api.slack.com/reference/surfaces/formatting)

---

**다음**: [SQL 쿼리 상세 가이드](SQL_GUIDE.md)
