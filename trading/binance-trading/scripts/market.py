"""
Binance Market Data Module
Price quotes, order books, K-lines, 24h stats, funding rates.
Uses CCXT for unified API access.
"""

import ccxt
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any


def _load_config() -> dict:
    """Load API config from references/config.json"""
    path = os.path.join(os.path.dirname(__file__), "..", "references", "config.json")
    if not os.path.exists(path):
        path = os.path.join(os.path.dirname(__file__), "..", "references", "config.example.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _get_exchange(config: dict = None) -> ccxt.Exchange:
    """Get configured Binance exchange instance."""
    if config is None:
        config = _load_config()

    exchange_config = {
        'apiKey': config.get('api_key', ''),
        'secret': config.get('secret_key', ''),
        'enableRateLimit': True,
        'timeout': 15000,
    }

    # Proxy support (REQUIRED for this environment)
    proxy = config.get('proxy')
    if proxy:
        exchange_config['proxies'] = {
            'http': proxy.get('http', 'http://127.0.0.1:1081'),
            'https': proxy.get('https', 'http://127.0.0.1:1081'),
        }

    # Market type
    default_market = config.get('default_market', 'spot')
    exchange_config['options'] = {'defaultType': default_market}

    # Use testnet if configured
    if config.get('testnet', False):
        exchange_config['urls'] = {
            'api': {
                'public': 'https://testnet.binance.vision/api/v3',
                'private': 'https://testnet.binance.vision/api/v3',
            }
        }

    return ccxt.binance(exchange_config)


# ============================================================
#  PRICE & TICKER
# ============================================================

def get_price(symbol: str, config: dict = None) -> dict:
    """Get current price for a symbol.

    Args:
        symbol: e.g. 'BTC/USDT', 'ETH/USDT'
    Returns:
        dict with symbol, bid, ask, mid, spread, timestamp
    """
    ex = _get_exchange(config)

    # Unified symbol format: ensure /USDT
    if '/' not in symbol:
        symbol = f"{symbol}/USDT"

    ticker = ex.fetch_ticker(symbol)
    return {
        "symbol": symbol,
        "bid": ticker.get('bid'),
        "ask": ticker.get('ask'),
        "mid": (ticker.get('bid', 0) + ticker.get('ask', 0)) / 2 if ticker.get('bid') and ticker.get('ask') else None,
        "spread": round(ticker.get('ask', 0) - ticker.get('bid', 0), 8) if ticker.get('bid') and ticker.get('ask') else None,
        "spread_pct": round((ticker.get('ask', 0) - ticker.get('bid', 0)) / ticker.get('ask', 1) * 100, 4) if ticker.get('bid') and ticker.get('ask') else None,
        "last": ticker.get('last'),
        "change_24h_pct": ticker.get('percentage'),
        "volume_24h": ticker.get('baseVolume'),
        "timestamp": datetime.now().isoformat(),
    }


def get_multi_price(symbols: List[str], config: dict = None) -> dict:
    """Get prices for multiple symbols at once.

    Args:
        symbols: list of symbols, e.g. ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
    """
    ex = _get_exchange(config)
    tickers = ex.fetch_tickers([s if '/' in s else f"{s}/USDT" for s in symbols])

    results = {}
    for sym in symbols:
        key = sym if '/' in sym else f"{sym}/USDT"
        t = tickers.get(key, {})
        results[sym] = {
            "price": t.get('last'),
            "change_24h_pct": t.get('percentage'),
            "volume_24h": t.get('baseVolume'),
        }
    return results


# ============================================================
#  K-LINES (CANDLESTICKS)
# ============================================================

def get_klines(symbol: str, timeframe: str = '1h', limit: int = 50,
               config: dict = None) -> dict:
    """Get OHLCV candlestick data.

    Args:
        symbol: e.g. 'BTC/USDT', 'ETH/USDT'
        timeframe: '1m', '5m', '15m', '1h', '4h', '1d', '1w'
        limit: number of candles (max 1000)
    """
    if '/' not in symbol:
        symbol = f"{symbol}/USDT"

    ex = _get_exchange(config)
    ohlcv = ex.fetch_ohlcv(symbol, timeframe, limit=limit)

    candles = []
    for row in ohlcv:
        candles.append({
            "time": datetime.fromtimestamp(row[0] / 1000).isoformat(),
            "open": row[1],
            "high": row[2],
            "low": row[3],
            "close": row[4],
            "volume": row[5],
        })

    # Calculate basic stats
    closes = [c['close'] for c in candles]
    if len(closes) >= 2:
        change = closes[-1] - closes[0]
        change_pct = (change / closes[0]) * 100
        high = max(c['high'] for c in candles)
        low = min(c['low'] for c in candles)
    else:
        change = change_pct = high = low = None

    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "candles": candles,
        "stats": {
            "count": len(candles),
            "change": round(change, 8) if change else None,
            "change_pct": round(change_pct, 4) if change_pct else None,
            "high": high,
            "low": low,
        }
    }


# ============================================================
#  ORDER BOOK
# ============================================================

