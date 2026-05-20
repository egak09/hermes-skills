"""
Bazi (八字) calculation module.
Computes the Four Pillars (年柱/月柱/日柱/时柱) from Gregorian birth date and time.
Uses the sexagenary cycle (干支) system.

Key references:
- Year pillar: based on Chinese calendar year start (lunar new year or solar term)
- Month pillar: based on solar terms (节气), not lunar months
- Day pillar: based on Julian Day Number modulo 60
- Hour pillar: based on 12 two-hour periods (时辰)
"""

from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Tuple, Dict, List

# === Constants ===

# Heavenly Stems (天干)
TIAN_GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
TIAN_GAN_ELEMENTS = {
    "甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
    "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水"
}
TIAN_GAN_YINYANG = {
    "甲": "阳", "乙": "阴", "丙": "阳", "丁": "阴", "戊": "阳",
    "己": "阴", "庚": "阳", "辛": "阴", "壬": "阳", "癸": "阴"
}

# Earthly Branches (地支)
DI_ZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
DI_ZHI_ELEMENTS = {
    "子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土", "巳": "火",
    "午": "火", "未": "土", "申": "金", "酉": "金", "戌": "土", "亥": "水"
}
DI_ZHI_ANIMALS = {
    "子": "鼠", "丑": "牛", "寅": "虎", "卯": "兔", "辰": "龙", "巳": "蛇",
    "午": "马", "未": "羊", "申": "猴", "酉": "鸡", "戌": "狗", "亥": "猪"
}

# Hidden stems in each branch (藏干)
HIDDEN_STEMS = {
    "子": ["癸"],
    "丑": ["己", "癸", "辛"],
    "寅": ["甲", "丙", "戊"],
    "卯": ["乙"],
    "辰": ["戊", "乙", "癸"],
    "巳": ["丙", "庚", "戊"],
    "午": ["丁", "己"],
    "未": ["己", "丁", "乙"],
    "申": ["庚", "壬", "戊"],
    "酉": ["辛"],
    "戌": ["戊", "辛", "丁"],
    "亥": ["壬", "甲"],
}

# Five Element interactions
# 生 (generating) cycle: 木→火→土→金→水→木
SHENG_MAP = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
# 克 (controlling) cycle: 木→土→火→金→土→水→火→金→水→土→木
KE_MAP = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}

# 24 Solar Terms (approximate dates for 2001)
# These are key for month pillar calculation
SOLAR_TERMS_2001 = {
    "立春": (2, 4), "雨水": (2, 18), "惊蛰": (3, 5), "春分": (3, 20),
    "清明": (4, 5), "谷雨": (4, 20), "立夏": (5, 5), "小满": (5, 21),
    "芒种": (6, 5), "夏至": (6, 21), "小暑": (7, 7), "大暑": (7, 23),
    "立秋": (8, 7), "处暑": (8, 23), "白露": (9, 7), "秋分": (9, 23),
    "寒露": (10, 8), "霜降": (10, 23), "立冬": (11, 7), "小雪": (11, 22),
    "大雪": (12, 7), "冬至": (12, 22), "小寒": (1, 5), "大寒": (1, 20),
}

# Month branch based on solar term
# Month 1 = 寅月 (starts at 立春)
MONTH_BRANCH_MAP = {
    1: "寅", 2: "卯", 3: "辰", 4: "巳", 5: "午", 6: "未",
    7: "申", 8: "酉", 9: "戌", 10: "亥", 11: "子", 12: "丑"
}

# Month stem based on year stem (五虎遁)
MONTH_STEM_MAP = {
    "甲": ["丙", "丁", "戊", "己", "庚", "辛", "壬", "癸", "甲", "乙", "丙", "丁"],
    "乙": ["戊", "己", "庚", "辛", "壬", "癸", "甲", "乙", "丙", "丁", "戊", "己"],
    "丙": ["庚", "辛", "壬", "癸", "甲", "乙", "丙", "丁", "戊", "己", "庚", "辛"],
    "丁": ["壬", "癸", "甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"],
    "戊": ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸", "甲", "乙"],
    "己": ["丙", "丁", "戊", "己", "庚", "辛", "壬", "癸", "甲", "乙", "丙", "丁"],
    "庚": ["戊", "己", "庚", "辛", "壬", "癸", "甲", "乙", "丙", "丁", "戊", "己"],
    "辛": ["庚", "辛", "壬", "癸", "甲", "乙", "丙", "丁", "戊", "己", "庚", "辛"],
    "壬": ["壬", "癸", "甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"],
    "癸": ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸", "甲", "乙"],
}

