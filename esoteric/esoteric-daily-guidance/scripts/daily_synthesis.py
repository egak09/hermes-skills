"""
Daily Synthesis Engine
Combines Bazi, Ziwei, and Western Astrology for daily action guidance.
"""

import sys
import os
import json
from datetime import date, datetime
from typing import Dict, List, Tuple

# Add scripts dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bazi import calculate_bazi, daily_clash, BaziFull
from ziwei import calculate_ziwei
from western_astro import calculate_natal_chart, daily_transits, NatalChart


def load_birth_data() -> dict:
    """Load birth data from references/birth_data.json"""
    path = os.path.join(os.path.dirname(__file__), "..", "references", "birth_data.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_daily_report(birth_data: dict = None, target_date: date = None) -> str:
    """Generate daily synthesis report."""

    if birth_data is None:
        birth_data = load_birth_data()

    if target_date is None:
        target_date = date.today()

    b = birth_data
    bd = b["birth"]
    coords = bd["coordinates"]

    # === 1. Bazi Daily Clash ===
    bazi = calculate_bazi(2001, 4, 16, 16, 50)
    clash = daily_clash(bazi, target_date)

    # === 2. Bazi Day Master Energy ===
    dm = b["bazi"]["day_master"]
    dm_elem = b["bazi"]["day_master_element"]

    # === 3. Western Daily Transits ===
    try:
        natal = calculate_natal_chart(2001, 4, 16, 16, 50,
                                      coords["lat"], coords["lon"], 8.0)
        transit = daily_transits(natal, target_date.year,
                                target_date.month, target_date.day)
    except Exception:
        transit = {"sun_sign": "N/A", "moon_sign": "N/A"}

    # === 4. Ziwei Context ===
    zw = b["ziwei"]
    sihua_info = ", ".join(f"{k}({v})" for k, v in zw["sihua"].items())

    # === 5. Build Report ===
    lines = []
    lines.append(f"## 🔮 {target_date} 每日玄学行动指南")
    lines.append("")

    # --- Bazi Section ---
    lines.append(f"### 八字流日")
    lines.append(f"日柱: **{clash['daily_gz']}** | 日主: **{dm}{dm_elem}**")
    lines.append(f"总体: {'🟢 吉' if clash['mood'] == '吉' else '🟡 平' if clash['mood'] == '平' else '🔴 凶'}")
    lines.append("")

    for ctype, desc, advice in clash["clashes"]:
        emoji = {"合": "🤝", "冲": "⚡", "害": "⚠️"}.get(ctype, "")
        lines.append(f"- {emoji} **{ctype}**: {desc} — {advice}")

    if not clash["clashes"]:
        lines.append("- 今日无特殊冲合，平稳之日")

    # --- Western Section ---
    lines.append("")
    lines.append(f"### 星盘行运")
    moon_s = transit.get("moon_sign", "N/A")
    sun_s = transit.get("sun_sign", "N/A")
    lines.append(f"太阳: **{sun_s}** | 月亮: **{moon_s}**")
    lines.append(f"上升: **{b['western']['ascendant']}**")

    # Moon sign interpretation
    moon_guidance = {
        "白羊": "情绪冲动直接，适合行动和竞争，不适合需要耐心的任务",
        "金牛": "情绪稳定慵懒，适合享受生活、理财规划，不适合冒险",
        "双子": "思维活跃多变，适合沟通学习短途出行，不适合深度专注",
        "巨蟹": "情感敏感怀旧，适合家务和家人时光，不适合公开场合",
        "狮子": "自信热情戏剧化，适合展示自己创意表达，不适合低调隐忍",
        "处女": "挑剔细致务实，适合整理分析精细工作，不适合粗放决策",
        "天秤": "追求平衡和谐，适合社交合作审美活动，不适合独断专制",
        "天蝎": "情绪深沉激烈，适合研究调查深度思考，不适合轻浮表面",
        "射手": "乐观自由冒险，适合旅行哲学探索学习，不适合束缚限制",
        "摩羯": "严肃务实克己，适合工作规划承担责任，不适合享乐放纵",
        "水瓶": "独立创新疏离，适合创意科技社交网络，不适合传统保守",
        "双鱼": "敏感梦幻慈悲，适合艺术灵性慈善，不适合现实务实决策",
    }
    guidance = moon_guidance.get(moon_s, "")
    if guidance:
        lines.append(f"月亮行运指引: {guidance}")

    # --- Integrated Advice ---
    lines.append("")
    lines.append("### 🤖 今日综合建议")

    # Combine all three systems
    advice = []

    # From Bazi
    clash_types = set(c[0] for c in clash["clashes"])
    if "冲" in clash_types:
        advice.append("⚡ **八字冲克**: 今日地支与命盘相冲，重大决策三思后行，适合低调观察而非主动出击")
    if "合" in clash_types:
        advice.append("🤝 **天干相合**: 贵人运佳，适合社交、合作、签约，主动联系关键人脉")
    if "害" in clash_types:
        advice.append("⚠️ **地支相害**: 谨防口舌是非，避免卷入他人纷争，说话留三分余地")
    if not clash_types:
        advice.append("📅 **平稳之日**: 适合日常事务处理，按计划推进即可")

    # From Western
    moon_elem = {"白羊": "火", "金牛": "土", "双子": "风", "巨蟹": "水",
                 "狮子": "火", "处女": "土", "天秤": "风", "天蝎": "水",
                 "射手": "火", "摩羯": "土", "水瓶": "风", "双鱼": "水"}.get(moon_s, "")
    if moon_elem == "火":
        advice.append("🔥 **火象月亮**: 行动力强，适合运动、竞争、启动新项目")
    elif moon_elem == "土":
        advice.append("🪨 **土象月亮**: 务实稳健，适合理财、规划、整理、长期布局")
    elif moon_elem == "风":
        advice.append("💨 **风象月亮**: 思维活跃，适合学习、社交、写作、头脑风暴")
    elif moon_elem == "水":
        advice.append("💧 **水象月亮**: 直觉敏锐，适合内省、创作、情感交流、灵性活动")

    # Market context (for Paradigme's trading)
    advice.append("")
    advice.append("### 📊 交易者特别提示")
    dm_advice = {
        "己": "己土日主今日宜以守为攻，土主信，稳健持仓优于频繁操作。注意申时(15-17)可能有变数。"
    }
    if dm in dm_advice:
        advice.append(dm_advice[dm])

    lines.extend(advice)

    # --- Ziwei Context ---
    lines.append("")
    lines.append(f"### 紫微背景")
    lines.append(f"命宫: **{zw['minggong']}** | 身宫: **{zw['shenggong']}** | 局: **{zw['wuxingju']}**")
    lines.append(f"四化: {sihua_info}")

    return "\n".join(lines)


if __name__ == "__main__":
    print(generate_daily_report())