def get_orderbook(symbol: str, depth: int = 10, config: dict = None) -> dict:
    """Get order book (bids and asks).

    Args:
        symbol: e.g. 'BTC/USDT'
        depth: number of levels per side
    """
    if '/' not in symbol:
        symbol = f"{symbol}/USDT"

    ex = _get_exchange(config)
    ob = ex.fetch_order_book(symbol, limit=depth)

    bids = ob['bids'][:depth]
    asks = ob['asks'][:depth]

    bid_vol = sum(b[1] for b in bids)
    ask_vol = sum(a[1] for a in asks)

    return {
        "symbol": symbol,
        "bids": [{"price": b[0], "amount": b[1]} for b in bids],
        "asks": [{"price": a[0], "amount": a[1]} for a in asks],
        "summary": {
            "best_bid": bids[0][0] if bids else None,
            "best_ask": asks[0][0] if asks else None,
            "spread": round(asks[0][0] - bids[0][0], 8) if bids and asks else None,
            "bid_volume": round(bid_vol, 4),
            "ask_volume": round(ask_vol, 4),
            "imbalance": round((bid_vol - ask_vol) / (bid_vol + ask_vol), 4) if (bid_vol + ask_vol) > 0 else 0,
        }
    }


# ============================================================
#  24H STATS
# ============================================================

def get_24h_stats(symbol: str, config: dict = None) -> dict:
    """Get 24-hour trading statistics."""
    if '/' not in symbol:
        symbol = f"{symbol}/USDT"

    ex = _get_exchange(config)
    ticker = ex.fetch_ticker(symbol)

    return {
        "symbol": symbol,
        "last_price": ticker.get('last'),
        "open_24h": ticker.get('open'),
        "high_24h": ticker.get('high'),
        "low_24h": ticker.get('low'),
        "change_24h": ticker.get('change'),
        "change_24h_pct": ticker.get('percentage'),
        "volume_24h": ticker.get('baseVolume'),
        "volume_24h_usdt": ticker.get('quoteVolume'),
        "vwap": ticker.get('vwap'),
        "bid": ticker.get('bid'),
        "ask": ticker.get('ask'),
    }


# ============================================================
#  FUNDING RATE (for perps)
# ============================================================

def get_funding_rate(symbol: str, config: dict = None) -> dict:
    """Get current funding rate for perpetual futures.

    Args:
        symbol: e.g. 'ETH/USDT' (will be mapped to ETH/USDT:USDT)
    """
    base = symbol.split('/')[0] if '/' in symbol else symbol
    future_sym = f"{base}/USDT:USDT"

    ex = _get_exchange(config)
    try:
        # Try to set market type to futures
        ex.options['defaultType'] = 'future'
        funding = ex.fetch_funding_rate(future_sym)
        ex.options['defaultType'] = 'spot'
        return {
            "symbol": future_sym,
            "funding_rate": funding.get('fundingRate'),
            "funding_rate_pct": round(funding.get('fundingRate', 0) * 100, 6),
            "funding_timestamp": funding.get('fundingTimestamp'),
            "next_funding_time": funding.get('nextFundingTime'),
            "mark_price": funding.get('markPrice'),
            "index_price": funding.get('indexPrice'),
        }
    except Exception:
        ex.options['defaultType'] = 'spot'
        return {"error": f"Funding rate not available for {future_sym}", "symbol": future_sym}


# ============================================================
#  MARKET OVERVIEW
# ============================================================

def market_overview(symbols: List[str] = None, config: dict = None) -> dict:
    """Get quick market overview for a watchlist.

    Default symbols if none provided: major crypto
    """
    if symbols is None:
        symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT',
                   'DOGE/USDT', 'ADA/USDT', 'AVAX/USDT', 'LINK/USDT', 'ARB/USDT']

    ex = _get_exchange(config)
    tickers = ex.fetch_tickers(symbols)

    overview = []
    for sym in symbols:
        t = tickers.get(sym, {})
        overview.append({
            "symbol": sym.replace('/USDT', ''),
            "price": t.get('last'),
            "change_24h": round(t.get('percentage') or 0, 2),
            "volume_m": round((t.get('quoteVolume') or 0) / 1_000_000, 2),
        })

    # Sort by volume
    overview.sort(key=lambda x: x['volume_m'], reverse=True)

    # Market summary
    avg_change = sum(o['change_24h'] for o in overview) / len(overview)
    gainers = sum(1 for o in overview if o['change_24h'] > 0)
    losers = sum(1 for o in overview if o['change_24h'] < 0)

    return {
        "timestamp": datetime.now().isoformat(),
        "watchlist": overview,
        "summary": {
            "avg_change_pct": round(avg_change, 2),
            "gainers": gainers,
            "losers": losers,
            "flat": len(overview) - gainers - losers,
            "sentiment": "🟢" if gainers > losers * 1.5 else "🔴" if losers > gainers * 1.5 else "🟡"
        }
    }


# === CLI ===
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        sym = sys.argv[2] if len(sys.argv) > 2 else 'BTC/USDT'

        if cmd == 'price':
            print(json.dumps(get_price(sym), indent=2))
        elif cmd == 'klines':
            tf = sys.argv[3] if len(sys.argv) > 3 else '1h'
            print(json.dumps(get_klines(sym, tf), indent=2, default=str))
        elif cmd == 'orderbook':
            print(json.dumps(get_orderbook(sym), indent=2))
        elif cmd == 'overview':
            watchlist = sys.argv[2:] if len(sys.argv) > 2 else None
            print(json.dumps(market_overview(watchlist), indent=2))
        elif cmd == 'funding':
            print(json.dumps(get_funding_rate(sym), indent=2))
        else:
            print(f"Unknown command: {cmd}")
    else:
        # Default: overview
        print(json.dumps(market_overview(), indent=2))
