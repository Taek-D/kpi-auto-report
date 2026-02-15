"""
KPI 통합 대시보드 HTML 생성 모듈
Supabase 데이터 조회 -> matplotlib 차트 base64 인라인 -> 단일 HTML 파일 출력.
브라우저에서 바로 열면 되는 self-contained 대시보드.
"""

import base64
import io
import logging
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import pandas as pd
from scipy import stats

from .supabase_loader import SupabaseLoader

logger = logging.getLogger(__name__)

OUTPUT_DIR = Path(__file__).parent.parent / "output"

BRAND_LABELS = {"minix": "미닉스", "thome": "톰", "protione": "프로티원"}
BRAND_COLORS = {"minix": "#FF6B35", "thome": "#4A90D9", "protione": "#7ED321"}

CHANNEL_LABELS = {
    "own_mall": "자사몰",
    "coupang": "쿠팡",
    "naver": "네이버",
    "gs_home": "GS홈쇼핑",
    "oliveyoung": "올리브영",
}
CHANNEL_COLORS = {
    "own_mall": "#FF6B35",
    "coupang": "#00B4D8",
    "naver": "#2DB400",
    "gs_home": "#FF69B4",
    "oliveyoung": "#9B59B6",
}
CHANNEL_ORDER = ["coupang", "own_mall", "naver", "gs_home", "oliveyoung"]

WEEKDAY_KR = ["월", "화", "수", "목", "금", "토", "일"]

# Slate palette for matplotlib charts
_SLATE = {
    "bg": "#ffffff",
    "grid": "#e2e8f0",
    "text": "#334155",
    "muted": "#94a3b8",
    "border": "#e2e8f0",
}


def _setup_korean_font():
    font_candidates = ["Malgun Gothic", "NanumGothic", "AppleGothic", "DejaVu Sans"]
    available = {f.name for f in fm.fontManager.ttflist}
    for font_name in font_candidates:
        if font_name in available:
            plt.rcParams["font.family"] = font_name
            plt.rcParams["axes.unicode_minus"] = False
            return


_setup_korean_font()


def _apply_chart_style(ax):
    """Apply clean slate style to matplotlib axes."""
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(_SLATE["grid"])
    ax.spines["bottom"].set_color(_SLATE["grid"])
    ax.tick_params(colors=_SLATE["muted"], labelsize=9)
    ax.yaxis.label.set_color(_SLATE["muted"])
    ax.xaxis.label.set_color(_SLATE["muted"])
    ax.title.set_color(_SLATE["text"])
    ax.grid(True, axis="y", color=_SLATE["grid"], linewidth=0.5, alpha=0.7)
    ax.set_axisbelow(True)


def _fig_to_base64(fig: plt.Figure) -> str:
    """matplotlib Figure -> base64 PNG string"""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="white", edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


