"""
Quick Status Check — runs all modules end-to-end.
Usage: python check.py
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from market import market_overview, get_funding_rate
from account import quick_status
from kelly import kelly_quick, format_kelly_report


def main():
    print("=" * 50)
    print("  Binance Trading — System Check")
    print("=" * 50)

    # 1. Market Overview
    print("\n### 1) 行情总览")
    try:
        watchlist = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'ARB/USDT']
        overview = market_overview(watchlist)
        for coin in overview['watchlist']:
            emoji = "🟢" if (coin.get('change_24h') or 0) > 0 else "🔴"
            price = coin.get('price') or 0
            vol = coin.get('volume_m') or 0
            print(f"  {coin['symbol']:6s} ${price:,.2f}  {emoji} {(coin.get('change_24h') or 0):+.2f}%  Vol:{vol:.1f}M")
        print(f"  → 情绪: {overview['summary']['sentiment']} ({overview['summary']['gainers']}涨/{overview['summary']['losers']}跌)")
    except Exception as e:
        print(f"  ❌ Market error: {e}")

    # 2. Funding Rates
    print("\n### 2) 资金费率")
    for sym in ['BTC', 'ETH', 'SOL']:
        try:
            fr = get_funding_rate(sym)
            if 'error' not in fr:
                rate = fr.get('funding_rate_pct', 0)
                emoji = "🟢" if rate < 0.01 else "🟡" if rate < 0.05 else "🔴"
                print(f"  {sym}: {rate:+.4f}% {emoji}")
            else:
                print(f"  {sym}: N/A")
        except Exception:
            print(f"  {sym}: Error")

    # 3. Account
    print("\n### 3) 账户状态")
    try:
        status = quick_status()
        print(f"  合约 USDT: {status['usdt_balance']:,.2f}")
        print(f"  持仓数: {status['position_count']}")
        if status['top_positions']:
            for p in status['top_positions']:
                print(f"    {p['asset']}: {p['amount']} ≈ ${p['value_usdt']:,.2f}")
    except Exception as e:
        print(f"  ❌ Account error: {e}")

    # 4. Kelly Example
    print("\n### 4) 凯利示例 (仅供参考)")
    capital = 1000
    result = kelly_quick(capital=capital, win_prob=0.55, reward_risk_ratio=2.0)
    print(format_kelly_report(result))

    print("\n" + "=" * 50)
    print("  ✅ All checks complete")
    print("=" * 50)


if __name__ == "__main__":
    main()
