"""Japanese TTS normalizer.

Handles:
- Cardinals (42 → 四十二)
- Ordinals (第1 → 第一)
- Decimals (3.14 → 三点一四)
- Percentages (50% → 五十パーセント)
- Currency (¥/$/€/£)
- Dates (2026-04-13, YYYY年M月D日)
- Times (10:30 → 十時三十分)
- Physical units (kg, km, cm, °C, …)
- Phone numbers (digit-by-digit)
- Scientific notation (1.5×10^6 → 百五十万)
- Version numbers (1.0.0 → 一点零点零)
- Common symbols
"""

from __future__ import annotations

import re
from typing import List

from .base import BaseNormalizer

# ---------------------------------------------------------------------------
# Digit maps
# ---------------------------------------------------------------------------
_DIGITS_JA = "〇一二三四五六七八九"
_MAGNITUDES_JA = ["", "万", "億", "兆"]


def _group4_to_ja(n: int) -> str:
    """Convert a 4-digit group (1–9999) to Japanese kanji.

    Rule: coefficient 1 is dropped before 十/百/千 (e.g. 百, 千)
    but kept before 万/億/兆 (handled in _int_to_ja).
    """
    units = ["", "十", "百", "千"]
    parts = []
    for i in range(3, -1, -1):
        d = n // (10 ** i) % 10
        if d == 0:
            continue
        if d == 1 and i > 0:
            parts.append(units[i])          # 一十→十, 一百→百, 一千→千
        else:
            parts.append(_DIGITS_JA[d] + units[i])
    return "".join(parts)


def _int_to_ja(n: int) -> str:
    """Convert a non-negative integer to Japanese spoken form."""
    if n < 0:
        return "マイナス" + _int_to_ja(-n)
    if n == 0:
        return "零"

    groups: List[int] = []
    tmp = n
    while tmp > 0:
        groups.append(tmp % 10000)
        tmp //= 10000

    result = ""
    for mag_idx, group in enumerate(reversed(groups)):
        if group == 0:
            continue
        mag = _MAGNITUDES_JA[len(groups) - 1 - mag_idx]
        result += _group4_to_ja(group) + mag

    return result or "零"


def _year_to_ja(year_str: str) -> str:
    """Read a year string digit-by-digit (二〇二六)."""
    return "".join(_DIGITS_JA[int(c)] for c in year_str)


def _decimal_to_ja(s: str) -> str:
    """Decimal → spoken (digit-by-digit after decimal point)."""
    integer_str, frac_str = s.split(".")
    return (_int_to_ja(int(integer_str)) + "点"
            + "".join(_DIGITS_JA[int(c)] for c in frac_str))


def _digits_to_ja(s: str) -> str:
    """Read digits one-by-one."""
    return "".join(_DIGITS_JA[int(c)] for c in s)


def _silent_hyphen_token_to_ja(token: str) -> str:
    """Drop no-space hyphens in code-like tokens and read digits digit-by-digit."""
    token = token.replace("-", "")
    return re.sub(r"\d+", lambda m: _digits_to_ja(m.group(0)), token)


def _sci_to_ja(base_str: str, exp_str: str, neg_exp: bool = False) -> str:
    e = int(exp_str)
    if neg_exp:
        denom = _int_to_ja(10 ** e)
        if "." in base_str:
            integer_str, frac_str = base_str.split(".")
            num = (_int_to_ja(int(integer_str)) + "・"
                   + "".join(_DIGITS_JA[int(c)] for c in frac_str))
        else:
            num = _int_to_ja(int(base_str))
        return denom + "分の" + num
    else:
        val = round(float(base_str) * (10 ** e))
        return _int_to_ja(val)


