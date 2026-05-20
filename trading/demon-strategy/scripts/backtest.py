"""
Demon Strategy Backtest Engine v1.0
====================================
30-day walk-forward backtest with full strategy simulation.

Features:
  - 5m K-line walk-forward (no look-ahead bias)
  - Pattern detection (rocket/breakout/flag/divergence)
  - Volume surge scoring + bonus indicators
  - Risk management: 5% per trade, 18% daily stop, 3 max positions
  - Slippage (0.05%) + fee (0.04% taker)
  - Stats: win rate, profit factor, max drawdown, Sharpe, Calmar

Usage:
  python backtest.py SOL/USDT          # single coin
  python backtest.py batch 20          # batch test top 20 coins
  python backtest.py report SOL/USDT   # detailed trade log
"""

import json
import os
import sys
import math
import time
import warnings
from datetime import datetime, timedelta, date
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field

import numpy as np
import ccxt

# Import pattern detectors from signals.py (same directory)
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SCRIPT_DIR)
# Also need the binance-trading path for market.py
_TRADING_DIR = os.path.join(_SCRIPT_DIR, "..", "..", "binance-trading", "scripts")
sys.path.insert(0, _TRADING_DIR)

from signals import (
    _candles_to_arrays,
    detect_rocket_launch,
    detect_volume_breakout,
    detect_flag_breakout,
    detect_bullish_divergence,
    check_bonus_indicators,
    score_volume_surge,
    STRATEGY_CONFIG,
    _format_symbol,
    _is_blacklisted,
)
from market import _load_config

warnings.filterwarnings("ignore")

# ============================================================
# CONFIG
# ============================================================

BACKTEST_CONFIG = {
    # Data
    "days": 30,                # Lookback period
    "timeframe": "5m",         # Primary timeframe
    "warmup_bars": 60,         # Minimum bars before trading

    # Risk
    "risk_per_trade_pct": 0.05,      # 5% risk per trade
    "daily_loss_limit_pct": 0.18,    # 18% daily stop
    "max_positions": 3,              # Max concurrent positions
    "cooling_bars": 6,               # 30 min cooling after stop loss

    # Position
    "default_leverage": 5,           # Default leverage
    "stop_loss_pct": -0.05,          # Default stop loss (5% from entry)
    "take_profit_pct": 0.10,         # Default take profit (10% from entry)
    "time_stop_bars": 48,            # 4 hours (48 × 5m)

    # Costs
    "slippage_pct": 0.0005,          # 0.05% slippage
    "fee_taker_pct": 0.0004,         # 0.04% taker fee
    "fee_maker_pct": 0.0002,         # 0.02% maker fee

    # Signal
    "signal_threshold": 78,          # Min score to trigger
    "min_patterns": 2,               # Min pattern types for trigger
}


# ============================================================
# DATA FETCHING
# ============================================================

def fetch_historical_klines(
    symbol: str,
    timeframe: str = "5m",
    days: int = 30,
    config: dict = None,
) -> Dict[str, np.ndarray]:
    """Fetch historical K-line data from Binance Futures.

    Returns dict with open/high/low/close/volume as numpy arrays,
    plus timestamps list.
    """
    sym = _format_symbol(symbol)

    if config is None:
        try:
            config = _load_config()
        except:
            config = {}

    ex = ccxt.binance({
        'enableRateLimit': True,
        'timeout': 30000,
    })
    if config.get('proxy'):
        ex.proxies = config['proxy']
    ex.options['defaultType'] = 'future'

    since = ex.parse8601((datetime.now() - timedelta(days=days)).isoformat() + 'Z')

    all_candles = []
    fetched_since = since

    print(f"  获取 {sym} {days}天 {timeframe} K线数据...")

    while True:
        try:
            candles = ex.fetch_ohlcv(sym, timeframe, since=fetched_since, limit=1000)
        except Exception as e:
            print(f"  请求失败: {e}, 重试...")
            time.sleep(2)
            continue

        if not candles or len(candles) == 0:
            break

        all_candles.extend(candles)

        if len(candles) < 1000:
            break

        fetched_since = candles[-1][0] + 1  # ms after last candle
        time.sleep(0.2)  # Rate limit

    if len(all_candles) < BACKTEST_CONFIG["warmup_bars"]:
        raise ValueError(f"数据不足: 仅 {len(all_candles)} 根K线 (需要≥{BACKTEST_CONFIG['warmup_bars']})")

    # Remove duplicates (by timestamp)
    seen = set()
    unique = []
    for c in all_candles:
        if c[0] not in seen:
            seen.add(c[0])
            unique.append(c)

    unique.sort(key=lambda x: x[0])

    timestamps = [datetime.fromtimestamp(c[0] / 1000) for c in unique]
    opens = np.array([c[1] for c in unique], dtype=np.float64)
    highs = np.array([c[2] for c in unique], dtype=np.float64)
    lows = np.array([c[3] for c in unique], dtype=np.float64)
    closes = np.array([c[4] for c in unique], dtype=np.float64)
    volumes = np.array([c[5] for c in unique], dtype=np.float64)

    n = len(unique)
    print(f"  获取完成: {n} 根K线 ({timestamps[0]} → {timestamps[-1]})")

    return {
        "open": opens,
        "high": highs,
        "low": lows,
        "close": closes,
        "volume": volumes,
        "timestamps": timestamps,
        "n": n,
        "symbol": sym,
    }


