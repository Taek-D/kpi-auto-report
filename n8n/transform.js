// ============================================================================
// File: transform.js
// Purpose: WoW 분석 + 이상 탐지 + Slack 메시지 포맷팅 (Code Node)
// Usage: n8n "WoW Analysis & Anomaly Detection" Code Node에 붙여넣기
// ============================================================================

// ============================================================================
// 1. Merge 노드에서 데이터 참조
// ============================================================================
// Merge (Append) 순서: input 0 = Yesterday, input 1 = Last Week, input 2 = Top Products
// 각 input의 아이템이 순서대로 합쳐져서 들어옴

const allItems = $input.all();

const DEFAULT_KPI = {
  total_orders: 0,
  total_revenue: 0,
  avg_order_value: 0,
  conversion_rate: 0,
  unique_customers: 0,
  total_units_sold: 0,
  total_visitors: 0
};

// 첫 번째 아이템 = Yesterday KPIs (input 0)
// 두 번째 아이템 = Last Week KPIs (input 1)
// 세 번째 이후 = Top Products (input 2)
const yesterday = (allItems.length > 0) ? allItems[0].json : DEFAULT_KPI;
const lastWeek = (allItems.length > 1) ? allItems[1].json : DEFAULT_KPI;
const topProducts = (allItems.length > 2) ? allItems.slice(2).map(function(item) { return item.json; }) : [];

// ============================================================================
// 2. 데이터 없음 감지 (조기 반환)
// ============================================================================

const today = new Date().toISOString().split('T')[0];
const hasNoData = allItems.length === 0 || !yesterday.total_orders;

if (hasNoData) {
  return [{
    json: {
      slackPayload: JSON.stringify({
        text: '📊 *일일 E-commerce KPI 리포트* | ' + today + '\n\n⚠️ 어제 날짜에 대한 데이터가 없습니다. 데이터 소스를 확인해 주세요.'
      }),
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

const hasLastWeek = allItems.length > 1 && lastWeek.total_orders;

const wowRevenue = hasLastWeek ? calculateWoW(yesterday.total_revenue, lastWeek.total_revenue) : null;
const wowOrders = hasLastWeek ? calculateWoW(yesterday.total_orders, lastWeek.total_orders) : null;
const wowAov = hasLastWeek ? calculateWoW(yesterday.avg_order_value, lastWeek.avg_order_value) : null;
const wowConvRate = hasLastWeek ? (yesterday.conversion_rate - lastWeek.conversion_rate) : null;

// ============================================================================
// 4. 이상 탐지 (Anomaly Detection)
// ============================================================================

var alerts = [];

// 매출 급락 감지 (20% 이상 하락 → Critical)
if (wowRevenue !== null && wowRevenue < -20) {
  alerts.push('🚨 *Critical*: 매출이 지난주 대비 ' + Math.abs(wowRevenue).toFixed(1) + '% 감소했습니다');
}

// 주문 수 급락 감지 (15% 이상 하락 → Warning)
if (wowOrders !== null && wowOrders < -15) {
  alerts.push('⚠️ *Warning*: 주문 수가 지난주 대비 ' + Math.abs(wowOrders).toFixed(1) + '% 감소했습니다');
}

// 전환율 급락 감지 (10%p 이상 하락 → Warning)
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
// 7. 출력 (Slack 노드로 전달)
// ============================================================================

return [{
  json: {
    slackPayload: JSON.stringify({ text: slackMessage }),
    message: slackMessage,
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
