"""
Kelly Criterion Module
Calculates optimal position sizing for crypto futures trading.

Kelly Formula:
  f* = (p * b - q) / b
  
where:
  f* = fraction of capital to risk
  p  = probability of winning
  q  = 1 - p (probability of losing)  
  b  = win/loss ratio (avg win / avg loss)

Conservative implementation:
  - Half-Kelly (f*/2) by default
  - Max position cap (避免黑天鹅)
  - Requires explicit win_probability input (不替你判断)
"""

import json
import math
from datetime import datetime
from typing import Dict, Optional, Tuple


def kelly_position_size(
    capital: float,
    win_probability: float,
    avg_win: float,
    avg_loss: float,
    fraction: float = 0.5,  # Half-Kelly default
    max_risk_pct: float = 0.25,  # Max 25% of capital
) -> Dict:
    """Calculate optimal position size using Kelly Criterion.

    Args:
        capital: Total trading capital (USDT)
        win_probability: Estimated probability of winning (0.0 - 1.0)
        avg_win: Expected average profit per winning trade (in USDT or %)
        avg_loss: Expected average loss per losing trade (in USDT or %)
        fraction: Kelly fraction (0.5 = Half-Kelly, 1.0 = Full-Kelly)
        max_risk_pct: Maximum percentage of capital to risk (safety cap)

    Returns:
        Dict with f_star, risk_amount, position_size, leverage suggestion, warnings
    """
    if win_probability <= 0 or win_probability >= 1:
        return {"error": "Win probability must be between 0 and 1 (exclusive)"}
    if avg_loss <= 0:
        return {"error": "Average loss must be positive"}
    if capital <= 0:
        return {"error": "Capital must be positive"}

    # Convert to ratios if absolute values given
    if avg_loss > capital * 0.5:
        # Assume percentages
        b = avg_win / avg_loss
    else:
        b = avg_win / avg_loss

    p = win_probability
    q = 1 - p

    # Full Kelly
    f_star_full = (p * b - q) / b

    # Apply fraction (Half-Kelly default)
    f_star = f_star_full * fraction

    # Safety cap
    f_star = max(0, min(f_star, max_risk_pct))

    # Calculate position
    risk_amount = capital * f_star
    position_size = risk_amount * (avg_loss / avg_loss if avg_loss > 0 else 1)  # Simplified

    # Edge check
    edge = p * b - q
    edge_pct = edge * 100

    # Warnings
    warnings = []
    if f_star_full <= 0:
        warnings.append("⚠️ Kelly negative — 不值得交易，期望值为负")
    elif f_star_full < 0.02:
        warnings.append("⚠️ 边缘极薄 — 考虑更优入场点")
    if f_star > max_risk_pct * 0.8:
        warnings.append(f"⚠️ Kelly 接近上限 — 已被 cap 在 {max_risk_pct*100:.0f}%")
    if win_probability < 0.35:
        warnings.append("⚠️ 胜率偏低 — 需要极高的盈亏比才能盈利")
    if win_probability > 0.8:
        warnings.append("⚠️ 胜率过高 — 可能过度拟合或样本不足")

    return {
        "timestamp": datetime.now().isoformat(),
        "capital": round(capital, 2),
        "win_probability": round(win_probability, 4),
        "avg_win": round(avg_win, 4),
        "avg_loss": round(avg_loss, 4),
        "win_loss_ratio": round(b, 4),
        "edge_pct": round(edge_pct, 2),
        "f_star_full": round(f_star_full, 4),
        "f_star_applied": round(f_star, 4),
        "fraction": fraction,
        "risk_amount": round(risk_amount, 2),
        "risk_pct": round(f_star * 100, 2),
        "verdict": "✅ 可交易" if f_star_full > 0.02 else (
            "⚠️ 边缘交易" if f_star_full > 0 else "❌ 不值得交易"
        ),
        "warnings": warnings,
        "max_loss_cap": round(capital * max_risk_pct, 2),
    }


def kelly_from_historical(
    capital: float,
    wins: int,
    losses: int,
    total_win_amount: float = None,
    total_loss_amount: float = None,
    fraction: float = 0.5,
) -> Dict:
    """Calculate Kelly from historical win/loss data.

    Args:
        capital: Current capital
        wins: Number of winning trades
        losses: Number of losing trades
        total_win_amount: Total profit from wins (optional, default: wins * 1)
        total_loss_amount: Total loss from losses (optional, default: losses * 1)
    """
    total = wins + losses
    if total == 0:
        return {"error": "No trade history"}

    p = wins / total
    avg_win = total_win_amount / wins if total_win_amount and wins > 0 else 1.0
    avg_loss = total_loss_amount / losses if total_loss_amount and losses > 0 else 1.0

    return kelly_position_size(capital, p, avg_win, avg_loss, fraction)


