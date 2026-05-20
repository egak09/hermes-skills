"""
Demon Strategy Notification System v2.0 (妖币通知系统)
======================================================
6 notification templates + Telegram Bot API sender + trade log.

Templates:
  1. Entry (开仓)
  2. Add Position (加仓)
  3. Take Profit (止盈)
  4. Stop Loss / Full Close (止损/全平)
  5. Daily Summary (每日总结)
  6. Alert (异常报警)

Config: references/notify_config.json  (bot_token, chat_id, proxy)
  - gitignored: never commit tokens
"""

import json
import os
import sys
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple

import requests

# ============================================================
# PATHS
# ============================================================

NOTIFY_DIR = os.path.join(os.path.dirname(__file__), "..", "references")
NOTIFY_CONFIG_PATH = os.path.join(NOTIFY_DIR, "notify_config.json")
TRADE_LOG_PATH = os.path.join(NOTIFY_DIR, "trade_log.json")
NOTIFY_GITIGNORE = os.path.join(NOTIFY_DIR, ".gitignore")

# ============================================================
# CONFIG
# ============================================================

DEFAULT_CONFIG = {
    "bot_token": "",
    "chat_id": "",
    "proxy": "http://127.0.0.1:1081",
    "enabled": False,
    "platform": "telegram",  # telegram | discord | both
}


def load_notify_config() -> dict:
    """Load notification config, creating default if missing."""
    if os.path.exists(NOTIFY_CONFIG_PATH):
        with open(NOTIFY_CONFIG_PATH, 'r') as f:
            return json.load(f)
    return DEFAULT_CONFIG.copy()


# ============================================================
# TELEGRAM SENDER
# ============================================================

class TelegramSender:
    """Send formatted messages via Telegram Bot API."""

    def __init__(self, config: dict = None):
        self.cfg = config or load_notify_config()
        self.bot_token = self.cfg.get("bot_token", "")
        self.chat_id = self.cfg.get("chat_id", "")
        self.proxy = self.cfg.get("proxy", "")
        self.enabled = self.cfg.get("enabled", False) and self.bot_token and self.chat_id
        self.api_base = f"https://api.telegram.org/bot{self.bot_token}"

    def send(self, text: str, parse_mode: str = "Markdown") -> bool:
        """Send a message via Telegram Bot API.

        Returns True if sent successfully.
        """
        if not self.enabled:
            print(f"[Notify] DISABLED — message not sent:\n{text[:200]}...")
            return False

        url = f"{self.api_base}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True,
        }

        proxies = None
        if self.proxy:
            proxies = {"http": self.proxy, "https": self.proxy}

        try:
            resp = requests.post(url, json=payload, proxies=proxies, timeout=15)
            if resp.status_code == 200:
                return True
            else:
                print(f"[Notify] Telegram API error: {resp.status_code} — {resp.text[:200]}")
                return False
        except Exception as e:
            print(f"[Notify] Send failed: {e}")
            return False


# Global sender singleton
_sender: Optional[TelegramSender] = None


def _get_sender() -> TelegramSender:
    global _sender
    if _sender is None:
        _sender = TelegramSender()
    return _sender


# ============================================================
# TRADE LOG (for daily summary)
# ============================================================

def _load_log() -> list:
    if os.path.exists(TRADE_LOG_PATH):
        with open(TRADE_LOG_PATH, 'r') as f:
            return json.load(f)
    return []


def _save_log(log: list):
    os.makedirs(NOTIFY_DIR, exist_ok=True)
    with open(TRADE_LOG_PATH, 'w') as f:
        json.dump(log, f, indent=2, ensure_ascii=False)


def _log_event(event: dict):
    """Log a trade event for daily summary."""
    log = _load_log()
    log.append(event)
    # Keep only last 30 days
    cutoff = (datetime.now() - timedelta(days=30)).isoformat()
    log = [e for e in log if e.get("timestamp", "") >= cutoff]
    _save_log(log)


# ============================================================
# NOTIFICATION TEMPLATES
# ============================================================

# ─── 1. ENTRY (开仓) ────────────────────────────────────────