class DashboardGenerator:
    """KPI 통합 대시보드 HTML 생성기"""

    def __init__(self):
        self.loader = SupabaseLoader()

    def run(self) -> str:
        """대시보드 생성 파이프라인"""
        logger.info("[대시보드] 데이터 수집 시작")

        # 1. 데이터 수집
        yesterday = self.loader.call_rpc("get_brand_kpis_yesterday")
        last_week = self.loader.call_rpc("get_brand_kpis_last_week")
        top_products = self.loader.call_rpc("get_top_products")
        sales_data = self.loader.fetch_brand_sales(days=30)
        trend_data = self.loader.fetch_search_trends(days=30)

        # 2. DataFrame 변환
        df_sales = pd.DataFrame(sales_data) if sales_data else pd.DataFrame()
        if not df_sales.empty:
            df_sales["sale_date"] = pd.to_datetime(df_sales["sale_date"])
            df_sales["revenue"] = pd.to_numeric(df_sales["revenue"], errors="coerce").fillna(0)
            df_sales["orders"] = pd.to_numeric(df_sales["orders"], errors="coerce").fillna(0)
            df_sales["ad_spend"] = pd.to_numeric(df_sales.get("ad_spend", 0), errors="coerce").fillna(0)

        df_trend = pd.DataFrame(trend_data) if trend_data else pd.DataFrame()
        if not df_trend.empty:
            df_trend["trend_date"] = pd.to_datetime(df_trend["trend_date"])
            df_trend["trend_value"] = pd.to_numeric(df_trend["trend_value"], errors="coerce").fillna(0)

        # yesterday가 비어있으면 last_week 데이터로 대체 (샘플 데이터 대응)
        kpi_source = yesterday if yesterday else last_week
        kpi_compare = last_week if yesterday else []

        # 3. 섹션별 HTML 생성
        header_html = self._build_header(kpi_source, kpi_compare)
        kpi_cards_html = self._build_kpi_cards(kpi_source, kpi_compare, df_sales)
        trend_html = self._build_trend_section(df_trend, df_sales)
        channel_html = self._build_channel_section(df_sales)
        ad_perf_html = self._build_ad_performance_section(df_sales)
        products_html = self._build_products_table(top_products)
        actions_html = self._build_actions(df_sales, df_trend)

        # 4. HTML 조립
        html = self._assemble_html(
            header_html, kpi_cards_html, trend_html,
            channel_html, ad_perf_html, products_html, actions_html,
        )

        # 5. 저장
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output_path = OUTPUT_DIR / "dashboard.html"
        output_path.write_text(html, encoding="utf-8")
        logger.info(f"[대시보드] HTML 저장: {output_path}")

        return f"[대시보드] 생성 완료: {output_path}"

    # ==================== 섹션 1: 스티키 헤더 ====================

    def _build_header(self, kpi_source: list[dict], kpi_compare: list[dict]) -> str:
        today_str = datetime.now().strftime("%Y-%m-%d")

        total_revenue = sum(float(r.get("total_revenue", 0)) for r in kpi_source)
        total_orders = sum(int(r.get("total_orders", 0)) for r in kpi_source)
        total_ad = sum(float(r.get("total_ad_spend", 0)) for r in kpi_source)
        total_roas = total_revenue / total_ad if total_ad > 0 else 0

        return f"""
        <header class="header">
            <div class="header-inner">
                <div class="header-left">
                    <div class="logo-icon">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>
                    </div>
                    <h1>앳홈 KPI 대시보드</h1>
                </div>
                <div class="header-right">
                    <div class="header-pill">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
                        {today_str}
                    </div>
                    <div class="header-pill">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg>
                        3개 브랜드
                    </div>
                    <div class="header-stat">
                        <span class="header-stat-label">총 매출</span>
                        <span class="header-stat-value">₩{total_revenue / 10000:,.0f}만</span>
                    </div>
                    <div class="header-stat">
                        <span class="header-stat-label">총 주문</span>
                        <span class="header-stat-value">{total_orders:,}건</span>
                    </div>
                    <div class="header-stat">
                        <span class="header-stat-label">ROAS</span>
                        <span class="header-stat-value">{total_roas:.1f}</span>
                    </div>
                </div>
            </div>
        </header>
        """

    # ==================== 섹션 2: KPI 카드 (4열) ====================

    def _build_kpi_cards(self, kpi_source: list[dict], kpi_compare: list[dict], df_sales: pd.DataFrame) -> str:
        cmp_map = {r["brand"]: r for r in kpi_compare}
        cards = []

        for row in kpi_source:
            brand = row.get("brand", "")
            label = BRAND_LABELS.get(brand, brand)
            color = BRAND_COLORS.get(brand, "#475569")

            revenue = float(row.get("total_revenue", 0))
            orders = int(row.get("total_orders", 0))
            ad_spend = float(row.get("total_ad_spend", 0))
            roas = revenue / ad_spend if ad_spend > 0 else 0

            cmp = cmp_map.get(brand, {})
            cmp_rev = float(cmp.get("total_revenue", 0))
            rev_wow = ((revenue / cmp_rev - 1) * 100) if cmp_rev > 0 else 0

            # 7일 스파크라인 데이터
            spark_svg = self._build_sparkline_svg(brand, df_sales, color)

            wow_cls = "badge-up" if rev_wow > 0 else ("badge-down" if rev_wow < 0 else "badge-flat")
            wow_str = f"+{rev_wow:.1f}%" if rev_wow > 0 else f"{rev_wow:.1f}%"
            wow_arrow = "&#8599;" if rev_wow > 0 else ("&#8600;" if rev_wow < 0 else "&#8594;")

            # 채널 비중 바
            ch_bar = self._build_channel_bar(brand, df_sales)

            cards.append(f"""
            <div class="kpi-card" style="border-top: 3px solid {color};">
                <div class="kpi-card-top">
                    <span class="kpi-card-label">{label}</span>
                    <span class="badge {wow_cls}">{wow_arrow} {wow_str}</span>
                </div>
                <div class="kpi-card-body">
                    <div class="kpi-card-main">
                        <div class="kpi-card-value">₩{revenue / 10000:,.0f}만</div>
                        <div class="kpi-card-sub">{orders:,}건 &middot; ROAS {roas:.1f}</div>
                    </div>
                    {spark_svg}
                </div>
                {ch_bar}
            </div>
            """)

        # 4번째 카드 (전체 합산 동행률)
        if not df_sales.empty and len(kpi_source) > 0:
            total_rev = sum(float(r.get("total_revenue", 0)) for r in kpi_source)
            cmp_total = sum(float(cmp_map.get(r.get("brand", ""), {}).get("total_revenue", 0)) for r in kpi_source)
            wow_total = ((total_rev / cmp_total - 1) * 100) if cmp_total > 0 else 0
            wow_cls_t = "badge-up" if wow_total > 0 else ("badge-down" if wow_total < 0 else "badge-flat")
            wow_str_t = f"+{wow_total:.1f}%" if wow_total > 0 else f"{wow_total:.1f}%"

            cards.append(f"""
            <div class="kpi-card" style="border-top: 3px solid #475569;">
                <div class="kpi-card-top">
                    <span class="kpi-card-label">전체 합산</span>
                    <span class="badge {wow_cls_t}">WoW {wow_str_t}</span>
                </div>
                <div class="kpi-card-body">
                    <div class="kpi-card-main">
                        <div class="kpi-card-value">₩{total_rev / 10000:,.0f}만</div>
                        <div class="kpi-card-sub">vs. 전주 동일 요일</div>
                    </div>
                </div>
            </div>
            """)

        return f'<div class="kpi-grid">{" ".join(cards)}</div>'

    def _build_sparkline_svg(self, brand: str, df_sales: pd.DataFrame, color: str) -> str:
        if df_sales.empty:
            return ""
        brand_df = df_sales[df_sales["brand"] == brand]
        if brand_df.empty:
            return ""

        daily = brand_df.groupby("sale_date")["revenue"].sum().sort_index().tail(7)
        if len(daily) < 2:
            return ""

        vals = daily.values
        mx = vals.max() if vals.max() > 0 else 1
        bars = []
        w = 8
        gap = 3
        h = 36
        for i, v in enumerate(vals):
            bh = max(2, v / mx * h)
            x = i * (w + gap)
            y = h - bh
            bars.append(f'<rect x="{x}" y="{y}" width="{w}" height="{bh}" rx="2" fill="{color}" opacity="0.7"/>')

        total_w = len(vals) * (w + gap) - gap
        return f'<svg width="{total_w}" height="{h}" class="sparkline">{"".join(bars)}</svg>'

    def _build_channel_bar(self, brand: str, df_sales: pd.DataFrame) -> str:
        if df_sales.empty:
            return ""
        brand_df = df_sales[df_sales["brand"] == brand]
        if brand_df.empty:
            return ""

        ch_rev = brand_df.groupby("channel")["revenue"].sum()
        total = ch_rev.sum()
        if total == 0:
            return ""

        segments = []
        legends = []
        for ch in CHANNEL_ORDER:
            if ch in ch_rev.index:
                pct = ch_rev[ch] / total * 100
                if pct > 1:
                    c = CHANNEL_COLORS.get(ch, "#94a3b8")
                    lbl = CHANNEL_LABELS.get(ch, ch)
                    segments.append(f'<div style="width:{pct:.1f}%;background:{c};"></div>')
                    legends.append(f'<span class="ch-legend-item"><span class="ch-dot" style="background:{c};"></span>{lbl} {pct:.0f}%</span>')

        return f"""
        <div class="ch-bar-wrap">
            <div class="ch-bar">{"".join(segments)}</div>
            <div class="ch-legend">{"".join(legends)}</div>
        </div>
        """

    # ==================== 섹션 3: 트렌드 + 신호 해석 (3:1 그리드) ====================

    def _build_trend_section(self, df_trend: pd.DataFrame, df_sales: pd.DataFrame) -> str:
        if df_trend.empty:
            return '<div class="card"><div class="card-header"><h3>검색 트렌드 상관 분석</h3></div><p class="no-data">트렌드 데이터가 없습니다.</p></div>'

        # 메인 차트: 상관 히트맵
        heatmap_b64 = self._chart_correlation_heatmap(df_trend, df_sales)

        # 선행 지표
        lead_b64, lead_results = self._chart_lead_lag(df_trend, df_sales)

        # 성수기
        peak_b64, peak_results = self._chart_peak_season(df_trend)

        # 신호 해석 사이드바
        signals = self._build_signal_cards(df_trend, df_sales, lead_results, peak_results)

        chart_parts = []
        if heatmap_b64:
            chart_parts.append(f'<img src="data:image/png;base64,{heatmap_b64}" class="chart-img" alt="상관 히트맵">')
        if lead_b64:
            chart_parts.append(f'<img src="data:image/png;base64,{lead_b64}" class="chart-img" alt="선행 지표">')
        if peak_b64:
            chart_parts.append(f'<img src="data:image/png;base64,{peak_b64}" class="chart-img" alt="성수기 탐지">')

        chart_content = "\n".join(chart_parts) if chart_parts else '<p class="no-data">분석 가능한 데이터 부족</p>'

        return f"""
        <div class="grid-3-1">
            <div class="card">
                <div class="card-header">
                    <div>
                        <h3>트렌드-매출 상관 분석</h3>
                        <p class="card-sub">Pearson/Spearman 상관, 선행 지표, 성수기 탐지</p>
                    </div>
                </div>
                {chart_content}
            </div>
            <div class="card">
                <div class="card-header">
                    <h3>신호 해석</h3>
                </div>
                {signals}
            </div>
        </div>
        """

    def _build_signal_cards(self, df_trend, df_sales, lead_results, peak_results) -> str:
        cards = []

        # 선행 지표 기반 신호
        for brand, data in lead_results.items():
            label = BRAND_LABELS.get(brand, brand)
            lag = data["best_lag"]
            corr = data["best_corr"]

            if lag > 0 and corr > 0.3:
                cards.append(self._signal_card(
                    "선행 신호 감지", f"{label}: 검색이 매출 {lag}일 선행 (r={corr:.2f})",
                    "emerald", "trending-up",
                ))
            elif lag == 0:
                cards.append(self._signal_card(
                    "동행 패턴", f"{label}: 검색-매출 동시 움직임 (r={corr:.2f})",
                    "slate", "activity",
                ))

        # 성수기 기반 신호
        for brand, periods in peak_results.items():
            label = BRAND_LABELS.get(brand, brand)
            long_peaks = [p for p in periods if p["days"] >= 3]
            if long_peaks:
                p = long_peaks[0]
                cards.append(self._signal_card(
                    "성수기 탐지",
                    f"{label}: {p['start'].strftime('%m/%d')}~{p['end'].strftime('%m/%d')} ({p['days']}일)",
                    "amber", "flame",
                ))

        if not cards:
            cards.append(self._signal_card(
                "데이터 수집 중", "트렌드 데이터 축적 후 신호 분석 가능",
                "slate", "info",
            ))

        return "\n".join(cards)

    @staticmethod
    def _signal_card(title: str, subtitle: str, variant: str, icon_type: str) -> str:
        icons = {
            "trending-up": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline><polyline points="17 6 23 6 23 12"></polyline></svg>',
            "activity": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>',
            "flame": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M8.5 14.5A2.5 2.5 0 0011 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 11-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 002.5 2.5z"></path></svg>',
            "info": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>',
            "alert": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>',
        }
        icon = icons.get(icon_type, icons["info"])

        return f"""
        <div class="signal-card signal-{variant}">
            <div class="signal-top">
                <span class="signal-title">{title}</span>
                <span class="signal-icon">{icon}</span>
            </div>
            <p class="signal-body">{subtitle}</p>
        </div>
        """

    def _chart_correlation_heatmap(self, df_trend, df_sales) -> str | None:
        if df_sales.empty:
            return None

        daily_sales = df_sales.groupby(["sale_date", "brand"])["revenue"].sum().reset_index()
        daily_trend = df_trend.groupby(["trend_date", "brand", "source"])["trend_value"].mean().reset_index()

        brands = sorted(df_trend["brand"].unique())
        sources = sorted(df_trend["source"].unique())
        data = np.full((len(brands), len(sources)), np.nan)

        for i, brand in enumerate(brands):
            b_sales = daily_sales[daily_sales["brand"] == brand].set_index("sale_date")["revenue"]
            for j, source in enumerate(sources):
                b_trend = daily_trend[
                    (daily_trend["brand"] == brand) & (daily_trend["source"] == source)
                ].set_index("trend_date")["trend_value"]
                common = b_sales.index.intersection(b_trend.index)
                if len(common) >= 3:
                    r, _ = stats.pearsonr(b_trend.loc[common].values, b_sales.loc[common].values)
                    data[i, j] = r

        if np.all(np.isnan(data)):
            return None

        fig, ax = plt.subplots(figsize=(7, 3.5))
        im = ax.imshow(data, cmap="RdYlGn", aspect="auto", vmin=-1, vmax=1)

        source_labels = {"google_trends": "Google Trends", "naver_datalab": "Naver DataLab"}
        ax.set_xticks(range(len(sources)))
        ax.set_xticklabels([source_labels.get(s, s) for s in sources], fontsize=10)
        ax.set_yticks(range(len(brands)))
        ax.set_yticklabels([BRAND_LABELS.get(b, b) for b in brands], fontsize=10)
        ax.spines[:].set_visible(False)
        ax.tick_params(length=0)

        for i in range(len(brands)):
            for j in range(len(sources)):
                val = data[i, j]
                if not np.isnan(val):
                    c = "white" if abs(val) > 0.5 else _SLATE["text"]
                    ax.text(j, i, f"{val:.3f}", ha="center", va="center", fontsize=12, fontweight="bold", color=c)

        ax.set_title("트렌드-매출 상관계수 (Pearson r)", fontsize=12, fontweight="bold", color=_SLATE["text"], pad=12)
        cbar = fig.colorbar(im, ax=ax, shrink=0.8, aspect=20)
        cbar.outline.set_visible(False)
        plt.tight_layout()
        return _fig_to_base64(fig)

    def _chart_lead_lag(self, df_trend, df_sales) -> tuple[str | None, dict]:
        results = {}
        if df_sales.empty:
            return None, results

        daily_sales = df_sales.groupby(["sale_date", "brand"])["revenue"].sum().reset_index()
        daily_trend = df_trend.groupby(["trend_date", "brand"])["trend_value"].mean().reset_index()

        for brand in sorted(df_trend["brand"].unique()):
            b_sales = daily_sales[daily_sales["brand"] == brand].sort_values("sale_date")
            b_trend = daily_trend[daily_trend["brand"] == brand].sort_values("trend_date")
            if len(b_sales) < 5 or len(b_trend) < 5:
                continue
            sales_ts = b_sales.set_index("sale_date")["revenue"]
            trend_ts = b_trend.set_index("trend_date")["trend_value"]
            lag_corrs = {}
            best_lag, best_corr = 0, -1
            for lag in range(-7, 8):
                shifted = trend_ts.copy()
                shifted.index = shifted.index + pd.Timedelta(days=lag)
                common = sales_ts.index.intersection(shifted.index)
                if len(common) < 3:
                    continue
                r, _ = stats.pearsonr(shifted.loc[common].values, sales_ts.loc[common].values)
                lag_corrs[lag] = r
                if abs(r) > abs(best_corr):
                    best_corr = r
                    best_lag = lag
            results[brand] = {"best_lag": best_lag, "best_corr": best_corr, "lags": lag_corrs}

        if not results:
            return None, results

        n = len(results)
        fig, axes = plt.subplots(1, n, figsize=(5 * n, 3))
        if n == 1:
            axes = [axes]

        for ax, brand in zip(axes, sorted(results.keys())):
            label = BRAND_LABELS.get(brand, brand)
            color = BRAND_COLORS.get(brand, "#475569")
            lag_data = results[brand]["lags"]
            best_lag = results[brand]["best_lag"]
            if not lag_data:
                continue
            lags = sorted(lag_data.keys())
            corrs = [lag_data[l] for l in lags]
            bar_colors = [color if l == best_lag else "#e2e8f0" for l in lags]
            ax.bar(lags, corrs, color=bar_colors, width=0.7, edgecolor="none")
            ax.axhline(y=0, color=_SLATE["grid"], linewidth=0.8)
            ax.axvline(x=0, color="#f87171", linewidth=0.8, linestyle="--", alpha=0.5)
            ax.set_title(f"{label}", fontsize=11, fontweight="bold", color=_SLATE["text"])
            ax.set_xlabel("Lag (일)", fontsize=9, color=_SLATE["muted"])
            ax.set_ylabel("Pearson r", fontsize=9, color=_SLATE["muted"])
            ax.set_ylim(-1, 1)
            _apply_chart_style(ax)

        fig.suptitle("선행 지표 분석 (Cross-Correlation)", fontsize=12, fontweight="bold", color=_SLATE["text"], y=1.02)
        plt.tight_layout()
        return _fig_to_base64(fig), results

    def _chart_peak_season(self, df_trend) -> tuple[str | None, dict]:
        brands = sorted(df_trend["brand"].unique())
        if not brands:
            return None, {}

        results = {}
        fig, axes = plt.subplots(len(brands), 1, figsize=(10, 3 * len(brands)), sharex=True)
        if len(brands) == 1:
            axes = [axes]

        for ax, brand in zip(axes, brands):
            label = BRAND_LABELS.get(brand, brand)
            color = BRAND_COLORS.get(brand, "#475569")
            brand_data = df_trend[df_trend["brand"] == brand]
            daily_avg = brand_data.groupby("trend_date")["trend_value"].mean().sort_index()
            if daily_avg.empty:
                continue

            threshold = daily_avg.quantile(0.75)
            peak_dates = daily_avg[daily_avg > threshold].index.tolist()

            ax.fill_between(daily_avg.index, daily_avg.values, alpha=0.15, color=color)
            ax.plot(daily_avg.index, daily_avg.values, color=color, linewidth=2)
            ax.axhline(y=threshold, color="#f87171", linewidth=1, linestyle="--", alpha=0.5)
            ax.set_ylabel("트렌드", fontsize=9, color=_SLATE["muted"])
            ax.set_title(f"{label}", fontsize=11, fontweight="bold", color=_SLATE["text"])
            ax.set_ylim(0, 100)
            _apply_chart_style(ax)

            periods = self._group_peak_periods(peak_dates) if peak_dates else []
            for p in periods:
                ax.axvspan(p["start"], p["end"], alpha=0.08, color="#f87171")
            results[brand] = periods

        axes[-1].tick_params(axis="x", rotation=45)
        fig.suptitle("성수기 탐지 (75th percentile 초과)", fontsize=12, fontweight="bold", color=_SLATE["text"], y=1.01)
        plt.tight_layout()
        return _fig_to_base64(fig), results

    @staticmethod
    def _group_peak_periods(peak_dates: list) -> list[dict]:
        periods = []
        if not peak_dates:
            return periods
        current_start = peak_dates[0]
        current_end = peak_dates[0]
        for date in peak_dates[1:]:
            if (date - current_end).days <= 2:
                current_end = date
            else:
                periods.append({"start": current_start, "end": current_end, "days": (current_end - current_start).days + 1})
                current_start = date
                current_end = date
        periods.append({"start": current_start, "end": current_end, "days": (current_end - current_start).days + 1})
        return periods

    # ==================== 섹션 4: 채널 믹스 & 요일 (2열) ====================

    def _build_channel_section(self, df_sales: pd.DataFrame) -> str:
        if df_sales.empty:
            return '<div class="card"><div class="card-header"><h3>채널 믹스 & 요일 패턴</h3></div><p class="no-data">매출 데이터 없음</p></div>'

        mix_b64 = self._chart_channel_mix(df_sales)
        heat_b64 = self._chart_weekday_heatmap(df_sales)

        left = f'<img src="data:image/png;base64,{mix_b64}" class="chart-img">' if mix_b64 else '<p class="no-data">데이터 부족</p>'
        right = f'<img src="data:image/png;base64,{heat_b64}" class="chart-img">' if heat_b64 else '<p class="no-data">데이터 부족</p>'

        return f"""
        <div class="grid-2">
            <div class="card">
                <div class="card-header"><h3>채널 비중 추이</h3><p class="card-sub">3일 이동평균, 브랜드별</p></div>
                {left}
            </div>
            <div class="card">
                <div class="card-header"><h3>요일별 매출 히트맵</h3><p class="card-sub">브랜드 x 요일 평균</p></div>
                {right}
            </div>
        </div>
        """

    def _chart_channel_mix(self, df_sales) -> str | None:
        brands = sorted(df_sales["brand"].unique())
        if not brands:
            return None
        fig, axes = plt.subplots(1, len(brands), figsize=(6 * len(brands), 4))
        if len(brands) == 1:
            axes = [axes]
        for ax, brand in zip(axes, brands):
            brand_df = df_sales[df_sales["brand"] == brand].copy()
            label = BRAND_LABELS.get(brand, brand)
            pivot = brand_df.pivot_table(index="sale_date", columns="channel", values="revenue", aggfunc="sum", fill_value=0)
            row_totals = pivot.sum(axis=1)
            pivot_pct = pivot.div(row_totals.replace(0, np.nan), axis=0).fillna(0) * 100
            pivot_smooth = pivot_pct.rolling(3, min_periods=1).mean()
            channels = [c for c in CHANNEL_ORDER if c in pivot_smooth.columns]
            ax.stackplot(
                pivot_smooth.index,
                [pivot_smooth[ch].values for ch in channels],
                labels=[CHANNEL_LABELS.get(ch, ch) for ch in channels],
                colors=[CHANNEL_COLORS.get(ch, "#94a3b8") for ch in channels],
                alpha=0.8,
            )
            ax.set_title(f"{label}", fontsize=11, fontweight="bold", color=_SLATE["text"])
            ax.set_ylabel("비중 (%)", fontsize=9, color=_SLATE["muted"])
            ax.set_ylim(0, 100)
            ax.legend(loc="upper left", fontsize=7, framealpha=0.9)
            ax.tick_params(axis="x", rotation=45)
            _apply_chart_style(ax)
        plt.tight_layout()
        return _fig_to_base64(fig)

    def _chart_weekday_heatmap(self, df_sales) -> str | None:
        df = df_sales.copy()
        df["day_of_week"] = df["sale_date"].dt.dayofweek
        heatmap_data = df.groupby(["brand", "day_of_week"])["revenue"].mean().unstack(fill_value=0)
        if heatmap_data.empty:
            return None
        brands = sorted(heatmap_data.index)
        data = heatmap_data.loc[brands].values / 10000

        fig, ax = plt.subplots(figsize=(8, 3.5))
        im = ax.imshow(data, cmap="YlOrRd", aspect="auto")
        ax.set_xticks(range(7))
        ax.set_xticklabels(WEEKDAY_KR, fontsize=10)
        ax.set_yticks(range(len(brands)))
        ax.set_yticklabels([BRAND_LABELS.get(b, b) for b in brands], fontsize=10)
        ax.spines[:].set_visible(False)
        ax.tick_params(length=0)

        for i in range(len(brands)):
            for j in range(7):
                val = data[i, j]
                c = "white" if val > data.max() * 0.6 else _SLATE["text"]
                ax.text(j, i, f"₩{val:,.0f}만", ha="center", va="center", fontsize=9, color=c, fontweight="bold")

        ax.set_title("브랜드별 요일 평균 매출", fontsize=12, fontweight="bold", color=_SLATE["text"], pad=12)
        cbar = fig.colorbar(im, ax=ax, shrink=0.8, aspect=20)
        cbar.outline.set_visible(False)
        plt.tight_layout()
        return _fig_to_base64(fig)

    # ==================== 섹션 5: 광고 퍼포먼스 ====================

    def _build_ad_performance_section(self, df_sales: pd.DataFrame) -> str:
        """광고 퍼포먼스 섹션: ROAS 테이블 + 기회 요약"""
        if df_sales.empty:
            return '<div class="card"><div class="card-header"><h3>광고 퍼포먼스</h3></div><p class="no-data">매출 데이터 없음</p></div>'

        # 채널별 ROAS 계산
        records = []
        for brand in sorted(df_sales["brand"].unique()):
            brand_df = df_sales[df_sales["brand"] == brand]
            for channel in sorted(brand_df["channel"].unique()):
                ch_df = brand_df[brand_df["channel"] == channel]
                avg_ad = ch_df["ad_spend"].mean()
                avg_rev = ch_df["revenue"].mean()
                avg_visitors = ch_df["visitors"].mean() if "visitors" in ch_df.columns else 0
                roas = avg_rev / avg_ad if avg_ad > 0 else 0
                cpc = avg_ad / avg_visitors if avg_visitors > 0 else 0
                roi_pct = ((avg_rev - avg_ad) / avg_ad * 100) if avg_ad > 0 else 0

                if roas >= 7.0:
                    grade = "S"
                elif roas >= 5.5:
                    grade = "A"
                elif roas >= 4.0:
                    grade = "B"
                else:
                    grade = "C"

                records.append({
                    "brand": brand, "channel": channel,
                    "roas": roas, "cpc": cpc, "roi_pct": roi_pct,
                    "grade": grade, "avg_ad": avg_ad, "avg_rev": avg_rev,
                })

        records.sort(key=lambda x: x["roas"], reverse=True)

        # ROAS 테이블
        grade_badge = {"S": "badge-up", "A": "badge-up", "B": "badge-flat", "C": "badge-down"}
        rows = []
        for i, r in enumerate(records[:10], 1):
            label = BRAND_LABELS.get(r["brand"], r["brand"])
            ch_label = CHANNEL_LABELS.get(r["channel"], r["channel"])
            color = BRAND_COLORS.get(r["brand"], "#475569")
            badge_cls = grade_badge.get(r["grade"], "badge-flat")
            rows.append(f"""
            <tr>
                <td class="td-rank">{i}</td>
                <td class="td-product"><span class="brand-pill" style="background:{color};">{label}</span>{ch_label}</td>
                <td class="td-num"><span class="badge {badge_cls}">{r['grade']}</span> {r['roas']:.1f}</td>
                <td class="td-num">₩{r['cpc']:,.0f}</td>
                <td class="td-num">{r['roi_pct']:.0f}%</td>
            </tr>
            """)

        # 기회 요약 카드
        avg_spend = np.mean([r["avg_ad"] for r in records]) if records else 0
        scale_up = [r for r in records if r["roas"] >= 7.0 and r["avg_ad"] < avg_spend]
        improve = [r for r in records if r["roas"] < 4.0 and r["avg_ad"] > avg_spend]

        signal_cards = []
        if scale_up:
            r = scale_up[0]
            label = BRAND_LABELS.get(r["brand"], r["brand"])
            ch_label = CHANNEL_LABELS.get(r["channel"], r["channel"])
            signal_cards.append(self._signal_card(
                "스케일업 기회", f"{label} {ch_label}: ROAS {r['roas']:.1f}이나 광고비 낮음",
                "emerald", "trending-up",
            ))
        if improve:
            r = improve[0]
            label = BRAND_LABELS.get(r["brand"], r["brand"])
            ch_label = CHANNEL_LABELS.get(r["channel"], r["channel"])
            signal_cards.append(self._signal_card(
                "효율 개선 필요", f"{label} {ch_label}: ROAS {r['roas']:.1f}, 광고비 높음",
                "rose", "alert",
            ))
        if not signal_cards:
            signal_cards.append(self._signal_card(
                "전체 효율 양호", "모든 채널 ROAS 적정 범위",
                "slate", "info",
            ))

        return f"""
        <div class="grid-3-1">
            <div class="card">
                <div class="card-header">
                    <div>
                        <h3>광고 퍼포먼스</h3>
                        <p class="card-sub">채널별 ROAS 효율 등급 (S/A/B/C), CPC, ROI%</p>
                    </div>
                </div>
                <table class="data-table">
                    <thead><tr>
                        <th class="th-rank">#</th><th>채널</th><th class="th-num">ROAS</th><th class="th-num">CPC</th><th class="th-num">ROI</th>
                    </tr></thead>
                    <tbody>{"".join(rows)}</tbody>
                </table>
            </div>
            <div class="card">
                <div class="card-header"><h3>광고 기회</h3></div>
                {"".join(signal_cards)}
            </div>
        </div>
        """

    # ==================== 섹션 6+7: 제품 테이블 + 액션 추천 (2열) ====================

    def _build_products_table(self, top_products: list[dict]) -> str:
        if not top_products:
            return """
            <div class="card">
                <div class="card-header"><h3>매출 Top 5 제품</h3></div>
                <p class="no-data">제품 데이터가 없습니다.</p>
            </div>
            """

        rows = []
        for i, p in enumerate(top_products[:5], 1):
            brand = p.get("brand", "")
            label = BRAND_LABELS.get(brand, brand)
            color = BRAND_COLORS.get(brand, "#475569")
            name = p.get("product_name", "")
            revenue = float(p.get("daily_revenue", 0))
            rating = float(p.get("avg_rating", 0))
            stars = "★" * int(round(rating)) + "☆" * (5 - int(round(rating)))

            rows.append(f"""
            <tr>
                <td class="td-rank">{i}</td>
                <td class="td-product"><span class="brand-pill" style="background:{color};">{label}</span>{name}</td>
                <td class="td-num">₩{revenue:,.0f}</td>
                <td class="td-rating">{stars} <span class="rating-num">{rating:.1f}</span></td>
            </tr>
            """)

        return f"""
        <div class="card">
            <div class="card-header"><h3>매출 Top 5 제품</h3></div>
            <table class="data-table">
                <thead><tr>
                    <th class="th-rank">#</th><th>제품</th><th class="th-num">일 매출</th><th>평점</th>
                </tr></thead>
                <tbody>{"".join(rows)}</tbody>
            </table>
        </div>
        """

    def _build_actions(self, df_sales: pd.DataFrame, df_trend: pd.DataFrame) -> str:
        """인사이트 스토리텔링: 발견 → 근거 → 제안 → 효과 4단계 구조"""
        actions = []

        if not df_sales.empty:
            df = df_sales.copy()
            df["day_of_week"] = df["sale_date"].dt.dayofweek

            # 브랜드별 전체 채널 ROAS 순위 계산 (발견 근거용)
            channel_stats = []
            for brand in sorted(df["brand"].unique()):
                brand_df = df[df["brand"] == brand]
                for channel in brand_df["channel"].unique():
                    ch_df = brand_df[brand_df["channel"] == channel]
                    avg_ad = ch_df["ad_spend"].mean()
                    avg_rev = ch_df["revenue"].mean()
                    roas = avg_rev / avg_ad if avg_ad > 0 else 0
                    avg_visitors = ch_df["visitors"].mean() if "visitors" in ch_df.columns else 0
                    avg_cr = ch_df["conversion_rate"].mean() if "conversion_rate" in ch_df.columns else 0
                    cpc = avg_ad / avg_visitors if avg_visitors > 0 else 0
                    channel_stats.append({
                        "brand": brand, "channel": channel, "roas": roas,
                        "avg_ad": avg_ad, "avg_rev": avg_rev, "avg_visitors": avg_visitors,
                        "avg_cr": avg_cr, "cpc": cpc, "avg_orders": ch_df["orders"].mean(),
                    })
            channel_stats.sort(key=lambda x: x["roas"], reverse=True)

            for brand in sorted(df["brand"].unique()):
                brand_df = df[df["brand"] == brand]
                label = BRAND_LABELS.get(brand, brand)
                ch_rev = brand_df.groupby("channel")["revenue"].sum()
                total = ch_rev.sum()
                if total == 0:
                    continue

                top_ch = ch_rev.idxmax()
                top_pct = ch_rev[top_ch] / total * 100

                # 마케팅 스토리텔링: 쿠팡 ROAS 우수
                if top_ch == "coupang" and top_pct > 35:
                    cs = next((c for c in channel_stats if c["brand"] == brand and c["channel"] == "coupang"), None)
                    if cs and cs["roas"] > 5:
                        rank = [i for i, c in enumerate(channel_stats, 1) if c["brand"] == brand or c["channel"] == "coupang"]
                        roas_rank = next((i for i, c in enumerate(channel_stats, 1) if c["brand"] == brand and c["channel"] == "coupang"), 0)
                        increase_amt = cs["avg_ad"] * 0.15
                        expected_orders = cs["avg_orders"] * 0.12
                        monthly_revenue = expected_orders * (cs["avg_rev"] / cs["avg_orders"]) * 30 if cs["avg_orders"] > 0 else 0
                        story = (
                            f"<b>[발견]</b> {label} 쿠팡 ROAS {cs['roas']:.1f} (전체 채널 중 {roas_rank}위)<br>"
                            f"<b>[근거]</b> 30일 평균 전환율 {cs['avg_cr']:.2f}%, 일 방문자 {cs['avg_visitors']:,.0f}명, CPC ₩{cs['cpc']:,.0f}<br>"
                            f"<b>[제안]</b> 광고비 15% 증액 (₩{cs['avg_ad']/1000:,.0f}K → ₩{(cs['avg_ad']+increase_amt)/1000:,.0f}K)<br>"
                            f"<b>[효과]</b> 예상 주문 +{expected_orders:.0f}건/일, 월 매출 +₩{monthly_revenue/10000:,.0f}만 (ROAS 유지 가정)"
                        )
                        actions.append(("marketing", story))

                # 프로모션 스토리텔링: 요일 패턴
                daily_orders = brand_df.groupby("day_of_week")["orders"].sum()
                if not daily_orders.empty:
                    best_day = daily_orders.idxmax()
                    if best_day < 5:
                        total_orders = daily_orders.sum()
                        best_pct = daily_orders[best_day] / total_orders * 100 if total_orders > 0 else 0
                        daily_rev = brand_df.groupby("day_of_week")["revenue"].sum()
                        best_day_rev = daily_rev[best_day] if best_day in daily_rev.index else 0
                        story = (
                            f"<b>[발견]</b> {label} {WEEKDAY_KR[best_day]}요일 주문 집중 (전체의 {best_pct:.0f}%)<br>"
                            f"<b>[근거]</b> {WEEKDAY_KR[best_day]}요일 평균 매출 ₩{best_day_rev/10000/len(brand_df['sale_date'].unique())*7:,.0f}만, 주문 {daily_orders[best_day]/len(brand_df['sale_date'].unique())*7:,.0f}건<br>"
                            f"<b>[제안]</b> {WEEKDAY_KR[max(0, best_day-1)]}요일 쿠팡 딜/네이버 특가 사전 등록<br>"
                            f"<b>[효과]</b> 피크 타이밍 노출 극대화 → 전환율 +0.1~0.3%p 개선 기대"
                        )
                        actions.append(("promo", story))

                # 채널 스토리텔링: 자사몰 ROAS
                own_df = brand_df[brand_df["channel"] == "own_mall"]
                if not own_df.empty:
                    own_rev = own_df["revenue"].sum()
                    own_ad = own_df["ad_spend"].sum()
                    own_roas = own_rev / own_ad if own_ad > 0 else 0
                    if own_roas > 7:
                        own_share = own_rev / total * 100
                        own_avg_orders = own_df["orders"].mean()
                        story = (
                            f"<b>[발견]</b> {label} 자사몰 ROAS {own_roas:.1f} (채널 중 최고 효율)<br>"
                            f"<b>[근거]</b> 매출 비중 {own_share:.1f}%, 일 평균 주문 {own_avg_orders:.0f}건, 마진율 우위<br>"
                            f"<b>[제안]</b> 자사몰 전용 적립금(5%) + 무료배송 혜택 강화<br>"
                            f"<b>[효과]</b> 자사몰 비중 +3~5%p → 채널 수수료 절감 + 고객 데이터 확보"
                        )
                        actions.append(("channel", story))

        # 트렌드 스토리텔링
        if not df_trend.empty and not df_sales.empty:
            daily_sales = df_sales.groupby(["sale_date", "brand"])["revenue"].sum().reset_index()
            daily_trend = df_trend.groupby(["trend_date", "brand"])["trend_value"].mean().reset_index()
            for brand in sorted(df_trend["brand"].unique()):
                label = BRAND_LABELS.get(brand, brand)
                b_s = daily_sales[daily_sales["brand"] == brand].set_index("sale_date")["revenue"]
                b_t = daily_trend[daily_trend["brand"] == brand].set_index("trend_date")["trend_value"]
                common = b_s.index.intersection(b_t.index)
                if len(common) >= 3:
                    r, p = stats.pearsonr(b_t.loc[common].values, b_s.loc[common].values)
                    if r > 0.5 and p < 0.05:
                        avg_trend = b_t.loc[common].mean()
                        recent_trend = b_t.loc[common].tail(3).mean()
                        trend_direction = "상승" if recent_trend > avg_trend else "하락"
                        story = (
                            f"<b>[발견]</b> {label} 검색 트렌드-매출 강한 상관 (r={r:.2f}, p={p:.3f})<br>"
                            f"<b>[근거]</b> 최근 3일 트렌드 {trend_direction} ({avg_trend:.0f} → {recent_trend:.0f}), 통계적 유의<br>"
                            f"<b>[제안]</b> 검색량 급증 감지 시 광고비 즉시 20% 증액<br>"
                            f"<b>[효과]</b> 트렌드 선행 구간 포착 → 경쟁사 대비 노출 우위 확보"
                        )
                        actions.append(("trend", story))

        if not actions:
            return '<div class="card"><div class="card-header"><h3>비즈니스 액션 추천</h3></div><p class="no-data">데이터 축적 후 추천 가능</p></div>'

        tag_styles = {
            "marketing": ("마케팅", "tag-marketing"),
            "promo": ("프로모션", "tag-promo"),
            "channel": ("채널", "tag-channel"),
            "trend": ("트렌드", "tag-trend"),
        }

        rows = []
        for i, (tag_key, text) in enumerate(actions[:8], 1):
            tag_label, tag_cls = tag_styles.get(tag_key, ("기타", "tag-slate"))
            rows.append(f"""
            <tr>
                <td class="td-rank">{i}</td>
                <td><span class="action-pill {tag_cls}">{tag_label}</span></td>
                <td class="td-action">{text}</td>
            </tr>
            """)

        return f"""
        <div class="card">
            <div class="card-header">
                <h3>비즈니스 액션 추천</h3>
                <p class="card-sub">발견 → 근거 → 제안 → 효과 스토리텔링</p>
            </div>
            <table class="data-table">
                <thead><tr><th class="th-rank">#</th><th>구분</th><th>추천 내용</th></tr></thead>
                <tbody>{"".join(rows)}</tbody>
            </table>
        </div>
        """

    # ==================== HTML 조립 ====================

    def _assemble_html(self, header, kpi_cards, trend, channel, ad_perf, products, actions) -> str:
        gen_time = datetime.now().strftime("%Y-%m-%d %H:%M")

        return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>앳홈 KPI 대시보드</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
