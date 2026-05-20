"""
Portfolio Tracking Module
Manual trade log, PnL calculation, performance analytics.
Supplements live exchange data with manual tracking for precision.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional


PORTFOLIO_DIR = os.path.join(os.path.dirname(__file__), "..", "references")
TRADES_FILE = os.path.join(PORTFOLIO_DIR, "trades.json")


def _load_trades() -> List[dict]:
    """Load trade log from JSON."""
    if not os.path.exists(TRADES_FILE):
        return []
    with open(TRADES_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def _save_trades(trades: List[dict]):
    """Save trade log to JSON."""
    os.makedirs(PORTFOLIO_DIR, exist_ok=True)
    with open(TRADES_FILE, "w", encoding="utf-8") as f:
        json.dump(trades, f, indent=2, ensure_ascii=False)


def log_trade(symbol: str, side: str, amount: float, price: float,
              cost: float = None, fee: float = 0, notes: str = "",
              timestamp: str = None) -> dict:
    """Log a trade manually.

    Args:
        symbol: e.g. 'ETH/USDT'
        side: 'buy' or 'sell'
        amount: base currency amount
        price: execution price
        cost: total cost (calculated if not provided)
        fee: fee in quote currency
        notes: optional notes (reasoning, tags)
        timestamp: ISO timestamp (defaults to now)
    """
    if cost is None:
        cost = amount * price

    trade = {
        "id": len(_load_trades()) + 1,
        "symbol": symbol,
        "side": side.lower(),
        "amount": amount,
        "price": price,
        "cost": round(cost, 8),
        "fee": fee,
        "net_cost": round(cost + fee, 8),
        "notes": notes,
        "timestamp": timestamp or datetime.now().isoformat(),
    }

    trades = _load_trades()
    trades.append(trade)
    _save_trades(trades)

    return trade


def get_trades(symbol: str = None, side: str = None, limit: int = 50) -> dict:
    """Get logged trades with filters.

    Args:
        symbol: filter by symbol
        side: filter by 'buy' or 'sell'
        limit: max trades to return
    """
    trades = _load_trades()

    if symbol:
        trades = [t for t in trades if t['symbol'] == symbol]
    if side:
        trades = [t for t in trades if t['side'] == side.lower()]

    trades = trades[-limit:]

    return {
        "count": len(trades),
        "trades": list(reversed(trades)),  # newest first
    }


def get_pnl(symbol: str = None, current_prices: dict = None) -> dict:
    """Calculate PnL from trade log.

    For closed positions: realized PnL
    For open positions: unrealized PnL based on current prices

    Args:
        symbol: filter by symbol
        current_prices: dict of {symbol: price} for unrealized PnL
    """
    trades = _load_trades()

    if symbol:
        trades = [t for t in trades if t['symbol'] == symbol]

    # Group by symbol
    positions = {}
    for t in trades:
        sym = t['symbol']
        if sym not in positions:
            # Extract base asset
            base = sym.split('/')[0]
            positions[sym] = {
                "symbol": sym,
                "base": base,
                "buys": [],
                "sells": [],
                "total_bought": 0,
                "total_sold": 0,
                "total_cost": 0,
                "total_revenue": 0,
                "total_fees": 0,
            }

        pos = positions[sym]
        pos['total_fees'] += t['fee']

        if t['side'] == 'buy':
            pos['buys'].append(t)
            pos['total_bought'] += t['amount']
            pos['total_cost'] += t['net_cost']
        else:
            pos['sells'].append(t)
            pos['total_sold'] += t['amount']
            pos['total_revenue'] += t['cost']  # cost for sell = revenue before fee

    # Calculate PnL per position
    results = []
    for sym, pos in positions.items():
        net_amount = pos['total_bought'] - pos['total_sold']

        # Realized PnL
        if pos['total_bought'] > 0:
            avg_entry = pos['total_cost'] / pos['total_bought']
        else:
            avg_entry = 0

        realized_pnl = pos['total_revenue'] - (
            pos['total_sold'] * avg_entry if pos['total_sold'] > 0 else 0
        ) - pos['total_fees']

        # Unrealized PnL
        unrealized_pnl = 0
        current_price = None
        if net_amount > 0.0001 and current_prices and sym in current_prices:
            current_price = current_prices[sym]
            unrealized_pnl = (current_price - avg_entry) * net_amount

        results.append({
            "symbol": sym,
            "net_amount": round(net_amount, 8),
            "avg_entry": round(avg_entry, 8),
            "current_price": current_price,
            "realized_pnl": round(realized_pnl, 2),
            "unrealized_pnl": round(unrealized_pnl, 2),
            "total_pnl": round(realized_pnl + unrealized_pnl, 2),
            "total_fees": round(pos['total_fees'], 4),
            "trade_count": len(pos['buys']) + len(pos['sells']),
            "status": "open" if net_amount > 0.0001 else "closed",
        })

    # Sort by total PnL
    results.sort(key=lambda x: x['total_pnl'], reverse=True)

    total_realized = sum(r['realized_pnl'] for r in results)
    total_unrealized = sum(r['unrealized_pnl'] for r in results)

    return {
        "timestamp": datetime.now().isoformat(),
        "positions": results,
        "summary": {
            "total_realized_pnl": round(total_realized, 2),
            "total_unrealized_pnl": round(total_unrealized, 2),
            "total_pnl": round(total_realized + total_unrealized, 2),
            "total_fees": round(sum(r['total_fees'] for r in results), 4),
            "open_positions": sum(1 for r in results if r['status'] == 'open'),
            "closed_positions": sum(1 for r in results if r['status'] == 'closed'),
            "total_trades": sum(r['trade_count'] for r in results),
        }
    }


def get_stats() -> dict:
    """Get trading statistics: win rate, avg PnL, best/worst trades."""
    trades = _load_trades()

    if not trades:
        return {"message": "No trades logged yet"}

    # Calculate per-trade PnL (simplified FIFO)
    buys = []
    total_buys = 0
    total_sells = 0
    win_count = 0
    pnls = []

    for t in trades:
        if t['side'] == 'buy':
            buys.append(t)
            total_buys += t['net_cost']
        elif t['side'] == 'sell' and buys:
            # Simple FIFO PnL
            entry = buys[0]
            pnl = t['cost'] - (entry['price'] * t['amount']) - t['fee'] - entry['fee']
            if entry['amount'] > t['amount']:
                entry['amount'] -= t['amount']
            else:
                buys.pop(0)
            pnls.append(pnl)
            total_sells += t['cost']
            if pnl > 0:
                win_count += 1

    if pnls:
        avg_pnl = sum(pnls) / len(pnls)
        win_rate = win_count / len(pnls) * 100 if pnls else 0
    else:
        avg_pnl = win_rate = 0

    return {
        "total_buys_volume": round(total_buys, 2),
        "total_sells_volume": round(total_sells, 2),
        "trade_pairs": len(pnls),
        "win_rate": round(win_rate, 1),
        "avg_pnl": round(avg_pnl, 2),
        "total_pnl": round(sum(pnls), 2),
        "best_trade": round(max(pnls), 2) if pnls else 0,
        "worst_trade": round(min(pnls), 2) if pnls else 0,
        "total_trades_logged": len(trades),
    }


if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'pnl'

    if cmd == 'log':
        # Example: python portfolio.py log ETH/USDT buy 0.5 3500
        sym = sys.argv[2]
        side = sys.argv[3]
        amount = float(sys.argv[4])
        price = float(sys.argv[5])
        notes = sys.argv[6] if len(sys.argv) > 6 else ""
        result = log_trade(sym, side, amount, price, notes=notes)
        print(json.dumps(result, indent=2))
    elif cmd == 'trades':
        sym = sys.argv[2] if len(sys.argv) > 2 else None
        print(json.dumps(get_trades(sym), indent=2))
    elif cmd == 'pnl':
        sym = sys.argv[2] if len(sys.argv) > 2 else None
        print(json.dumps(get_pnl(sym), indent=2))
    elif cmd == 'stats':
        print(json.dumps(get_stats(), indent=2))
    else:
        print(f"Unknown: {cmd}")