def notify_entry(
    symbol: str,
    side: str,          # "long" | "short"
    leverage: float,
    entry_price: float,
    position_pct: float,  # e.g. 68 → 68%
    total_capital: float,
    stop_loss: float,
    stop_loss_pct: float,  # e.g. -9.8
    signal_score: int,     # e.g. 86
    triggers: List[str],   # e.g. ["OI 1h +58%", "Volume 4.2x 爆发", "15m 火箭起飞形态"]
    expected_hold: str = "4~48小时",
    send: bool = True,
) -> str:
    """🚀 Entry notification."""
    sym = symbol.replace("/USDT", "")
    side_label = "多仓" if side == "long" else "空仓"
    dir_emoji = "🟢" if side == "long" else "🔴"

    msg = (
        f"🚀【Hermes-agent 全自动开仓】\n\n"
        f"*币种：* #{sym} / USDT  永续\n"
        f"*杠杆：* {leverage}x  {side_label}\n"
        f"*入场价：* {entry_price}\n"
        f"*仓位：* {position_pct}% (总资金 {total_capital:,.0f} USDT)\n"
        f"*止损：* {stop_loss} ({stop_loss_pct:+.1f}%)\n\n"
        f"*信号强度：* {signal_score}/100\n"
        f"*触发原因：*\n"
    )
    for t in triggers:
        msg += f"  • {t}\n"

    msg += f"\n*持仓时间预计：*{expected_hold}"

    # Log
    _log_event({
        "type": "entry",
        "symbol": sym,
        "side": side,
        "leverage": leverage,
        "price": entry_price,
        "position_pct": position_pct,
        "capital": total_capital,
        "stop_loss": stop_loss,
        "signal_score": signal_score,
        "timestamp": datetime.now().isoformat(),
    })

    if send:
        _get_sender().send(msg)

    return msg


# ─── 2. ADD POSITION (加仓) ─────────────────────────────────

def notify_add_position(
    symbol: str,
    add_price: float,
    add_pct: float,       # e.g. 25 → +25%
    avg_cost: float,
    send: bool = True,
) -> str:
    """➕ Add position notification."""
    sym = symbol.replace("/USDT", "")

    msg = (
        f"➕ *加仓* #{sym}\n\n"
        f"*加仓价：* {add_price}\n"
        f"*新增仓位：* +{add_pct}%\n"
        f"*当前平均成本：* {avg_cost}"
    )

    _log_event({
        "type": "add_position",
        "symbol": sym,
        "price": add_price,
        "add_pct": add_pct,
        "avg_cost": avg_cost,
        "timestamp": datetime.now().isoformat(),
    })

    if send:
        _get_sender().send(msg)

    return msg


# ─── 3. TAKE PROFIT (止盈) ──────────────────────────────────

def notify_take_profit(
    symbol: str,
    close_pct: float,      # e.g. 40 → 40%
    close_price: float,
    profit_pct: float,     # e.g. 112 → +112%
    profit_usdt: float,
    remaining_trailing: bool = True,
    send: bool = True,
) -> str:
    """✅ Partial take profit notification."""
    sym = symbol.replace("/USDT", "")

    msg = (
        f"✅ *部分止盈* #{sym}\n\n"
        f"*平仓比例：* {close_pct}%\n"
        f"*平仓价：* {close_price}\n"
        f"*盈利：* +{profit_pct}% (+{profit_usdt} USDT)\n"
    )
    if remaining_trailing:
        msg += f"\n_剩余仓位追踪止盈中..._"

    _log_event({
        "type": "take_profit",
        "symbol": sym,
        "close_pct": close_pct,
        "price": close_price,
        "pnl": profit_usdt,
        "pnl_pct": profit_pct,
        "timestamp": datetime.now().isoformat(),
    })

    if send:
        _get_sender().send(msg)

    return msg


# ─── 4. STOP LOSS / FULL CLOSE (止损/全平) ──────────────────