_RATE_UNIT_JA = {
    "kg": "キログラム", "g": "グラム", "mg": "ミリグラム",
    "km": "キロメートル", "m": "メートル", "cm": "センチメートル", "mm": "ミリメートル",
    "L": "リットル", "l": "リットル", "ml": "ミリリットル", "mL": "ミリリットル",
    "dL": "デシリットル", "dl": "デシリットル",
    "kWh": "キロワット時", "Wh": "ワット時", "kW": "キロワット", "W": "ワット",
    "TB": "テラバイト", "GB": "ギガバイト", "MB": "メガバイト", "KB": "キロバイト",
    "Tb": "テラビット", "Gb": "ギガビット", "Mb": "メガビット", "Kb": "キロビット",
    "tb": "テラビット", "gb": "ギガビット", "mb": "メガビット", "kb": "キロビット", "b": "ビット",
    "Hz": "ヘルツ", "kHz": "キロヘルツ", "MHz": "メガヘルツ", "GHz": "ギガヘルツ",
    "Pa": "パスカル", "kPa": "キロパスカル", "MPa": "メガパスカル",
    "beat": "拍", "beats": "拍", "breath": "呼吸", "breaths": "呼吸",
    "frame": "フレーム", "frames": "フレーム", "word": "語", "words": "語",
    "request": "リクエスト", "requests": "リクエスト", "r": "回転",
}

_RATE_DEN_JA = {
    **_RATE_UNIT_JA,
    "h": "時間", "hr": "時間", "hrs": "時間", "hour": "時間", "hours": "時間",
    "s": "秒", "sec": "秒", "secs": "秒", "second": "秒", "seconds": "秒",
    "min": "分", "mins": "分", "minute": "分", "minutes": "分",
    "d": "日", "day": "日", "days": "日",
    "wk": "週", "wks": "週", "week": "週", "weeks": "週",
    "mo": "月", "month": "月", "months": "月",
    "yr": "年", "yrs": "年", "year": "年", "years": "年",
    "person": "人", "people": "人", "unit": "単位", "units": "単位",
    "piece": "個", "pieces": "個", "serving": "食", "servings": "食",
    "seat": "席", "seats": "席",
}

_RATE_UNIT_RE_JA = "|".join(re.escape(u) for u in sorted(_RATE_UNIT_JA, key=len, reverse=True))
_RATE_DEN_RE_JA = "|".join(re.escape(u) for u in sorted(_RATE_DEN_JA, key=len, reverse=True))
_RATE_HOUR_DEN_JA = {"h", "hr", "hrs", "hour", "hours"}


def _rate_number_to_ja(s: str) -> str:
    return _decimal_to_ja(s) if "." in s else _int_to_ja(int(s))


def _rate_den_part_ja(token: str, count: str | None = None, power: str | None = None) -> str:
    unit = _RATE_DEN_JA.get(token, _RATE_DEN_JA[token.lower()])
    if power in ("2", "^2", "²"):
        unit += "の二乗"
    elif power in ("3", "^3", "³"):
        unit += "の三乗"
    return (_rate_number_to_ja(count) if count is not None else "一") + unit


def _slash_rate_ja(value: str, unit: str, denominator: str) -> str:
    den_match = re.fullmatch(r"([A-Za-z]+)", denominator.strip())
    if unit == "km" and den_match and den_match.group(1) in _RATE_HOUR_DEN_JA:
        return "時速" + _rate_number_to_ja(value) + "キロメートル"

    value_phrase = _rate_number_to_ja(value) + _RATE_UNIT_JA.get(unit, _RATE_UNIT_JA[unit.lower()])
    den_parts = []
    for part in re.split(r"\s*/\s*", denominator):
        m = re.fullmatch(r"(\d+(?:\.\d+)?)?\s*([A-Za-zμ]+)(\^?[23]|[²³])?", part)
        if not m:
            den_parts.append(part)
            continue
        den_parts.append(_rate_den_part_ja(m.group(2), m.group(1), m.group(3)))

    return "あたり".join(den_parts) + "あたり" + value_phrase


