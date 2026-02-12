// ============================================================================
// File: transform.js
// Purpose: n8n Function Node에서 실행되는 데이터 변환 및 이상 탐지 로직
// Usage: n8n Workflow의 Function Node에 붙여넣기
// ============================================================================

// ============================================================================
// 입력 데이터 구조 (n8n에서 전달받음)
// ============================================================================
// Input 0: Yesterday KPIs (1행) → { total_orders, total_revenue, avg_order_value, ... }
// Input 1: Last Week KPIs (1행) → { total_orders, total_revenue, avg_order_value, ... }
// Input 2+: Top Products (N행)  → { rank, product_name, total_revenue, units_sold, ... }

const inputs = $input.all();

const DEFAULT_KPI = {
  total_orders: 0,
  total_revenue: 0,
  avg_order_value: 0,
  conversion_rate: 0,
  unique_customers: 0,
  total_units_sold: 0,
  total_visitors: 0
};

const yesterday = (inputs[0] && inputs[0].json) ? inputs[0].json : DEFAULT_KPI;
const lastWeek = (inputs[1] && inputs[1].json) ? inputs[1].json : DEFAULT_KPI;
const topProductsRaw = inputs.slice(2);

// ============================================================================
// 0. 데이터 없음 감지 (조기 반환)
// ============================================================================

const today = new Date().toISOString().split('T')[0];
const hasNoData = !inputs[0] || !inputs[0].json || !inputs[0].json.total_orders;

if (hasNoData) {
  return {
    json: {
      message: '📊 **일일 E-commerce KPI 리포트** | ' + today + '\n\n⚠️ 어제 날짜에 대한 데이터가 없습니다. 데이터 소스를 확인해 주세요.',
      metadata: {
        date: today,
        has_data: false
      }
    }
  };
}

// ============================================================================
// 1. WoW (Week-over-Week) 변화율 계산
// ============================================================================

function calculateWoW(current, previous) {
  if (!previous || previous === 0) return null;
  return ((current - previous) / previous) * 100;
}

function formatWoW(value) {
  if (value === null) return 'N/A';
  return (value > 0 ? '+' : '') + value.toFixed(1) + '%';
}

const hasLastWeek = inputs[1] && inputs[1].json && inputs[1].json.total_orders;

const wowRevenue = hasLastWeek ? calculateWoW(yesterday.total_revenue, lastWeek.total_revenue) : null;
const wowOrders = hasLastWeek ? calculateWoW(yesterday.total_orders, lastWeek.total_orders) : null;
const wowAov = hasLastWeek ? calculateWoW(yesterday.avg_order_value, lastWeek.avg_order_value) : null;
const wowConvRate = hasLastWeek ? (yesterday.conversion_rate - lastWeek.conversion_rate) : null;

// ============================================================================
// 2. 이상 탐지 (Anomaly Detection)
// ============================================================================

var alerts = [];

// 매출 급락 감지 (20% 이상 하락)
if (wowRevenue !== null && wowRevenue < -20) {
  alerts.push('🚨 **Critical**: 매출이 지난주 대비 ' + Math.abs(wowRevenue).toFixed(1) + '% 감소했습니다');
}

// 주문 수 급락 감지 (15% 이상 하락)
if (wowOrders !== null && wowOrders < -15) {
  alerts.push('⚠️ **Warning**: 주문 수가 지난주 대비 ' + Math.abs(wowOrders).toFixed(1) + '% 감소했습니다');
}

// 전환율 급락 감지 (10%p 이상 하락)
if (wowConvRate !== null && wowConvRate < -10) {
  alerts.push('⚠️ **Warning**: 전환율이 지난주 대비 ' + Math.abs(wowConvRate).toFixed(1) + '%p 감소했습니다');
}

var anomalySection = alerts.length > 0
  ? '\n**🔔 이상 감지**\n' + alerts.join('\n') + '\n'
  : '';

// ============================================================================
// 3. 트렌드 방향 표시 (↑/↓)
// ============================================================================

function getTrendIcon(value) {
  if (value === null) return '';
  if (value > 0) return '↑';
  if (value < 0) return '↓';
  return '→';
}

// ============================================================================
// 4. 상위 제품 포맷팅
// ============================================================================

var topProducts = topProductsRaw.map(function(item) { return item.json; }).filter(Boolean);

var top3Formatted = topProducts.length > 0
  ? topProducts.slice(0, 3).map(function(p, index) {
      var revenue = Number(p.total_revenue || 0).toLocaleString('ko-KR');
      var units = Number(p.units_sold || 0).toLocaleString('ko-KR');
      return (index + 1) + '. **' + (p.product_name || '알 수 없음') + '**: ₩' + revenue + ' (' + units + ' 개 판매)';
    }).join('\n')
  : '데이터 없음';

// ============================================================================
// 5. WoW 포맷팅 (전환율은 %p 단위)
// ============================================================================

function formatWoWConvRate(value) {
  if (value === null) return 'N/A';
  return (value > 0 ? '+' : '') + value.toFixed(1) + '%p';
}

// ============================================================================
// 6. Slack 메시지 포맷팅
// ============================================================================

var slackMessage = '📊 **일일 E-commerce KPI 리포트** | ' + today + '\n\n'
  + '**핵심 지표 (어제 기준)**\n'
  + '━━━━━━━━━━━━━━━━━━━━━\n'
  + '💰 **매출**: ₩' + Number(yesterday.total_revenue).toLocaleString('ko-KR') + ' (' + formatWoW(wowRevenue) + ' ' + getTrendIcon(wowRevenue) + ')\n'
  + '📦 **주문 수**: ' + Number(yesterday.total_orders).toLocaleString('ko-KR') + '건 (' + formatWoW(wowOrders) + ' ' + getTrendIcon(wowOrders) + ')\n'
  + '🛒 **평균 주문 금액**: ₩' + Number(yesterday.avg_order_value).toLocaleString('ko-KR') + ' (' + formatWoW(wowAov) + ' ' + getTrendIcon(wowAov) + ')\n'
  + '📈 **전환율**: ' + yesterday.conversion_rate + '% (' + formatWoWConvRate(wowConvRate) + ' ' + getTrendIcon(wowConvRate) + ')\n'
  + anomalySection + '\n'
  + '**🏆 매출 상위 3개 제품**\n'
  + top3Formatted + '\n\n'
  + '📊 [대시보드 바로가기](https://tableau.example.com/dashboard) | ⏰ 리포트 생성: ' + new Date().toLocaleTimeString('ko-KR');

// ============================================================================
// 7. 출력 데이터 반환
// ============================================================================

return {
  json: {
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
};