:root {{
    --slate-50: #f8fafc; --slate-100: #f1f5f9; --slate-200: #e2e8f0;
    --slate-300: #cbd5e1; --slate-400: #94a3b8; --slate-500: #64748b;
    --slate-600: #475569; --slate-700: #334155; --slate-800: #1e293b;
    --slate-900: #0f172a;
    --emerald-50: #ecfdf5; --emerald-100: #d1fae5; --emerald-500: #10b981; --emerald-600: #059669; --emerald-700: #047857;
    --amber-50: #fffbeb; --amber-100: #fef3c7; --amber-500: #f59e0b; --amber-600: #d97706; --amber-700: #b45309;
    --rose-50: #fff1f2; --rose-100: #ffe4e6; --rose-500: #f43f5e; --rose-600: #e11d48;
    --radius: 16px;
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
    font-family: 'Inter', 'Malgun Gothic', -apple-system, sans-serif;
    background: var(--slate-50);
    color: var(--slate-700);
    line-height: 1.6;
    -webkit-font-smoothing: antialiased;
}}

/* === Header === */
.header {{
    background: white;
    border-bottom: 1px solid var(--slate-200);
    position: sticky;
    top: 0;
    z-index: 50;
}}
.header-inner {{
    max-width: 1600px;
    margin: 0 auto;
    padding: 16px 32px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 16px;
}}
.header-left {{
    display: flex;
    align-items: center;
    gap: 12px;
}}
.logo-icon {{
    background: var(--slate-600);
    color: white;
    padding: 8px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
}}
.header h1 {{
    font-size: 18px;
    font-weight: 800;
    color: var(--slate-800);
    letter-spacing: -0.02em;
}}
.header-right {{
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
}}
.header-pill {{
    display: flex;
    align-items: center;
    gap: 6px;
    background: var(--slate-100);
    border: 1px solid var(--slate-200);
    border-radius: 12px;
    padding: 6px 14px;
    font-size: 13px;
    font-weight: 500;
    color: var(--slate-500);
}}
.header-pill svg {{ color: var(--slate-400); }}
.header-stat {{
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 0 12px;
    border-left: 1px solid var(--slate-200);
}}
.header-stat:first-of-type {{ border-left: none; padding-left: 16px; }}
.header-stat-label {{
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--slate-400);
}}
.header-stat-value {{
    font-size: 15px;
    font-weight: 800;
    color: var(--slate-800);
}}