# Hour branch based on two-hour period
HOUR_BRANCH_MAP = {
    0: "子", 1: "丑", 2: "丑", 3: "寅", 4: "寅", 5: "卯", 6: "卯",
    7: "辰", 8: "辰", 9: "巳", 10: "巳", 11: "午", 12: "午",
    13: "未", 14: "未", 15: "申", 16: "申", 17: "酉", 18: "酉",
    19: "戌", 20: "戌", 21: "亥", 22: "亥", 23: "子"
}

# Hour stem based on day stem (五鼠遁)
HOUR_STEM_MAP = {
    "甲": ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸", "甲", "乙"],
    "乙": ["丙", "丁", "戊", "己", "庚", "辛", "壬", "癸", "甲", "乙", "丙", "丁"],
    "丙": ["戊", "己", "庚", "辛", "壬", "癸", "甲", "乙", "丙", "丁", "戊", "己"],
    "丁": ["庚", "辛", "壬", "癸", "甲", "乙", "丙", "丁", "戊", "己", "庚", "辛"],
    "戊": ["壬", "癸", "甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"],
    "己": ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸", "甲", "乙"],
    "庚": ["丙", "丁", "戊", "己", "庚", "辛", "壬", "癸", "甲", "乙", "丙", "丁"],
    "辛": ["戊", "己", "庚", "辛", "壬", "癸", "甲", "乙", "丙", "丁", "戊", "己"],
    "壬": ["庚", "辛", "壬", "癸", "甲", "乙", "丙", "丁", "戊", "己", "庚", "辛"],
    "癸": ["壬", "癸", "甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"],
}

# Day Stem attributes (十天干日主特性)
DAY_MASTER_TRAITS = {
    "甲": "参天大树，正直刚毅，领袖气质，好面子",
    "乙": "柔韧藤蔓，灵活变通，善借力，韧性强",
    "丙": "太阳之火，热情奔放，光明磊落，急性子",
    "丁": "灯烛之火，细腻内敛，洞察力强，心思缜密",
    "戊": "城墙之土，厚重诚信，脚踏实地，固执",
    "己": "田园之土，温和包容，滋养万物，犹豫",
    "庚": "刀剑之金，刚强果断，义气凛然，冲动",
    "辛": "珠玉之金，精致挑剔，完美主义，敏感",
    "壬": "江河之水，智慧通达，流动性强，善变",
    "癸": "雨露之水，细腻敏感，直觉力强，内敛",
}

# 10 Gods (十神) definitions
SHI_SHEN = {
    # (same/diff element, same/diff yinyang) -> name
    ("比", "同"): "比肩",
    ("比", "异"): "劫财",
    ("生", "同"): "食神",
    ("生", "异"): "伤官",
    ("克", "同"): "偏财",
    ("克", "异"): "正财",
    ("生我", "同"): "偏印",
    ("生我", "异"): "正印",
    ("克我", "同"): "七杀",
    ("克我", "异"): "正官",
}

# Additional stem-branch info for Year calculation
# 1900 is 庚子年, so year(-3) mod 60 maps to sexagenary index
GZ_YEAR_REFERENCE = (1900, "庚", "子")  # 1900 = 庚子


@dataclass
class BaziPillar:
    """A single pillar (柱): stem + branch"""
    stem: str      # 天干
    branch: str    # 地支
    hidden_stems: List[str]  # 藏干

    def __str__(self) -> str:
        return f"{self.stem}{self.branch}"

    def full(self) -> str:
        return f"{self.stem}{self.branch}（藏{'+'.join(self.hidden_stems)}）"


