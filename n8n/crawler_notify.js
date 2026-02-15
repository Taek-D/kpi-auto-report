// ============================================================================
// n8n Code Node: 크롤링 결과 파싱 + Slack 알림
// Execute Command 노드의 stdout을 파싱하여 Slack 웹훅으로 전송
// ============================================================================

const items = $input.all();

// Execute Command 결과에서 stdout 추출
const stdout = items[0]?.json?.stdout || '';
const stderr = items[0]?.json?.stderr || '';
const exitCode = items[0]?.json?.exitCode ?? -1;

const now = new Date();
const dateStr = now.toISOString().split('T')[0];
const timeStr = now.toTimeString().split(' ')[0];

// stdout에서 주요 정보 파싱
function parseResults(output) {
  const result = {
    crawlCount: 0,
    loadSuccess: 0,
    loadFailed: 0,
    charts: [],
    errors: [],
  };

  // 크롤링 건수
  const crawlMatch = output.match(/크롤링 완료: 총 (\d+)건/);
  if (crawlMatch) result.crawlCount = parseInt(crawlMatch[1]);

  // 적재 결과
  const loadMatch = output.match(/성공 (\d+)건 \/ 실패 (\d+)건/);
  if (loadMatch) {
    result.loadSuccess = parseInt(loadMatch[1]);
    result.loadFailed = parseInt(loadMatch[2]);
  }

  // 차트 파일
  const chartMatches = output.matchAll(/→ (.+\.png)/g);
  for (const m of chartMatches) {
    result.charts.push(m[1]);
  }

  // 에러
  const errorMatches = output.matchAll(/\[ERROR\] (.+)/g);
  for (const m of errorMatches) {
    result.errors.push(m[1]);
  }

  return result;
}

const parsed = parseResults(stdout);
const isSuccess = exitCode === 0 && parsed.loadFailed === 0;

// Slack 메시지 포맷
let message;

if (isSuccess) {
  message = [
    `✅ 크롤링 파이프라인 완료 | ${dateStr}`,
    '',
    '실행 결과',
    '━'.repeat(20),
    `📥 수집: ${parsed.crawlCount}건`,
    `💾 적재: 성공 ${parsed.loadSuccess}건`,
  ];

  if (parsed.charts.length > 0) {
    message.push(`📊 차트: ${parsed.charts.length}개 생성`);
    for (const chart of parsed.charts) {
      message.push(`  → ${chart}`);
    }
  }

  message.push('');
  message.push(`⏰ 완료 시각: ${timeStr}`);
} else {
  message = [
    `❌ 크롤링 파이프라인 실패 | ${dateStr}`,
    '',
    `Exit Code: ${exitCode}`,
    `적재 실패: ${parsed.loadFailed}건`,
  ];

  if (parsed.errors.length > 0) {
    message.push('');
    message.push('에러:');
    for (const err of parsed.errors) {
      message.push(`  ⚠️ ${err}`);
    }
  }

  if (stderr) {
    message.push('');
    message.push('stderr (최근 200자):');
    message.push(stderr.slice(-200));
  }

  message.push('');
  message.push(`⏰ 실패 시각: ${timeStr}`);
}

// Slack Webhook 전송
const SLACK_WEBHOOK_URL = 'YOUR_SLACK_WEBHOOK_URL';

const response = await this.helpers.httpRequest({
  method: 'POST',
  url: SLACK_WEBHOOK_URL,
  body: {
    text: message.join('\n'),
  },
  headers: {
    'Content-Type': 'application/json',
  },
});

return [
  {
    json: {
      status: isSuccess ? 'success' : 'failed',
      crawlCount: parsed.crawlCount,
      loadSuccess: parsed.loadSuccess,
      loadFailed: parsed.loadFailed,
      charts: parsed.charts,
      slackSent: true,
      timestamp: now.toISOString(),
    },
  },
];