/* === Layout === */
main {{
    max-width: 1600px;
    margin: 0 auto;
    padding: 32px;
}}
.kpi-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 20px;
    margin-bottom: 28px;
}}
.grid-3-1 {{
    display: grid;
    grid-template-columns: 3fr 1fr;
    gap: 20px;
    margin-bottom: 28px;
}}
.grid-2 {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    margin-bottom: 28px;
}}
.grid-2-bottom {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    margin-bottom: 28px;
}}
@media (max-width: 1024px) {{
    .grid-3-1 {{ grid-template-columns: 1fr; }}
    .grid-2 {{ grid-template-columns: 1fr; }}
    .grid-2-bottom {{ grid-template-columns: 1fr; }}
    main {{ padding: 16px; }}
}}

/* === Card === */
.card {{
    background: white;
    border-radius: var(--radius);
    border: 1px solid var(--slate-100);
    box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    padding: 28px;
    transition: box-shadow 0.2s;
}}
.card:hover {{ box-shadow: 0 4px 12px rgba(0,0,0,0.06); }}
.card-header {{
    margin-bottom: 20px;
}}
.card-header h3 {{
    font-size: 16px;
    font-weight: 700;
    color: var(--slate-800);
}}
.card-sub {{
    font-size: 13px;
    font-weight: 500;
    color: var(--slate-400);
    margin-top: 2px;
}}

