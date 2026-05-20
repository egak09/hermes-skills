"""
Demon Strategy Signal Engine v2.0 (妖币策略信号引擎)
=====================================================
Precision K-line pattern recognition with multi-factor scoring.

Patterns (must satisfy ≥2 for trigger):
  A. Rocket Launch (火箭起飞)     → +45 pts
  B. Volume Breakout (放量突破)    → +35 pts
  C. Flag/Triangle Break (旗形突破) → +25 pts
  D. Bullish Divergence (底背离)    → +20 pts

Bonus indicators:
  EMA7 ↑ EMA21 crossover           → +10 pts
  MACD golden cross                 → +8 pts

Trigger: total score ≥ 78 → auto-trade signal.

Primary timeframe: 5m (with 15m confirmation for flag/divergence).
"""

import json
import os
import sys
import time
import math
import warnings
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from collections import deque

import numpy as np
import pandas as pd
import ta

# Add binance-trading path for config loading and market data
_TRADING_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "binance-trading", "scripts")
sys.path.insert(0, _TRADING_DIR)
from market import get_klines, _load_config as _trading_load_config, _get_exchange as _trading_get_exchange

warnings.filterwarnings("ignore")

# ============================================================
# CONFIG
# ============================================================

STRATEGY_CONFIG = {
    "scan_interval_seconds": 180,  # 3 minutes
    "top_n_volume": 200,           # Top 200 by volume
    "signal_threshold": 78,        # Minimum score to trigger
    "funding_rate_max": 0.1,       # Max funding rate (10% = skip)

    # K-line lookback windows
    "klines_5m_limit": 60,         # 5m candles to fetch
    "klines_15m_limit": 60,        # 15m candles (for confirmation)

    # Pattern weights
    "weight_rocket": 45,
    "weight_volume_breakout": 35,
    "weight_flag_breakout": 25,
    "weight_divergence": 20,
    "weight_ema_cross": 10,
    "weight_macd_cross": 8,

    # Thresholds for Rocket Launch
    "rocket_body_pct": 0.08,       # 8% body
    "rocket_vol_mult": 4.0,        # 4x avg volume (5 bars)
    "rocket_rsi_max": 78,          # RSI must be < 78

    # Thresholds for Volume Breakout
    "vbrk_price_lookback": 10,     # Price > 10-bar high
    "vbrk_vol_mult": 3.5,          # 3.5x avg volume (20 bars)
    "vbrk_consecutive": 2,         # At least 2 consecutive bullish vol bars

    # Thresholds for Flag Breakout
    "flag_zone_start": 15,         # Start of convergence zone (bars ago)
    "flag_zone_end": 30,           # End of convergence zone
    "flag_vol_mult": 2.5,          # Breakout volume > 2.5x avg

    # Thresholds for Bullish Divergence
    "diverge_lookback": 30,        # Lookback for divergence detection
    "diverge_vol_mult": 3.0,       # Confirmation volume > 3x avg
    "diverge_body_pct": 0.03,      # Confirmation candle body > 3%

    # ---- OI + Volume Combo Scoring (NEW v2.1) ----
    # OI surge: 1h change + MA10 breakout
    "oi_change_1h_pct": 45,        # OI 1h change ≥ 45%
    "oi_ma10_mult": 1.25,           # OI > MA10 * 1.25
    "oi_score_base": 40,            # Base score for OI surge
    "oi_score_slope": 0.8,          # Extra score per % above threshold
    "oi_score_max_extra": 30,       # Max extra OI score (total max = 70)

    # Volume surge: precise thresholds
    "vol_ratio_strong": 3.8,        # ≥ 3.8x → 40 pts
    "vol_ratio_moderate": 2.8,      # ≥ 2.8x → 25 pts

    # OI+Volume combo
    "oi_weight_combo": 0.6,         # OI weight in combo
    "vol_weight_combo": 0.4,        # Volume weight in combo
    "combo_threshold": 55,          # Min combo score to add to total

    # Funding rate change
    "fr_change_window_min": 30,     # 30 min window
    "fr_change_threshold": 0.50,    # 50% rise → bonus

    # Blacklisted symbols
    "blacklist": ["BTC/USDT", "ETH/USDT"],
}

# ============================================================
# HELPERS
# ============================================================

def _format_symbol(symbol: str) -> str:
    """Ensure symbol format: ETH/USDT"""
    if '/' not in symbol:
        return f"{symbol}/USDT"
    return symbol


def _is_blacklisted(symbol: str) -> bool:
    """Check if symbol is blacklisted."""
    sym = _format_symbol(symbol)
    return sym in STRATEGY_CONFIG["blacklist"]


def _candles_to_arrays(candles: List[Dict]) -> Dict[str, np.ndarray]:
    """Convert candle dicts to numpy arrays for ta lib."""
    n = len(candles)
    return {
        "open": np.array([c["open"] for c in candles], dtype=np.float64),
        "high": np.array([c["high"] for c in candles], dtype=np.float64),
        "low": np.array([c["low"] for c in candles], dtype=np.float64),
        "close": np.array([c["close"] for c in candles], dtype=np.float64),
        "volume": np.array([c["volume"] for c in candles], dtype=np.float64),
        "n": n,
    }