@dataclass
class BaziFull:
    """Complete Bazi chart"""
    year: BaziPillar
    month: BaziPillar
    day: BaziPillar
    hour: BaziPillar
    day_master: str
    day_master_element: str
    day_master_yinyang: str
    traits: str

    def __str__(self) -> str:
        return (f"年柱: {self.year}  月柱: {self.month}"
                f"  日柱: {self.day}  时柱: {self.hour}"
                f"\n日主: {self.day_master}（{self.day_master_element}）"
                f"\n特质: {self.traits}")


def _to_ganzhi_index(stem_idx: int, branch_idx: int) -> int:
    """Combine stem and branch into sexagenary index (0-59)"""
    from math import gcd
    # stem and branch progress at different rates, LCM=60
    # Valid pair when (stem - branch) % 2 == 0
    return None  # Not needed for pillar calculation


def _julian_day(year: int, month: int, day: int) -> int:
    """Calculate Julian Day Number"""
    if month <= 2:
        year -= 1
        month += 12
    A = year // 100
    B = 2 - A + A // 4
    return int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + B - 1524


def _solar_month(birth_month: int, birth_day: int) -> int:
    """Determine the solar term month (1-12) for month pillar calculation.
    Month 1 (寅) starts at 立春 (~Feb 4), month 12 (丑) starts at 小寒 (~Jan 5).
    Key: For dates after 立春, month 12 belongs to the NEXT year's cycle, not this one."""

    # Check if before 立春 (Feb 4) — then it's month 12 of previous cycle
    if birth_month < 2 or (birth_month == 2 and birth_day < 4):
        return 12  # 丑月

    # Otherwise, find which month we're in
    # Each entry: (month_num, next_month_start_month, next_month_start_day)
    # A birth date falls in month M if it's BEFORE the start of month M+1
    month_bounds = [
        (1, 3, 5),    # 寅月: 立春 2/4 → 惊蛰 3/5
        (2, 4, 5),    # 卯月: 惊蛰 3/5 → 清明 4/5
        (3, 5, 5),    # 辰月: 清明 4/5 → 立夏 5/5
        (4, 6, 5),    # 巳月: 立夏 5/5 → 芒种 6/5
        (5, 7, 7),    # 午月: 芒种 6/5 → 小暑 7/7
        (6, 8, 7),    # 未月: 小暑 7/7 → 立秋 8/7
        (7, 9, 7),    # 申月: 立秋 8/7 → 白露 9/7
        (8, 10, 8),   # 酉月: 白露 9/7 → 寒露 10/8
        (9, 11, 7),   # 戌月: 寒露 10/8 → 立冬 11/7
        (10, 12, 7),  # 亥月: 立冬 11/7 → 大雪 12/7
        (11, 1, 5),   # 子月: 大雪 12/7 → 小寒 1/5
    ]

    for m, next_m, next_d in month_bounds:
        if birth_month < next_m or (birth_month == next_m and birth_day < next_d):
            return m

    return 12  # 丑月: 小寒 1/5 → 立春 2/4