_ASCII_ROMAN_VALUES_JA = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
_ASCII_ROMAN_RE_JA = r"M{0,3}(?:CM|CD|D?C{0,3})(?:XC|XL|L?X{0,3})(?:IX|IV|V?I{0,3})"
_WEEKDAY_JA = {
    "月": "月曜日", "火": "火曜日", "水": "水曜日", "木": "木曜日",
    "金": "金曜日", "土": "土曜日", "日": "日曜日",
}
_WHITELIST_JA = {
    "Dr.": "ドクター",
    "Prof.": "教授",
    "Mr.": "ミスター",
    "Mrs.": "ミセス",
    "Ms.": "ミズ",
    "No.": "第",
}


def _roman_to_ja(token: str) -> str:
    if not token or not re.fullmatch(_ASCII_ROMAN_RE_JA, token):
        return token
    total = 0
    prev = 0
    for ch in reversed(token):
        value = _ASCII_ROMAN_VALUES_JA[ch]
        if value < prev:
            total -= value
        else:
            total += value
            prev = value
    return _int_to_ja(total) if 1 <= total <= 3999 else token


def _range_number_ja(s: str) -> str:
    return _decimal_to_ja(s) if "." in s else _int_to_ja(int(s))


# ---------------------------------------------------------------------------
# Pattern registry
# ---------------------------------------------------------------------------

