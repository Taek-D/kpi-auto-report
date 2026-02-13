// ============================================================================
// File: slack_send.js
// Purpose: Slack Webhook으로 앳홈 KPI 리포트 전송 (Code Node)
// Usage: n8n "Slack: Send KPI Alert" Code Node에 붙여넣기
// ============================================================================

// ============================================================================
// 1. 이전 노드에서 메시지 수신
// ============================================================================

const items = $input.all();
const message = items[0].json.message;
const metadata = items[0].json.metadata;

// ============================================================================
// 2. Slack Webhook 전송
// ============================================================================
// 아래 URL을 실제 Slack Webhook URL로 교체하세요
const SLACK_WEBHOOK_URL = 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL';

await this.helpers.httpRequest({
  method: 'POST',
  url: SLACK_WEBHOOK_URL,
  body: { text: message },
  json: true
});

// ============================================================================
// 3. 전송 결과 반환
// ============================================================================

return [{
  json: {
    status: 'sent',
    title: '앳홈 Daily KPI 리포트',
    message: message,
    metadata: metadata,
    sent_at: new Date().toISOString()
  }
}];
