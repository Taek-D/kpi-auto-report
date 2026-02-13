// ============================================================================
// File: transform.js
// Purpose: 앳홈 브랜드별 WoW 분석 + 이상 탐지 + 경쟁사 모니터링 + Slack 메시지
// Usage: n8n "WoW Analysis & Anomaly Detection" Code Node에 붙여넣기
// ============================================================================

// ============================================================================
// 1. Merge 노드에서 데이터 참조
// ============================================================================
// Merge (Append) 순서:
//   input 0 = Yesterday Brand KPIs (배열: 브랜드별 행)
//   input 1 = Last Week Brand KPIs (배열: 브랜드별 행)
//   input 2 = Top Products (배열: 상위 제품)
//   input 3 = Competitor Changes (배열: 경쟁사 변동)

const allItems = $input.all();

// 데이터 소스별 분리 (위치 기반)
// Merge(append)는 모든 아이템을 순서대로 합침
// 각 HTTP Request의 응답 행 수에 따라 동적 파싱 필요

// 브랜드 목록 (앳홈 3개 브랜드)
var BRANDS = ['minix', 'thome', 'protione'];
var BRAND_NAMES = { minix: '미닉스', thome: '톰', protione: '프로티원' };
var BRAND_EMOJI = { minix: '🏠', thome: '💆', protione: '💪' };

// ============================================================================
// 2. 데이터 파싱 (Merge 아이템 분리)
// ============================================================================

// 각 아이템의 brand 필드로 Yesterday/LastWeek 구분
// Yesterday 데이터: brand 필드가 있고 channel_breakdown 존재
// Top Products: revenue_rank 필드 존재
// Competitor: current_ranking 필드 존재

var yesterdayBrands = [];
var lastWeekBrands = [];
var topProducts = [];
var competitors = [];

for (var i = 0; i < allItems.length; i++) {
  var item = allItems[i].json;

  if (item.revenue_rank !== undefined) {
    // Top Products 데이터
    topProducts.push(item);
  } else if (item.current_ranking !== undefined || item.ranking_change !== undefined) {
    // Competitor 데이터
    competitors.push(item);
  } else if (item.brand && item.total_revenue !== undefined) {
    // Brand KPI 데이터 - Yesterday vs LastWeek 구분
    // Yesterday 데이터가 먼저 들어오고, LastWeek가 뒤에 들어옴
    // channel_breakdown 필드가 있는 것이 RPC 응답
    if (yesterdayBrands.length < BRANDS.length) {
      yesterdayBrands.push(item);
    } else {
      lastWeekBrands.push(item);
    }
  }
}

// ============================================================================
// 3. 데이터 없음 감지
// ============================================================================

var today = new Date().toISOString().split('T')[0];
var hasNoData = yesterdayBrands.length === 0;

if (hasNoData) {
  return [{
    json: {
      slackPayload: JSON.stringify({
        text: '📊 *앳홈 Daily KPI 리포트* | ' + today + '\n\n⚠️ 어제 날짜에 대한 데이터가 없습니다. 데이터 소스를 확인해 주세요.'
      }),
      metadata: { date: today, has_data: false }
    }
  }];
}

// ============================================================================
// 4. WoW (Week-over-Week) 변화율 계산
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

function formatKRW(value) {
  return Number(value || 0).toLocaleString('ko-KR');
}

// LastWeek 데이터를 brand 키로 매핑
var lastWeekMap = {};
for (var j = 0; j < lastWeekBrands.length; j++) {
  lastWeekMap[lastWeekBrands[j].brand] = lastWeekBrands[j];
}

// ============================================================================
// 5. 브랜드별 WoW 분석 + 이상 탐지
// ============================================================================

var alerts = [];
var brandSections = [];
var totalRevenue = 0;
var totalOrders = 0;
var totalRevenueLastWeek = 0;
var totalOrdersLastWeek = 0;

for (var b = 0; b < yesterdayBrands.length; b++) {
  var yd = yesterdayBrands[b];
  var lw = lastWeekMap[yd.brand] || {};
  var brandName = BRAND_NAMES[yd.brand] || yd.brand;
  var emoji = BRAND_EMOJI[yd.brand] || '📊';

  totalRevenue += Number(yd.total_revenue || 0);
  totalOrders += Number(yd.total_orders || 0);
  totalRevenueLastWeek += Number(lw.total_revenue || 0);
  totalOrdersLastWeek += Number(lw.total_orders || 0);

  var wowRev = calculateWoW(Number(yd.total_revenue), Number(lw.total_revenue));
  var wowOrd = calculateWoW(Number(yd.total_orders), Number(lw.total_orders));
  var wowRoas = lw.avg_roas ? (Number(yd.avg_roas) - Number(lw.avg_roas)) : null;

  // 이상 탐지 (브랜드별)
  // 톰은 홈쇼핑 방송일에 변동이 크므로 별도 임계값
  var revenueThreshold = (yd.brand === 'thome') ? -30 : -20;
  var orderThreshold = (yd.brand === 'thome') ? -25 : -15;

  if (wowRev !== null && wowRev < revenueThreshold) {
    alerts.push('🚨 *' + brandName + '*: 매출 ' + Math.abs(wowRev).toFixed(1) + '% 감소');
  }
  if (wowOrd !== null && wowOrd < orderThreshold) {
    alerts.push('⚠️ *' + brandName + '*: 주문 ' + Math.abs(wowOrd).toFixed(1) + '% 감소');
  }

  // 채널 요약 (상위 2개)
  var channelInfo = '';
  if (yd.channel_breakdown && typeof yd.channel_breakdown === 'object') {
    var channels = Array.isArray(yd.channel_breakdown) ? yd.channel_breakdown : [];
    if (channels.length > 0) {
      var topChannels = channels.slice(0, 2).map(function(ch) {
        return ch.channel + ' ' + ch.share_pct + '%';
      });
      channelInfo = ' (' + topChannels.join(', ') + ')';
    }
  }

  brandSections.push(
    emoji + ' *' + brandName + '*\n'
    + '  매출: ₩' + formatKRW(yd.total_revenue) + ' (' + formatWoW(wowRev) + ' ' + getTrendIcon(wowRev) + ')\n'
    + '  주문: ' + formatKRW(yd.total_orders) + '건 | ROAS: ' + Number(yd.avg_roas || 0).toFixed(1) + channelInfo
  );
}

