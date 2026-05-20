"""
Demon Strategy Main Orchestrator (妖币策略主控)

Full flow: Scan → Score → Risk Check → Trade Plan → Notify

Usage:
  python main.py scan       # One scan cycle
  python main.py backtest   # 30-day backtest
  python main.py plan SYM   # Generate trade plan for a signal
"""

import sys
import os
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from signals import scan_market, scan_single, format_signal_report, fetch_top_altcoins
from risk import check_can_trade, get_risk_report, reset_daily, _load_state
from executor import simulate_trade, format_trade_plan
from notify import notify_trade_open, notify_alert, daily_summary


def full_scan_cycle(capital: float, top_n: int = 50, auto_execute: bool = False):
    """One complete scan cycle.
    
    1. Scan top N altcoins for signals
    2. For each signal ≥78, generate trade plan
    3. Show top 3 plans
    """
    print(f"\n{'='*60}")
    print(f"  妖币扫描周期 — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    # Risk check
    can, reason = check_can_trade(capital)
    if not can:
        print(f"❌ 无法交易: {reason}")
        return
    
    print(get_risk_report())
    print()
    
    # Scan market
    result = scan_market(top_n=top_n)
    signals = result.get('top_signals', [])
    
    if not signals:
        print("⚪ 本轮无符合条件的信号")
        return
    
    print(f"\n🔥 发现 {len(signals)} 个信号:\n")
    
    # Show top signals with scores
    for s in signals[:5]:
        print(format_signal_report(s))
        print()
    
    # Generate trade plans for top 3
    print("="*60)
    print("  交易计划 (Top 3)")
    print("="*60)
    
    plans = []
    for s in signals[:3]:
        sym = s['symbol']
        price = s.get('price', 0)
        score = s['total_score']
        
        # Estimate volatility from details
        vol = 5.0  # default
        if s.get('details', {}).get('volume', {}).get('ratio'):
            vol_ratio = s['details']['volume']['ratio']
            vol = min(vol_ratio * 3, 15)
        
        # Calculate SL (3% below entry)
        sl = price * 0.97
        
        plan = simulate_trade(
            symbol=sym,
            side='long',
            capital=capital,
            entry_price=price,
            stop_loss=sl,
            signal_score=score,
            volatility_pct=vol,
        )
        
        if plan.get('allowed'):
            plans.append(plan)
            print(f"\n{format_trade_plan(plan)}")
            print(f"\n{'-'*40}")
    
    # Notify
    if plans and auto_execute:
        print("\n🚀 自动执行已启用 — 发送开仓通知")
        for plan in plans[:1]:  # Only execute #1
            msg = notify_trade_open(plan)
            print(msg)
    
    return plans


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py [scan|risk|plan SYMBOL|backtest]")
        return
    
    cmd = sys.argv[1]
    
    # Load config from binance-trading
    config_path = os.path.join(os.path.dirname(__file__), "..", "binance-trading", "references", "config.json")
    
    # Default capital for demo
    capital = 1000.0
    
    # Try to get real balance
    try:
        import ccxt
        if os.path.exists(config_path):
            with open(config_path) as f:
                cfg = json.load(f)
            ex = ccxt.binance({
                'apiKey': cfg['api_key'],
                'secret': cfg['secret_key'],
                'proxies': cfg.get('proxy', {}),
                'timeout': 10000,
                'options': {'defaultType': 'future'},
            })
            bal = ex.fetch_balance()
            capital = bal['total'].get('USDT', 1000)
    except:
        pass
    
    if cmd == 'scan':
        top_n = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        full_scan_cycle(capital=capital, top_n=top_n)
    
    elif cmd == 'risk':
        print(get_risk_report())
    
    elif cmd == 'plan':
        if len(sys.argv) < 3:
            print("Usage: python main.py plan ARB/USDT")
            return
        sym = sys.argv[2]
        result = scan_single(sym)
        print(format_signal_report(result))
        
        if result.get('signal'):
            plan = simulate_trade(
                symbol=sym,
                side='long',
                capital=capital,
                entry_price=result.get('price', 0),
                stop_loss=result.get('price', 0) * 0.97,
                signal_score=result['total_score'],
                volatility_pct=5.0,
            )
            print()
            print(format_trade_plan(plan))
    
    elif cmd == 'reset':
        reset_daily()
        print("✅ 风控状态已重置")
    
    elif cmd == 'summary':
        print(daily_summary())
    
    else:
        print(f"Unknown command: {cmd}")


if __name__ == "__main__":
    main()