/* === KPI Cards === */
.kpi-card {{
    background: white;
    border-radius: var(--radius);
    border: 1px solid var(--slate-100);
    box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    padding: 20px 24px;
    transition: box-shadow 0.2s;
}}
.kpi-card:hover {{ box-shadow: 0 4px 12px rgba(0,0,0,0.06); }}
.kpi-card-top {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 14px;
}}
.kpi-card-label {{
    font-size: 13px;
    font-weight: 600;
    color: var(--slate-500);
}}
.badge {{
    display: inline-flex;
    align-items: center;
    gap: 2px;
    font-size: 12px;
    font-weight: 700;
    padding: 3px 10px;
    border-radius: 999px;
}}
.badge-up {{ background: var(--emerald-50); color: var(--emerald-600); }}
.badge-down {{ background: var(--rose-50); color: var(--rose-500); }}
.badge-flat {{ background: var(--slate-100); color: var(--slate-500); }}
.kpi-card-body {{
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
}}
.kpi-card-value {{
    font-size: 26px;
    font-weight: 800;
    color: var(--slate-900);
    letter-spacing: -0.02em;
}}
.kpi-card-sub {{
    font-size: 12px;
    color: var(--slate-400);
    margin-top: 2px;
    font-weight: 500;
}}
.sparkline {{ flex-shrink: 0; }}