def notify_stop_loss(
    symbol: str,
    close_price: float,
    loss_pct: float,       # e.g. -11.4
    loss_usdt: float,      # e.g. -68
    reason: str,           # e.g. "破关键支撑 + OI 大幅下降"
    daily_pnl: float = None,     # Today's total PnL
    daily_pnl_pct: float = None,  # e.g. 29
    send: bool = True,
) -> str:
    """🛑 Stop loss / full close notification."""
    sym = symbol.replace("/USDT", "")

    msg = (
        f"🛑 *止损平仓* #{sym}\n\n"
        f"*平仓价：* {close_price}\n"
        f"*亏损：* {loss_pct:+.1f}% ({loss_usdt:+.0f} USDT)\n"
        f"*原因：* {reason}\n"
    )
    if daily_pnl is not None:
        msg += f"\n*今日总盈亏：* {daily_pnl:+.0f} USDT ({daily_pnl_pct:+.0f}%)"

    _log_event({
        "type": "stop_loss",
        "symbol": sym,
        "price": close_price,
        "pnl": loss_usdt,
        "pnl_pct": loss_pct,
        "reason": reason,
        "timestamp": datetime.now().isoformat(),
    })

    if send:
        _get_sender().send(msg)

    return msg


# ─── 5. DAILY SUMMARY (每日总结) ─────────────────────────────

def notify_daily_summary(
    report_date: str = None,     # "2026-05-20" or None for today
    total_trades: int = None,    # auto-computed from log if None
    win_rate: float = None,      # 75 → 75%
    total_pnl: float = None,
    total_pnl_pct: float = None,
    max_drawdown: float = None,  # -9 → -9%
    current_positions: List[str] = None,  # ["#DOGE", "#PEPE"]
    status: str = "正常运行",
    account_balance: float = None,
    send: bool = True,
) -> str:
    """📊 Daily summary report."""
    if report_date is None:
        report_date = date.today().isoformat()

    # Auto-compute from log if values not provided
    if total_trades is None or total_pnl is None:
        log = _load_log()
        today = date.today().isoformat()
        today_events = [e for e in log if e.get("timestamp", "").startswith(today)]

        closes = [e for e in today_events if e["type"] in ("take_profit", "stop_loss")]
        entries = [e for e in today_events if e["type"] == "entry"]

        if total_trades is None:
            total_trades = len(entries)
        if total_pnl is None:
            total_pnl = sum(e.get("pnl", 0) for e in closes)
        if total_pnl_pct is None and account_balance:
            total_pnl_pct = (total_pnl / account_balance * 100) if account_balance > 0 else 0
        if win_rate is None:
            wins = sum(1 for e in closes if e.get("pnl", 0) > 0)
            total_close = len(closes)
            win_rate = (wins / total_close * 100) if total_close > 0 else 0

    pnl_emoji = "🟢" if (total_pnl or 0) > 0 else "🔴" if (total_pnl or 0) < 0 else "⚪"

    msg = (
        f"📊 *Hermes-agent 每日报告*\n\n"
        f"*日期：*{report_date}\n"
        f"*交易次数：* {total_trades or 0}\n"
        f"*胜率：* {win_rate or 0:.0f}%\n"
        f"{pnl_emoji} *总盈亏：* {total_pnl or 0:+.0f} USDT ({total_pnl_pct or 0:+.0f}%)\n"
    )
    if max_drawdown is not None:
        msg += f"*最大回撤：* {max_drawdown:+.0f}%\n"

    if current_positions:
        pos_str = ", ".join([f"\\{p}" for p in current_positions])
        msg += f"\n*当前持仓：* {len(current_positions)} 个 ({pos_str})"
    else:
        msg += f"\n*当前持仓：* 0 个"

    msg += f"\n\n*状态：*{status}"

    if account_balance:
        msg += f"\n💰 *账户余额：* {account_balance:,.0f} USDT"

    if send:
        _get_sender().send(msg)

    return msg


# ─── 6. ALERT (异常报警) ─────────────────────────────────────

def notify_alert(
    level: str,          # "critical" | "warning" | "info"
    title: str,
    message: str,
    send: bool = True,
) -> str:
    """🚨 Abnormal alert notification."""
    emojis = {"critical": "🚨", "warning": "⚠️", "info": "ℹ️"}
    emoji = emojis.get(level, "📢")

    msg = (
        f"{emoji} *{title}*\n\n"
        f"{message}"
    )

    _log_event({
        "type": "alert",
        "level": level,
        "title": title,
        "message": message,
        "timestamp": datetime.now().isoformat(),
    })

    if send:
        _get_sender().send(msg)

    return msg


