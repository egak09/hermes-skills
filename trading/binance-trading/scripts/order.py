"""
Binance Order Management Module
Place orders, cancel orders, check order status.
⚠️ CRITICAL: This module can execute real trades with real money.
Use testnet mode for testing. Always confirm before placing orders.
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
    ec = {
        'apiKey': config.get('api_key', ''),
        'secret': config.get('secret_key', ''),
        'enableRateLimit': True,
        'timeout': 15000,
        'options': {'defaultType': config.get('default_market', 'spot')},
    }
    if config.get('proxy'):
        ec['proxies'] = config['proxy']
    if config.get('testnet', False):
        ec['urls'] = {'api': {'public': 'https://testnet.binance.vision/api/v3', 'private': 'https://testnet.binance.vision/api/v3'}}
    return ccxt.binance(ec)


# ============================================================
#  MARKET ORDERS
# ============================================================

def market_buy(symbol: str, amount: float, config: dict = None) -> dict:
    """Execute a market buy order.

    Args:
        symbol: e.g. 'ETH/USDT'
        amount: amount in QUOTE currency (USDT) or BASE (ETH)
                CCXT uses 'amount' parameter based on symbol
                For spot, amount = base currency amount
    """
    if '/' not in symbol:
        symbol = f"{symbol}/USDT"

    ex = _get_exchange(config)
    order = ex.create_market_buy_order(symbol, amount)

    return {
        "action": "BUY",
        "type": "MARKET",
        "symbol": symbol,
        "amount": order.get('amount'),
        "price": order.get('price'),
        "cost": order.get('cost'),
        "fee": order.get('fee'),
        "order_id": order.get('id'),
        "status": order.get('status'),
        "timestamp": datetime.now().isoformat(),
    }


def market_sell(symbol: str, amount: float, config: dict = None) -> dict:
    """Execute a market sell order."""
    if '/' not in symbol:
        symbol = f"{symbol}/USDT"

    ex = _get_exchange(config)
    order = ex.create_market_sell_order(symbol, amount)

    return {
        "action": "SELL",
        "type": "MARKET",
        "symbol": symbol,
        "amount": order.get('amount'),
        "price": order.get('price'),
        "cost": order.get('cost'),
        "fee": order.get('fee'),
        "order_id": order.get('id'),
        "status": order.get('status'),
        "timestamp": datetime.now().isoformat(),
    }


# ============================================================
#  LIMIT ORDERS
# ============================================================

def limit_buy(symbol: str, amount: float, price: float, config: dict = None) -> dict:
    """Place a limit buy order."""
    if '/' not in symbol:
        symbol = f"{symbol}/USDT"

    ex = _get_exchange(config)
    order = ex.create_limit_buy_order(symbol, amount, price)

    return {
        "action": "BUY",
        "type": "LIMIT",
        "symbol": symbol,
        "amount": amount,
        "price": price,
        "order_id": order.get('id'),
        "status": order.get('status'),
        "filled": order.get('filled', 0),
        "remaining": order.get('remaining', amount),
        "timestamp": datetime.now().isoformat(),
    }


def limit_sell(symbol: str, amount: float, price: float, config: dict = None) -> dict:
    """Place a limit sell order."""
    if '/' not in symbol:
        symbol = f"{symbol}/USDT"

    ex = _get_exchange(config)
    order = ex.create_limit_sell_order(symbol, amount, price)

    return {
        "action": "SELL",
        "type": "LIMIT",
        "symbol": symbol,
        "amount": amount,
        "price": price,
        "order_id": order.get('id'),
        "status": order.get('status'),
        "filled": order.get('filled', 0),
        "remaining": order.get('remaining', amount),
        "timestamp": datetime.now().isoformat(),
    }


# ============================================================
#  ORDER MANAGEMENT
# ============================================================

def cancel_order(order_id: str, symbol: str, config: dict = None) -> dict:
    """Cancel an open order."""
    if '/' not in symbol:
        symbol = f"{symbol}/USDT"

    ex = _get_exchange(config)
    result = ex.cancel_order(order_id, symbol)

    return {
        "order_id": order_id,
        "symbol": symbol,
        "status": result.get('status', 'canceled'),
        "timestamp": datetime.now().isoformat(),
    }


def cancel_all_orders(symbol: str = None, config: dict = None) -> dict:
    """Cancel all open orders, optionally filtered by symbol."""
    ex = _get_exchange(config)
    open_orders = ex.fetch_open_orders(symbol)

    canceled = []
    for order in open_orders:
        try:
            ex.cancel_order(order['id'], order['symbol'])
            canceled.append(order['id'])
        except Exception as e:
            canceled.append(f"FAILED: {order['id']} — {e}")

    return {
        "total_open": len(open_orders),
        "canceled": len(canceled),
        "order_ids": canceled,
        "timestamp": datetime.now().isoformat(),
    }


def get_open_orders(symbol: str = None, config: dict = None) -> dict:
    """Get all open orders."""
    ex = _get_exchange(config)
    orders = ex.fetch_open_orders(symbol)

    return {
        "timestamp": datetime.now().isoformat(),
        "count": len(orders),
        "orders": [
            {
                "id": o['id'],
                "symbol": o['symbol'],
                "side": o['side'],
                "type": o['type'],
                "price": o.get('price'),
                "amount": o['amount'],
                "filled": o.get('filled', 0),
                "remaining": o.get('remaining', o['amount']),
                "status": o['status'],
            }
            for o in orders
        ]
    }


def get_order_status(order_id: str, symbol: str, config: dict = None) -> dict:
    """Check status of a specific order."""
    if '/' not in symbol:
        symbol = f"{symbol}/USDT"

    ex = _get_exchange(config)
    order = ex.fetch_order(order_id, symbol)

    return {
        "id": order['id'],
        "symbol": order['symbol'],
        "side": order['side'],
        "type": order['type'],
        "price": order.get('price'),
        "amount": order['amount'],
        "filled": order.get('filled', 0),
        "remaining": order.get('remaining', 0),
        "cost": order.get('cost', 0),
        "fee": order.get('fee'),
        "status": order['status'],
        "timestamp": datetime.now().isoformat(),
    }


if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'help'

    commands = {
        "market-buy": "market_buy(symbol, amount)",
        "market-sell": "market_sell(symbol, amount)",
        "limit-buy": "limit_buy(symbol, amount, price)",
        "limit-sell": "limit_sell(symbol, amount, price)",
        "cancel": "cancel_order(order_id, symbol)",
        "cancel-all": "cancel_all_orders(symbol)",
        "open": "get_open_orders(symbol)",
        "status": "get_order_status(order_id, symbol)",
    }

    if cmd == 'help':
        print("=== Binance Order Commands ===")
        for c, desc in commands.items():
            print(f"  {c}: {desc}")
    elif cmd == 'open':
        sym = sys.argv[2] if len(sys.argv) > 2 else None
        print(json.dumps(get_open_orders(sym), indent=2))
    elif cmd == 'cancel-all':
        sym = sys.argv[2] if len(sys.argv) > 2 else None
        print(json.dumps(cancel_all_orders(sym), indent=2))
