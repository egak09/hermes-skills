"""
Demon Strategy Execution Engine (妖币执行引擎)

Features:
  - Batch open/close (分批开仓/平仓)
  - Trailing Stop (追踪止损)
  - Time-based Take Profit (时间止盈)
  - Dynamic leverage from risk module
"""

import time
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from dataclasses import dataclass, field

from risk import (
    RISK_CONFIG, calculate_position_size, calculate_leverage,
    register_trade, close_trade, check_can_trade, _load_state
)


@dataclass
class TrailingStop:
    """Tracks trailing stop for a position."""
    symbol: str
    entry_price: float
    highest_price: float
    trailing_pct: float
    active: bool = False
    stop_price: float = 0
    
    def update(self, current_price: float) -> Tuple[bool, float]:
        """Update trailing stop.
        
        Returns (stopped_out, current_stop_price).
        """
        if not self.active:
            # Check activation threshold
            profit_pct = (current_price - self.entry_price) / self.entry_price * 100
            if profit_pct >= RISK_CONFIG["trailing_stop_activation"]:
                self.active = True
                self.highest_price = current_price
                self.stop_price = current_price * (1 - RISK_CONFIG["trailing_stop_distance"] / 100)
        
        if self.active:
            if current_price > self.highest_price:
                self.highest_price = current_price
                self.stop_price = current_price * (1 - RISK_CONFIG["trailing_stop_distance"] / 100)
            
            if current_price <= self.stop_price:
                return True, self.stop_price
        
        return False, self.stop_price


@dataclass 
class TimeStop:
    """Tracks time-based exit."""
    entry_time: datetime
    max_hold_minutes: int
    
    def should_exit(self) -> bool:
        elapsed = (datetime.now() - self.entry_time).total_seconds() / 60
        return elapsed >= self.max_hold_minutes


# ============================================================
# BATCH EXECUTION
# ============================================================

def calculate_batch_entries(capital: float, entry_price: float,
                           stop_loss: float, leverage: int,
                           batches: int = 3) -> list:
    """Calculate batch entry sizes.
    
    Entry pattern: 50% / 30% / 20%
    """
    size_result = calculate_position_size(
        capital=capital,
        entry_price=entry_price,
        stop_loss_price=stop_loss,
        leverage=leverage
    )
    
    total_qty = size_result["contract_qty"]
    ratios = [0.5, 0.3, 0.2]
    
    batches = []
    for i, ratio in enumerate(ratios[:batches]):
        batches.append({
            "batch": i + 1,
            "ratio": ratio,
            "qty": round(total_qty * ratio, 4),
            "notional": round(size_result["position_notional"] * ratio, 2),
            "condition": "立即" if i == 0 else f"价格确认 +{0.5*i}%后"
        })
    
    return batches


def calculate_batch_exits(position_qty: float, batches: int = 3) -> list:
    """Calculate batch exit sizes.
    
    Exit pattern: 40% at TP1, 35% at TP2, 25% trailing
    """
    ratios = [0.4, 0.35, 0.25]
    exits = []
    
    tp_levels = [1.0, 2.0, None]  # TP multipliers (None = trailing)
    
    for i, (ratio, tp_mult) in enumerate(zip(ratios[:batches], tp_levels[:batches])):
        exits.append({
            "batch": i + 1,
            "ratio": ratio,
            "qty": round(position_qty * ratio, 4),
            "tp_multiplier": tp_mult,
            "type": "止盈" if tp_mult else "追踪止损"
        })
    
    return exits


# ============================================================
# EXECUTION SIMULATOR (Paper Trading)
# ============================================================