def _to_series(arr: np.ndarray) -> pd.Series:
    """Convert numpy array to pandas Series for ta library compatibility."""
    return pd.Series(arr)


def _safe_rsi(close: np.ndarray, window: int = 14) -> np.ndarray:
    """Compute RSI safely, returning NaN for insufficient data."""
    if len(close) < window + 1:
        return np.full(len(close), np.nan)
    series = _to_series(close)
    rsi = ta.momentum.RSIIndicator(series, window=window).rsi()
    return np.array(rsi, dtype=np.float64)


def _safe_ema(close: np.ndarray, window: int) -> np.ndarray:
    """Compute EMA safely."""
    if len(close) < window:
        return np.full(len(close), np.nan)
    series = _to_series(close)
    ema = ta.trend.EMAIndicator(series, window=window).ema_indicator()
    return np.array(ema, dtype=np.float64)


def _safe_macd(close: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute MACD, signal line, histogram."""
    if len(close) < 35:
        n = len(close)
        return np.full(n, np.nan), np.full(n, np.nan), np.full(n, np.nan)
    series = _to_series(close)
    macd_ind = ta.trend.MACD(series)
    return (
        np.array(macd_ind.macd(), dtype=np.float64),
        np.array(macd_ind.macd_signal(), dtype=np.float64),
        np.array(macd_ind.macd_diff(), dtype=np.float64),
    )


def _ema_cross_up(ema_fast: np.ndarray, ema_slow: np.ndarray) -> Tuple[bool, int]:
    """Check if fast EMA just crossed above slow EMA (within last 3 bars)."""
    for i in range(len(ema_fast) - 1, max(len(ema_fast) - 4, -1), -1):
        if i <= 0:
            break
        if (ema_fast[i] > ema_slow[i] and
            ema_fast[i-1] <= ema_slow[i-1] and
            not np.isnan(ema_fast[i]) and not np.isnan(ema_slow[i])):
            return True, i
    return False, -1


def _macd_golden_cross(macd: np.ndarray, signal: np.ndarray) -> Tuple[bool, int]:
    """Check if MACD just crossed above signal line (golden cross, last 3 bars)."""
    for i in range(len(macd) - 1, max(len(macd) - 4, -1), -1):
        if i <= 0:
            break
        if (macd[i] > signal[i] and
            macd[i-1] <= signal[i-1] and
            not np.isnan(macd[i]) and not np.isnan(signal[i])):
            return True, i
    return False, -1


# ============================================================
# PATTERN A: ROCKET LAUNCH (火箭起飞) — 45 pts
# ============================================================

def detect_rocket_launch(arr: Dict[str, np.ndarray]) -> Tuple[bool, str]:
    """Detect Rocket Launch pattern.

    Conditions:
      1. Current candle body > 8% (|close - open| / open >= 0.08)
      2. Current volume >= 4x average of previous 5 bars
      3. Price breaks above 20-bar high
      4. RSI(14) < 78 (not extremely overbought)
    """
    open_ = arr["open"]
    high = arr["high"]
    close = arr["close"]
    volume = arr["volume"]
    n = arr["n"]

    if n < 22:
        return False, "数据不足(需≥22根K线)"

    # Current bar
    cur_open = open_[-1]
    cur_close = close[-1]
    cur_vol = volume[-1]
    cur_high = high[-1]

    # Condition 1: Body > 8%
    if cur_open <= 0:
        return False, "开盘价为0"
    body_pct = abs(cur_close - cur_open) / cur_open
    if body_pct < STRATEGY_CONFIG["rocket_body_pct"]:
        return False, f"实体不足 ({body_pct*100:.1f}% < 8%)"

    # Condition 2: Volume >= 4x avg of previous 5
    prev_5_vol = volume[-6:-1]  # 5 bars before current
    avg_5 = np.mean(prev_5_vol) if len(prev_5_vol) > 0 else 0
    if avg_5 <= 0:
        return False, "无前期量能数据"
    vol_ratio = cur_vol / avg_5
    if vol_ratio < STRATEGY_CONFIG["rocket_vol_mult"]:
        return False, f"量能不足 ({vol_ratio:.1f}x < 4x)"

    # Condition 3: Price breaks 20-bar high (excluding current)
    prev_20_high = np.max(high[-21:-1]) if n >= 21 else 0
    if cur_close <= prev_20_high and cur_high <= prev_20_high:
        return False, f"未突破20线高点 (${cur_close:.4f} ≤ ${prev_20_high:.4f})"

    # Condition 4: RSI < 78
    rsi = _safe_rsi(close, 14)
    cur_rsi = rsi[-1]
    if np.isnan(cur_rsi):
        return False, "RSI计算失败"
    if cur_rsi >= STRATEGY_CONFIG["rocket_rsi_max"]:
        return False, f"RSI超买 ({cur_rsi:.1f} ≥ 78)"

    direction = "↑多" if cur_close > cur_open else "↓空"
    return True, (
        f"🚀火箭起飞 {direction} "
        f"实体{body_pct*100:.1f}%"
        f" | 量{vol_ratio:.1f}x"
        f" | 破{prev_20_high:.4f}"
        f" | RSI{cur_rsi:.0f}"
    )


# ============================================================
# PATTERN B: VOLUME BREAKOUT (放量突破) — 35 pts
# ============================================================

def detect_volume_breakout(arr: Dict[str, np.ndarray]) -> Tuple[bool, str]:
    """Detect Volume Breakout pattern.

    Conditions:
      1. Price > 10-bar high (new high)
      2. Current volume >= 3.5x 20-bar average
      3. Current candle is bullish (close > open)
      4. At least 2 consecutive bullish volume bars
    """
    open_ = arr["open"]
    high = arr["high"]
    close = arr["close"]
    volume = arr["volume"]
    n = arr["n"]

    if n < 22:
        return False, "数据不足(需≥22根K线)"

    cur_close = close[-1]
    cur_open = open_[-1]
    cur_vol = volume[-1]

    # Condition 1: Price > 10-bar high
    prev_10_high = np.max(high[-11:-1]) if n >= 11 else 0
    if cur_close <= prev_10_high:
        return False, f"未破10线高 (${cur_close:.4f} ≤ ${prev_10_high:.4f})"

    # Condition 2: Volume >= 3.5x 20-bar avg
    prev_20_vol = volume[-21:-1]
    avg_20 = np.mean(prev_20_vol) if len(prev_20_vol) > 0 else 0
    if avg_20 <= 0:
        return False, "无前期量能数据"
    vol_ratio = cur_vol / avg_20
    if vol_ratio < STRATEGY_CONFIG["vbrk_vol_mult"]:
        return False, f"量能不足 ({vol_ratio:.1f}x < 3.5x)"

    # Condition 3: Bullish candle
    if cur_close <= cur_open:
        return False, "非阳线"

    # Condition 4: At least 2 consecutive bullish volume bars
    # (volume > 2x avg_20 AND close > open)
    consecutive = 0
    for i in range(n - 1, max(n - 6, -1), -1):
        if i < 0:
            break
        if volume[i] > avg_20 * 2.0 and close[i] > open_[i]:
            consecutive += 1
        else:
            break
    if consecutive < STRATEGY_CONFIG["vbrk_consecutive"]:
        return False, f"连续放量阳线不足 ({consecutive} < 2)"

    return True, (
        f"📈放量突破 "
        f"破{prev_10_high:.4f}"
        f" | 量{vol_ratio:.1f}x"
        f" | 连续{consecutive}根"
    )


# ============================================================
# PATTERN C: FLAG / TRIANGLE BREAKOUT (旗形/三角形突破) — 25 pts
# ============================================================

def _detect_convergence(high: np.ndarray, low: np.ndarray,
                        start: int, end: int) -> Tuple[bool, float, float]:
    """Detect if the range is converging (high-low decreasing over time).
    
    Returns (is_converging, upper_bound, lower_bound).
    Uses linear regression on the high-low range to detect narrowing.
    """
    zone_len = end - start
    if zone_len < 10:
        return False, 0, 0

    # Split zone into two halves
    mid = start + zone_len // 2
    first_half_range = np.max(high[start:mid]) - np.min(low[start:mid])
    second_half_range = np.max(high[mid:end]) - np.min(low[mid:end])

    # Range should be shrinking
    if second_half_range >= first_half_range * 0.85:
        return False, 0, 0

    # Also check linear trend of range
    ranges = high[start:end] - low[start:end]
    x = np.arange(len(ranges))
    # Simple linear regression slope
    if len(ranges) >= 2:
        slope = np.polyfit(x, ranges, 1)[0]
        if slope >= 0:  # Not shrinking
            return False, 0, 0
    else:
        return False, 0, 0

    # Upper bound = recent high of zone, lower bound = recent low
    upper = np.max(high[start:end])
    lower = np.min(low[start:end])

    return True, upper, lower


def detect_flag_breakout(arr_5m: Dict[str, np.ndarray]) -> Tuple[bool, str]:
    """Detect Flag / Triangle Breakout pattern.

    Conditions:
      1. Past 15-30 bars show converging range (high-low shrinking)
      2. Current bar breaks above the upper bound of the zone
      3. Breakout volume > 2.5x average volume
      4. 1-2 bars after breakout do NOT fall back below the upper bound
    """
    high = arr_5m["high"]
    low = arr_5m["low"]
    close = arr_5m["close"]
    volume = arr_5m["volume"]
    n = arr_5m["n"]

    min_bars = STRATEGY_CONFIG["flag_zone_start"] + 5  # at least 20
    if n < min_bars:
        return False, f"数据不足(需≥{min_bars}根K线)"

    # Try different zone windows: 15-30, 20-30, 15-25
    best_upper = 0
    best_lower = 0
    best_start = 0
    best_end = 0
    best_zone_mid = 0

    for start in range(n - STRATEGY_CONFIG["flag_zone_end"],
                       n - STRATEGY_CONFIG["flag_zone_start"]):
        end = min(n - 3, start + 20)  # Leave 2 bars for confirmation
        if end - start < 10:
            continue
        is_conv, upper, lower = _detect_convergence(high, low, start, end)
        if is_conv:
            best_upper = upper
            best_lower = lower
            best_start = start
            best_end = end
            break

    if best_upper <= 0:
        return False, "未检测到收敛形态"

    # Condition 2: Break above upper bound
    # Check if current bar (or the bar just after the zone) breaks out
    breakout_idx = best_end
    for i in range(best_end, min(n, best_end + 3)):
        if close[i] > best_upper:
            breakout_idx = i
            break
    else:
        return False, f"未突破上轨 (${close[best_end]:.4f} ≤ ${best_upper:.4f})"

    # Condition 3: Volume > 2.5x average
    avg_vol = np.mean(volume[best_start:best_end])
    breakout_vol = volume[breakout_idx]
    if avg_vol <= 0:
        return False, "无平均量能数据"
    vol_ratio = breakout_vol / avg_vol
    if vol_ratio < STRATEGY_CONFIG["flag_vol_mult"]:
        return False, f"突破量能不足 ({vol_ratio:.1f}x < 2.5x)"

    # Condition 4: 1-2 bars after breakout do NOT fall back
    confirmed = True
    for i in range(breakout_idx + 1, min(n, breakout_idx + 3)):
        if close[i] < best_upper * 0.995 and low[i] < best_upper * 0.99:
            confirmed = False
            break
    if not confirmed:
        return False, "突破后回破上轨"

    zone_range = best_upper - best_lower
    return True, (
        f"🚩旗形突破 "
        f"区间{zone_range:.4f}"
        f" | 量{vol_ratio:.1f}x"
        f" | 确认不破"
    )


# ============================================================
# PATTERN D: BULLISH DIVERGENCE (底背离放量反转) — 20 pts
# ============================================================

def detect_bullish_divergence(arr: Dict[str, np.ndarray]) -> Tuple[bool, str]:
    """Detect Bullish Divergence with volume reversal.

    Conditions:
      1. RSI(14) shows bullish divergence:
         Price makes lower low, but RSI makes higher low
      2. Volume surge >= 3x average on reversal candle
      3. Reversal candle is a strong bullish candle (body > 3%)
    """
    close = arr["close"]
    low = arr["low"]
    volume = arr["volume"]
    open_ = arr["open"]
    n = arr["n"]

    if n < 32:
        return False, "数据不足(需≥32根K线)"

    rsi = _safe_rsi(close, 14)
    if np.all(np.isnan(rsi[-10:])):
        return False, "RSI计算失败"

    # Find recent swing lows in the lookback window
    lookback = STRATEGY_CONFIG["diverge_lookback"]
    window_start = max(0, n - lookback)

    # Find local minima in price (low points)
    price_lows = []  # (index, price)
    rsi_lows = []    # (index, rsi_value)

    for i in range(window_start + 2, n - 3):
        if (low[i] < low[i-1] and low[i] < low[i-2] and
            low[i] <= low[i+1] and low[i] <= low[i+2]):
            price_lows.append((i, low[i]))
            rsi_at_low = rsi[i] if not np.isnan(rsi[i]) else rsi[max(0, i-1)]
            if not np.isnan(rsi_at_low):
                rsi_lows.append((i, rsi_at_low))

    if len(price_lows) < 2:
        return False, f"摆动低点不足 ({len(price_lows)}个)"

    # Check last two swing lows for divergence
    last_price_low = price_lows[-1][1]
    prev_price_low = price_lows[-2][1]
    last_rsi_low = rsi_lows[-1][1] if len(rsi_lows) >= 2 else None
    prev_rsi_low = rsi_lows[-2][1] if len(rsi_lows) >= 2 else None

    if last_rsi_low is None or prev_rsi_low is None:
        return False, "RSI低点数据不足"

    # Divergence: price lower low, RSI higher low
    if not (last_price_low < prev_price_low and last_rsi_low > prev_rsi_low):
        return False, (
            f"无底背离 "
            f"(价格 {last_price_low:.4f} vs {prev_price_low:.4f}, "
            f"RSI {last_rsi_low:.1f} vs {prev_rsi_low:.1f})"
        )

    # Now check for volume + bullish candle confirmation on the reversal
    # Look at the candles after the last price low
    reversal_start = price_lows[-1][0] + 1

    # Average volume before the reversal
    avg_vol = np.mean(volume[max(0, reversal_start-20):reversal_start])

    # Check the next 3 bars for confirmation
    confirmed = False
    confirm_desc = ""
    for i in range(reversal_start, min(n, reversal_start + 4)):
        if i >= n:
            break
        vol_ratio = volume[i] / avg_vol if avg_vol > 0 else 0
        body_pct = abs(close[i] - open_[i]) / open_[i] if open_[i] > 0 else 0
        is_bullish = close[i] > open_[i]

        if (vol_ratio >= STRATEGY_CONFIG["diverge_vol_mult"] and
            body_pct >= STRATEGY_CONFIG["diverge_body_pct"] and
            is_bullish):
            confirmed = True
            confirm_desc = f"量{vol_ratio:.1f}x 实体{body_pct*100:.1f}%"
            break

    if not confirmed:
        return False, "背离后无放量大阳确认"

    return True, (
        f"🔄底背离反转 "
        f"价{last_price_low:.4f}<{prev_price_low:.4f}"
        f" | RSI{last_rsi_low:.0f}>{prev_rsi_low:.0f}"
        f" | {confirm_desc}"
    )


# ============================================================
# BONUS INDICATORS
# ============================================================

def check_bonus_indicators(arr: Dict[str, np.ndarray]) -> Tuple[int, List[str]]:
    """Check EMA crossover and MACD golden cross for bonus points.

    Returns (bonus_score, descriptions).
    """
    close = arr["close"]
    n = arr["n"]
    score = 0
    descs = []

    if n < 25:
        return 0, []

    # EMA(7) and EMA(21)
    ema7 = _safe_ema(close, 7)
    ema21 = _safe_ema(close, 21)

    crossed, idx = _ema_cross_up(ema7, ema21)
    if crossed:
        score += STRATEGY_CONFIG["weight_ema_cross"]
        descs.append(f"EMA7↑EMA21 (bar {n-idx-1} ago)")

    # MACD
    macd, signal, hist = _safe_macd(close)
    crossed_macd, idx_m = _macd_golden_cross(macd, signal)
    if crossed_macd:
        score += STRATEGY_CONFIG["weight_macd_cross"]
        descs.append(f"MACD金叉 (bar {n-idx_m-1} ago)")

    return score, descs


# ============================================================
# OI + VOLUME PRECISION SCORING (v2.1)
# ============================================================

def fetch_oi_history(symbol: str, config: dict = None, limit: int = 14) -> List[float]:
    """Fetch OI history from Binance Futures.

    Gets the last `limit` OI readings at 5m intervals.
    Returns list of OI values (oldest first).
    """
    import ccxt
    from market import _load_config

    if config is None:
        try:
            config = _load_config()
        except:
            pass

    ex = ccxt.binance({
        'enableRateLimit': True,
        'timeout': 15000,
    })
    if config and config.get('proxy'):
        ex.proxies = config['proxy']
    ex.options['defaultType'] = 'future'

    sym = _format_symbol(symbol)

    try:
        # fetch_open_interest_history(symbol, timeframe, since, limit)
        # Returns list of {timestamp, openInterestValue}
        ohlcv = ex.fetch_open_interest_history(sym, timeframe='5m', limit=limit)
        if ohlcv and len(ohlcv) > 0:
            values = [float(v['openInterestValue']) for v in ohlcv]
            return values
        return []
    except Exception as e:
        # Fallback: try REST ticker for current OI only
        try:
            ticker = ex.fetch_ticker(sym)
            info = ticker.get('info', {})
            oi = float(info.get('openInterest', 0))
            return [oi] if oi > 0 else []
        except:
            return []


def score_oi_surge(oi_values: List[float]) -> Tuple[float, str]:
    """Score OI surge using precise formula.

    oi_change_1h = (oi_current - oi_1h_ago) / oi_1h_ago * 100
    oi_ma10 = average of last 10 OI readings

    Strong signal: oi_change_1h >= 45% AND oi_current > oi_ma10 * 1.25
    Score: 40 + min((change - 45) * 0.8, 30) → max 70

    Returns (score, description).
    """
    cfg = STRATEGY_CONFIG

    if len(oi_values) < 2:
        return 0, "OI数据不足"

    oi_current = oi_values[-1]
    if oi_current <= 0:
        return 0, "OI为0"

    # 1h change (12 × 5m)
    oi_1h_idx = max(0, len(oi_values) - 13)  # ensure we have 12 bars back
    oi_1h_ago = oi_values[oi_1h_idx]
    if oi_1h_ago <= 0:
        return 0, "OI基准无效"

    oi_change_1h = (oi_current - oi_1h_ago) / oi_1h_ago * 100

    # MA10
    oi_last_10 = oi_values[-10:] if len(oi_values) >= 10 else oi_values
    oi_ma10 = sum(oi_last_10) / len(oi_last_10)

    # Check threshold
    if oi_change_1h >= cfg["oi_change_1h_pct"] and oi_current > oi_ma10 * cfg["oi_ma10_mult"]:
        extra = min((oi_change_1h - cfg["oi_change_1h_pct"]) * cfg["oi_score_slope"],
                    cfg["oi_score_max_extra"])
        score = cfg["oi_score_base"] + extra
        return round(score, 1), (
            f"OI暴增 {oi_change_1h:.1f}%/1h"
            f" | OI>{oi_ma10*cfg['oi_ma10_mult']:.0f}"
            f" | MA10={oi_ma10:.0f}"
        )
    elif oi_change_1h >= 25:
        # Partial signal: OI rising but below threshold
        partial = min(oi_change_1h * 0.4, 25)
        return round(partial, 1), f"OI上升 {oi_change_1h:.1f}%/1h"
    else:
        return 0, f"OI平稳 ({oi_change_1h:.1f}%/1h | MA10={oi_ma10:.0f})"


def score_volume_surge(vol_current: float, vol_ma20: float) -> Tuple[float, str]:
    """Score volume surge with precise thresholds.

    vol_ratio = vol_current / vol_ma20
    >= 3.8 → 40 pts
    >= 2.8 → 25 pts
    else → 0 pts

    Returns (score, description).
    """
    cfg = STRATEGY_CONFIG

    if vol_ma20 <= 0:
        return 0, "无均量数据"

    ratio = vol_current / vol_ma20

    if ratio >= cfg["vol_ratio_strong"]:
        return float(cfg["vol_ratio_strong"] * 10.5), f"量能暴增 {ratio:.1f}x"  # ~40
    elif ratio >= cfg["vol_ratio_moderate"]:
        return 25.0, f"量能激增 {ratio:.1f}x"
    else:
        return 0, f"量能正常 ({ratio:.1f}x)"


def score_oi_volume_combo(oi_score: float, vol_score: float) -> Tuple[float, str]:
    """Calculate OI + Volume combo strength.

    combined_score = (oi_score * 0.6 + vol_score * 0.4)
    Only adds to total if combined_score >= 55 AND there's a price breakout.

    Returns (combo_score, description).
    """
    cfg = STRATEGY_CONFIG
    combo = oi_score * cfg["oi_weight_combo"] + vol_score * cfg["vol_weight_combo"]
    desc = f"OI×0.6+Vol×0.4 = {combo:.1f}"

    if combo >= cfg["combo_threshold"]:
        desc += " 🔥强劲"
    elif combo >= 35:
        desc += " 🟡中等"
    else:
        desc += ""

    return round(combo, 1), desc


def check_funding_rate_change(symbol: str, config: dict = None) -> Tuple[bool, float, str]:
    """Check funding rate change over 30 minutes.

    Fetches current funding rate and compares to 30 min ago.
    Returns (is_rising_fast, change_ratio, description).

    Note: Binance funding rate changes every 8 hours, so 30-min change
    detection uses the funding rate trend from ticker snapshots.
    """
    # Binance futures funding rate is fixed for 8h periods.
    # We detect if rate has flipped to extreme positive in last 30 min
    # by comparing the current rate to a threshold.
    import ccxt
    from market import _load_config

    if config is None:
        try:
            config = _load_config()
        except:
            pass

    try:
        ex = ccxt.binance({
            'enableRateLimit': True,
            'timeout': 10000,
        })
        if config and config.get('proxy'):
            ex.proxies = config['proxy']
        ex.options['defaultType'] = 'future'

        sym = _format_symbol(symbol)
        ticker = ex.fetch_ticker(sym)
        fr = ticker.get('info', {}).get('lastFundingRate')
        if not fr:
            return False, 0, "费率不可用"

        fr_val = float(fr)
        fr_pct = fr_val * 100

        # Rate above threshold means high long pressure
        if fr_val >= 0.00075:  # 0.075%
            return True, fr_val, f"费率偏高 {fr_pct:.4f}% → 多头拥挤"
        elif fr_val <= -0.00075:
            return True, abs(fr_val), f"费率偏低 {fr_pct:.4f}% → 空头拥挤"
        else:
            return False, fr_val, f"费率正常 {fr_pct:.4f}%"

    except Exception as e:
        return False, 0, f"费率获取失败: {e}"

def scan_single(symbol: str, config: dict = None) -> Dict:
    """Scan a single symbol with all pattern detectors + bonus indicators.

    Returns complete signal analysis.
    """
    sym = _format_symbol(symbol)
    cfg = STRATEGY_CONFIG

    if _is_blacklisted(sym):
        return {"symbol": sym, "signal": False, "reason": "黑名单"}

    result = {
        "symbol": sym,
        "timestamp": datetime.now().isoformat(),
        "signal": False,
        "total_score": 0,
        "scores": {},
        "patterns": {},
        "details": {},
        "verdict": "",
    }

    try:
        # Fetch 5m K-lines (primary)
        klines_5m = get_klines(sym, '5m', limit=cfg["klines_5m_limit"], config=config)
        candles_5m = klines_5m.get('candles', [])
        if len(candles_5m) < 20:
            result["reason"] = "K线数据不足(5m)"
            return result

        arr = _candles_to_arrays(candles_5m)
        current_price = arr["close"][-1]
        result["price"] = current_price

        # ---- Pattern Detection ----
        total_score = 0
        pattern_count = 0

        # A. Rocket Launch (+45)
        rocket_hit, rocket_desc = detect_rocket_launch(arr)
        result["patterns"]["rocket"] = {"hit": rocket_hit, "desc": rocket_desc}
        if rocket_hit:
            total_score += cfg["weight_rocket"]
            pattern_count += 1

        # B. Volume Breakout (+35)
        vbrk_hit, vbrk_desc = detect_volume_breakout(arr)
        result["patterns"]["volume_breakout"] = {"hit": vbrk_hit, "desc": vbrk_desc}
        if vbrk_hit:
            total_score += cfg["weight_volume_breakout"]
            pattern_count += 1

        # C. Flag Breakout (+25)
        flag_hit, flag_desc = detect_flag_breakout(arr)
        result["patterns"]["flag_breakout"] = {"hit": flag_hit, "desc": flag_desc}
        if flag_hit:
            total_score += cfg["weight_flag_breakout"]
            pattern_count += 1

        # D. Bullish Divergence (+20)
        diverge_hit, diverge_desc = detect_bullish_divergence(arr)
        result["patterns"]["divergence"] = {"hit": diverge_hit, "desc": diverge_desc}
        if diverge_hit:
            total_score += cfg["weight_divergence"]
            pattern_count += 1

        # ---- Bonus Indicators ----
        bonus_score, bonus_descs = check_bonus_indicators(arr)
        total_score += bonus_score
        result["bonus"] = {"score": bonus_score, "descs": bonus_descs}

        # ---- OI + Volume Combo Scoring (v2.1) ----
        oi_result = {"score": 0, "desc": "", "values": [], "vol_score": 0, "combo": 0}
        has_breakout = rocket_hit or vbrk_hit or flag_hit

        # OI history (async-friendly: try/catch so it never blocks the scan)
        try:
            oi_values = fetch_oi_history(sym, config, limit=14)
            if oi_values and len(oi_values) >= 2:
                oi_score, oi_desc = score_oi_surge(oi_values)
                oi_result["score"] = oi_score
                oi_result["desc"] = oi_desc
                oi_result["values"] = [float(v) for v in oi_values[-3:]]  # last 3
        except Exception as e:
            oi_result["desc"] = f"OI获取失败: {e}"

        # Volume surge (from existing K-line data)
        vol_current = arr["volume"][-1]
        vol_ma20_val = np.mean(arr["volume"][-20:]) if arr["n"] >= 20 else 0
        vol_score, vol_desc = score_volume_surge(vol_current, vol_ma20_val)
        oi_result["vol_score"] = vol_score
        oi_result["vol_desc"] = vol_desc
        oi_result["vol_ratio"] = round(vol_current / vol_ma20_val, 2) if vol_ma20_val > 0 else 0

        # Combo score
        combo_score, combo_desc = score_oi_volume_combo(oi_result["score"], vol_score)
        oi_result["combo"] = combo_score
        oi_result["combo_desc"] = combo_desc

        # Only add combo to total if ≥ 55 AND price breakout exists
        if combo_score >= cfg["combo_threshold"] and has_breakout:
            total_score += combo_score
            oi_result["applied"] = True
            oi_result["applied_reason"] = "组合强劲+价格突破"
        elif combo_score >= cfg["combo_threshold"]:
            oi_result["applied"] = False
            oi_result["applied_reason"] = "组合强劲但无价格突破"
        else:
            oi_result["applied"] = False
            oi_result["applied_reason"] = "组合未达阈值"

        result["oi_volume"] = oi_result

        # ---- Funding Rate Check ----
        fr_alert, fr_val, fr_desc = check_funding_rate_change(sym, config)
        result["funding_rate"] = fr_val if fr_val else None
        result["fr_alert"] = fr_alert
        result["fr_desc"] = fr_desc

        # Check extreme funding rate
        if fr_val and abs(fr_val) > cfg["funding_rate_max"]:
            result["reason"] = f"资金费率过高 ({fr_val*100:.2f}%)"
            result["signal"] = False
            return result

        result["total_score"] = round(total_score, 1)
        result["pattern_count"] = pattern_count

        # ---- Signal Decision ----
        threshold = cfg["signal_threshold"]

        # Must have at least 2 patterns for a strong signal
        if pattern_count < 2 and total_score >= threshold:
            result["verdict"] = f"⚠️ 分数达标但形态不足 ({pattern_count}种 < 2种)"
            result["signal"] = False
        elif total_score >= threshold:
            result["signal"] = True
            result["verdict"] = f"🔥 强烈信号 ({total_score}/{threshold}, {pattern_count}形态)"
        elif total_score >= threshold * 0.8:
            result["verdict"] = f"🟡 接近阈值 ({total_score}/{threshold})"
        else:
            result["verdict"] = f"⚪ 未触发 ({total_score}/{threshold})"

    except Exception as e:
        import traceback
        result["reason"] = f"扫描异常: {e}"
        result["traceback"] = traceback.format_exc()

    return result


# ============================================================
# MARKET-WIDE SCAN
# ============================================================

def fetch_top_altcoins(config: dict = None, n: int = None) -> List[str]:
    """Fetch top N altcoins by 24h volume from Binance Futures."""
    if n is None:
        n = STRATEGY_CONFIG["top_n_volume"]

    import ccxt
    from market import _load_config, _get_exchange

    if config is None:
        try:
            config = _load_config()
        except:
            pass

    ex = ccxt.binance({
        'enableRateLimit': True,
        'timeout': 10000,
    })
    if config and config.get('proxy'):
        ex.proxies = config['proxy']

    ex.options['defaultType'] = 'future'

    try:
        tickers = ex.fetch_tickers()
        candidates = []
        for sym, t in tickers.items():
            if not sym.endswith('/USDT') or _is_blacklisted(sym):
                continue
            vol = t.get('quoteVolume') or 0
            candidates.append((sym, vol))

        candidates.sort(key=lambda x: x[1], reverse=True)
        top = [s for s, v in candidates[:n]]
        return top

    except Exception as e:
        print(f"Error fetching tickers: {e}")
        return [
            "SOL/USDT", "ARB/USDT", "OP/USDT", "SUI/USDT", "APT/USDT",
            "LDO/USDT", "WLD/USDT", "TIA/USDT", "SEI/USDT", "STRK/USDT",
            "RUNE/USDT", "INJ/USDT", "FET/USDT", "AGIX/USDT", "RNDR/USDT",
        ]


def scan_market(config: dict = None, top_n: int = 50) -> Dict:
    """Scan top N altcoins and return all signals."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 扫描 Top {top_n} 山寨币...")

    try:
        symbols = fetch_top_altcoins(config, n=min(top_n, 200))
    except Exception as e:
        symbols = fetch_top_altcoins(None, n=50)
    print(f"  获取 {len(symbols)} 个候选币")

    signals = []
    all_results = []

    for i, sym in enumerate(symbols):
        if i % 10 == 0:
            print(f"  进度: {i}/{len(symbols)}")

        result = scan_single(sym, config)
        all_results.append(result)

        if result.get('signal'):
            signals.append(result)

    print(f"  扫描完成: {len(all_results)} 个币, {len(signals)} 个信号")

    signals.sort(key=lambda x: x['total_score'], reverse=True)

    return {
        "timestamp": datetime.now().isoformat(),
        "scanned": len(all_results),
        "signals_count": len(signals),
        "top_signals": signals[:10],
        "all_signals": signals,
        "summary": {
            "total_scored": sum(1 for r in all_results if r.get('total_score', 0) > 0),
            "avg_score": round(sum(r.get('total_score', 0) for r in all_results) / max(len(all_results), 1), 1),
            "strong_signals": len(signals),
        }
    }


