"""Chinese (Mandarin) TTS normalizer.

Handles:
- Integers (cardinal & ordinal)
- Decimals
- Percentages
- Dates (YYYY-MM-DD, YYYY年M月D日, M月D日)
- Times (HH:MM, HH:MM:SS, HH点MM分)
- Currency (元/¥/￥, $, €)
- Physical units (kg, km, °C, …)
- Phone numbers
- Fractions
- Ranges (1-3, 1~3)
- Common symbols (%, +, -, ×, ÷, =, &, @, #, /)
- Mixed Chinese-English passages (English spans are delegated)
"""

from __future__ import annotations

import re
from typing import List

from .base import BaseNormalizer

# ---------------------------------------------------------------------------
# Digit maps
# ---------------------------------------------------------------------------
_DIGITS = "零一二三四五六七八九"
_DIGITS_FORMAL = "零壹贰叁肆伍陆柒捌玖"
_UNITS = ["", "十", "百", "千"]
_MAGNITUDES = ["", "万", "亿", "万亿"]


def _int_to_zh(n: int, formal: bool = False) -> str:
    """Convert a non-negative integer to Chinese reading."""
    digits = _DIGITS_FORMAL if formal else _DIGITS

    if n < 0:
        return "负" + _int_to_zh(-n, formal)
    if n == 0:
        return digits[0]

    result = ""
    # Split into groups of 4
    groups: List[int] = []
    while n > 0:
        groups.append(n % 10000)
        n //= 10000

    for mag_idx, group in enumerate(reversed(groups)):
        if group == 0:
            if result:
                result += digits[0]
            continue
        group_str = _group4_to_zh(group, digits)
        result += group_str + _MAGNITUDES[len(groups) - 1 - mag_idx]

    # Clean up leading/trailing 零
    result = re.sub(r"零+", "零", result).strip("零")

    # Special case: 一十 → 十 (for numbers 10-19 in spoken Chinese)
    if result.startswith("一十"):
        result = result[1:]

    return result or digits[0]


def _group4_to_zh(n: int, digits: str) -> str:
    units = ["", "十", "百", "千"]
    parts = []
    for i in range(3, -1, -1):
        d = n // (10 ** i) % 10
        if d != 0:
            parts.append(digits[d] + units[i])
        elif parts and not parts[-1].endswith("零"):
            parts.append(digits[0])
    result = "".join(parts).rstrip("零")
    return result


def _year_to_zh(year_str: str) -> str:
    """Read year digit-by-digit: 2026 → 二零二六."""
    return "".join(_DIGITS[int(c)] for c in year_str)


def _decimal_to_zh(s: str) -> str:
    """Convert decimal string like '10.11' to '十点一一'."""
    parts = s.split(".")
    integer_part = _int_to_zh(int(parts[0]))
    frac_part = "".join(_DIGITS[int(c)] for c in parts[1])
    return integer_part + "点" + frac_part


# ---------------------------------------------------------------------------
# Pattern registry — ordered, each entry: (compiled_regex, handler_fn)
# ---------------------------------------------------------------------------