# ============================================================
# SETUP HELPER
# ============================================================

def setup_notify_config(bot_token: str, chat_id: str, proxy: str = None):
    """Create or update the notify config file.

    Also ensures .gitignore is in place to protect tokens.
    """
    os.makedirs(NOTIFY_DIR, exist_ok=True)

    config = {
        "bot_token": bot_token,
        "chat_id": chat_id,
        "proxy": proxy or "http://127.0.0.1:1081",
        "enabled": True,
        "platform": "telegram",
    }

    with open(NOTIFY_CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=2)

    # Ensure .gitignore
    with open(NOTIFY_GITIGNORE, 'w') as f:
        f.write("notify_config.json\ntrade_log.json\n")

    # Refresh sender singleton
    global _sender
    _sender = TelegramSender(config)

    print(f"[Notify] Config saved to {NOTIFY_CONFIG_PATH}")
    print(f"[Notify] Sender {'enabled' if _sender.enabled else 'disabled (check token/chat_id)'}")

    return config


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "test"

    if cmd == "setup":
        if len(sys.argv) < 4:
            print("Usage: python notify.py setup <bot_token> <chat_id> [proxy]")
            sys.exit(1)
        token = sys.argv[2]
        cid = sys.argv[3]
        proxy = sys.argv[4] if len(sys.argv) > 4 else None
        setup_notify_config(token, cid, proxy)

    elif cmd == "test":
        print("=== 通知模板测试 ===\n")

        # 1. Entry
        print("1. 开仓通知:")
        entry = notify_entry(
            symbol="SOL/USDT",
            side="long",
            leverage=12,
            entry_price=148.35,
            position_pct=68,
            total_capital=820,
            stop_loss=135.20,
            stop_loss_pct=-9.8,
            signal_score=86,
            triggers=["OI 1h +58%", "Volume 4.2x 爆发", "15m 火箭起飞形态"],
            send=False,
        )
        print(entry)
        print()

        # 2. Add Position
        print("2. 加仓通知:")
        add = notify_add_position(
            symbol="PEPE/USDT",
            add_price=0.00001245,
            add_pct=25,
            avg_cost=0.0000121,
            send=False,
        )
        print(add)
        print()

        # 3. Take Profit
        print("3. 止盈通知:")
        tp = notify_take_profit(
            symbol="BONK/USDT",
            close_pct=40,
            close_price=0.0000289,
            profit_pct=112,
            profit_usdt=156,
            send=False,
        )
        print(tp)
        print()

        # 4. Stop Loss
        print("4. 止损通知:")
        sl = notify_stop_loss(
            symbol="WIF/USDT",
            close_price=2.18,
            loss_pct=-11.4,
            loss_usdt=-68,
            reason="破关键支撑 + OI 大幅下降",
            daily_pnl=245,
            daily_pnl_pct=29,
            send=False,
        )
        print(sl)
        print()

        # 5. Daily Summary
        print("5. 每日总结:")
        ds = notify_daily_summary(
            report_date="2026-05-20",
            total_trades=4,
            win_rate=75,
            total_pnl=312,
            total_pnl_pct=38,
            max_drawdown=-9,
            current_positions=["#DOGE", "#PEPE"],
            account_balance=820,
            send=False,
        )
        print(ds)
        print()

        # 6. Alert
        print("6. 异常报警:")
        al = notify_alert(
            level="critical",
            title="日亏损超限",
            message="今日亏损 19.2%，已暂停所有交易\n当前时间：2026-05-20 15:45\n下一恢复扫描：明日 00:00",
            send=False,
        )
        print(al)

    elif cmd == "daily":
        print(notify_daily_summary(send=True))

    elif cmd == "status":
        sender = _get_sender()
        print(f"[Notify] Config: {NOTIFY_CONFIG_PATH}")
        print(f"[Notify] Enabled: {sender.enabled}")
        if sender.enabled:
            print(f"[Notify] Bot: ...{sender.bot_token[-6:] if len(sender.bot_token) > 6 else '???'}")
            print(f"[Notify] Chat: {sender.chat_id}")
            print(f"[Notify] Proxy: {sender.proxy}")

    else:
        print("Commands: test | setup <token> <chat_id> | daily | status")
