"""
Demon Strategy Signal Engine (妖币策略信号引擎)
Scans Binance Futures for high-volatility altcoin signals based on:
  - OI (Open Interest) surge
  - Volume surge
  - K-line breakout patterns

Scoring: ≥78 points → signal triggered
"""

import json
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import deque

# Add binance-trading path for config loading and market data
_TRADING_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "binance-trading", "scripts")
sys.path.insert(0, _TRADING_DIR)
from market import get_klines, _load_config as _trading_load_config, _get_exchange as _trading_get_exchange

# ============================================================
# CONFIG
# ============================================================

STRATEGY_CONFIG = {
    "scan_interval_seconds": 180,  # 3 minutes
    "top_n_volume": 200,           # Top 200 by volume
    "signal_threshold": 78,        # Minimum score to trigger
    "oi_baseline_minutes": 30,     # OI baseline period
    "volume_baseline_bars": 20,    # Volume baseline (K-lines)
    "breakout_lookback": 20,       # K-line lookback for breakout
    "funding_rate_max": 0.1,       # Max funding rate (10% = skip)
    
    # Weights
    "weight_oi": 30,
    "weight_volume": 30,
    "weight_breakout": 40,
    
    # OI thresholds
    "oi_surge_major": 0.20,    # 20% surge → max score
    "oi_surge_moderate": 0.10, # 10% surge
    "oi_surge_minor": 0.05,    # 5% surge
    
    # Volume thresholds
    "vol_surge_major": 3.0,    # 3x avg
    "vol_surge_moderate": 2.0, # 2x avg
    "vol_surge_minor": 1.5,    # 1.5x avg
    
    # Blacklisted symbols
    "blacklist": ["BTC/USDT", "ETH/USDT"],  # Don't trade majors with this strategy
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


# ============================================================
# DATA FETCHING (via REST for simplicity; WebSocket for prod)
# ============================================================

def fetch_top_altcoins(config: dict = None, n: int = None) -> List[str]:
    """Fetch top N altcoins by 24h volume from Binance Futures.
    
    Returns list of symbols like 'SOL/USDT', 'ARB/USDT', etc.
    """
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
        
        # Filter USDT pairs, exclude blacklist
        candidates = []
        for sym, t in tickers.items():
            if not sym.endswith('/USDT') or _is_blacklisted(sym):
                continue
            vol = t.get('quoteVolume') or 0
            candidates.append((sym, vol))
        
        # Sort by volume, take top N
        candidates.sort(key=lambda x: x[1], reverse=True)
        top = [s for s, v in candidates[:n]]
        
        return top
        
    except Exception as e:
        print(f"Error fetching tickers: {e}")
        # Fallback: use a static watchlist
        return [
            "SOL/USDT", "ARB/USDT", "OP/USDT", "SUI/USDT", "APT/USDT",
            "LDO/USDT", "WLD/USDT", "TIA/USDT", "SEI/USDT", "STRK/USDT",
            "RUNE/USDT", "INJ/USDT", "FET/USDT", "AGIX/USDT", "RNDR/USDT",
        ]


def fetch_oi_data(symbol: str, config: dict = None) -> Dict:
    """Fetch Open Interest data for a symbol.
    
    Returns dict with current OI and recent changes.
    Note: CCXT doesn't directly expose OI history well.
    We use the ticker's info field where available.
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
        'timeout': 10000,
    })
    if config and config.get('proxy'):
        ex.proxies = config['proxy']
    ex.options['defaultType'] = 'future'
    
    sym = _format_symbol(symbol)
    
    try:
        ticker = ex.fetch_ticker(sym)
        info = ticker.get('info', {})
        
        return {
            "symbol": sym,
            "last_price": ticker.get('last'),
            "oi": float(info.get('openInterest', 0)) if info.get('openInterest') else None,
            "oi_value": None,  # Would need OI * price
            "volume_24h": ticker.get('quoteVolume'),
            "funding_rate": ticker.get('info', {}).get('lastFundingRate'),
        }
    except Exception as e:
        return {"symbol": sym, "error": str(e)}


# ============================================================
# SIGNAL SCORING
# ============================================================

def score_oi_surge(current_oi: float, baseline_oi: float) -> Tuple[float, str]:
    """Score Open Interest surge.
    
    Returns (score, description).
    """
    if baseline_oi <= 0:
        return 0, "无基准数据"
    
    change = (current_oi - baseline_oi) / baseline_oi
    
    cfg = STRATEGY_CONFIG
    if change >= cfg["oi_surge_major"]:
        return cfg["weight_oi"], f"OI暴增 {change*100:.1f}%"
    elif change >= cfg["oi_surge_moderate"]:
        return cfg["weight_oi"] * 0.67, f"OI激增 {change*100:.1f}%"
    elif change >= cfg["oi_surge_minor"]:
        return cfg["weight_oi"] * 0.33, f"OI上升 {change*100:.1f}%"
    else:
        return 0, f"OI平稳 {change*100:.1f}%"


def score_volume_surge(current_vol: float, avg_vol: float) -> Tuple[float, str]:
    """Score Volume surge vs baseline average.
    
    Returns (score, description).
    """
    if avg_vol <= 0:
        return 0, "无基准数据"
    
    ratio = current_vol / avg_vol
    
    cfg = STRATEGY_CONFIG
    if ratio >= cfg["vol_surge_major"]:
        return cfg["weight_volume"], f"量能暴增 {ratio:.1f}x"
    elif ratio >= cfg["vol_surge_moderate"]:
        return cfg["weight_volume"] * 0.67, f"量能激增 {ratio:.1f}x"
    elif ratio >= cfg["vol_surge_minor"]:
        return cfg["weight_volume"] * 0.33, f"量能放大 {ratio:.1f}x"
    else:
        return 0, f"量能正常 {ratio:.1f}x"


def score_breakout(candles: List[Dict], current_price: float) -> Tuple[float, str]:
    """Score K-line breakout pattern.
    
    Analyzes recent candles for breakout signals:
    - Price above recent high + momentum
    - Bullish engulfing / breakout candle
    - MA crossover
    
    Returns (score, description).
    """
    if len(candles) < 10:
        return 0, "K线数据不足"
    
    cfg = STRATEGY_CONFIG
    
    # Calculate indicators
    closes = [c['close'] for c in candles]
    highs = [c['high'] for c in candles]
    lows = [c['low'] for c in candles]
    volumes = [c['volume'] for c in candles]
    
    # Recent 20-bar high/low
    lookback = min(cfg["breakout_lookback"], len(candles) - 1)
    recent_high = max(highs[-lookback:-1])  # exclude current bar
    recent_low = min(lows[-lookback:-1])
    
    # MA20
    ma20 = sum(closes[-20:]) / min(20, len(closes[-20:])) if len(closes) >= 20 else sum(closes) / len(closes)
    
    # Current bar
    current_close = closes[-1]
    current_high = highs[-1]
    current_low = lows[-1]
    current_vol = volumes[-1]
    prev_close = closes[-2] if len(closes) >= 2 else current_close
    
    # Average volume
    avg_vol = sum(volumes[-20:]) / min(20, len(volumes[-20:]))
    
    score = 0
    reasons = []
    
    # Check 1: Break above recent high (momentum breakout)
    if current_close > recent_high:
        score += 20
        reasons.append("突破近期高点")
    
    # Check 2: Break above MA20
    if current_close > ma20 and prev_close <= ma20:
        score += 10
        reasons.append("突破MA20")
    elif current_close > ma20:
        score += 5
        reasons.append("站上MA20")
    
    # Check 3: Bullish candle (close near high, open near low)
    body = abs(current_close - prev_close)
    upper_wick = current_high - max(current_close, prev_close)
    lower_wick = min(current_close, prev_close) - current_low
    
    if body > 0 and upper_wick < body * 0.3 and lower_wick > body * 0.5:
        # Bullish engulfing or hammer-like
        if current_close > prev_close:
            score += 10
            reasons.append("看涨吞没形态")
    
    # Check 4: Volume confirmation
    if current_vol > avg_vol * 1.5:
        score += 5
        reasons.append("放量突破")
    
    # Cap at max weight
    score = min(score, cfg["weight_breakout"])
    
    return score, ", ".join(reasons) if reasons else "无明确突破信号"


# ============================================================
# COMPREHENSIVE SIGNAL SCAN
# ============================================================

def scan_single(symbol: str, config: dict = None) -> Dict:
    """Scan a single symbol for trading signals.
    
    Returns complete signal analysis with scores.
    """
    sym = _format_symbol(symbol)
    
    if _is_blacklisted(sym):
        return {"symbol": sym, "signal": False, "reason": "黑名单"}
    
    result = {
        "symbol": sym,
        "timestamp": datetime.now().isoformat(),
        "signal": False,
        "total_score": 0,
        "scores": {},
        "details": {},
    }
    
    try:
        # 1. Get K-line data
        klines = get_klines(sym, '5m', limit=50, config=config)
        candles = klines.get('candles', [])
        if len(candles) < 10:
            result["reason"] = "K线数据不足"
            return result
        
        current_price = candles[-1]['close']
        result["price"] = current_price
        
        # 2. Volume surge score
        recent_vol = candles[-1]['volume']
        avg_vol = sum(c['volume'] for c in candles[-20:]) / min(20, len(candles[-20:]))
        vol_score, vol_desc = score_volume_surge(recent_vol, avg_vol)
        result["scores"]["volume"] = round(vol_score, 1)
        result["details"]["volume"] = {
            "current": recent_vol,
            "average": round(avg_vol, 2),
            "ratio": round(recent_vol / avg_vol, 2) if avg_vol > 0 else 0,
            "desc": vol_desc,
        }
        
        # 3. Breakout score
        breakout_score, breakout_desc = score_breakout(candles, current_price)
        result["scores"]["breakout"] = round(breakout_score, 1)
        result["details"]["breakout"] = {
            "ma20": round(sum(c['close'] for c in candles[-20:]) / 20, 6) if len(candles) >= 20 else None,
            "recent_high": round(max(c['high'] for c in candles[-20:-1]), 6) if len(candles) >= 20 else None,
            "desc": breakout_desc,
        }
        
        # 4. OI data (best effort)
        try:
            oi_data = fetch_oi_data(sym, config)
            if oi_data.get('oi') and oi_data['oi'] > 0:
                # For real OI surge, need historical baseline
                # Simplified: use OI value as positive indicator if > 0
                oi_score = 10  # Base OI participation score
                oi_desc = f"OI: {oi_data['oi']:,.0f}"
            else:
                oi_score = 0
                oi_desc = "OI不可用"
            
            # Check funding rate
            fr = oi_data.get('funding_rate')
            if fr:
                fr_val = float(fr)
                if abs(fr_val) > STRATEGY_CONFIG["funding_rate_max"]:
                    result["reason"] = f"资金费率过高 ({fr_val*100:.2f}%)"
                    result["signal"] = False
                    return result
        except:
            oi_score = 5  # Conservative: give partial credit
            oi_desc = "OI获取失败(保守评分)"
        
        result["scores"]["oi"] = round(oi_score, 1)
        result["details"]["oi"] = {"desc": oi_desc}
        
        # 5. Total score
        total = sum(result["scores"].values())
        result["total_score"] = round(total, 1)
        
        # 6. Signal decision
        threshold = STRATEGY_CONFIG["signal_threshold"]
        if total >= threshold:
            result["signal"] = True
            result["verdict"] = f"🔥 强烈信号 ({total}/{threshold})"
        elif total >= threshold * 0.8:
            result["verdict"] = f"🟡 接近阈值 ({total}/{threshold})"
        else:
            result["verdict"] = f"⚪ 未触发 ({total}/{threshold})"
        
    except Exception as e:
        result["reason"] = f"扫描异常: {e}"
    
    return result


def scan_market(config: dict = None, top_n: int = 50) -> Dict:
    """Scan top N altcoins and return all signals.
    
    This is the main entry point for the 3-minute scan.
    """
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 扫描 Top {top_n} 山寨币...")
    
    # Fetch top altcoins
    try:
        symbols = fetch_top_altcoins(config, n=min(top_n, 200))
    except Exception as e:
        symbols = fetch_top_altcoins(None, n=50)
    print(f"  获取 {len(symbols)} 个候选币")
    
    # Scan each
    signals = []
    all_results = []
    
    for i, sym in enumerate(symbols):
        if i % 10 == 0:
            print(f"  进度: {i}/{len(symbols)}")
        
        result = scan_single(sym, config)
        all_results.append(result)
        
        if result.get('signal'):
            signals.append(result)
    
    # Summary
    print(f"  扫描完成: {len(all_results)} 个币, {len(signals)} 个信号")
    
    # Sort signals by score
    signals.sort(key=lambda x: x['total_score'], reverse=True)
    
    return {
        "timestamp": datetime.now().isoformat(),
        "scanned": len(all_results),
        "signals_count": len(signals),
        "top_signals": signals[:10],  # Top 10
        "all_signals": signals,
        "summary": {
            "total_scored": sum(1 for r in all_results if r['total_score'] > 0),
            "avg_score": round(sum(r['total_score'] for r in all_results) / max(len(all_results), 1), 1),
            "strong_signals": len(signals),
        }
    }


def format_signal_report(signal: Dict) -> str:
    """Format a single signal for display."""
    lines = []
    sym = signal['symbol'].replace('/USDT', '')
    score = signal['total_score']
    price = signal.get('price', 0)
    
    emoji = "🔥" if score >= 85 else "🟢" if score >= 78 else "🟡"
    lines.append(f"{emoji} **{sym}** — {score:.0f}分 | ${price:,.4f}")
    
    scores = signal.get('scores', {})
    for k, v in scores.items():
        if v > 0:
            bar = "█" * int(v / 5)
            lines.append(f"  {k}: {bar} {v:.0f}分")
    
    details = signal.get('details', {})
    for k, v in details.items():
        if isinstance(v, dict) and v.get('desc'):
            lines.append(f"  {k}: {v['desc']}")
    
    return "\n".join(lines)


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    import sys
    
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'scan'
    
    if cmd == 'scan':
        top_n = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        result = scan_market(top_n=top_n)
        
        print(f"\n{'='*50}")
        print(f"  妖币扫描结果 — {result['timestamp']}")
        print(f"{'='*50}")
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
        result = scan_single(sym)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    else:
        print("Usage: python signals.py scan [top_n]")
        print("       python signals.py test [SYMBOL]")
