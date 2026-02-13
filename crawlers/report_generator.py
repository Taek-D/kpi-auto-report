"""
주간/월간 요약 리포트 생성 모듈
Supabase RPC → Pandas DataFrame → Slack 포맷 텍스트 + matplotlib 차트
"""

import logging
from datetime import date, timedelta
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import pandas as pd

from .supabase_loader import SupabaseLoader

logger = logging.getLogger(__name__)

OUTPUT_DIR = Path(__file__).parent.parent / "output"

BRAND_LABELS = {
    "minix": ("미닉스", "🏠"),
    "thome": ("톰", "💆"),
    "protione": ("프로티원", "💪"),
}

BRAND_COLORS = {
    "minix": "#FF6B35",
    "thome": "#4A90D9",
    "protione": "#7ED321",
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


class WeeklyReportGenerator:
    """주간 요약 리포트 생성"""

    def __init__(self):
        self.loader = SupabaseLoader()

    def generate(self, end_date: date | None = None) -> str:
        """주간 요약 생성 → Slack 포맷 텍스트 반환"""
        if end_date is None:
            end_date = date.today() - timedelta(days=1)

        start_date = end_date - timedelta(days=6)

        data = self.loader.call_rpc(
            "get_weekly_summary",
            {"p_end_date": end_date.isoformat()},
        )

        if not data:
            return "[주간 리포트] 데이터가 없습니다."

        df = pd.DataFrame(data)

        lines = [
            f"📊 앳홈 주간 KPI 요약 | {start_date} ~ {end_date}",
            "",
            "브랜드별 주간 실적",
            "━" * 30,
        ]

        total_revenue = df["week_revenue"].sum()
        total_orders = df["week_orders"].sum()
        lines.append(f"💰 총 매출: ₩{total_revenue:,.0f}")
        lines.append(f"📦 총 주문: {total_orders:,}건")
        lines.append("")

        for _, row in df.iterrows():
            label, emoji = BRAND_LABELS.get(row["brand"], (row["brand"], "📌"))
            rev = row["week_revenue"]
            orders = row["week_orders"]
            wow = row["revenue_wow_pct"]
            wow_icon = "↑" if wow > 0 else "↓" if wow < 0 else "→"
            best_ch = row.get("best_channel", "")
            worst_ch = row.get("worst_channel", "")

            lines.append(f"{emoji} {label}")
            lines.append(f"  매출: ₩{rev:,.0f} (WoW {wow:+.1f}% {wow_icon})")
            lines.append(f"  주문: {orders:,}건 | ROAS: {row['week_roas']}")
            if best_ch:
                lines.append(f"  Best: {best_ch} / Worst: {worst_ch}")
            lines.append("")

        # 채널별 요약
        lines.append("채널별 매출 비중")
        lines.append("━" * 30)
        for _, row in df.iterrows():
            label, _ = BRAND_LABELS.get(row["brand"], (row["brand"], ""))
            breakdown = row.get("channel_breakdown", [])
            if isinstance(breakdown, list):
                ch_str = ", ".join(
                    f"{ch['channel']} {ch['share_pct']}%"
                    for ch in breakdown[:3]
                )
                lines.append(f"  {label}: {ch_str}")

        return "\n".join(lines)


class MonthlyReportGenerator:
    """월간 요약 리포트 생성 + 차트"""

    def __init__(self):
        self.loader = SupabaseLoader()

    def generate(self, year: int | None = None, month: int | None = None) -> str:
        """월간 요약 생성 → 텍스트 + 차트 파일 경로 반환"""
        today = date.today()
        if year is None:
            year = today.year
        if month is None:
            month = today.month

        data = self.loader.call_rpc(
            "get_monthly_summary",
            {"p_year": year, "p_month": month},
        )

        if not data:
            return f"[월간 리포트] {year}년 {month}월 데이터가 없습니다."

        df = pd.DataFrame(data)

        lines = [
            f"📊 앳홈 월간 KPI 요약 | {year}년 {month}월",
            "",
            "브랜드별 월간 실적",
            "━" * 30,
        ]

        total_revenue = df["month_revenue"].sum()
        total_orders = df["month_orders"].sum()
        lines.append(f"💰 총 매출: ₩{total_revenue:,.0f}")
        lines.append(f"📦 총 주문: {total_orders:,}건")
        lines.append("")

        for _, row in df.iterrows():
            label, emoji = BRAND_LABELS.get(row["brand"], (row["brand"], "📌"))
            rev = row["month_revenue"]
            orders = row["month_orders"]
            mom = row["revenue_mom_pct"]
            mom_icon = "↑" if mom > 0 else "↓" if mom < 0 else "→"

            lines.append(f"{emoji} {label}")
            lines.append(f"  매출: ₩{rev:,.0f} (MoM {mom:+.1f}% {mom_icon})")
            lines.append(f"  주문: {orders:,}건 | ROAS: {row['month_roas']}")
            lines.append("")

        # 차트 생성
        chart_path = self._plot_monthly_bar(df, year, month)
        if chart_path:
            lines.append(f"[차트] {chart_path}")

        return "\n".join(lines)

    def _plot_monthly_bar(self, df: pd.DataFrame, year: int, month: int) -> str | None:
        """브랜드별 월간 매출 bar chart"""
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        fig, ax = plt.subplots(figsize=(10, 6))

        brands = df["brand"].tolist()
        revenues = df["month_revenue"].astype(float).tolist()
        colors = [BRAND_COLORS.get(b, "#999999") for b in brands]
        labels = [BRAND_LABELS.get(b, (b, ""))[0] for b in brands]

        bars = ax.bar(labels, revenues, color=colors, edgecolor="white", width=0.6)

        for bar, rev in zip(bars, revenues):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(revenues) * 0.02,
                f"₩{rev / 10000:,.0f}만",
                ha="center",
                va="bottom",
                fontsize=11,
                fontweight="bold",
            )

        ax.set_title(f"앳홈 브랜드별 월간 매출 ({year}년 {month}월)", fontsize=14, fontweight="bold")
        ax.set_ylabel("매출 (원)")
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"₩{x / 10000:,.0f}만"))
        ax.grid(True, axis="y", alpha=0.3)
        plt.tight_layout()

        path = OUTPUT_DIR / "monthly_report.png"
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        logger.info(f"[리포트] 월간 차트 저장: {path}")
        return str(path)