def _build_patterns():
    p = []

    # 0. 大字（正式漢字）→ 通常漢字（TTS誤読防止）
    _daiji = {"壱": "一", "弐": "二", "参": "三", "伍": "五", "玖": "九", "拾": "十",
              "佰": "百", "仟": "千", "萬": "万"}
    p.append((
        re.compile("[" + "".join(_daiji.keys()) + "]"),
        lambda m, d=_daiji: d.get(m.group(0), m.group(0)),
    ))

    # 0b. Thousands comma removal (12,345 → 12345)
    p.append((re.compile(r"(?<=\d),(?=\d{3})"), lambda m: ""))

    # 1a. IP address (before version-number and decimal patterns)
    p.append((
        re.compile(r"\b(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})\b"),
        lambda m: "点".join(
            "".join(_DIGITS_JA[int(c)] for c in part)
            for part in [m.group(1), m.group(2), m.group(3), m.group(4)]
        ),
    ))

    # 1a1. Conservative ASCII Roman numerals in Japanese/CJK contexts.
    roman_token_ja = r"(?=[MDCLXVI])" + _ASCII_ROMAN_RE_JA
    p.append((
        re.compile(rf"第({roman_token_ja})(?=[章节章巻卷部幕篇])"),
        lambda m: "第" + _roman_to_ja(m.group(1)),
    ))
    p.append((
        re.compile(rf"\b({roman_token_ja})(?=型|類|級|期|区|組)"),
        lambda m: _roman_to_ja(m.group(1)),
    ))

    # 1a2. Strict cased whitelist for mixed English abbreviations.
    whitelist_ja_re = "|".join(re.escape(k) for k in sorted(_WHITELIST_JA, key=len, reverse=True))
    p.append((
        re.compile(rf"(?<![A-Za-z])({whitelist_ja_re})(?![A-Za-z])"),
        lambda m: _WHITELIST_JA[m.group(1)],
    ))

    # 1b. Scientific notation (before integer/decimal)
    p.append((
        re.compile(r"(\d+(?:\.\d+)?)[×x\*]10\^-(\d+)"),
        lambda m: _sci_to_ja(m.group(1), m.group(2), neg_exp=True),
    ))
    p.append((
        re.compile(r"(\d+(?:\.\d+)?)[×x\*]10\^(\d+)"),
        lambda m: _sci_to_ja(m.group(1), m.group(2)),
    ))
    p.append((
        re.compile(r"(\d+(?:\.\d+)?)[eE]-(\d+)"),
        lambda m: _sci_to_ja(m.group(1), m.group(2), neg_exp=True),
    ))
    p.append((
        re.compile(r"(\d+(?:\.\d+)?)[eE]\+?(\d+)"),
        lambda m: _sci_to_ja(m.group(1), m.group(2)),
    ))

    # 1b1. Dot date must precede version numbers.
    p.append((
        re.compile(r"(\d{4})\.(\d{1,2})\.(\d{1,2})"),
        lambda m: (
            _year_to_ja(m.group(1)) + "年"
            + _int_to_ja(int(m.group(2))) + "月"
            + _int_to_ja(int(m.group(3))) + "日"
        ),
    ))

    # 1c. Version numbers: N.N.N… (3+ components) → 一点零点零
    p.append((
        re.compile(r"\d+(?:\.\d+){2,}"),
        lambda m: "点".join(_int_to_ja(int(part)) for part in m.group(0).split(".")),
    ))

    # 1d. 第N ordinal
    p.append((
        re.compile(r"第(\d+)"),
        lambda m: "第" + _int_to_ja(int(m.group(1))),
    ))

    # 1e. Date variants with slashes/dots must precede generic fractions.
    p.append((
        re.compile(r"(\d{4})[/.](\d{1,2})[/.](\d{1,2})"),
        lambda m: (
            _year_to_ja(m.group(1)) + "年"
            + _int_to_ja(int(m.group(2))) + "月"
            + _int_to_ja(int(m.group(3))) + "日"
        ),
    ))
    p.append((
        re.compile(r"\b(0?[1-9]|1[0-2])/([0-2]?\d|3[01])/(\d{4})\b"),
        lambda m: (
            _year_to_ja(m.group(3)) + "年"
            + _int_to_ja(int(m.group(1))) + "月"
            + _int_to_ja(int(m.group(2))) + "日"
        ),
    ))
    p.append((
        re.compile(r"\b(1[3-9]|2\d|3[01])/([0]?[1-9]|1[0-2])/(\d{4})\b"),
        lambda m: (
            _year_to_ja(m.group(3)) + "年"
            + _int_to_ja(int(m.group(2))) + "月"
            + _int_to_ja(int(m.group(1))) + "日"
        ),
    ))
    p.append((
        re.compile(r"(?<![A-Za-z0-9])([12])H(\d{2})(?![A-Za-z0-9])"),
        lambda m: "二〇" + _digits_to_ja(m.group(2)) + "年" + ("上半期" if m.group(1) == "1" else "下半期"),
    ))
    p.append((
        re.compile(r"(?<![A-Za-z0-9])([1-4])Q(\d{2})(?![A-Za-z0-9])"),
        lambda m: "二〇" + _digits_to_ja(m.group(2)) + "年第" + _int_to_ja(int(m.group(1))) + "四半期",
    ))

    p.append((re.compile(r"(?<!\d)24/7(?!\d)"), lambda m: "二十四時間年中無休"))

    # 1f. Fractions (1/2 → 二分の一)
    p.append((
        re.compile(r"\b(\d+)/(\d+)\b"),
        lambda m: _int_to_ja(int(m.group(2))) + "分の" + _int_to_ja(int(m.group(1))),
    ))

    # 2. Date: YYYY-MM-DD or YYYY/MM/DD
    p.append((
        re.compile(r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})"),
        lambda m: (
            _year_to_ja(m.group(1)) + "年"
            + _int_to_ja(int(m.group(2))) + "月"
            + _int_to_ja(int(m.group(3))) + "日"
        ),
    ))

    # 2b. Year ranges before standalone YYYY年.
    p.append((
        re.compile(r"(\d{4})\s*(?:-|から|~|〜)\s*(\d{4})年"),
        lambda m: _year_to_ja(m.group(1)) + "から" + _year_to_ja(m.group(2)) + "年",
    ))

    # 3. Year: YYYY年 → digit-by-digit
    p.append((
        re.compile(r"(\d{4})年"),
        lambda m: _year_to_ja(m.group(1)) + "年",
    ))

    # 4. Time: HH:MM:SS
    p.append((
        re.compile(r"(\d{1,2}):(\d{2}):(\d{2})(?!\d)"),
        lambda m: (
            _int_to_ja(int(m.group(1))) + "時"
            + _int_to_ja(int(m.group(2))) + "分"
            + _int_to_ja(int(m.group(3))) + "秒"
        ),
    ))

    # 5. Time: HH:MM
    # Omit 分 when minutes == 0, EXCEPT at 0:00 (midnight) where explicit 零時零分 is clearer
    p.append((
        re.compile(r"(\d{1,2}):(\d{2})(?!\d)"),
        lambda m: (
            _int_to_ja(int(m.group(1))) + "時"
            + ("" if int(m.group(2)) == 0 and int(m.group(1)) != 0
               else _int_to_ja(int(m.group(2))) + "分")
        ),
    ))

    # 5b. Ratio N:M → N対M (after time patterns to avoid conflict)
    p.append((
        re.compile(r"(\d+):(\d+)"),
        lambda m: _int_to_ja(int(m.group(1))) + "対" + _int_to_ja(int(m.group(2))),
    ))

    # 6. Slash rates / compound units: Nkm/hour, N mg/dL, N MB/s, etc.
    p.append((
        re.compile(
            rf"(\d+(?:\.\d+)?)\s*({_RATE_UNIT_RE_JA})\s*/\s*"
            rf"((?:\d+(?:\.\d+)?\s*)?(?:{_RATE_DEN_RE_JA})(?:\^?[23]|[²³])?"
            rf"(?:\s*/\s*(?:\d+(?:\.\d+)?\s*)?(?:{_RATE_DEN_RE_JA})(?:\^?[23]|[²³])?)*)"
        ),
        lambda m: _slash_rate_ja(m.group(1), m.group(2), m.group(3)),
    ))

    _implied_rate_ja = {
        "mph": ("時間", "マイル"), "kph": ("時間", "キロメートル"), "rpm": ("分", "回転"),
        "bpm": ("分", "拍"), "fps": ("秒", "フレーム"), "dpi": ("インチ", "ドット"),
        "ppm": ("百万", "部"), "kbps": ("秒", "キロビット"), "Kbps": ("秒", "キロビット"),
        "Mbps": ("秒", "メガビット"), "Gbps": ("秒", "ギガビット"), "Tbps": ("秒", "テラビット"),
    }
    implied_rate_re_ja = "|".join(re.escape(u) for u in sorted(_implied_rate_ja, key=len, reverse=True))
    p.append((
        re.compile(rf"(\d+(?:\.\d+)?)\s?({implied_rate_re_ja})\b"),
        lambda m, irm=_implied_rate_ja: "一" + irm[m.group(2)][0] + "あたり" + _rate_number_to_ja(m.group(1)) + irm[m.group(2)][1],
    ))

    # Percentage range must precede standalone percentage.
    p.append((
        re.compile(r"(\d+(?:\.\d+)?)%\s*(?:-|から|~|〜)\s*(\d+(?:\.\d+)?)%"),
        lambda m: _range_number_ja(m.group(1)) + "から" + _range_number_ja(m.group(2)) + "パーセント",
    ))

    # 7. Percentage
    p.append((
        re.compile(r"(\d+(?:\.\d+)?)%"),
        lambda m: (
            _decimal_to_ja(m.group(1)) if "." in m.group(1) else _int_to_ja(int(m.group(1)))
        ) + "パーセント",
    ))

    # 7a. Ranges that should precede hyphenated IDs and plain numbers.
    p.append((
        re.compile(r"([月火水木金土日])曜?日?\s*(?:-|から|~|〜)\s*([月火水木金土日])曜?日?"),
        lambda m: _WEEKDAY_JA[m.group(1)] + "から" + _WEEKDAY_JA[m.group(2)],
    ))
    p.append((
        re.compile(r"(?<![A-Za-z0-9])(\d+(?:\.\d+)?)\s*(?:-|から|~|〜)\s*(\d+(?:\.\d+)?)(?=[一-龯ぁ-んァ-ン])"),
        lambda m: _range_number_ja(m.group(1)) + "から" + _range_number_ja(m.group(2)),
    ))
    p.append((
        re.compile(r"~\s*(\d+(?:\.\d+)?)"),
        lambda m: "約" + _range_number_ja(m.group(1)),
    ))

    # 7b. Currency per unit before plain currency amounts.
    _currency_unit_ja = {"$": "ドル", "€": "ユーロ", "£": "ポンド", "¥": "円", "￥": "円"}
    p.append((
        re.compile(rf"([$€£¥￥])(\d+(?:\.\d+)?)\s*/\s*((?:{_RATE_DEN_RE_JA}))"),
        lambda m, cm=_currency_unit_ja: _rate_den_part_ja(m.group(3)) + "あたり" + _rate_number_to_ja(m.group(2)) + cm[m.group(1)],
    ))

    # 7b. Negative currency: -¥N → マイナスN円
    p.append((
        re.compile(r"-[¥￥](\d+(?:\.\d+)?)"),
        lambda m: "マイナス" + (
            _decimal_to_ja(m.group(1)) if "." in m.group(1) else _int_to_ja(int(m.group(1)))
        ) + "円",
    ))

    # 8. Currency: ¥/￥ → 円
    p.append((
        re.compile(r"[¥￥](\d+(?:\.\d+)?)"),
        lambda m: (
            _decimal_to_ja(m.group(1)) if "." in m.group(1) else _int_to_ja(int(m.group(1)))
        ) + "円",
    ))

    # 9. USD $
    p.append((
        re.compile(r"\$(\d+(?:\.\d+)?)"),
        lambda m: (
            _decimal_to_ja(m.group(1)) if "." in m.group(1) else _int_to_ja(int(m.group(1)))
        ) + "ドル",
    ))

    # 10. Euro €
    p.append((
        re.compile(r"€(\d+(?:\.\d+)?)"),
        lambda m: (
            _decimal_to_ja(m.group(1)) if "." in m.group(1) else _int_to_ja(int(m.group(1)))
        ) + "ユーロ",
    ))

    # 11. GBP £
    p.append((
        re.compile(r"£(\d+(?:\.\d+)?)"),
        lambda m: (
            _decimal_to_ja(m.group(1)) if "." in m.group(1) else _int_to_ja(int(m.group(1)))
        ) + "ポンド",
    ))

    # 12. Temperature: -5°C / 37°F
    p.append((
        re.compile(r"(-?\d+(?:\.\d+)?)[°℃]C?"),
        lambda m: (
            ("マイナス" if m.group(1).startswith("-") else "")
            + (_decimal_to_ja(m.group(1).lstrip("-")) if "." in m.group(1)
               else _int_to_ja(abs(int(m.group(1)))))
            + "度"
        ),
    ))

    # 13. Units
    _unit_map_ja = {
        "kg": "キログラム", "g": "グラム", "mg": "ミリグラム",
        "km": "キロメートル", "m": "メートル", "cm": "センチメートル", "mm": "ミリメートル",
        "L": "リットル", "ml": "ミリリットル", "mL": "ミリリットル",
        "GHz": "ギガヘルツ", "MHz": "メガヘルツ", "kHz": "キロヘルツ", "Hz": "ヘルツ",
        "kW": "キロワット", "W": "ワット",
    }
    unit_re_ja = "|".join(re.escape(u) for u in sorted(_unit_map_ja, key=len, reverse=True))

    # Negative units: -Nunit → マイナスNunit (must precede positive unit pattern)
    p.append((
        re.compile(rf"-(\d+(?:\.\d+)?)({unit_re_ja})\b"),
        lambda m, um=_unit_map_ja: "マイナス" + (
            _decimal_to_ja(m.group(1)) if "." in m.group(1) else _int_to_ja(int(m.group(1)))
        ) + um[m.group(2)],
    ))

    p.append((
        re.compile(rf"(\d+(?:\.\d+)?)({unit_re_ja})\b"),
        lambda m, um=_unit_map_ja: (
            (_decimal_to_ja(m.group(1)) if "." in m.group(1) else _int_to_ja(int(m.group(1))))
            + um[m.group(2)]
        ),
    ))

    # 14. Japanese phone: 0X-XXXX-XXXX or 0X0-XXXX-XXXX
    p.append((
        re.compile(r"\b(0\d{1,4})-(\d{2,4})-(\d{4})\b"),
        lambda m: "".join(_DIGITS_JA[int(c)] for c in m.group(1) + m.group(2) + m.group(3)),
    ))

    # 14b. Minus / hyphen: only spaced non-whitespace expressions read the hyphen.
    p.append((re.compile(r"(?<=\S)\s+-\s+(?=\S)"), lambda m: "マイナス"))

    # 14c. No-space hyphenated tokens: hyphen is silent; digits are read as IDs.
    p.append((
        re.compile(r"(?<!-)([^\s-]+(?:-[^\s-]+)+)"),
        lambda m: _silent_hyphen_token_to_ja(m.group(1)),
    ))

    # 15. Decimal
    p.append((
        re.compile(r"-?\d+\.\d+"),
        lambda m: ("マイナス" if m.group(0).startswith("-") else "")
                  + _decimal_to_ja(m.group(0).lstrip("-")),
    ))

    # 16. Plain integer
    p.append((
        re.compile(r"-?\d+"),
        lambda m: ("マイナス" if m.group(0).startswith("-") else "")
                  + _int_to_ja(abs(int(m.group(0)))),
    ))

    # 17. Symbol map
    _sym_map_ja = {
        "+": "プラス", "×": "かける", "÷": "わる", "=": "イコール",
        "≈": "ほぼ等しい", "≠": "等しくない", "≤": "以下", "≥": "以上",
        "<": "より小さい", ">": "より大きい",
        "&": "アンド", "@": "アット", "#": "シャープ",
        "~": "から",
        "〜": "から",
        "·": "", "•": "",
    }
    sym_re_ja = "[" + re.escape("".join(_sym_map_ja.keys())) + "]"
    p.append((
        re.compile(sym_re_ja),
        lambda m, sm=_sym_map_ja: sm.get(m.group(0), m.group(0)),
    ))

    return p


