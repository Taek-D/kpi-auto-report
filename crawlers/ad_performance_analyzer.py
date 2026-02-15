"""
광고 퍼포먼스 분석 모듈
채널별 ROAS/CPC/ROI 효율 분석, 예산 재배분 시뮬레이션, 성장 기회 탐지.
brand_daily_sales 테이블의 ad_spend, roas, conversion_rate, visitors, revenue 활용.
"""

import logging
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import pandas as pd

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

GRADE_COLORS = {"S": "#10b981", "A": "#3b82f6", "B": "#f59e0b", "C": "#ef4444"}
GRADE_THRESHOLDS = {"S": 7.0, "A": 5.5, "B": 4.0}  # ROAS 기준


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
    """Clean chart style"""
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#e2e8f0")
    ax.spines["bottom"].set_color("#e2e8f0")
    ax.tick_params(colors="#94a3b8", labelsize=9)
    ax.grid(True, axis="y" if ax.get_subplotspec() else "both", color="#e2e8f0", linewidth=0.5, alpha=0.7)
    ax.set_axisbelow(True)


class AdPerformanceAnalyzer:
    """광고 퍼포먼스 분석기

    분석 항목:
    A. 채널별 광고 효율 (ROAS, CPC, ROI%, 효율 등급 S/A/B/C)
    B. 예산 재배분 시뮬레이션 (ROAS 가중 비례 배분)
    C. 성장 기회 탐지 (High ROAS + Low Spend = 스케일업)
    """

    def __init__(self):
        self.loader = SupabaseLoader()

    def run(self, days: int = 30) -> str:
        """전체 광고 퍼포먼스 분석 파이프라인"""
        raw_data = self.loader.fetch_brand_sales(days=days)
        if not raw_data:
            return "[광고 분석] 매출 데이터가 없습니다. Supabase 연결을 확인해주세요."

        df = pd.DataFrame(raw_data)
        df["sale_date"] = pd.to_datetime(df["sale_date"])
        for col in ["revenue", "orders", "ad_spend", "roas", "conversion_rate", "visitors"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        lines = [
            "📈 광고 퍼포먼스 분석",
            "=" * 55,
            "",
        ]

        # A. 채널별 광고 효율 분석
        efficiency = self._channel_efficiency(df)
        lines.extend(efficiency["lines"])

        # B. 예산 재배분 시뮬레이션
        simulation = self._budget_simulation(df, efficiency["data"])
        lines.extend(simulation["lines"])

        # C. 성장 기회 탐지
        opportunities = self._growth_opportunities(efficiency["data"])
        lines.extend(opportunities)

        # 차트 생성
        self._plot_roas_comparison(efficiency["data"])
        self._plot_budget_simulation(simulation["data"])
        self._plot_opportunity_matrix(efficiency["data"])

        lines.append("")
        lines.append("[차트] output/ad_roas_comparison.png - 브랜드x채널 ROAS 비교")
        lines.append("[차트] output/ad_budget_simulation.png - 현재 vs 최적 예산 배분")
        lines.append("[차트] output/ad_opportunity_matrix.png - ROAS vs 광고비 기회 매트릭스")

        return "\n".join(lines)

    # ========== A. 채널별 광고 효율 분석 ==========

    def _channel_efficiency(self, df: pd.DataFrame) -> dict:
        """브랜드 x 채널별 ROAS, CPC, ROI% 계산 + 효율 등급"""
        lines = [
            "💰 채널별 ROAS 랭킹",
            "━" * 50,
        ]

        records = []
        for brand in sorted(df["brand"].unique()):
            brand_df = df[df["brand"] == brand]
            for channel in sorted(brand_df["channel"].unique()):
                ch_df = brand_df[brand_df["channel"] == channel]

                avg_revenue = ch_df["revenue"].mean()
                avg_ad_spend = ch_df["ad_spend"].mean()
                avg_visitors = ch_df["visitors"].mean() if "visitors" in ch_df.columns else 0
                avg_orders = ch_df["orders"].mean()
                total_ad_spend = ch_df["ad_spend"].sum()

                roas = avg_revenue / avg_ad_spend if avg_ad_spend > 0 else 0
                cpc = avg_ad_spend / avg_visitors if avg_visitors > 0 else 0
                roi_pct = ((avg_revenue - avg_ad_spend) / avg_ad_spend * 100) if avg_ad_spend > 0 else 0

                # 효율 등급
                if roas >= GRADE_THRESHOLDS["S"]:
                    grade = "S"
                elif roas >= GRADE_THRESHOLDS["A"]:
                    grade = "A"
                elif roas >= GRADE_THRESHOLDS["B"]:
                    grade = "B"
                else:
                    grade = "C"

                records.append({
                    "brand": brand,
                    "channel": channel,
                    "avg_revenue": avg_revenue,
                    "avg_ad_spend": avg_ad_spend,
                    "total_ad_spend": total_ad_spend,
                    "avg_visitors": avg_visitors,
                    "avg_orders": avg_orders,
                    "roas": roas,
                    "cpc": cpc,
                    "roi_pct": roi_pct,
                    "grade": grade,
                })

        # ROAS 기준 내림차순 정렬
        records.sort(key=lambda x: x["roas"], reverse=True)

        for r in records:
            label = BRAND_LABELS.get(r["brand"], r["brand"])
            ch_label = CHANNEL_LABELS.get(r["channel"], r["channel"])
            lines.append(
                f"  [{r['grade']}등급] {label} {ch_label}: "
                f"ROAS {r['roas']:.1f} | CPC ₩{r['cpc']:,.0f} | ROI {r['roi_pct']:.0f}%"
            )

        lines.append("")
        return {"lines": lines, "data": records}

    # ========== B. 예산 재배분 시뮬레이션 ==========

    def _budget_simulation(self, df: pd.DataFrame, efficiency_data: list[dict]) -> dict:
        """ROAS 가중 비례 예산 재배분 시뮬레이션"""
        lines = [
            "📊 예산 재배분 시뮬레이션",
            "━" * 50,
        ]

        if not efficiency_data:
            lines.append("  데이터 부족으로 시뮬레이션 불가")
            lines.append("")
            return {"lines": lines, "data": {}}

        total_budget = sum(r["total_ad_spend"] for r in efficiency_data)
        current_revenue = sum(r["avg_revenue"] * (r["total_ad_spend"] / r["avg_ad_spend"])
                              if r["avg_ad_spend"] > 0 else 0 for r in efficiency_data)

        # ROAS 가중 비례 배분 (최소 10% 제약)
        total_roas = sum(max(r["roas"], 0.1) for r in efficiency_data)
        n_channels = len(efficiency_data)
        min_share = 0.10

        simulation = []
        for r in efficiency_data:
            current_share = r["total_ad_spend"] / total_budget if total_budget > 0 else 0
            roas_weight = max(r["roas"], 0.1) / total_roas
            optimal_share = max(roas_weight, min_share)
            simulation.append({**r, "current_share": current_share, "optimal_share": optimal_share})

        # 정규화: optimal_share 합이 1이 되도록
        total_optimal = sum(s["optimal_share"] for s in simulation)
        if total_optimal > 0:
            for s in simulation:
                s["optimal_share"] = s["optimal_share"] / total_optimal

        # 최적 배분 시 예상 매출 계산
        optimal_revenue = 0
        for s in simulation:
            optimal_budget = total_budget * s["optimal_share"]
            optimal_revenue += optimal_budget * s["roas"]
            s["optimal_budget"] = optimal_budget
            s["current_budget"] = s["total_ad_spend"]
            s["expected_revenue"] = optimal_budget * s["roas"]

        revenue_change = ((optimal_revenue / current_revenue - 1) * 100) if current_revenue > 0 else 0

        lines.append(f"  현재 총 광고비: ₩{total_budget:,.0f} → 예상 매출: ₩{current_revenue:,.0f}")
        lines.append(f"  최적 재배분 시: ₩{total_budget:,.0f} → 예상 매출: ₩{optimal_revenue:,.0f} ({'+' if revenue_change > 0 else ''}{revenue_change:.1f}%)")
        lines.append("")

        # 변동 큰 채널 상위 5개
        simulation.sort(key=lambda x: abs(x["optimal_share"] - x["current_share"]), reverse=True)
        lines.append("  주요 변동 (상위 5개):")
        for s in simulation[:5]:
            label = BRAND_LABELS.get(s["brand"], s["brand"])
            ch_label = CHANNEL_LABELS.get(s["channel"], s["channel"])
            current_pct = s["current_share"] * 100
            optimal_pct = s["optimal_share"] * 100
            change = optimal_pct - current_pct
            arrow = "↑" if change > 0 else "↓"
            lines.append(
                f"    {label} {ch_label}: {current_pct:.1f}% → {optimal_pct:.1f}% ({arrow}{abs(change):.1f}%p)"
            )

        lines.append("")
        return {
            "lines": lines,
            "data": {
                "simulation": simulation,
                "total_budget": total_budget,
                "current_revenue": current_revenue,
                "optimal_revenue": optimal_revenue,
                "revenue_change": revenue_change,
            },
        }

    # ========== C. 성장 기회 탐지 ==========

    def _growth_opportunities(self, efficiency_data: list[dict]) -> list[str]:
        """ROAS vs 광고비 기준 성장 기회 탐지"""
        lines = [
            "🎯 성장 기회",
            "━" * 50,
        ]

        if not efficiency_data:
            lines.append("  데이터 부족")
            lines.append("")
            return lines

        avg_spend = np.mean([r["total_ad_spend"] for r in efficiency_data])
        avg_roas = np.mean([r["roas"] for r in efficiency_data])

        scale_up = []  # High ROAS + Low Spend
        maintain = []  # OK
        improve = []   # Low ROAS + High Spend
        reduce = []    # Low ROAS + Low Spend

        avg_cr = np.mean([r.get("avg_orders", 0) / r.get("avg_visitors", 1) * 100
                          if r.get("avg_visitors", 0) > 0 else 0 for r in efficiency_data])

        for r in efficiency_data:
            label = BRAND_LABELS.get(r["brand"], r["brand"])
            ch_label = CHANNEL_LABELS.get(r["channel"], r["channel"])
            name = f"{label} {ch_label}"
            spend_share = r["total_ad_spend"] / sum(x["total_ad_spend"] for x in efficiency_data) * 100 if efficiency_data else 0
            cr = r.get("avg_orders", 0) / r.get("avg_visitors", 1) * 100 if r.get("avg_visitors", 0) > 0 else 0

            visitors = r.get("avg_visitors", 0)

            if r["roas"] >= 7.0 and r["total_ad_spend"] < avg_spend:
                scale_up.append((name, r["roas"], spend_share, cr, visitors))
            elif r["roas"] < 4.0 and r["total_ad_spend"] > avg_spend:
                improve.append((name, r["roas"], spend_share, cr, visitors))
            elif r["roas"] < 4.0:
                reduce.append((name, r["roas"], spend_share, cr, visitors))
            else:
                maintain.append((name, r["roas"], spend_share, cr, visitors))

        for name, roas, share, cr, _ in scale_up:
            lines.append(f"  🟢 스케일업: {name} (ROAS {roas:.1f}, 광고비 비중 {share:.1f}%, 전환율 {cr:.2f}%)")

        for name, roas, share, cr, _ in maintain:
            lines.append(f"  🟡 유지: {name} (ROAS {roas:.1f}, 적정 수준)")

        for name, roas, share, cr, visitors in improve:
            cr_gap = avg_cr - cr
            extra_orders = visitors * (cr_gap / 100) if cr_gap > 0 else 0
            lines.append(f"  🔴 개선필요: {name} (ROAS {roas:.1f}, 광고비 비중 {share:.1f}%, 전환율 {cr:.2f}% → 평균 수준 개선 시 +{extra_orders:.0f}건/일)")

        for name, roas, share, cr, _ in reduce:
            lines.append(f"  ⚪ 축소검토: {name} (ROAS {roas:.1f}, 광고비 비중 {share:.1f}%, 전환율 {cr:.2f}%)")

        if not any([scale_up, improve, reduce]):
            lines.append("  전체 채널 효율 적정 범위")

        lines.append("")
        return lines

    # ========== 차트 1: ROAS 비교 (수평 바) ==========

    def _plot_roas_comparison(self, efficiency_data: list[dict]) -> None:
        """브랜드x채널 ROAS 비교 수평 바 차트"""
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        if not efficiency_data:
            return

        data = sorted(efficiency_data, key=lambda x: x["roas"])

        labels = []
        values = []
        colors = []
        for r in data:
            label = BRAND_LABELS.get(r["brand"], r["brand"])
            ch_label = CHANNEL_LABELS.get(r["channel"], r["channel"])
            labels.append(f"{label} {ch_label}")
            values.append(r["roas"])
            colors.append(GRADE_COLORS[r["grade"]])

        fig, ax = plt.subplots(figsize=(10, max(5, len(data) * 0.5)))
        bars = ax.barh(range(len(labels)), values, color=colors, edgecolor="white", height=0.6)
        ax.set_yticks(range(len(labels)))
        ax.set_yticklabels(labels, fontsize=10)
        ax.set_xlabel("ROAS", fontsize=11, color="#64748b")
        ax.set_title("채널별 광고 효율 (ROAS 등급)", fontsize=13, fontweight="bold", color="#334155")

        # 등급 기준선
        for threshold, grade_label in [(7.0, "S"), (5.5, "A"), (4.0, "B")]:
            ax.axvline(x=threshold, color="#e2e8f0", linewidth=1, linestyle="--", alpha=0.8)
            ax.text(threshold, len(labels) - 0.5, f" {grade_label}", fontsize=9, color="#94a3b8", va="bottom")

        # 값 표시
        for bar, val in zip(bars, values):
            ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height() / 2,
                    f"{val:.1f}", va="center", fontsize=10, fontweight="bold", color="#334155")

        _apply_chart_style(ax)
        plt.tight_layout()

        path = OUTPUT_DIR / "ad_roas_comparison.png"
        fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        logger.info(f"[광고 분석] ROAS 비교 차트 저장: {path}")

    # ========== 차트 2: 예산 재배분 시뮬레이션 ==========

    def _plot_budget_simulation(self, sim_data: dict) -> None:
        """현재 vs 최적 예산 배분 Grouped bar + 예상 매출 변화"""
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        simulation = sim_data.get("simulation", [])
        if not simulation:
            return

        # 상위 8개만 표시 (공간 제약)
        simulation = sorted(simulation, key=lambda x: x["total_ad_spend"], reverse=True)[:8]

        labels = []
        current_vals = []
        optimal_vals = []
        for s in simulation:
            label = BRAND_LABELS.get(s["brand"], s["brand"])
            ch_label = CHANNEL_LABELS.get(s["channel"], s["channel"])
            labels.append(f"{label}\n{ch_label}")
            current_vals.append(s["current_budget"] / 10000)
            optimal_vals.append(s["optimal_budget"] / 10000)

        x = np.arange(len(labels))
        width = 0.35

        fig, ax = plt.subplots(figsize=(12, 6))
        bars1 = ax.bar(x - width / 2, current_vals, width, label="현재 배분", color="#94a3b8", alpha=0.8)
        bars2 = ax.bar(x + width / 2, optimal_vals, width, label="최적 배분", color="#3b82f6", alpha=0.8)

        ax.set_xticks(x)
        ax.set_xticklabels(labels, fontsize=9)
        ax.set_ylabel("광고비 (만원)", fontsize=11, color="#64748b")

        revenue_change = sim_data.get("revenue_change", 0)
        sign = "+" if revenue_change > 0 else ""
        ax.set_title(
            f"예산 재배분 시뮬레이션 (예상 매출 {sign}{revenue_change:.1f}%)",
            fontsize=13, fontweight="bold", color="#334155",
        )
        ax.legend(fontsize=10, loc="upper right")

        _apply_chart_style(ax)
        plt.tight_layout()

        path = OUTPUT_DIR / "ad_budget_simulation.png"
        fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        logger.info(f"[광고 분석] 예산 재배분 차트 저장: {path}")

    # ========== 차트 3: 기회 매트릭스 (산점도) ==========

    def _plot_opportunity_matrix(self, efficiency_data: list[dict]) -> None:
        """ROAS vs 광고비 산점도 (사분면: 스케일업/유지/개선/축소)"""
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        if not efficiency_data:
            return

        fig, ax = plt.subplots(figsize=(10, 8))

        avg_spend = np.mean([r["total_ad_spend"] for r in efficiency_data])
        avg_roas = np.mean([r["roas"] for r in efficiency_data])

        for r in efficiency_data:
            label = BRAND_LABELS.get(r["brand"], r["brand"])
            ch_label = CHANNEL_LABELS.get(r["channel"], r["channel"])
            color = BRAND_COLORS.get(r["brand"], "#475569")
            size = max(r["avg_revenue"] / 5000, 30)

            ax.scatter(r["total_ad_spend"] / 10000, r["roas"], s=size, color=color,
                       alpha=0.7, edgecolors="white", linewidth=1.5, zorder=5)
            ax.annotate(f"{label}\n{ch_label}", (r["total_ad_spend"] / 10000, r["roas"]),
                        fontsize=8, ha="center", va="bottom",
                        xytext=(0, 8), textcoords="offset points", color="#334155")

        # 사분면 기준선
        ax.axhline(y=avg_roas, color="#e2e8f0", linewidth=1.5, linestyle="--")
        ax.axvline(x=avg_spend / 10000, color="#e2e8f0", linewidth=1.5, linestyle="--")

        # 사분면 라벨
        x_min, x_max = ax.get_xlim()
        y_min, y_max = ax.get_ylim()
        label_alpha = 0.08
        # 1사분면 (High ROAS, High Spend) = 유지
        ax.fill_between([avg_spend / 10000, x_max], avg_roas, y_max, alpha=label_alpha, color="#3b82f6")
        ax.text(avg_spend / 10000 + (x_max - avg_spend / 10000) * 0.5, y_max - (y_max - avg_roas) * 0.1,
                "유지 (효율적)", ha="center", fontsize=11, fontweight="bold", color="#3b82f6", alpha=0.7)
        # 2사분면 (High ROAS, Low Spend) = 스케일업
        ax.fill_between([x_min, avg_spend / 10000], avg_roas, y_max, alpha=label_alpha, color="#10b981")
        ax.text(x_min + (avg_spend / 10000 - x_min) * 0.5, y_max - (y_max - avg_roas) * 0.1,
                "스케일업 기회", ha="center", fontsize=11, fontweight="bold", color="#10b981", alpha=0.7)
        # 3사분면 (Low ROAS, Low Spend) = 축소
        ax.fill_between([x_min, avg_spend / 10000], y_min, avg_roas, alpha=label_alpha, color="#94a3b8")
        ax.text(x_min + (avg_spend / 10000 - x_min) * 0.5, y_min + (avg_roas - y_min) * 0.1,
                "축소 검토", ha="center", fontsize=11, fontweight="bold", color="#94a3b8", alpha=0.7)
        # 4사분면 (Low ROAS, High Spend) = 개선 필요
        ax.fill_between([avg_spend / 10000, x_max], y_min, avg_roas, alpha=label_alpha, color="#ef4444")
        ax.text(avg_spend / 10000 + (x_max - avg_spend / 10000) * 0.5, y_min + (avg_roas - y_min) * 0.1,
                "효율 개선 필요", ha="center", fontsize=11, fontweight="bold", color="#ef4444", alpha=0.7)

        ax.set_xlabel("총 광고비 (만원)", fontsize=11, color="#64748b")
        ax.set_ylabel("ROAS", fontsize=11, color="#64748b")
        ax.set_title("광고 기회 매트릭스 (ROAS vs 광고비)", fontsize=13, fontweight="bold", color="#334155")

        # 브랜드 범례
        from matplotlib.lines import Line2D
        legend_elements = [
            Line2D([0], [0], marker="o", color="w", markerfacecolor=c, markersize=10, label=BRAND_LABELS[b])
            for b, c in BRAND_COLORS.items()
        ]
        ax.legend(handles=legend_elements, loc="upper right", fontsize=10)

        _apply_chart_style(ax)
        plt.tight_layout()

        path = OUTPUT_DIR / "ad_opportunity_matrix.png"
        fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        logger.info(f"[광고 분석] 기회 매트릭스 차트 저장: {path}")