def calculate_bazi(year: int, month: int, day: int, hour: int, minute: int = 0) -> BaziFull:
    """Calculate complete Bazi chart from Gregorian birth date and time."""

    # === Year Pillar ===
    # Year stem-branch based on year of birth
    # 2001: (2001 - 4) % 10 = 7 → 辛; (2001 - 4) % 12 = 5 → 巳
    # Actually use the conventional formula
    year_stem_idx = (year - 4) % 10
    year_branch_idx = (year - 4) % 12
    year_stem = TIAN_GAN[year_stem_idx]
    year_branch = DI_ZHI[year_branch_idx]

    # === Month Pillar ===
    # First determine solar month
    solar_m = _solar_month(month, day)
    month_branch = MONTH_BRANCH_MAP[solar_m]
    month_branch_idx = DI_ZHI.index(month_branch)
    month_stem = MONTH_STEM_MAP[year_stem][solar_m - 1]

    # === Day Pillar ===
    # Based on Julian Day Number modulo 60
    jd = _julian_day(year, month, day)
    # Reference: known Bazi day stem
    # For 2001-04-16 (JD=2452016), we need to validate
    # Standard formula: stem = (jd + 9) % 10, branch = (jd + 1) % 12
    # Alternative formula commonly used in Bazi:
    # day_stem = (jd + 10) % 10, day_branch = (jd + 2) % 12
    # Let's use a verified reference point: 1900-01-01 = 甲子日
    # Actually 1900-01-01 JD=2415021
    # 甲 = 0 in TIAN_GAN, 子 = 0 in DI_ZHI
    # So the offset from JD to ganzhi index is: jd % 60 should give us the right mapping
    # Reference: 1900-01-31 = 甲辰日, JD=2415051
    # Let me use: day_gan_idx = (jd + 9) % 10, day_zhi_idx = (jd + 1) % 12
    # Actually the most reliable: use known reference points
    # 2000-01-01 = 戊午日 (confirmed)
    # JD for 2000-01-01 = 2451545
    # 戊 = 4, 午 = 6
    # So: 4 = (2451545 + offset_gan) % 10 → offset_gan = 9
    #     6 = (2451545 + offset_zhi) % 12 → offset_zhi = 1
    day_stem_idx = (jd + 9) % 10
    day_branch_idx = (jd + 1) % 12
    day_stem = TIAN_GAN[day_stem_idx]
    day_branch = DI_ZHI[day_branch_idx]

    # === Hour Pillar ===
    hour_branch = HOUR_BRANCH_MAP[hour]
    hour_branch_idx = DI_ZHI.index(hour_branch)
    hour_stem = HOUR_STEM_MAP[day_stem][hour_branch_idx]

    # === Build pillars ===
    year_pillar = BaziPillar(
        stem=year_stem,
        branch=year_branch,
        hidden_stems=HIDDEN_STEMS[year_branch]
    )
    month_pillar = BaziPillar(
        stem=month_stem,
        branch=month_branch,
        hidden_stems=HIDDEN_STEMS[month_branch]
    )
    day_pillar = BaziPillar(
        stem=day_stem,
        branch=day_branch,
        hidden_stems=HIDDEN_STEMS[day_branch]
    )
    hour_pillar = BaziPillar(
        stem=hour_stem,
        branch=hour_branch,
        hidden_stems=HIDDEN_STEMS[hour_branch]
    )

    # === Day Master ===
    day_master = day_stem
    day_master_elem = TIAN_GAN_ELEMENTS[day_master]
    day_master_yy = TIAN_GAN_YINYANG[day_master]
    traits = DAY_MASTER_TRAITS[day_master]

    return BaziFull(
        year=year_pillar,
        month=month_pillar,
        day=day_pillar,
        hour=hour_pillar,
        day_master=day_master,
        day_master_element=day_master_elem,
        day_master_yinyang=day_master_yy,
        traits=traits,
    )


def calculate_shi_shen(bazi: BaziFull) -> Dict[str, List[str]]:
    """Calculate Ten Gods (十神) for each pillar's stem in relation to day master."""
    result = {}

    for name, pillar in [("年", bazi.year), ("月", bazi.month), ("日", bazi.day), ("时", bazi.hour)]:
        gods = []
        for hs in [pillar.stem]:
            if hs == bazi.day_master:
                gods.append("日主")
                continue
            elem_me = TIAN_GAN_ELEMENTS[hs]
            elem_dm = TIAN_GAN_ELEMENTS[bazi.day_master]
            yy_me = TIAN_GAN_YINYANG[hs]
            yy_dm = TIAN_GAN_YINYANG[bazi.day_master]

            # Determine relationship
            if elem_me == elem_dm:
                # Same element: 比劫
                rel_type = "比"
            elif SHENG_MAP.get(elem_me) == elem_dm:
                # I generate day master: 印星
                rel_type = "生我"
            elif SHENG_MAP.get(elem_dm) == elem_me:
                # Day master generates me: 食伤
                rel_type = "生"
            elif KE_MAP.get(elem_me) == elem_dm:
                # I control day master: 官杀
                rel_type = "克我"
            elif KE_MAP.get(elem_dm) == elem_me:
                # Day master controls me: 财星
                rel_type = "克"
            else:
                gods.append("?")
                continue

            yy_same = "同" if yy_me == yy_dm else "异"
            god = SHI_SHEN.get((rel_type, yy_same), "?")
            gods.append(god)

        result[name] = gods

    return result


