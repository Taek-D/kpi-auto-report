# Slack 연동 가이드

## Webhook 설정

1. https://api.slack.com/apps 접속
2. "Create New App" → "From scratch"
3. "Incoming Webhooks" 활성화
4. Webhook URL 복사

## 테스트

```bash
curl -X POST YOUR_WEBHOOK_URL \
  -H 'Content-Type: application/json' \
  -d '{"text": "테스트 메시지"}'
```

## 메시지 포맷

### 기본 구조
```javascript
{
  "text": "📊 일일 KPI 리포트",
  "blocks": [...]
}
```

### 이모지
- 📊 `:bar_chart:`
- 💰 `:moneybag:`
- ⚠️ `:warning:`

## 참고 자료
- [Slack Webhooks 문서](https://api.slack.com/messaging/webhooks)
