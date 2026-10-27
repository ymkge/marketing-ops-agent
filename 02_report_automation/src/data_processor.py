"""Data processor using pandas for ad performance aggregation and KPI calculation."""

import json
from pathlib import Path
from typing import Optional, Union
import numpy as np
import pandas as pd

from .models import AggregatedData, MetricSummary, ChannelSummary, DailyTrend


def _safe_div(numerator: Optional[float], denominator: Optional[float], multiplier: float = 1.0) -> Optional[float]:
    """ゼロ除算やNaN/Infを安全に防ぎ、Noneまたは数値を返却する"""
    if denominator is None or np.isnan(denominator) or denominator == 0:
        return None
    if numerator is None or np.isnan(numerator):
        return None
    val = (numerator / denominator) * multiplier
    if np.isinf(val) or np.isnan(val):
        return None
    return round(float(val), 2)


def calculate_metrics(cost: float, imp: int, clicks: int, cv: float, rev: float) -> MetricSummary:
    """合算値から加重平均KPI（CTR, CPC, CVR, CPA, ROAS）を算出"""
    ctr = _safe_div(clicks, imp, multiplier=100.0)      # %
    cpc = _safe_div(cost, clicks)                       # 円
    cvr = _safe_div(cv, clicks, multiplier=100.0)        # %
    cpa = _safe_div(cost, cv)                           # 円
    roas = _safe_div(rev, cost, multiplier=100.0)       # %

    return MetricSummary(
        cost=round(float(cost), 2),
        impressions=int(imp),
        clicks=int(clicks),
        conversions=round(float(cv), 2),
        revenue=round(float(rev), 2),
        ctr=ctr,
        cpc=cpc,
        cvr=cvr,
        cpa=cpa,
        roas=roas
    )


class DataProcessor:
    """広告配信実績のデータ加工・集計クラス"""

    def __init__(self, data_source: Union[str, Path, pd.DataFrame]):
        if isinstance(data_source, pd.DataFrame):
            self.df = data_source.copy()
        else:
            self.df = self._load_data(Path(data_source))
        self._clean_data()

    def _load_data(self, path: Path) -> pd.DataFrame:
        """CSVまたはJSONファイルからDataFrameを読み込む"""
        if not path.exists():
            raise FileNotFoundError(f"データファイルが見つかりません: {path}")

        if path.stat().st_size == 0:
            raise ValueError(f"データファイルが空です: {path}")

        suffix = path.suffix.lower()
        if suffix == ".csv":
            df = pd.read_csv(path)
        elif suffix == ".json":
            with open(path, "r", encoding="utf-8") as f:
                content = json.load(f)
            df = pd.DataFrame(content)
        else:
            raise ValueError(f"未対応のファイル形式です: {suffix} (.csv または .json のみ対応)")

        if df.empty:
            raise ValueError(f"データファイルに有効なレコードが含まれていません: {path}")

        return df

    def _clean_data(self):
        """カラム検証、型変換、クレンジング処理"""
        required_cols = {"date", "channel", "impressions", "clicks", "cost", "conversions"}
        missing_cols = required_cols - set(self.df.columns)
        if missing_cols:
            raise ValueError(f"必須カラムが不足しています: {missing_cols}")

        if "revenue" not in self.df.columns:
            self.df["revenue"] = 0.0

        # 日付パース（無効な日付行は除外）
        parsed_dates = pd.to_datetime(self.df["date"], errors="coerce")
        self.df = self.df[parsed_dates.notna()].copy()
        self.df["date"] = parsed_dates[parsed_dates.notna()].dt.strftime("%Y-%m-%d")

        # 文字列型数値（カンマや通貨記号）のクレンジング
        num_cols = ["impressions", "clicks", "cost", "conversions", "revenue"]
        for col in num_cols:
            if self.df[col].dtype == object:
                self.df[col] = (
                    self.df[col]
                    .astype(str)
                    .str.replace(",", "", regex=False)
                    .str.replace("¥", "", regex=False)
                    .str.replace("$", "", regex=False)
                    .str.strip()
                )
            self.df[col] = pd.to_numeric(self.df[col], errors="coerce").fillna(0.0)

        # 整数変換
        self.df["impressions"] = self.df["impressions"].astype(int)
        self.df["clicks"] = self.df["clicks"].astype(int)

    def process(self) -> AggregatedData:
        """3層集計（全体、媒体別、日別）を実行し AggregatedData を返す"""
        df = self.df

        period_start = str(df["date"].min())
        period_end = str(df["date"].max())

        # 1. 全体サマリー (Total)
        total_cost = df["cost"].sum()
        total_imp = df["impressions"].sum()
        total_clicks = df["clicks"].sum()
        total_cv = df["conversions"].sum()
        total_rev = df["revenue"].sum()

        total_metrics = calculate_metrics(
            cost=total_cost,
            imp=total_imp,
            clicks=total_clicks,
            cv=total_cv,
            rev=total_rev
        )

        # 2. 媒体別集計 (By Channel)
        by_channel = []
        channel_grp = df.groupby("channel", as_index=False).agg({
            "cost": "sum",
            "impressions": "sum",
            "clicks": "sum",
            "conversions": "sum",
            "revenue": "sum"
        })

        for _, row in channel_grp.iterrows():
            ch_metrics = calculate_metrics(
                cost=row["cost"],
                imp=row["impressions"],
                clicks=row["clicks"],
                cv=row["conversions"],
                rev=row["revenue"]
            )
            cost_share = _safe_div(row["cost"], total_cost, multiplier=100.0) or 0.0
            cv_share = _safe_div(row["conversions"], total_cv, multiplier=100.0) or 0.0

            by_channel.append(
                ChannelSummary(
                    channel=str(row["channel"]),
                    metrics=ch_metrics,
                    cost_share=cost_share,
                    conversion_share=cv_share
                )
            )

        # コスト消化順にソート
        by_channel.sort(key=lambda x: x.metrics.cost, reverse=True)

        # 3. 日別推移 (Daily Trends)
        daily_trends = []
        daily_grp = df.groupby("date", as_index=False).agg({
            "cost": "sum",
            "clicks": "sum",
            "conversions": "sum",
            "revenue": "sum"
        }).sort_values("date")

        for _, row in daily_grp.iterrows():
            day_cpa = _safe_div(row["cost"], row["conversions"])
            day_roas = _safe_div(row["revenue"], row["cost"], multiplier=100.0)
            daily_trends.append(
                DailyTrend(
                    date=str(row["date"]),
                    cost=round(float(row["cost"]), 2),
                    clicks=int(row["clicks"]),
                    conversions=round(float(row["conversions"]), 2),
                    cpa=day_cpa,
                    roas=day_roas
                )
            )

        return AggregatedData(
            period_start=period_start,
            period_end=period_end,
            total=total_metrics,
            by_channel=by_channel,
            daily_trends=daily_trends
        )
