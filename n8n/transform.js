// ============================================================================
// File: transform.js
// Purpose: Supabase RPC 호출 + 데이터 변환 + 이상 탐지 (단일 Code 노드)
// Usage: n8n Workflow의 Code Node에 붙여넣기
// ============================================================================

const SUPABASE_URL = 'https://rjulhuseewaaxpbgyaah.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJqdWxodXNlZXdhYXhwYmd5YWFoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzA3MjM5NjMsImV4cCI6MjA4NjI5OTk2M30.HzfdZo19oy6Lp7T6BSkNjRuUF1KWEaOS429r5O-iNIo';

// ============================================================================
// 0. Supabase RPC 호출 함수 (n8n 내장 httpRequest 사용)
// ============================================================================

async function callRpc(functionName) {
  return await this.helpers.httpRequest({
    method: 'POST',
    url: SUPABASE_URL + '/rest/v1/rpc/' + functionName,
    headers: {
      'apikey': SUPABASE_ANON_KEY,
      'Authorization': 'Bearer ' + SUPABASE_ANON_KEY,
      'Content-Type': 'application/json'
    },
    body: {},
    json: true
  });
}

// ============================================================================
// 1. 3개 RPC 병렬 호출
// ============================================================================

const [yesterdayData, lastWeekData, topProductsData] = await Promise.all([
  callRpc.call(this, 'get_kpis_yesterday'),
  callRpc.call(this, 'get_kpis_last_week'),
  callRpc.call(this, 'get_top_products')
]);

const DEFAULT_KPI = {
  total_orders: 0,
  total_revenue: 0,
  avg_order_value: 0,
  conversion_rate: 0,
  unique_customers: 0,
  total_units_sold: 0,
  total_visitors: 0
};

const yesterday = (yesterdayData && yesterdayData[0]) ? yesterdayData[0] : DEFAULT_KPI;
const lastWeek = (lastWeekData && lastWeekData[0]) ? lastWeekData[0] : DEFAULT_KPI;
const topProducts = (topProductsData && topProductsData.length > 0) ? topProductsData : [];

// ============================================================================
// 2. 데이터 없음 감지 (조기 반환)
// ============================================================================

const today = new Date().toISOString().split('T')[0];
const hasNoData = !yesterdayData || !yesterdayData[0] || !yesterdayData[0].total_orders;

if (hasNoData) {
  return [{
    json: {
      message: '📊 *일일 E-commerce KPI 리포트* | ' + today + '\n\n⚠️ 어제 날짜에 대한 데이터가 없습니다. 데이터 소스를 확인해 주세요.',
      metadata: { date: today, has_data: false }
    }
  }];
}

// ============================================================================
// 3. WoW (Week-over-Week) 변화율 계산
// ============================================================================

function calculateWoW(current, previous) {
  if (!previous || previous === 0) return null;
  return ((current - previous) / previous) * 100;
}

function formatWoW(value) {
  if (value === null) return 'N/A';
  return (value > 0 ? '+' : '') + value.toFixed(1) + '%';
}

function formatWoWConvRate(value) {
  if (value === null) return 'N/A';
  return (value > 0 ? '+' : '') + value.toFixed(1) + '%p';
}

function getTrendIcon(value) {
  if (value === null) return '';
  if (value > 0) return '↑';
  if (value < 0) return '↓';
  return '→';
}

const hasLastWeek = lastWeekData && lastWeekData[0] && lastWeekData[0].total_orders;

const wowRevenue = hasLastWeek ? calculateWoW(yesterday.total_revenue, lastWeek.total_revenue) : null;
const wowOrders = hasLastWeek ? calculateWoW(yesterday.total_orders, lastWeek.total_orders) : null;
const wowAov = hasLastWeek ? calculateWoW(yesterday.avg_order_value, lastWeek.avg_order_value) : null;
const wowConvRate = hasLastWeek ? (yesterday.conversion_rate - lastWeek.conversion_rate) : null;

// ============================================================================
// 4. 이상 탐지 (Anomaly Detection)
// ============================================================================

var alerts = [];

if (wowRevenue !== null && wowRevenue < -20) {
  alerts.push('🚨 *Critical*: 매출이 지난주 대비 ' + Math.abs(wowRevenue).toFixed(1) + '% 감소했습니다');
}
if (wowOrders !== null && wowOrders < -15) {
  alerts.push('⚠️ *Warning*: 주문 수가 지난주 대비 ' + Math.abs(wowOrders).toFixed(1) + '% 감소했습니다');
}
if (wowConvRate !== null && wowConvRate < -10) {
  alerts.push('⚠️ *Warning*: 전환율이 지난주 대비 ' + Math.abs(wowConvRate).toFixed(1) + '%p 감소했습니다');
}

var anomalySection = alerts.length > 0
  ? '\n*🔔 이상 감지*\n' + alerts.join('\n') + '\n'
  : '';

// ============================================================================
// 5. 상위 제품 포맷팅
// ============================================================================

var top3Formatted = topProducts.length > 0
  ? topProducts.slice(0, 3).map(function(p, index) {
      var revenue = Number(p.total_revenue || 0).toLocaleString('ko-KR');
      var units = Number(p.units_sold || 0).toLocaleString('ko-KR');
      return (index + 1) + '. *' + (p.product_name || '알 수 없음') + '*: ₩' + revenue + ' (' + units + '개 판매)';
    }).join('\n')
  : '데이터 없음';

// ============================================================================
// 6. Slack 메시지 포맷팅
// ============================================================================

var slackMessage = '📊 *일일 E-commerce KPI 리포트* | ' + today + '\n\n'
  + '*핵심 지표 (어제 기준)*\n'
  + '━━━━━━━━━━━━━━━━━━━━━\n'
  + '💰 *매출*: ₩' + Number(yesterday.total_revenue).toLocaleString('ko-KR') + ' (' + formatWoW(wowRevenue) + ' ' + getTrendIcon(wowRevenue) + ')\n'
  + '📦 *주문 수*: ' + Number(yesterday.total_orders).toLocaleString('ko-KR') + '건 (' + formatWoW(wowOrders) + ' ' + getTrendIcon(wowOrders) + ')\n'
  + '🛒 *평균 주문 금액*: ₩' + Number(yesterday.avg_order_value).toLocaleString('ko-KR') + ' (' + formatWoW(wowAov) + ' ' + getTrendIcon(wowAov) + ')\n'
  + '📈 *전환율*: ' + yesterday.conversion_rate + '% (' + formatWoWConvRate(wowConvRate) + ' ' + getTrendIcon(wowConvRate) + ')\n'
  + anomalySection + '\n'
  + '*🏆 매출 상위 3개 제품*\n'
  + top3Formatted + '\n\n'
  + '⏰ 리포트 생성: ' + new Date().toLocaleTimeString('ko-KR');

// ============================================================================
// 7. Slack Webhook 전송
// ============================================================================

// Slack Webhook URL은 n8n 컨테이너 환경변수에서 읽음
const SLACK_WEBHOOK_URL = process.env.SLACK_WEBHOOK_URL;

await this.helpers.httpRequest({
  method: 'POST',
  url: SLACK_WEBHOOK_URL,
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ text: slackMessage }),
});

// ============================================================================
// 8. 출력 데이터 반환
// ============================================================================

return [{
  json: {
    message: slackMessage,
    slack_sent: true,
    metadata: {
      date: today,
      revenue: yesterday.total_revenue,
      orders: yesterday.total_orders,
      wow_revenue: wowRevenue,
      wow_orders: wowOrders,
      alerts_count: alerts.length,
      has_anomaly: alerts.length > 0,
      has_data: true
    }
  }
}];