# ============================================================
# FORMATTING
# ============================================================

def format_signal_report(signal: Dict) -> str:
    """Format a single signal for display."""
    lines = []
    sym = signal['symbol'].replace('/USDT', '')
    score = signal['total_score']
    price = signal.get('price', 0)

    emoji = "🔥" if score >= 85 else "🟢" if score >= 78 else "🟡"
    lines.append(f"{emoji} **{sym}** — {score:.0f}分 | ${price:,.4f}")

    # Patterns
    patterns = signal.get('patterns', {})
    for name, p in patterns.items():
        if p.get('hit'):
            lines.append(f"  {p['desc']}")

    # OI + Volume Combo
    oiv = signal.get('oi_volume', {})
    if oiv.get('applied') or oiv.get('combo', 0) > 0:
        lines.append(f"  📊 OI+Vol组合: {oiv.get('combo_desc', '')}")
        if oiv.get('desc'):
            lines.append(f"    OI: {oiv['desc']}")
        if oiv.get('vol_desc'):
            lines.append(f"    Vol: {oiv['vol_desc']}")

    # Bonus
    bonus = signal.get('bonus', {})
    if bonus.get('descs'):
        for d in bonus['descs']:
            lines.append(f"  ✨ {d}")

    # Funding rate
    fr_desc = signal.get('fr_desc')
    if fr_desc:
        lines.append(f"  💰 {fr_desc}")

    return "\n".join(lines)


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    import sys

    cmd = sys.argv[1] if len(sys.argv) > 1 else 'test'

    if cmd == 'scan':
        top_n = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        result = scan_market(top_n=top_n)

        print(f"\n{'='*60}")
        print(f"  妖币扫描 v2.1 — {result['timestamp']}")
        print(f"{'='*60}")
        print(f"扫描: {result['scanned']}个 | 信号: {result['signals_count']}个")
        print(f"平均分: {result['summary']['avg_score']:.0f}")
        print()

        if result['top_signals']:
            for s in result['top_signals'][:5]:
                print(format_signal_report(s))
                print()
        else:
            print("  今日无符合条件的信号")

    elif cmd == 'test':
        sym = sys.argv[2] if len(sys.argv) > 2 else 'ARB/USDT'
        print(f"测试 {sym} 信号引擎 v2.1...")
        result = scan_single(sym)

        # Pretty print
        print(f"\n{'='*60}")
        print(f"  {result['symbol']} — ${result.get('price', 0):,.4f}")
        print(f"  {result['verdict']}")
        print(f"{'='*60}")

        print("\n📊 形态检测:")
        for name, p in result.get('patterns', {}).items():
            status = "✅" if p['hit'] else "❌"
            print(f"  {status} {name}: {p['desc']}")

        oiv = result.get('oi_volume', {})
        print(f"\n📊 OI+Vol 组合:")
        print(f"  OI评分: {oiv.get('score', 0)} — {oiv.get('desc', 'N/A')}")
        print(f"  Vol评分: {oiv.get('vol_score', 0)} — {oiv.get('vol_desc', 'N/A')}")
        print(f"  组合: {oiv.get('combo_desc', 'N/A')}")
        print(f"  应用: {'✅' if oiv.get('applied') else '❌'} ({oiv.get('applied_reason', '')})")

        bonus = result.get('bonus', {})
        if bonus.get('descs'):
            print(f"\n📈 指标加分: +{bonus['score']}")
            for d in bonus['descs']:
                print(f"  ✨ {d}")

        print(f"\n💰 {result.get('fr_desc', '费率: N/A')}")
        print(f"🔥 信号: {'触发' if result['signal'] else '未触发'}")

    elif cmd == 'diagnose':
        sym = sys.argv[2] if len(sys.argv) > 2 else 'ARB/USDT'
        result = scan_single(sym)
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