_PATTERNS = _build_patterns()

_ENTITY_RE_JA = re.compile(
    r"https?://\S+"
    r"|`[^`]*`"
    r"|(?<![a-zA-Z\d])(?:[A-Z]{2,}-?\d+(?:\.\d+)*[a-zA-Z]?|[A-Z]-?\d{2,}(?:\.\d+)*[a-zA-Z]?)(?![A-Z\d])"
)
_SLOT_BASE_JA = 0xE000


def _make_slot_ja(i: int) -> str:
    return "\x00J" + chr(_SLOT_BASE_JA + i) + "\x00"


_SLOT_RE_JA = re.compile(r"\x00J([\uE000-\uF8FF])\x00")
_CLEANUP_DECIMAL_JA = re.compile(r"\d+\.\d+")
_CLEANUP_INT_JA = re.compile(r"\d+")


class JaNormalizer(BaseNormalizer):
    def normalize(self, text: str) -> str:
        return self._apply_patterns(text)

    def normalize_token(self, token: str) -> str:
        return self._apply_patterns(token)

    def _apply_patterns(self, text: str) -> str:
        slots: list[str] = []

        def _protect(m: re.Match) -> str:
            slots.append(m.group(0))
            return _make_slot_ja(len(slots) - 1)

        text = _ENTITY_RE_JA.sub(_protect, text)

        for pattern, handler in _PATTERNS:
            text = pattern.sub(handler, text)

        def _restore(m: re.Match) -> str:
            value = slots[ord(m.group(1)) - _SLOT_BASE_JA]
            if value.startswith(("http://", "https://", "`")):
                return value
            if re.search(r"\S-\S", value):
                return _silent_hyphen_token_to_ja(value)
            return value

        text = _SLOT_RE_JA.sub(_restore, text)

        text = _CLEANUP_DECIMAL_JA.sub(lambda m: _decimal_to_ja(m.group(0)), text)
        text = _CLEANUP_INT_JA.sub(lambda m: _int_to_ja(int(m.group(0))), text)

        return text