def slice_to_candles(data: Dict, end_idx: int) -> List[Dict]:
    """Convert numpy arrays from [0:end_idx+1] to candle dicts list.

    Used to create point-in-time snapshots for pattern detection.
    """
    candles = []
    for i in range(end_idx + 1):
        candles.append({
            "open": float(data["open"][i]),
            "high": float(data["high"][i]),
            "low": float(data["low"][i]),
            "close": float(data["close"][i]),
            "volume": float(data["volume"][i]),
        })
    return candles


# ============================================================
# POSITION
# ============================================================

@dataclass
class Position:
    symbol: str
    direction: str            # "long" | "short"
    entry_price: float
    entry_idx: int
    stop_loss: float
    take_profit: float
    time_stop_idx: int
    leverage: float
    size_usdt: float          # Position size in USDT
    margin: float             # Margin used
    risk_usdt: float          # Max loss if stopped out

    # Tracked during walk
    exit_price: float = 0
    exit_idx: int = 0
    exit_reason: str = ""     # "tp" | "sl" | "time" | "daily_limit"
    pnl_usdt: float = 0
    pnl_pct: float = 0
    bars_held: int = 0


# ============================================================
# BACKTEST ENGINE
# ============================================================

class BacktestEngine:
    """Walk-forward backtest engine for demon strategy."""

    def __init__(self, symbol: str, capital: float = 1000, config: dict = None):
        self.symbol = _format_symbol(symbol)
        self.initial_capital = capital
        self.capital = capital
        self.config = config
        self.cfg = BACKTEST_CONFIG

        # Data
        self.data: Dict = {}
        self.warmup = self.cfg["warmup_bars"]

        # State
        self.positions: List[Position] = []
        self.closed_trades: List[Position] = []
        self.equity_curve: List[float] = []
        self.daily_pnl: Dict[str, float] = {}  # date → pnl
        self.max_capital = capital
        self.min_capital = capital
        self.cooling_until: int = 0  # candle index when cooling ends
        self.daily_stopped: Dict[str, bool] = {}  # date → stopped

        self.entry_fills = 0
        self.signal_checks = 0
        self.max_score_seen = 0
        self.max_score_at = "N/A"

    # ── Signal Detection at a Point in Time ────────────────

    def _check_signals(self, idx: int) -> Tuple[bool, int, int, Dict]:
        """Run pattern detection at candle index `idx`.

        Only uses data up to idx (no look-ahead).
        Returns (triggered, score, pattern_count, details).
        """
        self.signal_checks += 1

        candles = slice_to_candles(self.data, idx)
        arr = _candles_to_arrays(candles)

        if arr["n"] < self.warmup:
            return False, 0, 0, {}

        details = {
            "price": float(arr["close"][-1]),
            "patterns": {},
            "bonus": {"score": 0, "descs": []},
            "vol_score": 0,
        }

        total = 0
        pattern_count = 0
        has_breakout = False

        # Pattern detection
        rocket_hit, rocket_desc = detect_rocket_launch(arr)
        details["patterns"]["rocket"] = {"hit": rocket_hit, "desc": rocket_desc}
        if rocket_hit:
            total += STRATEGY_CONFIG["weight_rocket"]
            pattern_count += 1
            has_breakout = True

        vbrk_hit, vbrk_desc = detect_volume_breakout(arr)
        details["patterns"]["volume_breakout"] = {"hit": vbrk_hit, "desc": vbrk_desc}
        if vbrk_hit:
            total += STRATEGY_CONFIG["weight_volume_breakout"]
            pattern_count += 1
            has_breakout = True

        flag_hit, flag_desc = detect_flag_breakout(arr)
        details["patterns"]["flag_breakout"] = {"hit": flag_hit, "desc": flag_desc}
        if flag_hit:
            total += STRATEGY_CONFIG["weight_flag_breakout"]
            pattern_count += 1
            has_breakout = True

        diverge_hit, diverge_desc = detect_bullish_divergence(arr)
        details["patterns"]["divergence"] = {"hit": diverge_hit, "desc": diverge_desc}
        if diverge_hit:
            total += STRATEGY_CONFIG["weight_divergence"]
            pattern_count += 1

        # Bonus indicators
        bonus_score, bonus_descs = check_bonus_indicators(arr)
        total += bonus_score
        details["bonus"] = {"score": bonus_score, "descs": bonus_descs}

        # Volume surge (as proxy for OI+Vol combo)
        vol_current = arr["volume"][-1]
        vol_ma20 = np.mean(arr["volume"][-20:]) if arr["n"] >= 20 else 0
        vol_score, vol_desc = score_volume_surge(vol_current, vol_ma20)
        details["vol_score"] = vol_score
        details["vol_desc"] = vol_desc

        total = round(total, 1)

        # Track max score
        if total > self.max_score_seen:
            self.max_score_seen = total
            ts = self.data["timestamps"][idx] if self.data.get("timestamps") else ""
            self.max_score_at = str(ts)

        triggered = total >= self.cfg["signal_threshold"] and pattern_count >= self.cfg["min_patterns"]

        return triggered, total, pattern_count, details

    # ── Position Management ───────────────────────────────

    def _calculate_position_size(self, entry_price: float, stop_price: float,
                                  leverage: float) -> Tuple[float, float, float]:
        """Calculate position size based on risk rules.

        Returns (size_usdt, margin, risk_usdt).
        """
        risk_usdt = self.capital * self.cfg["risk_per_trade_pct"]
        stop_distance_pct = abs(entry_price - stop_price) / entry_price

        if stop_distance_pct < 0.002:
            stop_distance_pct = 0.002  # min 0.2% stop

        # Position size = risk / stop_distance (with leverage multiplier)
        size_usdt = risk_usdt / stop_distance_pct
        # Cap at capital * max_positions
        max_size = self.capital * 0.95
        size_usdt = min(size_usdt, max_size)
        margin = size_usdt / leverage

        return size_usdt, margin, risk_usdt

    def _open_position(self, idx: int, signal_details: Dict):
        """Open a new position at candle index idx."""
        entry_price = self.data["close"][idx]

        # Apply slippage (worse for taker)
        entry_price = entry_price * (1 + self.cfg["slippage_pct"])

        stop_loss = entry_price * (1 + self.cfg["stop_loss_pct"])
        take_profit = entry_price * (1 + self.cfg["take_profit_pct"])
        leverage = self.cfg["default_leverage"]
        time_stop_idx = idx + self.cfg["time_stop_bars"]

        size_usdt, margin, risk_usdt = self._calculate_position_size(
            entry_price, stop_loss, leverage
        )

        if size_usdt < 10:  # Min position size
            return

        pos = Position(
            symbol=self.symbol,
            direction="long",
            entry_price=entry_price,
            entry_idx=idx,
            stop_loss=stop_loss,
            take_profit=take_profit,
            time_stop_idx=time_stop_idx,
            leverage=leverage,
            size_usdt=size_usdt,
            margin=margin,
            risk_usdt=risk_usdt,
        )

        self.positions.append(pos)
        self.entry_fills += 1

    def _check_exits(self, idx: int):
        """Check all open positions for exit conditions."""
        for pos in self.positions[:]:  # iterate copy
            high = self.data["high"][idx]
            low = self.data["low"][idx]
            close = self.data["close"][idx]
            ts = self.data["timestamps"][idx]

            exit_price = 0
            reason = ""

            # Check stop loss
            if low <= pos.stop_loss:
                exit_price = pos.stop_loss
                reason = "sl"
            # Check take profit
            elif high >= pos.take_profit:
                exit_price = pos.take_profit
                reason = "tp"
            # Check time stop
            elif idx >= pos.time_stop_idx:
                exit_price = close
                reason = "time"
            # Check daily loss limit
            elif self._check_daily_stop(ts):
                exit_price = close
                reason = "daily_limit"

            if reason:
                pos.exit_price = exit_price
                pos.exit_idx = idx
                pos.exit_reason = reason
                pos.bars_held = idx - pos.entry_idx

                # Calculate PnL
                gross_pnl_pct = (exit_price - pos.entry_price) / pos.entry_price
                if reason == "sl":
                    gross_pnl_pct = (pos.stop_loss - pos.entry_price) / pos.entry_price

                # Apply fees (entry + exit)
                fee = self.cfg["fee_taker_pct"] * 2  # taker both sides
                net_pnl_pct = gross_pnl_pct - fee
                pos.pnl_pct = net_pnl_pct * pos.leverage
                pos.pnl_usdt = pos.size_usdt * net_pnl_pct

                # Update capital
                self.capital += pos.pnl_usdt
                if self.capital < 0:
                    self.capital = 0

                # Track equity
                self.max_capital = max(self.max_capital, self.capital)
                self.min_capital = min(self.min_capital, self.capital)

                # Daily PnL
                day_key = ts.strftime("%Y-%m-%d") if hasattr(ts, 'strftime') else str(ts)[:10]
                self.daily_pnl[day_key] = self.daily_pnl.get(day_key, 0) + pos.pnl_usdt

                # Move to closed
                self.closed_trades.append(pos)
                self.positions.remove(pos)

                # Cooling after SL
                if reason == "sl":
                    self.cooling_until = idx + self.cfg["cooling_bars"]

    def _check_daily_stop(self, ts) -> bool:
        """Check if daily loss limit reached."""
        day_key = ts.strftime("%Y-%m-%d") if hasattr(ts, 'strftime') else str(ts)[:10]
        daily_loss = self.daily_pnl.get(day_key, 0)
        if daily_loss <= -self.initial_capital * self.cfg["daily_loss_limit_pct"]:
            self.daily_stopped[day_key] = True
            return True
        return False

    # ── Main Loop ─────────────────────────────────────────

    def run(self) -> Dict:
        """Run the backtest.

        Returns dict with stats and trade log.
        """
        t0 = time.time()

        if not self.data:
            print("  获取历史数据...")
            self.data = fetch_historical_klines(
                self.symbol,
                timeframe=self.cfg["timeframe"],
                days=self.cfg["days"],
                config=self.config,
            )

        n = self.data["n"]
        self.equity_curve = [self.initial_capital] * self.warmup

        print(f"  回测 {self.symbol}: {n} 根K线 (前{self.warmup}根预热)")
        print(f"  区间: {self.data['timestamps'][self.warmup]} → {self.data['timestamps'][-1]}")

        report_interval = max(n // 10, 100)

        for i in range(self.warmup, n):
            # Progress
            if i % report_interval == 0:
                pct = (i - self.warmup) / (n - self.warmup) * 100
                print(f"  进度: {pct:.0f}% | 资金: ${self.capital:,.0f} | 持仓: {len(self.positions)} | 成交: {len(self.closed_trades)}")

            # Check exits first (to free up capital)
            self._check_exits(i)

            # Skip if cooling
            if i < self.cooling_until:
                self.equity_curve.append(self.capital)
                continue

            # Skip if max positions
            if len(self.positions) >= self.cfg["max_positions"]:
                self.equity_curve.append(self.capital)
                continue

            # Check signals
            triggered, score, pattern_count, details = self._check_signals(i)

            if triggered:
                self._open_position(i, details)

            # Track equity
            unrealized = 0
            for pos in self.positions:
                current_price = self.data["close"][i]
                pnl_pct = (current_price - pos.entry_price) / pos.entry_price
                unrealized += pos.size_usdt * (pnl_pct - self.cfg["fee_taker_pct"])

            self.equity_curve.append(self.capital + unrealized)

        # Close any remaining positions at last price
        final_price = self.data["close"][-1]
        for pos in self.positions[:]:
            pos.exit_price = final_price
            pos.exit_idx = n - 1
            pos.exit_reason = "eod"
            pos.bars_held = n - 1 - pos.entry_idx
            pnl_pct = (final_price - pos.entry_price) / pos.entry_price - self.cfg["fee_taker_pct"] * 2
            pos.pnl_pct = pnl_pct * pos.leverage
            pos.pnl_usdt = pos.size_usdt * pnl_pct
            self.capital += pos.pnl_usdt
            self.closed_trades.append(pos)
        self.positions = []

        elapsed = time.time() - t0
        print(f"  回测完成: {elapsed:.1f}s | 最终资金: ${self.capital:,.2f} | {len(self.closed_trades)} 笔交易")

        return self.generate_report()

    # ── Report ────────────────────────────────────────────

    def generate_report(self) -> Dict:
        """Generate comprehensive backtest report."""
        trades = self.closed_trades
        n_trades = len(trades)

        wins = [t for t in trades if t.pnl_usdt > 0]
        losses = [t for t in trades if t.pnl_usdt <= 0]
        n_wins = len(wins)
        n_losses = len(losses)
        win_rate = n_wins / n_trades * 100 if n_trades > 0 else 0

        avg_win = np.mean([t.pnl_usdt for t in wins]) if wins else 0
        avg_loss = abs(np.mean([t.pnl_usdt for t in losses])) if losses else 0
        profit_factor = (sum(t.pnl_usdt for t in wins) / abs(sum(t.pnl_usdt for t in losses))) if losses and sum(t.pnl_usdt for t in losses) != 0 else float('inf')
        if profit_factor == float('inf') and n_losses > 0:
            profit_factor = 999

        total_pnl = sum(t.pnl_usdt for t in trades)
        total_return_pct = (self.capital - self.initial_capital) / self.initial_capital * 100

        # Max drawdown from equity curve
        eq = np.array(self.equity_curve)
        peak = np.maximum.accumulate(eq)
        drawdowns = (peak - eq) / peak * 100
        max_dd = np.max(drawdowns) if len(drawdowns) > 0 else 0
        max_dd_idx = np.argmax(drawdowns) if len(drawdowns) > 0 else 0

        # Sharpe ratio (simplified: daily returns)
        if len(eq) > 288:  # at least 1 day at 5m
            daily_eq = eq[::288]  # sample daily
            daily_returns = np.diff(daily_eq) / daily_eq[:-1]
            sharpe = np.mean(daily_returns) / np.std(daily_returns) * np.sqrt(365) if np.std(daily_returns) > 0 else 0
        else:
            sharpe = 0

        # Calmar ratio
        calmar = abs(total_return_pct / max_dd) if max_dd > 0 else 0

        # Avg bars held
        avg_bars = np.mean([t.bars_held for t in trades]) if trades else 0

        # Exit reason distribution
        exit_reasons = {}
        for t in trades:
            exit_reasons[t.exit_reason] = exit_reasons.get(t.exit_reason, 0) + 1

        # Daily stats
        positive_days = sum(1 for v in self.daily_pnl.values() if v > 0)
        negative_days = sum(1 for v in self.daily_pnl.values() if v < 0)
        total_days = len(self.daily_pnl)

        # Top/bottom trades
        sorted_trades = sorted(trades, key=lambda t: t.pnl_usdt, reverse=True)
        top_3 = sorted_trades[:3]
        bottom_3 = sorted_trades[-3:]
        # Signal stats
        report = {
            "symbol": self.symbol,
            "period": {
                "start": str(self.data["timestamps"][self.warmup]) if self.data.get("timestamps") else "N/A",
                "end": str(self.data["timestamps"][-1]) if self.data.get("timestamps") else "N/A",
                "candles": self.data.get("n", 0),
            },
            "capital": {
                "initial": self.initial_capital,
                "final": round(self.capital, 2),
                "peak": round(self.max_capital, 2),
                "trough": round(self.min_capital, 2),
            },
            "performance": {
                "total_return_pct": round(total_return_pct, 2),
                "total_pnl_usdt": round(total_pnl, 2),
                "sharpe_ratio": round(sharpe, 2),
                "calmar_ratio": round(calmar, 2),
                "max_drawdown_pct": round(max_dd, 2),
            },
            "trades": {
                "total": n_trades,
                "wins": n_wins,
                "losses": n_losses,
                "win_rate_pct": round(win_rate, 1),
                "profit_factor": round(min(profit_factor, 999), 2),
                "avg_win_usdt": round(avg_win, 2),
                "avg_loss_usdt": round(avg_loss, 2),
                "avg_bars_held": round(avg_bars, 1),
                "exit_reasons": exit_reasons,
            },
            "daily": {
                "total_days": total_days,
                "positive_days": positive_days,
                "negative_days": negative_days,
                "daily_stops_triggered": sum(1 for v in self.daily_stopped.values() if v),
            },
            "top_trades": [
                {"price": t.entry_price, "pnl": round(t.pnl_usdt, 2),
                 "pnl_pct": round(t.pnl_pct, 2), "bars": t.bars_held,
                 "exit": t.exit_reason}
                for t in (sorted_trades[:3] if n_trades > 0 else [])
            ],
            "worst_trades": [
                {"price": t.entry_price, "pnl": round(t.pnl_usdt, 2),
                 "pnl_pct": round(t.pnl_pct, 2), "bars": t.bars_held,
                 "exit": t.exit_reason}
                for t in (sorted_trades[-3:] if n_trades > 0 else [])
            ],
            "signal_stats": {
                "checks": self.signal_checks,
                "entry_fills": self.entry_fills,
                "fill_rate_pct": round(self.entry_fills / max(self.signal_checks, 1) * 100, 2),
                "max_score_seen": getattr(self, 'max_score_seen', 0),
                "max_score_at": getattr(self, 'max_score_at', "N/A"),
            },
        }

        # Verdict
        if n_trades == 0:
            report["verdict"] = "⚠️ 无交易信号，策略在回测期间未触发"
        elif win_rate >= 55 and profit_factor >= 1.5 and max_dd < 30:
            report["verdict"] = "✅ 策略达标，建议上线"
        elif win_rate >= 45 and profit_factor >= 1.2:
            report["verdict"] = "⚠️ 策略边缘，需优化参数"
        else:
            report["verdict"] = "❌ 策略未达标，不建议上线"

        return report


# ============================================================
# REPORT FORMATTING
# ============================================================

def format_report(report: Dict) -> str:
    """Format backtest report for human reading."""
    r = report
    p = r.get("performance", {})
    t = r.get("trades", {})
    c = r.get("capital", {})
    d = r.get("daily", {})

    lines = []
    lines.append("=" * 60)
    lines.append(f"  🔬 Demon Strategy 回测报告 — {r['symbol']}")
    lines.append("=" * 60)

    period = r.get("period", {})
    lines.append(f"\n📅 回测区间: {period.get('start', 'N/A')} → {period.get('end', 'N/A')}")
    lines.append(f"   总K线: {period.get('candles', 0)} 根 (5m)")

    lines.append(f"\n💰 资金曲线:")
    lines.append(f"   初始: ${c.get('initial', 0):,.0f} → 最终: ${c.get('final', 0):,.0f}")
    lines.append(f"   峰值: ${c.get('peak', 0):,.0f} | 谷底: ${c.get('trough', 0):,.0f}")

    lines.append(f"\n📊 绩效指标:")
    lines.append(f"   总收益: {p.get('total_return_pct', 0):+.2f}% (${p.get('total_pnl_usdt', 0):+,.2f})")
    lines.append(f"   最大回撤: {p.get('max_drawdown_pct', 0):.2f}%")
    lines.append(f"   夏普比率: {p.get('sharpe_ratio', 0):.2f}")
    lines.append(f"   Calmar比率: {p.get('calmar_ratio', 0):.2f}")

    lines.append(f"\n📈 交易统计:")
    lines.append(f"   总交易: {t.get('total', 0)} | 胜: {t.get('wins', 0)} | 负: {t.get('losses', 0)}")
    lines.append(f"   胜率: {t.get('win_rate_pct', 0):.1f}%")
    lines.append(f"   盈亏比: {t.get('profit_factor', 0):.2f}")
    lines.append(f"   平均盈利: ${t.get('avg_win_usdt', 0):+,.2f} | 平均亏损: ${t.get('avg_loss_usdt', 0):,.2f}")
    lines.append(f"   平均持仓: {t.get('avg_bars_held', 0):.0f} 根K线")

    reasons = t.get("exit_reasons", {})
    if reasons:
        lines.append(f"   出场分布: {json.dumps(reasons)}")

    lines.append(f"\n📅 日统计:")
    lines.append(f"   交易天数: {d.get('total_days', 0)} | 盈利日: {d.get('positive_days', 0)} | 亏损日: {d.get('negative_days', 0)}")
    lines.append(f"   日止损触发: {d.get('daily_stops_triggered', 0)} 次")

    top = r.get("top_trades", [])
    if top:
        lines.append(f"\n🏆 最佳交易:")
        for t in top:
            lines.append(f"   ${t['entry_price']:.4f} → PnL: ${t['pnl']:+,.2f} ({t['pnl_pct']:+.1f}%) | {t['bars']}K | {t['exit']}")

    worst = r.get("worst_trades", [])
    if worst:
        lines.append(f"\n💀 最差交易:")
        for t in worst:
            lines.append(f"   ${t['entry_price']:.4f} → PnL: ${t['pnl']:+,.2f} ({t['pnl_pct']:+.1f}%) | {t['bars']}K | {t['exit']}")

    lines.append(f"\n{'='*60}")
    lines.append(f"  {r.get('verdict', 'N/A')}")
    lines.append(f"{'='*60}")

    return "\n".join(lines)


# ============================================================
# BATCH BACKTEST
# ============================================================

def batch_backtest(symbols: List[str], capital: float = 1000,
                   config: dict = None, top_n: int = None) -> List[Dict]:
    """Run backtest on multiple symbols."""
    if top_n:
        symbols = symbols[:top_n]

    results = []
    for i, sym in enumerate(symbols):
        print(f"\n[{i+1}/{len(symbols)}] {sym}")
        try:
            engine = BacktestEngine(sym, capital, config)
            report = engine.run()
            results.append(report)
        except Exception as e:
            print(f"  ❌ 失败: {e}")
            import traceback
            traceback.print_exc()

    # Sort by total return
    results.sort(key=lambda r: r.get("performance", {}).get("total_return_pct", 0), reverse=True)
    return results


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"

    if cmd == "help":
        print("""
Demon Strategy Backtest v1.0

Commands:
  backtest.py SOL/USDT        单币回测
  backtest.py report SOL/USDT  详细报告
  backtest.py batch 20         批量回测 Top 20 山寨币
  backtest.py quick            快速回测热门币种
""")

    elif cmd == "quick":
        symbols = ["SOL/USDT", "ARB/USDT", "OP/USDT", "SUI/USDT", "APT/USDT"]
        print(f"快速回测 {len(symbols)} 个币种...")
        results = batch_backtest(symbols, capital=1000)
        for r in results:
            p = r.get("performance", {})
            t = r.get("trades", {})
            print(f"\n{r['symbol']}: {p.get('total_return_pct', 0):+.1f}% | "
                  f"胜率{t.get('win_rate_pct', 0):.0f}% | "
                  f"PF{t.get('profit_factor', 0):.1f} | "
                  f"DD{p.get('max_drawdown_pct', 0):.1f}% | "
                  f"{t.get('total', 0)}笔")
            print(f"  → {r.get('verdict', 'N/A')}")

    elif cmd == "batch":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        # Fetch top symbols
        from signals import fetch_top_altcoins
        symbols = fetch_top_altcoins(n=n)
        print(f"批量回测 Top {len(symbols)} 山寨币...")
        results = batch_backtest(symbols, capital=1000)

        # Summary
        passing = [r for r in results if "达标" in r.get("verdict", "")]
        marginal = [r for r in results if "边缘" in r.get("verdict", "")]
        failing = [r for r in results if "未达标" in r.get("verdict", "")]

        print(f"\n{'='*60}")
        print(f"  批量回测总结")
        print(f"{'='*60}")
        print(f"  达标: {len(passing)} | 边缘: {len(marginal)} | 未达标: {len(failing)}")
        print(f"\n  ⭐ 达标币种:")
        for r in passing:
            p = r.get("performance", {})
            t = r.get("trades", {})
            print(f"    {r['symbol']}: {p.get('total_return_pct', 0):+.1f}% | PF{t.get('profit_factor', 0):.1f} | DD{p.get('max_drawdown_pct', 0):.1f}%")

    elif cmd == "report":
        sym = sys.argv[2] if len(sys.argv) > 2 else "SOL/USDT"
        engine = BacktestEngine(sym, capital=1000)
        report = engine.run()
        print(format_report(report))

        # Save JSON
        out_dir = os.path.join(os.path.dirname(__file__), "..", "references")
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f"backtest_{sym.replace('/', '_')}_{date.today().isoformat()}.json")
        with open(out_path, 'w') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        print(f"\n📁 详细报告已保存: {out_path}")

    else:
        # Assume it's a symbol
        sym = sys.argv[1]
        engine = BacktestEngine(sym, capital=1000)
        report = engine.run()
        print(format_report(report))