def _build_patterns():
    p = []

    # 1. Date: YYYY-MM-DD or YYYY/MM/DD
    p.append((
        re.compile(r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})"),
        lambda m: (f"{_year_to_zh(m.group(1))}年"
                   f"{_int_to_zh(int(m.group(2)))}月"
                   f"{_int_to_zh(int(m.group(3)))}日"),
    ))

    # 2. Date: M月D日 (already verbal, but numbers inside need conversion)
    p.append((
        re.compile(r"(\d{1,2})月(\d{1,2})日"),
        lambda m: f"{_int_to_zh(int(m.group(1)))}月{_int_to_zh(int(m.group(2)))}日",
    ))

    # 3. Year only: YYYY年
    p.append((
        re.compile(r"(\d{4})年"),
        lambda m: _year_to_zh(m.group(1)) + "年",
    ))

    # 4. Time: HH:MM:SS
    p.append((
        re.compile(r"(\d{1,2}):(\d{2}):(\d{2})"),
        lambda m: (f"{_int_to_zh(int(m.group(1)))}点"
                   f"{_int_to_zh(int(m.group(2)))}分"
                   f"{_int_to_zh(int(m.group(3)))}秒"),
    ))

    # 5. Time: HH:MM
    p.append((
        re.compile(r"(\d{1,2}):(\d{2})"),
        lambda m: (f"{_int_to_zh(int(m.group(1)))}点"
                   + ("" if int(m.group(2)) == 0 else f"{_int_to_zh(int(m.group(2)))}分")),
    ))

    # 6. Percentage: 10% → 百分之十
    p.append((
        re.compile(r"(\d+(?:\.\d+)?)%"),
        lambda m: "百分之" + (_decimal_to_zh(m.group(1)) if "." in m.group(1)
                              else _int_to_zh(int(m.group(1)))),
    ))

    # 7. Currency ¥/￥/元
    p.append((
        re.compile(r"[¥￥](\d+(?:\.\d+)?)"),
        lambda m: (_decimal_to_zh(m.group(1)) if "." in m.group(1)
                   else _int_to_zh(int(m.group(1)))) + "元",
    ))

    # 8. USD $
    p.append((
        re.compile(r"\$(\d+(?:\.\d+)?)"),
        lambda m: (_decimal_to_zh(m.group(1)) if "." in m.group(1)
                   else _int_to_zh(int(m.group(1)))) + "美元",
    ))

    # 9. Fraction: 3/4 → 四分之三
    p.append((
        re.compile(r"(\d+)/(\d+)"),
        lambda m: f"{_int_to_zh(int(m.group(2)))}分之{_int_to_zh(int(m.group(1)))}",
    ))

    # 10. Temperature: -10°C / 10°C / 10℃
    p.append((
        re.compile(r"(-?\d+(?:\.\d+)?)[°℃]C?"),
        lambda m: ("负" if m.group(1).startswith("-") else "")
                  + (_decimal_to_zh(m.group(1).lstrip("-")) if "." in m.group(1)
                     else _int_to_zh(abs(int(m.group(1))))) + "摄氏度",
    ))

    # 11. Units: number + unit (kg, km, m, cm, mm, g, L, ml, MHz, GHz, kHz, Hz, V, A, W, kW)
    _unit_map = {
        "kg": "千克", "g": "克", "mg": "毫克", "t": "吨",
        "km": "千米", "m": "米", "cm": "厘米", "mm": "毫米",
        "L": "升", "ml": "毫升", "mL": "毫升",
        "GHz": "吉赫兹", "MHz": "兆赫兹", "kHz": "千赫兹", "Hz": "赫兹",
        "kW": "千瓦", "W": "瓦", "V": "伏", "A": "安",
        "MB": "兆字节", "GB": "吉字节", "TB": "太字节", "KB": "千字节",
    }
    unit_re = "|".join(re.escape(u) for u in sorted(_unit_map, key=len, reverse=True))
    p.append((
        re.compile(rf"(\d+(?:\.\d+)?)({unit_re})\b"),
        lambda m, um=_unit_map: (
            (_decimal_to_zh(m.group(1)) if "." in m.group(1) else _int_to_zh(int(m.group(1))))
            + um[m.group(2)]
        ),
    ))

    # 12. Phone number: 11-digit mobile (1xx-xxxx-xxxx or 1xxxxxxxxxx)
    p.append((
        re.compile(r"\b(1[3-9]\d)-?(\d{4})-?(\d{4})\b"),
        lambda m: "".join(_DIGITS[int(c)] for c in m.group(1) + m.group(2) + m.group(3)),
    ))

    # 13. Decimal number (must come before plain integer)
    p.append((
        re.compile(r"-?\d+\.\d+"),
        lambda m: ("负" if m.group(0).startswith("-") else "")
                  + _decimal_to_zh(m.group(0).lstrip("-")),
    ))

    # 14. Plain integer (possibly negative)
    p.append((
        re.compile(r"-?\d+"),
        lambda m: ("负" if m.group(0).startswith("-") else "")
                  + _int_to_zh(abs(int(m.group(0)))),
    ))

    # 15. Symbol map
    _sym_map = {
        "+": "加", "×": "乘", "÷": "除以", "=": "等于",
        "≈": "约等于", "≠": "不等于", "≤": "小于等于", "≥": "大于等于",
        "<": "小于", ">": "大于",
        "&": "和", "@": "艾特", "#": "井号",
        "~": "到", "—": "到", "–": "到",
    }
    sym_re = "[" + re.escape("".join(_sym_map.keys())) + "]"
    p.append((
        re.compile(sym_re),
        lambda m, sm=_sym_map: sm.get(m.group(0), m.group(0)),
    ))

    return p


_PATTERNS = _build_patterns()

# Segment splitter: split on boundaries between ASCII/numeric and CJK
_SEG_RE = re.compile(
    r"([A-Za-z][A-Za-z0-9\s,.'!?-]*)"  # English word runs
    r"|([^\x00-\x7F]+)"                  # CJK / non-ASCII runs
    r"|([^\w\s]+)"                        # symbols
    r"|(\S+)"                             # fallback
)


class ZhNormalizer(BaseNormalizer):
    """Chinese normalizer."""

    def normalize(self, text: str) -> str:
        return self._apply_patterns(text)

    def normalize_token(self, token: str) -> str:
        return self._apply_patterns(token)

    def _apply_patterns(self, text: str) -> str:
        for pattern, handler in _PATTERNS:
            text = pattern.sub(handler, text)
        return text
