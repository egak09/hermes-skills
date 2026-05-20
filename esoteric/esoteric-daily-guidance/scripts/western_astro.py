"""
Western Astrology module using Skyfield for planetary positions.
Computes natal chart (planets, houses, aspects) and daily transits.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import math

# === Zodiac Signs ===
SIGNS = [
    "白羊♈", "金牛♉", "双子♊", "巨蟹♋",
    "狮子♌", "处女♍", "天秤♎", "天蝎♏",
    "射手♐", "摩羯♑", "水瓶♒", "双鱼♓"
]

SIGN_EMOJIS = {
    "白羊": "♈", "金牛": "♉", "双子": "♊", "巨蟹": "♋",
    "狮子": "♌", "处女": "♍", "天秤": "♎", "天蝎": "♏",
    "射手": "♐", "摩羯": "♑", "水瓶": "♒", "双鱼": "♓"
}

SIGN_ELEMENTS = {
    "白羊": "火", "狮子": "火", "射手": "火",
    "金牛": "土", "处女": "土", "摩羯": "土",
    "双子": "风", "天秤": "风", "水瓶": "风",
    "巨蟹": "水", "天蝎": "水", "双鱼": "水",
}

SIGN_MODALITIES = {
    "白羊": "开创", "巨蟹": "开创", "天秤": "开创", "摩羯": "开创",
    "金牛": "固定", "狮子": "固定", "天蝎": "固定", "水瓶": "固定",
    "双子": "变动", "处女": "变动", "射手": "变动", "双鱼": "变动",
}

SIGN_RULERS = {
    "白羊": "火星", "金牛": "金星", "双子": "水星", "巨蟹": "月亮",
    "狮子": "太阳", "处女": "水星", "天秤": "金星", "天蝎": "冥王",
    "射手": "木星", "摩羯": "土星", "水瓶": "天王", "双鱼": "海王",
}

PLANETS = ["太阳", "月亮", "水星", "金星", "火星", "木星", "土星", "天王", "海王", "冥王"]

PLANET_TRAITS = {
    "太阳": "自我意识、生命力、核心人格",
    "月亮": "情绪、潜意识、内在需求",
    "水星": "思维、沟通、学习方式",
    "金星": "爱情、审美、价值观",
    "火星": "行动力、欲望、竞争方式",
    "木星": "扩张、幸运、信念系统",
    "土星": "责任、限制、人生课题",
    "天王": "革新、独立、突变",
    "海王": "梦想、直觉、灵性",
    "冥王": "蜕变、权力、深层转化",
}

ASPECT_TYPES = {
    "合": (0, 8), "冲": (180, 8), "拱": (120, 8),
    "刑": (90, 6), "六合": (60, 6),
}

ASPECT_MEANINGS = {
    "合": "融合加强",
    "冲": "对立张力",
    "拱": "和谐流畅",
    "刑": "冲突挑战",
    "六合": "机会助力",
}

HOUSE_MEANINGS = {
    1: "自我形象、外在表现",
    2: "金钱、价值观、资源",
    3: "沟通、学习、短途",
    4: "家庭、根源、安全感",
    5: "创造、恋爱、享乐",
    6: "工作、健康、日常",
    7: "伴侣、合作、一对一",
    8: "深层、共享资源、转化",
    9: "高等学习、旅行、信仰",
    10: "事业、社会地位、声望",
    11: "社群、友谊、理想",
    12: "潜意识、灵性、隐秘",
}


@dataclass
class PlanetPosition:
    name: str
    sign: str
    degree: float
    house: int
    retrograde: bool = False

    def __str__(self) -> str:
        r = " ℞" if self.retrograde else ""
        return f"{self.name}: {self.sign} {self.degree:.1f}° {r}— {PLANET_TRAITS.get(self.name, '')}"


@dataclass
class Aspect:
    planet1: str
    planet2: str
    aspect_type: str
    orb: float

    def __str__(self) -> str:
        return f"{self.planet1} {self.aspect_type} {self.planet2} ({self.orb:.1f}°)"


@dataclass
class NatalChart:
    """Western natal chart"""
    planets: List[PlanetPosition]
    ascendant: str
    asc_degree: float
    mc: str
    mc_degree: float
    houses: List[Tuple[str, float]]
    aspects: List[Aspect]
    sun_sign: str
    moon_sign: str
    asc_sign: str

    def format(self) -> str:
        lines = []
        lines.append(f"上升: {self.asc_sign} {self.asc_degree:.1f}° | 天顶: {self.mc} {self.mc_degree:.1f}°")
        lines.append(f"太阳: {self.sun_sign} | 月亮: {self.moon_sign} | 上升: {self.asc_sign}")
        lines.append("")
        lines.append("=== 行星位置 ===")
        for p in self.planets:
            lines.append(f"  {p}")
        lines.append("")
        lines.append("=== 主要相位 ===")
        for a in self.aspects:
            lines.append(f"  {a}")
        return "\n".join(lines)


def _sign_from_longitude(lon: float) -> Tuple[str, float]:
    """Convert ecliptic longitude to sign and degree."""
    idx = int(lon // 30) % 12
    degree = lon % 30
    sign = SIGNS[idx].rstrip("♈♉♊♋♌♍♎♏♐♑♒♓")
    return sign, degree


def _calculate_houses(asc_lon: float, mc_lon: float) -> List[Tuple[str, float]]:
    """Calculate house cusps (simplified equal house system)."""
    houses = []
    for i in range(12):
        cusp_lon = (asc_lon + i * 30) % 360
        sign, deg = _sign_from_longitude(cusp_lon)
        houses.append((sign, deg))
    return houses


def _house_for_longitude(lon: float, asc_lon: float) -> int:
    """Determine which house a longitude falls in."""
    diff = (lon - asc_lon) % 360
    return int(diff // 30) + 1


def _calculate_aspects(planets: List[PlanetPosition]) -> List[Aspect]:
    """Calculate aspects between planets."""
    aspects = []

    # Sign-degree to absolute longitude
    sign_starts = {
        "白羊": 0, "金牛": 30, "双子": 60, "巨蟹": 90,
        "狮子": 120, "处女": 150, "天秤": 180, "天蝎": 210,
        "射手": 240, "摩羯": 270, "水瓶": 300, "双鱼": 330,
    }

    def _get_lon(p: PlanetPosition) -> float:
        return sign_starts.get(p.sign, 0) + p.degree

    for i in range(len(planets)):
        for j in range(i + 1, len(planets)):
            p1, p2 = planets[i], planets[j]
            lon1 = _get_lon(p1)
            lon2 = _get_lon(p2)
            diff = abs(lon1 - lon2)
            if diff > 180:
                diff = 360 - diff

            for aspect_name, (target, max_orb) in ASPECT_TYPES.items():
                orb = abs(diff - target)
                if orb <= max_orb:
                    aspects.append(Aspect(p1.name, p2.name, aspect_name, orb))

    return aspects


def calculate_natal_chart(year: int, month: int, day: int,
                          hour: int, minute: int,
                          lat: float, lon: float,
                          tz_offset: float = 8.0) -> NatalChart:
    """
    Calculate natal chart using Skyfield.

    Args:
        year, month, day: birth date (Gregorian)
        hour, minute: birth time
        lat, lon: birth location coordinates
        tz_offset: timezone offset from UTC (hours)
    """
    from skyfield.api import load, wgs84
    from skyfield.framelib import ecliptic_frame

    ts = load.timescale()

    # Birth time
    utc_hour = hour - tz_offset
    birth_dt = datetime(year, month, day, int(utc_hour),
                        int((utc_hour - int(utc_hour)) * 60 + minute))
    birth_time = ts.utc(birth_dt.year, birth_dt.month, birth_dt.day,
                        birth_dt.hour, birth_dt.minute, birth_dt.second)

    # Load ephemeris
    eph = load('de421.bsp')
    earth = eph['earth']
    observer = earth + wgs84.latlon(lat, lon)

    # Calculate planet positions
    planet_bodies = {
        "太阳": eph['sun'],
        "月亮": eph['moon'],
        "水星": eph['mercury'],
        "金星": eph['venus'],
        "火星": eph['mars'],
        "木星": eph['jupiter barycenter'],
        "土星": eph['saturn barycenter'],
        "天王": eph['uranus barycenter'],
        "海王": eph['neptune barycenter'],
        "冥王": eph['pluto barycenter'],
    }

    planets = []
    for name, body in planet_bodies.items():
        astrometric = observer.at(birth_time).observe(body)
        lat_ec, lon_ec, _ = astrometric.frame_latlon(ecliptic_frame)
        ecliptic_lon = lon_ec.degrees % 360
        sign, degree = _sign_from_longitude(ecliptic_lon)
        planets.append(PlanetPosition(name=name, sign=sign, degree=round(degree, 2), house=0))

    # Calculate ASC and MC
    # ASC = exact degree rising on eastern horizon at birth
    # Simplified calculation using Local Sidereal Time
    from skyfield.framelib import itrs
    from skyfield.positionlib import Geocentric

    # Accurate LST calculation
    # Use the observer's position at birth time
    geo = observer.at(birth_time)

    # Get RA/Dec
    ra, dec, _ = geo.radec()

    # Calculate GST (Greenwich Sidereal Time)
    # Using the sidereal_time method from skyfield
    gst = birth_time.gmst + ra.hours
    lst = gst + lon / 15.0
    lst = lst % 24

    # Convert LST hours to RAMC in degrees
    ramc = lst * 15.0

    # ASC = RAMC + 90° on ecliptic (simplified)
    asc_lon = (ramc + 90) % 360
    mc_lon = ramc % 360

    asc_sign, asc_deg = _sign_from_longitude(asc_lon)
    mc_sign, mc_deg = _sign_from_longitude(mc_lon)

    # Assign houses
    for p in planets:
        sign_starts_map = {
            "白羊": 0, "金牛": 30, "双子": 60, "巨蟹": 90,
            "狮子": 120, "处女": 150, "天秤": 180, "天蝎": 210,
            "射手": 240, "摩羯": 270, "水瓶": 300, "双鱼": 330,
        }
        p_lon = sign_starts_map.get(p.sign, 0) + p.degree
        p.house = _house_for_longitude(p_lon, asc_lon)

    # Calculate aspects
    aspects = _calculate_aspects(planets)

    # Houses
    houses = _calculate_houses(asc_lon, mc_lon)

    # Sun, Moon, ASC signs
    sun_planet = next(p for p in planets if p.name == "太阳")
    moon_planet = next(p for p in planets if p.name == "月亮")

    return NatalChart(
        planets=planets,
        ascendant=asc_sign,
        asc_degree=round(asc_deg, 2),
        mc=mc_sign,
        mc_degree=round(mc_deg, 2),
        houses=houses,
        aspects=aspects,
        sun_sign=sun_planet.sign,
        moon_sign=moon_planet.sign,
        asc_sign=asc_sign,
    )


def daily_transits(natal: NatalChart,
                   target_year: int = None, target_month: int = None,
                   target_day: int = None) -> Dict:
    """Calculate daily transiting planets vs natal chart."""
    if target_year is None:
        now = datetime.now()
        target_year, target_month, target_day = now.year, now.month, now.day

    # Simple daily transit - just check moon sign and sun sign for basic guidance
    # In production, we'd calculate full transits

    from skyfield.api import load, wgs84
    from skyfield.framelib import ecliptic_frame

    ts = load.timescale()
    transit_time = ts.utc(target_year, target_month, target_day, 12, 0)
    eph = load('de421.bsp')
    earth = eph['earth']

    body = eph['sun']
    astrometric = earth.at(transit_time).observe(body)
    _, lon_ec, _ = astrometric.frame_latlon(ecliptic_frame)
    sun_lon = lon_ec.degrees % 360
    current_sun_sign, _ = _sign_from_longitude(sun_lon)

    body = eph['moon']
    astrometric = earth.at(transit_time).observe(body)
    _, lon_ec, _ = astrometric.frame_latlon(ecliptic_frame)
    moon_lon = lon_ec.degrees % 360
    current_moon_sign, _ = _sign_from_longitude(moon_lon)

    return {
        "date": f"{target_year}-{target_month:02d}-{target_day:02d}",
        "sun_sign": current_sun_sign,
        "moon_sign": current_moon_sign,
        "sun_element": SIGN_ELEMENTS.get(current_sun_sign, ""),
        "moon_element": SIGN_ELEMENTS.get(current_moon_sign, ""),
    }


if __name__ == "__main__":
    # Paradigme: 2001-04-16 16:50, Datong Qinghai (36.9°N, 101.6°E), UTC+8
    try:
        chart = calculate_natal_chart(2001, 4, 16, 16, 50, 36.9, 101.6, 8.0)
        print(chart.format())
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
