"""Shared Python implementation for 《AI时代的蜡烛图分析》.

The module loads eQuant packages directly from the sibling My-Pkg workspace so
examples always follow the source currently being documented.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/ai-candlestick-numba")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/ai-candlestick-mpl")


def _find_mypkg() -> Path:
    configured = os.environ.get("XQUANT_MYPKG")
    if configured:
        return Path(configured).expanduser().resolve()
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "My-Pkg"
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError("Set XQUANT_MYPKG to the xquant-work/My-Pkg directory")


MYPKG = _find_mypkg()
for package_dir in (
    MYPKG / "eQuant-Py",
    MYPKG / "eQuant-Py" / "eCandleSticks-Py",
    MYPKG / "eQuant-Py" / "eFinCharts-Py",
    MYPKG / "eQuant-Py" / "eTTR-Py",
    MYPKG / "eQuant-Py" / "eBacktestCraft-Py",
    MYPKG / "eQuant-Py" / "eFactorCraft-Py",
):
    sys.path.insert(0, str(package_dir))


def load_data(path: str | Path = "data/aapl_daily.csv.gz") -> pd.DataFrame:
    data = pd.read_csv(path, parse_dates=["date"])
    required = {"date", "code", "open", "high", "low", "close", "volume"}
    missing = required.difference(data.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    data = data.sort_values(["code", "date"], kind="stable").reset_index(drop=True)
    if data.duplicated(["code", "date"]).any():
        raise ValueError("Duplicated code-date key")
    return data


def to_ohlcv(data: pd.DataFrame) -> pd.DataFrame:
    out = data.set_index("date")[["open", "high", "low", "close", "volume"]].copy()
    out.columns = ["Open", "High", "Low", "Close", "Volume"]
    return out


def pattern_signal(name: str, data: pd.DataFrame | None = None) -> pd.Series:
    from ecandlesticks import (
        add_counter_attack,
        add_doji,
        add_engulfing,
        add_gap,
        add_hammer,
        add_harami,
        add_inverted_hammer,
        add_separating_lines,
        add_shooting_star,
        add_star,
        add_tasuki_gap,
        add_three_methods,
    )

    panel = load_data() if data is None else data.copy()
    ohlcv = to_ohlcv(panel)
    ret_5 = ohlcv["Close"].pct_change(5)
    detectors = {
        "hammer": (add_hammer, "Hammer", None),
        "shooting": (add_shooting_star, None, "ShootingStar"),
        "inverted": (add_inverted_hammer, "InvertedHammer", None),
        "engulfing": (add_engulfing, "BullEngulfing", "BearEngulfing"),
        "star": (add_star, "MorningStar", "EveningStar"),
        "harami": (add_harami, "BullHarami", "BearHarami"),
        "counter": (add_counter_attack, "BullCounterAttack", "BearCounterAttack"),
        "methods": (add_three_methods, "RisingThreeMethods", "FallingThreeMethods"),
        "separating": (add_separating_lines, "BullSeparatingLines", "BearSeparatingLines"),
        "tasuki": (add_tasuki_gap, "UpsideTasukiGap", "DownsideTasukiGap"),
        "gap": (add_gap, "GapUp", "GapDown"),
    }
    if name == "doji":
        detected = add_doji(ohlcv)["Doji"]
        return pd.Series(np.where(detected, -np.sign(ret_5), 0), index=ohlcv.index).fillna(0).astype(int)
    if name not in detectors:
        raise KeyError(f"Unknown pattern: {name}")
    function, bull_col, bear_col = detectors[name]
    detected = function(ohlcv)
    bull = detected[bull_col].astype(int) if bull_col else 0
    bear = detected[bear_col].astype(int) if bear_col else 0
    return pd.Series(bull - bear, index=ohlcv.index, dtype=int)


def event_summary(
    signal: pd.Series,
    data: pd.DataFrame | None = None,
    horizon: int = 5,
    cost_bps: float = 10,
) -> dict[str, float]:
    panel = load_data() if data is None else data.copy()
    aligned = signal.reindex(pd.DatetimeIndex(panel["date"])).fillna(0).astype(int)
    entry = panel["open"].shift(-1).to_numpy()
    exit_price = panel["open"].shift(-(horizon + 1)).to_numpy()
    gross = aligned.to_numpy() * (exit_price / entry - 1)
    event = aligned.to_numpy() != 0
    values = gross[event] - cost_bps / 10_000
    values = values[np.isfinite(values)]
    standard_error = values.std(ddof=1) / np.sqrt(len(values)) if len(values) > 1 else np.nan
    return {
        "events": int(len(values)),
        "mean_net": float(values.mean()) if len(values) else np.nan,
        "win_rate": float((values > 0).mean()) if len(values) else np.nan,
        "ci_low": float(values.mean() - 1.96 * standard_error) if len(values) > 1 else np.nan,
        "ci_high": float(values.mean() + 1.96 * standard_error) if len(values) > 1 else np.nan,
    }


def save_chart(
    signal: pd.Series,
    filename: str | Path,
    start: str = "2023-01-01",
    end: str = "2024-12-31",
    title: str = "AAPL candlestick signals",
) -> None:
    from efincharts import candlestick

    ohlcv = to_ohlcv(load_data()).loc[start:end]
    selected = signal.reindex(ohlcv.index).fillna(0)
    bull = selected.to_frame("signal").assign(signal=lambda x: x["signal"] > 0)
    bear = selected.to_frame("signal").assign(signal=lambda x: x["signal"] < 0)
    chart = candlestick(ohlcv, volume=True, title=title)
    chart.add_pattern(bull, name="bull", bull=True)
    chart.add_pattern(bear, name="bear", bull=False)
    chart.save(str(filename))