def kelly_leverage(
    capital: float,
    win_prob: float,
    avg_win_pct: float,
    avg_loss_pct: float,
    max_leverage: float = 20,
    fraction: float = 0.5,
) -> Dict:
    """Calculate optimal leverage for futures trading.

    Args:
        capital: Total capital
        win_prob: Win probability
        avg_win_pct: Average win as percentage (e.g., 5 for 5%)
        avg_loss_pct: Average loss as percentage (e.g., 3 for 3%)
        max_leverage: Maximum allowed leverage (Binance max = 125, suggested cap = 20)
        fraction: Kelly fraction

    Returns:
        Dict with recommended leverage, position notional, etc.
    """
    b = avg_win_pct / avg_loss_pct
    p = win_prob
    q = 1 - p

    f_star = (p * b - q) / b
    f_star = f_star * fraction
    f_star = max(0, f_star)

    # Leverage = f_star / avg_loss_pct (simplified)
    # If you risk f_star of capital, and avg loss is avg_loss_pct,
    # then position size = capital * (f_star / avg_loss_pct)
    if avg_loss_pct > 0:
        notional_multiplier = f_star / (avg_loss_pct / 100)
        leverage = min(notional_multiplier, max_leverage)
    else:
        leverage = 1
        notional_multiplier = 1

    position_notional = capital * leverage

    return {
        "capital": round(capital, 2),
        "win_prob": round(win_prob, 4),
        "avg_win_pct": avg_win_pct,
        "avg_loss_pct": avg_loss_pct,
        "f_star": round(f_star, 4),
        "recommended_leverage": round(leverage, 1),
        "position_notional": round(position_notional, 2),
        "margin_required": round(position_notional / leverage * (1 / leverage) if leverage > 0 else 0, 2) if leverage > 0 else 0,
        "liquidation_risk": "高" if leverage > 10 else "中" if leverage > 5 else "低",
        "verdict": "✅ 安全" if leverage <= max_leverage * 0.5 else "⚠️ 注意杠杆" if leverage <= max_leverage else "❌ 杠杆过高",
    }


def kelly_quick(capital: float, win_prob: float, reward_risk_ratio: float,
                fraction: float = 0.5) -> Dict:
    """Quick Kelly check with simple reward/risk ratio.

    Args:
        capital: Total capital
        win_prob: Estimated win probability
        reward_risk_ratio: Reward:Risk ratio (e.g., 2.0 means 2:1 reward/risk)
        fraction: Kelly fraction
    """
    return kelly_position_size(
        capital=capital,
        win_probability=win_prob,
        avg_win=reward_risk_ratio,
        avg_loss=1.0,
        fraction=fraction,
    )


def format_kelly_report(result: Dict) -> str:
    """Format Kelly result as readable report."""
    if "error" in result:
        return f"❌ {result['error']}"

    lines = []
    lines.append(f"## 📊 凯利仓位计算")
    lines.append(f"")
    lines.append(f"| 参数 | 值 |")
    lines.append(f"|------|-----|")
    lines.append(f"| 资金 | {result.get('capital', 0):,.2f} USDT |")
    lines.append(f"| 胜率 | {result.get('win_probability', result.get('win_prob', 0))*100:.1f}% |")
    lines.append(f"| 盈亏比 | {result.get('win_loss_ratio', 0):.2f} |")
    lines.append(f"| 期望优势 | {result.get('edge_pct', 0):.1f}% |")
    lines.append(f"| 凯利比例 | {result.get('f_star_full', 0)*100:.1f}% |")
    lines.append(f"| 实际仓位 | {result.get('risk_pct', 0):.1f}% ({result.get('fraction', 0.5)*100:.0f}%-Kelly) |")
    lines.append(f"| 风险金额 | {result.get('risk_amount', 0):,.2f} USDT |")
    lines.append(f"| **结论** | **{result.get('verdict', 'N/A')}** |")

    if result.get('recommended_leverage'):
        lines.append(f"| 建议杠杆 | {result['recommended_leverage']}x |")
        lines.append(f"| 名义仓位 | {result.get('position_notional', 0):,.2f} USDT |")

    if result.get('warnings'):
        lines.append(f"")
        for w in result['warnings']:
            lines.append(f"- {w}")

    return "\n".join(lines)


# === CLI ===
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 5:
        print("Usage: python kelly.py <capital> <win_prob> <avg_win> <avg_loss> [fraction]")
        print("Example: python kelly.py 1000 0.55 2.0 1.0 0.5")
        sys.exit(1)

    capital = float(sys.argv[1])
    win_prob = float(sys.argv[2])
    avg_win = float(sys.argv[3])
    avg_loss = float(sys.argv[4])
    fraction = float(sys.argv[5]) if len(sys.argv) > 5 else 0.5

    result = kelly_quick(capital, win_prob, avg_win / avg_loss if avg_loss > 0 else 2.0, fraction)
    print(format_kelly_report(result))
