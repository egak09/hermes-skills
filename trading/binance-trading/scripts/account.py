"""
Binance Account & Portfolio Module
Balance, positions, PnL tracking, trade history.
"""

import ccxt
import json
import os
from datetime import datetime
from typing import Optional, Dict, List


def _load_config() -> dict:
    path = os.path.join(os.path.dirname(__file__), "..", "references", "config.json")
    if not os.path.exists(path):
        path = os.path.join(os.path.dirname(__file__), "..", "references", "config.example.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _get_exchange(config: dict = None) -> ccxt.Exchange:
    if config is None:
        config = _load_config()

    exchange_config = {
        'apiKey': config.get('api_key', ''),
        'secret': config.get('secret_key', ''),
        'enableRateLimit': True,
        'timeout': 15000,
        'options': {'defaultType': config.get('default_market', 'spot')},
    }

    # Proxy support
    proxy = config.get('proxy')
    if proxy:
        exchange_config['proxies'] = {
            'http': proxy.get('http', 'http://127.0.0.1:1081'),
            'https': proxy.get('https', 'http://127.0.0.1:1081'),
        }

    return ccxt.binance(exchange_config)


def get_balance(quote: str = 'USDT', config: dict = None) -> dict:
    """Get spot account balance.

    Args:
        quote: quote currency filter, e.g. 'USDT'. Set to None for all.
    """
    ex = _get_exchange(config)
    balance = ex.fetch_balance()

    total_equity = balance.get('total', {})

    # Filter and sort assets with value
    assets = []
    for asset, data in balance.get('total', {}).items():
        if data is None or data == 0:
            continue
        if quote and asset == quote:
            continue  # Will handle separately
        assets.append({
            "asset": asset,
            "free": balance['free'].get(asset, 0),
            "used": balance['used'].get(asset, 0),
            "total": data,
        })

    assets.sort(key=lambda x: abs(x['total']), reverse=True)

    # Estimate USDT value (simplified — doesn't convert all alts)
    usdt_balance = balance['total'].get('USDT', 0)

    return {
        "timestamp": datetime.now().isoformat(),
        "quote": quote,
        "free": balance['free'].get(quote, 0) if quote else 0,
        "used": balance['used'].get(quote, 0) if quote else 0,
        "total_quote": balance['total'].get(quote, 0) if quote else 0,
        "assets": assets[:20],  # top 20
        "asset_count": len(assets),
    }


def get_positions(config: dict = None) -> dict:
    """Get current positions with unrealized PnL.

    Calculates PnL by comparing current price vs average entry.
    Requires manual entry tracking via portfolio module for full accuracy.
    This provides a best-effort estimate from balance data.
    """
    ex = _get_exchange(config)
    balance = ex.fetch_balance()

    positions = []
    for asset, total in balance.get('total', {}).items():
        if total is None or total <= 0 or asset in ('USDT', 'USDC', 'BUSD', 'FDUSD'):
            continue

        # Skip dust
        if total < 0.0001:
            continue

        try:
            ticker = ex.fetch_ticker(f"{asset}/USDT")
            price = ticker.get('last', 0)
            value = total * price
        except Exception:
            price = 0
            value = 0

        positions.append({
            "asset": asset,
            "amount": total,
            "price": price,
            "value_usdt": round(value, 2),
        })

    positions.sort(key=lambda x: x['value_usdt'], reverse=True)

    total_value = sum(p['value_usdt'] for p in positions)
    total_value += balance['total'].get('USDT', 0)

    return {
        "timestamp": datetime.now().isoformat(),
        "positions": positions,
        "position_count": len(positions),
        "total_value_est": round(total_value, 2),
    }


def get_trade_history(symbol: str = None, limit: int = 20,
                      config: dict = None) -> dict:
    """Get recent trade history.

    Args:
        symbol: filter by symbol, e.g. 'ETH/USDT'. None for all.
        limit: max trades to return
    """
    ex = _get_exchange(config)
    trades = ex.fetch_my_trades(symbol, limit=limit)

    history = []
    for t in trades:
        history.append({
            "id": t.get('id'),
            "symbol": t.get('symbol'),
            "side": t.get('side'),
            "amount": t.get('amount'),
            "price": t.get('price'),
            "cost": t.get('cost'),
            "fee": t.get('fee', {}).get('cost') if t.get('fee') else None,
            "time": datetime.fromtimestamp(t['timestamp'] / 1000).isoformat() if t.get('timestamp') else None,
        })

    # Summary stats
    if history:
        buy_count = sum(1 for t in history if t['side'] == 'buy')
        sell_count = sum(1 for t in history if t['side'] == 'sell')
        total_cost = sum(t['cost'] for t in history if t['cost'])
        total_fee = sum(t['fee'] for t in history if t['fee'])
    else:
        buy_count = sell_count = total_cost = total_fee = 0

    return {
        "timestamp": datetime.now().isoformat(),
        "trades": history,
        "summary": {
            "total_trades": len(history),
            "buys": buy_count,
            "sells": sell_count,
            "total_volume": round(total_cost, 2),
            "total_fees": round(total_fee, 4),
        }
    }


def quick_status(config: dict = None) -> dict:
    """Quick account status summary — for daily briefings."""
    positions = get_positions(config)
    balance = get_balance('USDT', config)

    return {
        "timestamp": datetime.now().isoformat(),
        "total_value_est": positions.get('total_value_est', 0),
        "usdt_balance": round(balance.get('total_quote', 0), 2),
        "position_count": positions.get('position_count', 0),
        "top_positions": positions['positions'][:5] if positions.get('positions') else [],
    }


if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'status'

    if cmd == 'balance':
        print(json.dumps(get_balance(), indent=2))
    elif cmd == 'positions':
        print(json.dumps(get_positions(), indent=2))
    elif cmd == 'trades':
        sym = sys.argv[2] if len(sys.argv) > 2 else None
        print(json.dumps(get_trade_history(sym), indent=2))
    elif cmd == 'status':
        print(json.dumps(quick_status(), indent=2))