// 전체 합계 WoW
var totalWowRevenue = calculateWoW(totalRevenue, totalRevenueLastWeek);
var totalWowOrders = calculateWoW(totalOrders, totalOrdersLastWeek);

// ============================================================================
// 6. 상위 제품 포맷팅
// ============================================================================

var top5Formatted = topProducts.length > 0
  ? topProducts.slice(0, 5).map(function(p, index) {
      var revenue = formatKRW(p.total_revenue);
      var brand = BRAND_NAMES[p.brand] || p.brand;
      var rating = p.avg_rating ? ' ★' + p.avg_rating : '';
      return (index + 1) + '. *' + (p.product_name || '알 수 없음') + '* [' + brand + ']: ₩' + revenue + rating;
    }).join('\n')
  : '데이터 없음';

// ============================================================================
// 7. 경쟁사 모니터링 포맷팅
// ============================================================================

var competitorAlerts = [];
for (var c = 0; c < competitors.length; c++) {
  var comp = competitors[c];

  // 순위 변동 알림 (2단계 이상 변동만)
  if (comp.ranking_change && Math.abs(comp.ranking_change) >= 2) {
    var direction = comp.ranking_change > 0 ? '상승' : '하락';
    var icon = comp.ranking_change > 0 ? '📈' : '📉';
    competitorAlerts.push(
      icon + ' ' + comp.product_name + ' [' + comp.source + '] '
      + comp.prev_ranking + '위→' + comp.current_ranking + '위 (' + direction + ')'
    );
  }

  // 가격 변동 알림
  if (comp.price_change && comp.price_change !== 0) {
    var priceDir = comp.price_change > 0 ? '인상' : '인하';
    competitorAlerts.push(
      '💰 ' + comp.product_name + ' [' + comp.brand + '] '
      + '₩' + formatKRW(Math.abs(comp.price_change)) + ' ' + priceDir
    );
  }
}

var competitorSection = competitorAlerts.length > 0
  ? '\n*🔍 경쟁사 모니터링*\n' + competitorAlerts.slice(0, 5).join('\n') + '\n'
  : '';

// ============================================================================
// 8. 이상 탐지 섹션
// ============================================================================

var anomalySection = alerts.length > 0
  ? '\n*🔔 이상 감지*\n' + alerts.join('\n') + '\n'
  : '';

// ============================================================================
// 9. Slack 메시지 조립
// ============================================================================

var slackMessage = '📊 *앳홈 Daily KPI 리포트* | ' + today + '\n\n'
  + '*전체 실적 (어제 기준)*\n'
  + '━━━━━━━━━━━━━━━━━━━━━\n'
  + '💰 *총 매출*: ₩' + formatKRW(totalRevenue) + ' (' + formatWoW(totalWowRevenue) + ' ' + getTrendIcon(totalWowRevenue) + ')\n'
  + '📦 *총 주문*: ' + formatKRW(totalOrders) + '건 (' + formatWoW(totalWowOrders) + ' ' + getTrendIcon(totalWowOrders) + ')\n\n'
  + '*브랜드별 실적*\n'
  + '━━━━━━━━━━━━━━━━━━━━━\n'
  + brandSections.join('\n\n') + '\n'
  + anomalySection
  + '\n*🏆 매출 Top 5 제품*\n'
  + top5Formatted + '\n'
  + competitorSection + '\n'
  + '⏰ 리포트 생성: ' + new Date().toLocaleTimeString('ko-KR');

// ============================================================================
// 10. 출력 (Slack 노드로 전달)
// ============================================================================

return [{
  json: {
    slackPayload: JSON.stringify({ text: slackMessage }),
    message: slackMessage,
    metadata: {
      date: today,
      total_revenue: totalRevenue,
      total_orders: totalOrders,
      wow_revenue: totalWowRevenue,
      wow_orders: totalWowOrders,
      alerts_count: alerts.length,
      competitor_alerts: competitorAlerts.length,
      has_anomaly: alerts.length > 0,
      has_data: true,
      brands: yesterdayBrands.map(function(b) { return b.brand; })
    }
  }
}];