def simulate_trade(symbol: str, side: str, capital: float,
                   entry_price: float, stop_loss: float,
                   signal_score: float, volatility_pct: float,
                   config: dict = None) -> Dict:
    """Simulate a trade with full risk management.
    
    Returns complete trade plan for review before execution.
    """
    # 1. Check if can trade
    can_trade, reason = check_can_trade(capital)
    if not can_trade:
        return {"allowed": False, "reason": reason}
    
    # 2. Dynamic leverage
    leverage = calculate_leverage(capital, volatility_pct, signal_score)
    
    # 3. Position sizing
    position = calculate_position_size(capital, entry_price, stop_loss, leverage)
    
    # 4. Batch entries
    entries = calculate_batch_entries(capital, entry_price, stop_loss, leverage)
    
    # 5. Take profit levels
    tp1 = entry_price * (1 + RISK_CONFIG["take_profit_pct"] / 100)
    tp2 = entry_price * (1 + RISK_CONFIG["take_profit_pct"] * 1.5 / 100)
    
    # 6. Batch exits
    exits = calculate_batch_exits(position["contract_qty"])
    
    # 7. Time stop
    time_stop = RISK_CONFIG["time_stop_minutes"]
    
    return {
        "allowed": True,
        "symbol": symbol,
        "side": side,
        "signal_score": signal_score,
        "volatility_pct": round(volatility_pct, 1),
        "leverage": leverage,
        "entry_price": entry_price,
        "stop_loss": stop_loss,
        "take_profit_1": round(tp1, 6),
        "take_profit_2": round(tp2, 6),
        "position_size": position["contract_qty"],
        "position_notional": round(position["position_notional"], 2),
        "margin": round(position["margin_required"], 2),
        "max_loss": round(position["max_loss"], 2),
        "max_loss_pct": round(position["sl_distance_pct"], 2),
        "risk_reward": round(RISK_CONFIG["take_profit_pct"] / position["sl_distance_pct"], 1),
        "time_stop_minutes": time_stop,
        "batch_entries": entries,
        "batch_exits": exits,
        "trailing_activation": f"{RISK_CONFIG['trailing_stop_activation']}%",
        "trailing_distance": f"{RISK_CONFIG['trailing_stop_distance']}%",
        "timestamp": datetime.now().isoformat(),
    }


def format_trade_plan(plan: Dict) -> str:
    """Format a trade plan for display/review."""
    if not plan.get("allowed"):
        return f"❌ 不允许交易: {plan['reason']}"
    
    lines = []
    lines.append(f"## 📋 交易计划 — {plan['symbol']}")
    lines.append("")
    lines.append(f"| 参数 | 值 |")
    lines.append(f"|------|-----|")
    lines.append(f"| 方向 | {'🟢 做多' if plan['side'] == 'long' else '🔴 做空'} |")
    lines.append(f"| 信号分数 | {plan['signal_score']}分 |")
    lines.append(f"| 杠杆 | {plan['leverage']}x |")
    lines.append(f"| 入场价 | {plan['entry_price']} |")
    lines.append(f"| 止损价 | {plan['stop_loss']} |")
    lines.append(f"| 止盈1 | {plan['take_profit_1']} |")
    lines.append(f"| 止盈2 | {plan['take_profit_2']} |")
    lines.append(f"| 仓位 | {plan['position_size']:.4f} 张 |")
    lines.append(f"| 名义价值 | ${plan['position_notional']:,.2f} |")
    lines.append(f"| 保证金 | ${plan['margin']:,.2f} |")
    lines.append(f"| 最大亏损 | ${plan['max_loss']:,.2f} ({plan['max_loss_pct']}%) |")
    lines.append(f"| 盈亏比 | 1:{plan['risk_reward']} |")
    lines.append(f"| 追踪止损 | 激活{plan['trailing_activation']} 距离{plan['trailing_distance']} |")
    lines.append(f"| 时间止盈 | {plan['time_stop_minutes']}分钟 |")
    lines.append("")
    lines.append("### 分批入场")
    for b in plan.get('batch_entries', []):
        lines.append(f"- 第{b['batch']}批: {b['ratio']*100:.0f}% ({b['qty']:.4f}张) — {b['condition']}")
    lines.append("")
    lines.append("### 分批出场")
    for b in plan.get('batch_exits', []):
        tp_str = f"TP{b['tp_multiplier']}x" if b['tp_multiplier'] else "Trailing"
        lines.append(f"- 第{b['batch']}批: {b['ratio']*100:.0f}% ({b['qty']:.4f}张) — {tp_str}")
    
    return "\n".join(lines)


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    # Simulate a trade
    plan = simulate_trade(
        symbol="ARB/USDT",
        side="long",
        capital=1000,
        entry_price=0.12,
        stop_loss=0.114,
        signal_score=82,
        volatility_pct=5.5,
    )
    
    print(format_trade_plan(plan))