/* === Channel Bar === */
.ch-bar-wrap {{ margin-top: 14px; }}
.ch-bar {{
    display: flex;
    height: 6px;
    border-radius: 3px;
    overflow: hidden;
    background: var(--slate-100);
}}
.ch-bar > div {{ min-width: 4px; }}
.ch-legend {{
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    margin-top: 6px;
}}
.ch-legend-item {{
    font-size: 10px;
    font-weight: 600;
    color: var(--slate-500);
    display: flex;
    align-items: center;
    gap: 4px;
}}
.ch-dot {{
    width: 6px;
    height: 6px;
    border-radius: 50%;
    display: inline-block;
}}

/* === Signal Cards === */
.signal-card {{
    padding: 16px;
    border-radius: 12px;
    border: 1px solid transparent;
    margin-bottom: 12px;
}}
.signal-emerald {{ background: var(--emerald-50); border-color: var(--emerald-100); color: var(--emerald-700); }}
.signal-amber {{ background: var(--amber-50); border-color: var(--amber-100); color: var(--amber-700); }}
.signal-rose {{ background: var(--rose-50); border-color: var(--rose-100); color: var(--rose-600); }}
.signal-slate {{ background: var(--slate-50); border-color: var(--slate-200); color: var(--slate-600); }}
.signal-top {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;
}}
.signal-title {{
    font-size: 10px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}}
