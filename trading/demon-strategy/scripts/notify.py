"""
Demon Strategy Notification System (妖币通知系统)

Channels:
  - Telegram (via Hermes send_message or terminal echo)
  - Daily summary report
  - Abnormal alerts
"""

import json
import os
from datetime import datetime, date
from typing import Dict, List


NOTIFY_DIR = os.path.join(os.path.dirname(__file__), "..", "references")
TRADE_LOG = os.path.join(NOTIFY_DIR, "trade_log.json")


def _load_log() -> list:
    if os.path.exists(TRADE_LOG):
        with open(TRADE_LOG, 'r') as f:
            return json.load(f)
    return []


def _save_log(log: list):
    os.makedirs(NOTIFY_DIR, exist_ok=True)
    with open(TRADE_LOG, 'w') as f:
        json.dump(log, f, indent=2, ensure_ascii=False)


def notify_trade_open(plan: Dict) -> str:
    """Trade open notification."""
    sym = plan['symbol'].replace('/USDT', '')
    emoji = "🟢" if plan['side'] == 'long' else "🔴"
    
    msg = f"""🔥 **妖币信号触发 — {sym}**

{emoji} {'做多' if plan['side'] == 'long' else '做空'} | 信号: {plan['signal_score']}分
💵 入场: ${plan['entry_price']} | 止损: ${plan['stop_loss']}
📐 杠杆: {plan['leverage']}x | 仓位: {plan['position_size']:.4f}张
💰 保证金: ${plan['margin']:,.2f} | 最大亏损: ${plan['max_loss']:,.2f}
⏱️ 时间止盈: {plan['time_stop_minutes']}分钟"""
    
    # Log
    log = _load_log()
    log.append({
        "type": "open",
        "timestamp": datetime.now().isoformat(),
        "symbol": sym,
        "side": plan['side'],
        "price": plan['entry_price'],
        "leverage": plan['leverage'],
    })
    _save_log(log)
    
    return msg


def notify_trade_close(symbol: str, pnl: float, pnl_pct: float, 
                       reason: str, exit_price: float) -> str:
    """Trade close notification."""
    sym = symbol.replace('/USDT', '')
    emoji = "🟢" if pnl > 0 else "🔴"
    icon = "✅" if pnl > 0 else "❌"
    
    msg = f"""{icon} **平仓 — {sym}**

{emoji} 盈亏: {pnl:+.2f} USDT ({pnl_pct:+.2f}%)
💵 平仓价: ${exit_price}
📋 原因: {reason}"""
    
    # Log
    log = _load_log()
    log.append({
        "type": "close",
        "timestamp": datetime.now().isoformat(),
        "symbol": sym,
        "pnl": pnl,
        "pnl_pct": pnl_pct,
        "reason": reason,
    })
    _save_log(log)
    
    return msg


def notify_alert(level: str, title: str, message: str) -> str:
    """Abnormal alert notification."""
    emojis = {"critical": "🚨", "warning": "⚠️", "info": "ℹ️"}
    emoji = emojis.get(level, "📢")
    
    return f"""{emoji} **{title}**

{message}"""


def daily_summary(trades: List[Dict] = None, account_status: Dict = None) -> str:
    """Generate daily trading summary."""
    today = date.today().isoformat()
    
    log = _load_log()
    today_trades = [t for t in log if t.get('timestamp', '').startswith(today)]
    
    opens = [t for t in today_trades if t['type'] == 'open']
    closes = [t for t in today_trades if t['type'] == 'close']
    
    total_pnl = sum(t.get('pnl', 0) for t in closes)
    wins = sum(1 for t in closes if t.get('pnl', 0) > 0)
    losses = sum(1 for t in closes if t.get('pnl', 0) < 0)
    total = wins + losses
    
    win_rate = (wins / total * 100) if total > 0 else 0
    
    emoji = "🟢" if total_pnl > 0 else "🔴" if total_pnl < 0 else "⚪"
    
    msg = f"""📊 **妖币日报 — {today}**

{emoji} 总盈亏: {total_pnl:+.2f} USDT
📈 交易次数: {total} (开{len(opens)} 平{len(closes)})
🎯 胜率: {win_rate:.0f}% ({wins}胜{losses}负)

🛡️ 风控状态: 正常
⏰ 下次扫描: 3分钟后"""
    
    if account_status:
        msg += f"\n💰 账户余额: {account_status.get('balance', 'N/A')} USDT"
    
    return msg


if __name__ == "__main__":
    # Test
    plan = {
        'symbol': 'ARB/USDT',
        'side': 'long',
        'signal_score': 82,
        'entry_price': 0.1145,
        'stop_loss': 0.109,
        'leverage': 5,
        'position_size': 8760,
        'margin': 200,
        'max_loss': 48,
        'time_stop_minutes': 240,
    }
    
    print("=== 开仓通知 ===")
    print(notify_trade_open(plan))
    print()
    
    print("=== 平仓通知 ===")
    print(notify_trade_close("ARB/USDT", 25.3, 2.5, "TP1 触发", 0.1175))
    print()
    
    print("=== 日报 ===")
    print(daily_summary())
    print()
    
    print("=== 警报 ===")
    print(notify_alert("critical", "日亏损超限", "今日亏损 19.2%，已暂停所有交易"))
