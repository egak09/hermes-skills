"""
Demon Strategy Risk Management (妖币风控系统)

Enforces:
  - Single trade risk ≤ 5% of capital
  - Daily loss ≥ 18% → halt all trading
  - Max 3 concurrent positions
  - Dynamic leverage adjustment
  - Black swan protection
"""

import json
import os
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field


# ============================================================
# CONFIG
# ============================================================

RISK_CONFIG = {
    "max_risk_per_trade_pct": 5.0,       # Max 5% per trade
    "max_daily_loss_pct": 18.0,          # Halt after 18% daily loss
    "max_concurrent_positions": 3,       # Max 3 open
    "max_leverage": 20,                  # Max leverage
    "default_leverage": 5,               # Default leverage
    "trailing_stop_activation": 2.0,     # Activate trailing after 2% profit
    "trailing_stop_distance": 1.5,       # Trail 1.5% behind
    "time_stop_minutes": 240,            # Max hold time 4 hours
    "take_profit_pct": 5.0,              # Default TP
    "stop_loss_pct": 3.0,                # Default SL
    "max_slippage_pct": 0.5,             # Max slippage
    "cooldown_minutes": 30,              # Cooldown after stop loss
}

# ============================================================
# STATE
# ============================================================

STATE_FILE = os.path.join(os.path.dirname(__file__), "..", "references", "risk_state.json")


