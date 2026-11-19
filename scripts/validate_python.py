"""Syntax and smoke checks for Python examples and eQuant source packages."""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from python.candlestick_lab import event_summary, load_data, pattern_signal


def check_code_blocks() -> int:
    checked = 0
    for path in sorted(ROOT.glob("*.Rmd")):
        text = path.read_text(encoding="utf-8")
        for number, block in enumerate(re.findall(r"```python\n(.*?)\n```", text, re.S), start=1):
            ast.parse(block, filename=f"{path.name}:python-block-{number}")
            checked += 1
    return checked


def smoke_test() -> None:
    panel = load_data(ROOT / "data" / "aapl_daily.csv.gz")
    for name in ("hammer", "engulfing", "doji", "star", "harami"):
        signal = pattern_signal(name, panel)
        if len(signal) != len(panel) or not set(signal.unique()).issubset({-1, 0, 1}):
            raise AssertionError(f"Invalid signal: {name}")
        event_summary(signal, panel)

    from ettr import obv, rsi, sma

    assert "SMA_20" in sma(panel, n=20).columns
    assert "RSI_14" in rsi(panel, n=14).columns
    assert "OBV" in obv(panel).columns

    from ebacktestcraft import Config

    assert Config(exec_price_col="open").exec_price_col == "open"


if __name__ == "__main__":
    count = check_code_blocks()
    smoke_test()
    print(f"PASS: {count} Python code blocks and eQuant smoke tests")