.signal-icon {{ opacity: 0.7; }}
.signal-body {{
    font-size: 13px;
    font-weight: 600;
    line-height: 1.5;
}}

/* === Chart === */
.chart-img {{
    display: block;
    max-width: 100%;
    height: auto;
    margin: 8px auto 16px;
    border-radius: 12px;
}}

/* === Data Table === */
.data-table {{
    width: 100%;
    border-collapse: collapse;
    text-align: left;
}}
.data-table thead tr {{
    border-bottom: 1px solid var(--slate-100);
    background: var(--slate-50);
}}
.data-table th {{
    padding: 12px 20px;
    font-size: 10px;
    font-weight: 800;
    color: var(--slate-400);
    text-transform: uppercase;
    letter-spacing: 0.1em;
}}
.data-table td {{
    padding: 14px 20px;
    font-size: 13px;
    font-weight: 500;
    color: var(--slate-700);
    border-bottom: 1px solid var(--slate-50);
}}
.data-table tbody tr:hover {{ background: rgba(248,250,252,0.5); }}
.th-rank, .td-rank {{ width: 48px; text-align: center; }}
.td-rank {{ font-weight: 700; color: var(--slate-400); }}
.th-num, .td-num {{ text-align: right; }}
.td-num {{ font-weight: 700; color: var(--slate-800); }}
.td-product {{ font-weight: 600; color: var(--slate-700); }}
.td-rating {{ color: #f59e0b; white-space: nowrap; }}
.td-action {{ font-weight: 500; line-height: 1.5; }}
.rating-num {{ color: var(--slate-400); font-size: 11px; margin-left: 4px; }}
.brand-pill {{
    display: inline-block;
    color: white;
    font-size: 10px;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 999px;
    margin-right: 6px;
    vertical-align: middle;
}}
.action-pill {{
    display: inline-block;
    font-size: 10px;
    font-weight: 800;
    padding: 3px 10px;
    border-radius: 999px;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}}
.tag-marketing {{ background: #fff7ed; color: #ea580c; }}
.tag-promo {{ background: #eff6ff; color: #2563eb; }}
.tag-channel {{ background: #f0fdf4; color: #16a34a; }}
.tag-trend {{ background: #faf5ff; color: #9333ea; }}
.tag-slate {{ background: var(--slate-100); color: var(--slate-600); }}

/* === No Data === */
.no-data {{
    color: var(--slate-400);
    text-align: center;
    padding: 32px;
    font-size: 13px;
    font-weight: 500;
}}

/* === Footer === */
.footer {{
    max-width: 1600px;
    margin: 0 auto;
    padding: 32px 32px 48px;
    border-top: 1px solid var(--slate-200);
    display: flex;
    justify-content: space-between;
    align-items: center;
}}
.footer-left {{
    font-size: 11px;
    font-weight: 700;
    color: var(--slate-400);
    text-transform: uppercase;
    letter-spacing: 0.15em;
}}
.footer-right {{
    font-size: 10px;
    font-weight: 800;
    color: var(--slate-300);
    text-transform: uppercase;
    letter-spacing: 0.2em;
}}
</style>
</head>
<body>

{header}

<main>
    {kpi_cards}

    {trend}

    {channel}

    {ad_perf}

    <div class="grid-2-bottom">
        {products}
        {actions}
    </div>
</main>

<footer class="footer">
    <span class="footer-left">데이터 기준일: {gen_time}</span>
    <span class="footer-right">&copy; 2026 Athome Intelligence</span>
</footer>

</body>
</html>"""