def _load_state() -> dict:
    """Load risk state from file."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return _default_state()


def _default_state() -> dict:
    return {
        "trading_halted": False,
        "halt_reason": "",
        "daily_pnl": 0,
        "daily_pnl_pct": 0,
        "date": str(date.today()),
        "open_positions": [],
        "today_trades": [],
        "cooldown_until": None,
    }


def _save_state(state: dict):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)


# ============================================================
# RISK CHECKS
# ============================================================

def reset_daily():
    """Reset daily state at start of new day."""
    state = _default_state()
    _save_state(state)
    return state


def check_can_trade(capital: float) -> Tuple[bool, str]:
    """Check if trading is allowed right now.
    
    Returns (allowed, reason).
    """
    state = _load_state()
    
    # Check date reset
    today = str(date.today())
    if state.get("date") != today:
        state = reset_daily()
    
    # Check halted
    if state.get("trading_halted"):
        return False, f"交易已暂停: {state.get('halt_reason')}"
    
    # Check daily loss limit
    daily_loss_pct = abs(state.get("daily_pnl_pct", 0))
    if daily_loss_pct >= RISK_CONFIG["max_daily_loss_pct"]:
        state["trading_halted"] = True
        state["halt_reason"] = f"日亏损 {daily_loss_pct:.1f}% 超过上限 {RISK_CONFIG['max_daily_loss_pct']}%"
        _save_state(state)
        return False, state["halt_reason"]
    
    # Check max positions
    open_pos = state.get("open_positions", [])
    if len(open_pos) >= RISK_CONFIG["max_concurrent_positions"]:
        return False, f"持仓已满 ({len(open_pos)}/{RISK_CONFIG['max_concurrent_positions']})"
    
    # Check cooldown
    cooldown = state.get("cooldown_until")
    if cooldown:
        cooldown_dt = datetime.fromisoformat(cooldown)
        if datetime.now() < cooldown_dt:
            remaining = (cooldown_dt - datetime.now()).seconds // 60
            return False, f"冷却中 ({remaining}分钟)"
    
    # Check capital
    if capital <= 0:
        return False, "资金为零"
    
    return True, "可以交易"


def calculate_position_size(capital: float, entry_price: float, 
                           stop_loss_price: float, leverage: int = None) -> Dict:
    """Calculate position size based on risk rules.
    
    Single trade risk ≤ 5% means:
      loss_on_sl ≤ capital * 5%
      position_size = risk_amount / |entry - sl| * entry / leverage
    
    Returns dict with position details.
    """
    max_risk_amount = capital * (RISK_CONFIG["max_risk_per_trade_pct"] / 100)
    
    if leverage is None:
        leverage = RISK_CONFIG["default_leverage"]
    
    # Cap leverage
    leverage = min(leverage, RISK_CONFIG["max_leverage"])
    
    # SL distance
    sl_distance_pct = abs(entry_price - stop_loss_price) / entry_price
    
    if sl_distance_pct < 0.001:
        sl_distance_pct = 0.01  # Minimum 1%
    
    # Position size = risk_amount / sl_distance_pct
    # For futures: controlled by contract quantity
    position_notional = max_risk_amount / sl_distance_pct
    margin = position_notional / leverage
    contract_qty = position_notional / entry_price
    
    # Check margin vs capital
    if margin > capital * 0.5:
        # Reduce to 50% max margin usage
        margin = capital * 0.5
        position_notional = margin * leverage
        contract_qty = position_notional / entry_price
    
    return {
        "capital": round(capital, 2),
        "max_risk": round(max_risk_amount, 2),
        "leverage": leverage,
        "entry_price": entry_price,
        "stop_loss": stop_loss_price,
        "sl_distance_pct": round(sl_distance_pct * 100, 2),
        "position_notional": round(position_notional, 2),
        "margin_required": round(margin, 2),
        "contract_qty": round(contract_qty, 4),
        "max_loss": round(position_notional * sl_distance_pct, 2),
    }


def calculate_leverage(capital: float, volatility_pct: float, 
                       signal_score: float) -> int:
    """Dynamic leverage based on signal strength and volatility.
    
    Stronger signal + lower volatility = higher leverage
    Weaker signal + higher volatility = lower leverage
    """
    base = RISK_CONFIG["default_leverage"]
    max_lev = RISK_CONFIG["max_leverage"]
    
    # Signal multiplier (0.5 - 1.5)
    signal_factor = 0.5 + (signal_score / 100)
    
    # Volatility dampener (inverse)
    if volatility_pct > 10:
        vol_factor = 0.3
    elif volatility_pct > 5:
        vol_factor = 0.6
    elif volatility_pct > 3:
        vol_factor = 0.8
    else:
        vol_factor = 1.0
    
    leverage = int(base * signal_factor * vol_factor)
    leverage = max(1, min(leverage, max_lev))
    
    return leverage


def register_trade(symbol: str, side: str, amount: float, price: float, 
                   leverage: int, sl: float, tp: float) -> Dict:
    """Register a new trade in risk state."""
    state = _load_state()
    
    trade = {
        "id": len(state.get("today_trades", [])) + 1,
        "symbol": symbol,
        "side": side,
        "amount": amount,
        "entry_price": price,
        "leverage": leverage,
        "stop_loss": sl,
        "take_profit": tp,
        "entry_time": datetime.now().isoformat(),
        "status": "open",
        "pnl": 0,
        "pnl_pct": 0,
    }
    
    state.setdefault("today_trades", []).append(trade)
    state.setdefault("open_positions", []).append(trade)
    _save_state(state)
    
    return trade


def close_trade(trade_id: int, exit_price: float, pnl: float, pnl_pct: float):
    """Close a trade and update daily PnL."""
    state = _load_state()
    
    # Update daily PnL
    state["daily_pnl"] = round(state.get("daily_pnl", 0) + pnl, 2)
    
    # Find and update trade
    for trade in state.get("today_trades", []):
        if trade["id"] == trade_id:
            trade["status"] = "closed"
            trade["exit_price"] = exit_price
            trade["exit_time"] = datetime.now().isoformat()
            trade["pnl"] = round(pnl, 2)
            trade["pnl_pct"] = round(pnl_pct, 2)
    
    # Remove from open
    state["open_positions"] = [t for t in state.get("open_positions", []) 
                               if t["id"] != trade_id]
    
    # Check stop-loss → apply cooldown
    if pnl_pct < -RISK_CONFIG["stop_loss_pct"]:
        cooldown_until = datetime.now() + timedelta(minutes=RISK_CONFIG["cooldown_minutes"])
        state["cooldown_until"] = cooldown_until.isoformat()
    
    _save_state(state)
    return state


def get_risk_report() -> str:
    """Generate risk status report."""
    state = _load_state()
    
    lines = []
    lines.append("## 🛡️ 风控状态")
    lines.append(f"交易允许: {'❌ 已暂停' if state.get('trading_halted') else '✅ 正常'}")
    if state.get('halt_reason'):
        lines.append(f"暂停原因: {state['halt_reason']}")
    
    daily_pnl = state.get('daily_pnl', 0)
    emoji = "🔴" if daily_pnl < 0 else "🟢"
    lines.append(f"今日盈亏: {emoji} {daily_pnl:+.2f} USDT")
    
    lines.append(f"持仓数: {len(state.get('open_positions', []))}/{RISK_CONFIG['max_concurrent_positions']}")
    lines.append(f"今日交易: {len(state.get('today_trades', []))} 笔")
    
    cooldown = state.get('cooldown_until')
    if cooldown:
        cd_dt = datetime.fromisoformat(cooldown)
        if datetime.now() < cd_dt:
            remaining = (cd_dt - datetime.now()).seconds // 60
            lines.append(f"⏳ 冷却中: {remaining}分钟")
    
    lines.append(f"\n单笔风险上限: {RISK_CONFIG['max_risk_per_trade_pct']}%")
    lines.append(f"日亏损上限: {RISK_CONFIG['max_daily_loss_pct']}%")
    
    return "\n".join(lines)


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    # Reset and test
    reset_daily()
    
    print(get_risk_report())
    print()
    
    # Test position sizing
    print("=== 仓位计算示例 ===")
    result = calculate_position_size(
        capital=1000,
        entry_price=2.00,
        stop_loss_price=1.90,
        leverage=5
    )
    for k, v in result.items():
        print(f"  {k}: {v}")
    
    print()
    print("=== 杠杆动态调整 ===")
    for score, vol in [(85, 3), (70, 8), (90, 2)]:
        lev = calculate_leverage(1000, vol, score)
        print(f"  信号{score}分 波动{vol}% → {lev}x")