def daily_clash(bazi: BaziFull, target_date=None) -> Dict:
    """Check daily stem-branch clash with natal Bazi."""
    from datetime import date

    if target_date is None:
        target_date = date.today()

    # Calculate day pillar for target date
    jd = _julian_day(target_date.year, target_date.month, target_date.day)
    day_stem_idx = (jd + 9) % 10
    day_branch_idx = (jd + 1) % 12
    daily_stem = TIAN_GAN[day_stem_idx]
    daily_branch = DI_ZHI[day_branch_idx]

    clashes = []

    # Check branch clashes (六冲)
    branch_clash_pairs = [
        ("子", "午"), ("丑", "未"), ("寅", "申"),
        ("卯", "酉"), ("辰", "戌"), ("巳", "亥"),
    ]
    for b1, b2 in branch_clash_pairs:
        for name, pillar in [("年", bazi.year), ("月", bazi.month), ("日", bazi.day), ("时", bazi.hour)]:
            if pillar.branch == b1 and daily_branch == b2:
                clashes.append(("冲", f"日支{daily_branch}冲{name}支{pillar.branch}",
                               "今日地支与命盘相冲，宜谨慎行事，避免重大决策"))
            elif pillar.branch == b2 and daily_branch == b1:
                clashes.append(("冲", f"日支{daily_branch}冲{name}支{pillar.branch}",
                               "今日地支与命盘相冲，宜谨慎行事，避免重大决策"))

    # Check stem combinations (天干五合)
    stem_combine_pairs = [
        ("甲", "己"), ("乙", "庚"), ("丙", "辛"),
        ("丁", "壬"), ("戊", "癸"),
    ]
    for s1, s2 in stem_combine_pairs:
        for name, pillar in [("年", bazi.year), ("月", bazi.month), ("日", bazi.day), ("时", bazi.hour)]:
            if (pillar.stem == s1 and daily_stem == s2) or (pillar.stem == s2 and daily_stem == s1):
                clashes.append(("合", f"日干{daily_stem}合{name}干{pillar.stem}",
                               "天干相合，贵人运佳，适合合作、社交、签约"))

    # Check branch harm (六害)
    harm_pairs = [
        ("子", "未"), ("丑", "午"), ("寅", "巳"),
        ("卯", "辰"), ("申", "亥"), ("酉", "戌"),
    ]
    for b1, b2 in harm_pairs:
        for name, pillar in [("年", bazi.year), ("月", bazi.month), ("日", bazi.day), ("时", bazi.hour)]:
            if (pillar.branch == b1 and daily_branch == b2) or (pillar.branch == b2 and daily_branch == b1):
                clashes.append(("害", f"日支{daily_branch}害{name}支{pillar.branch}",
                               "今日地支相害，小心口舌是非，注意人际关系"))

    return {
        "date": str(target_date),
        "daily_stem": daily_stem,
        "daily_branch": daily_branch,
        "daily_gz": f"{daily_stem}{daily_branch}",
        "clashes": clashes,
        "mood": "吉" if not clashes or all(c[0] == "合" for c in clashes) else
                "凶" if any(c[0] == "冲" for c in clashes) else "平"
    }


# === Quick test ===
if __name__ == "__main__":
    # Paradigme: 2001-04-16, 16:50
    bazi = calculate_bazi(2001, 4, 16, 16, 50)
    print("=== 八字命盘 ===")
    print(bazi)
    print(f"\n日主: {bazi.day_master}{bazi.day_master_element}{bazi.day_master_yinyang}")
    print(f"特质: {bazi.traits}")
    print(f"\n=== 十神 ===")
    for pillar, gods in calculate_shi_shen(bazi).items():
        print(f"{pillar}: {', '.join(gods)}")
    print(f"\n=== 今日流日 ===")
    print(daily_clash(bazi))
