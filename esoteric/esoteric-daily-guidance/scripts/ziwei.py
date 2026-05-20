"""
Ziwei Doushu (紫微斗数) calculation module.
Computes the 12 palaces, major stars, and Four Transformations (四化)
based on birth date, time, and gender.

Key references:
- 命宫 based on birth month (lunar) + birth hour
- 12 palaces derived from 命宫
- 14 major stars (紫微系 + 天府系) placed by birth day and hour
- 四化 (化禄/化权/化科/化忌) based on birth year stem
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# === Constants ===

# Heavenly Stems & Earthly Branches (same as bazi.py)
TIAN_GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
DI_ZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# 12 Palaces (in order)
PALACES = [
    "命宫", "兄弟", "夫妻", "子女", "财帛", "疾厄",
    "迁移", "交友", "官禄", "田宅", "福德", "父母"
]

# Palace element attributes
PALACE_ATTRIBUTES = {
    "命宫": "自我、性格、命运总纲",
    "兄弟": "兄弟姐妹、合作伙伴、平辈关系",
    "夫妻": "配偶、婚姻、感情",
    "子女": "子女、创作、享乐",
    "财帛": "财运、理财能力",
    "疾厄": "健康、体质、灾病",
    "迁移": "外出、变动、社交形象",
    "交友": "朋友、下属、人际关系",
    "官禄": "事业、工作、社会地位",
    "田宅": "房产、家庭、根基",
    "福德": "精神、福报、内心世界",
    "父母": "父母、长辈、上司",
}

# Star categories
STAR_CATEGORIES = {
    "紫微": "帝星", "天机": "智星", "太阳": "贵星", "武曲": "财星",
    "天同": "福星", "廉贞": "囚星", "天府": "库星", "太阴": "富星",
    "贪狼": "桃花", "巨门": "暗星", "天相": "印星", "天梁": "寿星",
    "七杀": "将星", "破军": "耗星",
}

# Star attributes (brief)
STAR_ATTRIBUTES = {
    "紫微": {"五行": "己土", "化气": "尊", "特质": "帝王之气，领导力强，自尊心重"},
    "天机": {"五行": "乙木", "化气": "善", "特质": "智慧机敏，善谋划，多变动"},
    "太阳": {"五行": "丙火", "化气": "贵", "特质": "光明磊落，热情外向，奔波劳碌"},
    "武曲": {"五行": "辛金", "化气": "财", "特质": "刚毅果断，理财能力强，孤克"},
    "天同": {"五行": "壬水", "化气": "福", "特质": "温和享福，随遇而安，懒散"},
    "廉贞": {"五行": "丁火", "化气": "囚", "特质": "刚烈执着，才华横溢，桃花"},
    "天府": {"五行": "戊土", "化气": "库", "特质": "稳重包容，善于管理，保守"},
    "太阴": {"五行": "癸水", "化气": "富", "特质": "温柔细腻，富艺术气质，重感情"},
    "贪狼": {"五行": "甲木", "化气": "桃花", "特质": "多才多艺，交际手腕强，欲望重"},
    "巨门": {"五行": "癸水", "化气": "暗", "特质": "口才犀利，喜钻研，易招是非"},
    "天相": {"五行": "壬水", "化气": "印", "特质": "公正仁慈，辅佐之才，服务心强"},
    "天梁": {"五行": "戊土", "化气": "荫", "特质": "老成稳重，济世助人，长寿"},
    "七杀": {"五行": "庚金", "化气": "杀", "特质": "果断刚猛，开拓进取，冲动"},
    "破军": {"五行": "癸水", "化气": "耗", "特质": "破旧立新，变革力强，不稳定"},
}

# 四化 for each year stem
# (化禄, 化权, 化科, 化忌)
SIHUA_MAP = {
    "甲": ("廉贞", "破军", "武曲", "太阳"),
    "乙": ("天机", "天梁", "紫微", "太阴"),
    "丙": ("天同", "天机", "文昌", "廉贞"),
    "丁": ("太阴", "天同", "天机", "巨门"),
    "戊": ("贪狼", "太阴", "右弼", "天机"),
    "己": ("武曲", "贪狼", "天梁", "文曲"),
    "庚": ("太阳", "武曲", "太阴", "天同"),
    "辛": ("巨门", "太阳", "文曲", "文昌"),
    "壬": ("天梁", "紫微", "左辅", "武曲"),
    "癸": ("破军", "巨门", "太阴", "贪狼"),
}

# 命宫 table: (lunar_month, hour_branch) → 命宫 branch
# hour_branch: 子=0, 丑=1, ..., 亥=11
# Returns index into DI_ZHI for 命宫 branch
MINGGONG_MATRIX = {
    # month: {hour_index: minggong_branch_index}
    1:  {0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 8, 9: 9, 10: 10, 11: 11},
    2:  {0: 11, 1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6, 8: 7, 9: 8, 10: 9, 11: 10},
    3:  {0: 10, 1: 11, 2: 0, 3: 1, 4: 2, 5: 3, 6: 4, 7: 5, 8: 6, 9: 7, 10: 8, 11: 9},
    4:  {0: 9, 1: 10, 2: 11, 3: 0, 4: 1, 5: 2, 6: 3, 7: 4, 8: 5, 9: 6, 10: 7, 11: 8},
    5:  {0: 8, 1: 9, 2: 10, 3: 11, 4: 0, 5: 1, 6: 2, 7: 3, 8: 4, 9: 5, 10: 6, 11: 7},
    6:  {0: 7, 1: 8, 2: 9, 3: 10, 4: 11, 5: 0, 6: 1, 7: 2, 8: 3, 9: 4, 10: 5, 11: 6},
    7:  {0: 6, 1: 7, 2: 8, 3: 9, 4: 10, 5: 11, 6: 0, 7: 1, 8: 2, 9: 3, 10: 4, 11: 5},
    8:  {0: 5, 1: 6, 2: 7, 3: 8, 4: 9, 5: 10, 6: 11, 7: 0, 8: 1, 9: 2, 10: 3, 11: 4},
    9:  {0: 4, 1: 5, 2: 6, 3: 7, 4: 8, 5: 9, 6: 10, 7: 11, 8: 0, 9: 1, 10: 2, 11: 3},
    10: {0: 3, 1: 4, 2: 5, 3: 6, 4: 7, 5: 8, 6: 9, 7: 10, 8: 11, 9: 0, 10: 1, 11: 2},
    11: {0: 2, 1: 3, 2: 4, 3: 5, 4: 6, 5: 7, 6: 8, 7: 9, 8: 10, 9: 11, 10: 0, 11: 1},
    12: {0: 1, 1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 9, 9: 10, 10: 11, 11: 0},
}

# 紫微星 position based on 五行局 and birth day
# 五行局 determined by 命宫 stem-branch
# (nayin_element, nayin_phase) → ziwei_offset table
# We'll compute ziwei position using the standard algorithm

# 五行局 (Five Element Bureau) determined by 命宫 stem-branch 纳音
# Key: (minggong_stem, minggong_branch) → ("element", "局数")
NAYIN = {
    ("甲", "子"): ("金", 4), ("乙", "丑"): ("金", 4),
    ("丙", "寅"): ("火", 6), ("丁", "卯"): ("火", 6),
    ("戊", "辰"): ("木", 3), ("己", "巳"): ("木", 3),
    ("庚", "午"): ("土", 5), ("辛", "未"): ("土", 5),
    ("壬", "申"): ("金", 4), ("癸", "酉"): ("金", 4),
    ("甲", "戌"): ("火", 6), ("乙", "亥"): ("火", 6),
    ("丙", "子"): ("水", 2), ("丁", "丑"): ("水", 2),
    ("戊", "寅"): ("土", 5), ("己", "卯"): ("土", 5),
    ("庚", "辰"): ("金", 4), ("辛", "巳"): ("金", 4),
    ("壬", "午"): ("木", 3), ("癸", "未"): ("木", 3),
    ("甲", "申"): ("水", 2), ("乙", "酉"): ("水", 2),
    ("丙", "戌"): ("土", 5), ("丁", "亥"): ("土", 5),
    ("戊", "子"): ("火", 6), ("己", "丑"): ("火", 6),
    ("庚", "寅"): ("木", 3), ("辛", "卯"): ("木", 3),
    ("壬", "辰"): ("水", 2), ("癸", "巳"): ("水", 2),
    ("甲", "午"): ("金", 4), ("乙", "未"): ("金", 4),
    ("丙", "申"): ("火", 6), ("丁", "酉"): ("火", 6),
    ("戊", "戌"): ("木", 3), ("己", "亥"): ("木", 3),
    ("庚", "子"): ("土", 5), ("辛", "丑"): ("土", 5),
    ("壬", "寅"): ("金", 4), ("癸", "卯"): ("金", 4),
    ("甲", "辰"): ("火", 6), ("乙", "巳"): ("火", 6),
    ("丙", "午"): ("水", 2), ("丁", "未"): ("水", 2),
    ("戊", "申"): ("土", 5), ("己", "酉"): ("土", 5),
    ("庚", "戌"): ("金", 4), ("辛", "亥"): ("金", 4),
    ("壬", "子"): ("木", 3), ("癸", "丑"): ("木", 3),
    ("甲", "寅"): ("水", 2), ("乙", "卯"): ("水", 2),
    ("丙", "辰"): ("土", 5), ("丁", "巳"): ("土", 5),
    ("戊", "午"): ("火", 6), ("己", "未"): ("火", 6),
    ("庚", "申"): ("木", 3), ("辛", "酉"): ("木", 3),
    ("壬", "戌"): ("水", 2), ("癸", "亥"): ("水", 2),
}

# Ziwei star position: computed from 五行局 number and birth day
# ziwei_branch_idx = (birth_day + offset) % 12, where offset depends on 局数
# Standard algorithm for offset based on 局数:
ZIWEI_OFFSETS = {
    2: [2, 4, 6, 8, 10, 0],  # 水二局
    3: [3, 6, 9, 0],          # 木三局
    4: [4, 8, 0],             # 金四局
    5: [5, 10, 3, 8, 1, 6, 11, 4, 9, 2, 7, 0],  # 土五局
    6: [6, 0],                # 火六局
}

# 天府系星 position relative to 天府 (which is symmetric to 紫微)
# 天府_branch = (2 * (DI_ZHI.index(命宫_branch)) - DI_ZHI.index(紫微_branch)) % 12
# Then 天府系 stars:
TIANFU_SERIES = {
    "天府": 0, "太阴": 1, "贪狼": 2, "巨门": 3,
    "天相": 4, "天梁": 5, "七杀": 6,
}

# 紫微系星 position relative to 紫微
ZIWEI_SERIES = {
    "紫微": 0, "天机": -1, "太阳": -3, "武曲": -4,
    "天同": -5, "廉贞": -7,
}


@dataclass
class ZiweiPalace:
    """A single palace in Ziwei chart"""
    name: str
    branch: str
    major_stars: List[str] = field(default_factory=list)
    minor_stars: List[str] = field(default_factory=list)
    sihua: Optional[str] = None  # 化禄/化权/化科/化忌

    def __str__(self) -> str:
        stars = ", ".join(self.major_stars) or "无主星"
        sihua_str = f" [{self.sihua}]" if self.sihua else ""
        return f"{self.name}({self.branch}): {stars}{sihua_str}"


@dataclass
class ZiweiChart:
    """Complete Ziwei Doushu chart"""
    palaces: Dict[str, ZiweiPalace]  # palace_name → ZiweiPalace
    minggong_name: str
    minggong_branch: str
    shenggong_name: str
    wuxing_ju: Tuple[str, int]
    sihua: Dict[str, str]  # star→sihua_type

    def format_chart(self) -> str:
        """Format chart in a readable layout"""
        order = ["命宫", "兄弟", "夫妻", "子女", "财帛", "疾厄",
                 "迁移", "交友", "官禄", "田宅", "福德", "父母"]
        lines = []
        for name in order:
            p = self.palaces[name]
            lines.append(str(p))
        return "\n".join(lines)


def _gregorian_to_lunar(year: int, month: int, day: int) -> Tuple[int, int, int, bool]:
    """Convert Gregorian date to lunar date.
    Returns (lunar_year, lunar_month, lunar_day, is_leap_month).
    Uses lunardate library."""
    import lunardate
    ld = lunardate.LunarDate.fromSolarDate(year, month, day)
    # lunardate doesn't directly expose leap month status easily
    # We'll use a simplified conversion
    return ld.year, ld.month, ld.day, False


def _hour_to_branch_idx(hour: int) -> int:
    """Convert hour (0-23) to branch index (0=子, 1=丑, ..., 11=亥)."""
    return (hour + 1) // 2 % 12


def calculate_ziwei(year: int, month: int, day: int, hour: int,
                    year_stem: str, gender: str = "男") -> ZiweiChart:
    """Calculate complete Ziwei Doushu chart."""

    # 1. Convert to lunar date
    lunar_y, lunar_m, lunar_d, _ = _gregorian_to_lunar(year, month, day)

    # 2. Determine 命宫
    hour_idx = _hour_to_branch_idx(hour)
    minggong_branch_idx = MINGGONG_MATRIX[lunar_m][hour_idx]
    minggong_branch = DI_ZHI[minggong_branch_idx]

    # 3. Determine 命宫 stem (寅宫 stem based on year stem)
    # 五虎遁: starting stem for 寅 based on year stem
    wuhu_start = {
        "甲": "丙", "乙": "戊", "丙": "庚", "丁": "壬",
        "戊": "甲", "己": "丙", "庚": "戊", "辛": "庚",
        "壬": "壬", "癸": "甲",
    }
    yin_stem = wuhu_start[year_stem]
    yin_stem_idx = TIAN_GAN.index(yin_stem)
    minggong_stem_idx = (yin_stem_idx + minggong_branch_idx - 2) % 10  # 寅=2
    minggong_stem = TIAN_GAN[minggong_stem_idx]

    # 4. 五行局
    nayin_key = (minggong_stem, minggong_branch)
    element, ju_shu = NAYIN.get(nayin_key, ("土", 5))

    # 5. 紫微星位置
    birth_day = lunar_d
    ziwei_offset_list = ZIWEI_OFFSETS[ju_shu]
    # Find the offset where (birth_day + offset) % ju_shu == 0
    # Then ziwei_branch = offset_to_branch(offset)
    # Standard algorithm:
    #   Divide birth_day by ju_shu, get quotient and remainder
    #   The offset that gives exact division determines ziwei position
    quotient = (birth_day - 1) // ju_shu
    remainder = birth_day % ju_shu
    if remainder == 0:
        remainder = ju_shu

    # Map to offset array
    ziwei_offset = ziwei_offset_list[remainder - 1]
    ziwei_branch_idx = (ziwei_offset + quotient) % 12

    # 6. 天府星位置 (symmetric to 紫微)
    tianfu_branch_idx = (2 * (2) - ziwei_branch_idx) % 12  # 寅=2
    # Actually: 天府 = (寅_idx + 寅_idx - 紫微_idx) mod 12
    tianfu_branch_idx = (4 - ziwei_branch_idx) % 12

    # 7. Place stars
    # Initialize 12 palaces
    palaces = {}
    for i, palace_name in enumerate(PALACES):
        branch_idx = (minggong_branch_idx + i) % 12
        palaces[palace_name] = ZiweiPalace(
            name=palace_name,
            branch=DI_ZHI[branch_idx],
        )

    # Place 紫微系 stars
    for star_name, offset in ZIWEI_SERIES.items():
        star_branch_idx = (ziwei_branch_idx + offset) % 12
        star_branch = DI_ZHI[star_branch_idx]
        # Find which palace has this branch
        for palace_name, palace in palaces.items():
            if palace.branch == star_branch:
                palace.major_stars.append(star_name)

    # Place 天府系 stars
    for star_name, offset in TIANFU_SERIES.items():
        star_branch_idx = (tianfu_branch_idx + offset) % 12
        star_branch = DI_ZHI[star_branch_idx]
        for palace_name, palace in palaces.items():
            if palace.branch == star_branch:
                palace.major_stars.append(star_name)

    # 8. 四化
    sihua_stars = SIHUA_MAP.get(year_stem, ("", "", "", ""))
    sihua = {
        "化禄": sihua_stars[0],
        "化权": sihua_stars[1],
        "化科": sihua_stars[2],
        "化忌": sihua_stars[3],
    }

    # Annotate palaces with sihua
    for sihua_type, star in sihua.items():
        if not star:
            continue
        for palace in palaces.values():
            if star in palace.major_stars:
                palace.sihua = sihua_type

    # 9. 身宫 (at lunar month offset from 命宫, reversed for male? No, it's fixed)
    # 身宫: from 命宫, count clockwise lunar_month positions
    shengong_idx = (minggong_branch_idx + lunar_m - 1) % 12
    shengong_name = PALACES[shengong_idx % 12]

    return ZiweiChart(
        palaces=palaces,
        minggong_name=PALACES[0],
        minggong_branch=minggong_branch,
        shenggong_name=shengong_name,
        wuxing_ju=(element, ju_shu),
        sihua=sihua,
    )


def format_ziwei_chart(chart: ZiweiChart) -> str:
    """Format chart for display."""
    lines = []
    lines.append(f"命宫: {chart.minggong_branch} | 身宫: {chart.shenggong_name}")
    lines.append(f"五行局: {chart.wuxing_ju[0]}（局数 {chart.wuxing_ju[1]}）")
    lines.append(f"四化: {', '.join(f'{k}({v})' for k, v in chart.sihua.items() if v)}")
    lines.append("")
    lines.append("=== 十二宫 ===")
    for name in PALACES:
        p = chart.palaces[name]
        stars = ", ".join(p.major_stars) if p.major_stars else "无主星"
        sihua = f" [{p.sihua}]" if p.sihua else ""
        attr = PALACE_ATTRIBUTES.get(name, "")
        lines.append(f"  {name}({p.branch}): {stars}{sihua}  — {attr}")
    return "\n".join(lines)


# === Quick test ===
if __name__ == "__main__":
    # Paradigme: 2001-04-16, 16:50, 辛巳年
    chart = calculate_ziwei(2001, 4, 16, 16, "辛", "男")
    print(format_ziwei_chart(chart))
