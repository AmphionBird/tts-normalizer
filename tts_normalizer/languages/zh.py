"""Chinese (Mandarin) TTS normalizer.

Handles:
- Integers (cardinal & ordinal), with 两 for 2 before 百/千/万/亿
- Decimals (digit-by-digit after decimal point)
- Percentages (100% → 百分之百)
- Dates (YYYY-MM-DD, YYYY年M月D日, M月D日, N.M号)
- Times (HH:MM, HH:MM:SS, leading-zero minutes → 零X分)
- Currency (元/¥/￥ with 角/分; $)
- Physical units (kg, km, km/h, °C, …)
- Version numbers (1.0.0 → 一点零点零)
- Phone numbers (mobile 11-digit; landline 0xx-xxxxxxxx)
- Fractions
- Ordinals (第N, No.N)
- Subtraction (digit-minus-digit → 减)
- Common symbols (%, +, -, ×, ÷, =, &, @, #, /)
- Mixed Chinese-English passages
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
_MAGNITUDES = ["", "万", "亿", "万亿"]


def _int_to_zh(n: int, formal: bool = False) -> str:
    """Convert a non-negative integer to Chinese reading."""
    digits = _DIGITS_FORMAL if formal else _DIGITS

    if n < 0:
        return "负" + _int_to_zh(-n, formal)
    if n == 0:
        return digits[0]

    result = ""
    groups: List[int] = []
    tmp = n
    while tmp > 0:
        groups.append(tmp % 10000)
        tmp //= 10000

    for mag_idx, group in enumerate(reversed(groups)):
        if group == 0:
            if result:
                result += digits[0]
            continue
        group_str = _group4_to_zh(group, digits)
        result += group_str + _MAGNITUDES[len(groups) - 1 - mag_idx]

    # Clean up repeated/trailing 零
    result = re.sub(r"零+", "零", result).strip("零")

    # 一十 → 十 for 10-19 in spoken Chinese
    if result.startswith("一十"):
        result = result[1:]

    # 二 → 两 before 百/千/万/亿 (spoken Chinese convention)
    result = re.sub(r"二(百|千|万|亿)", r"两\1", result)

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
    return "".join(parts).rstrip("零")


def _year_to_zh(year_str: str) -> str:
    """Read year digit-by-digit: 2026 → 二零二六."""
    return "".join(_DIGITS[int(c)] for c in year_str)


def _decimal_to_zh(s: str) -> str:
    """Convert decimal string like '10.11' to '十点一一' (digit-by-digit after point)."""
    parts = s.split(".")
    integer_part = _int_to_zh(int(parts[0]))
    frac_part = "".join(_DIGITS[int(c)] for c in parts[1])
    return integer_part + "点" + frac_part


def _cny_to_zh(int_str: str, dec_str: str) -> str:
    """Convert CNY amount to spoken form with 元/角/分.

    int_str: integer part string (may be "0")
    dec_str: decimal part string (1-2 chars, e.g. "5" or "50")
    """
    # Pad/truncate decimal to 2 digits
    dec_str = (dec_str + "0")[:2]
    jiao = int(dec_str[0])
    fen = int(dec_str[1])

    yuan_val = int(int_str)
    result = ""
    if yuan_val > 0:
        result += _int_to_zh(yuan_val) + "元"
    if jiao > 0:
        result += _DIGITS[jiao] + "角"
        if fen > 0:
            result += _DIGITS[fen] + "分"
    elif fen > 0:
        result += "零" + _DIGITS[fen] + "分"
    # If both zero (e.g. ¥100.00), result already has 元
    if not result:
        result = "零元"
    return result


# ---------------------------------------------------------------------------
# Pattern registry — ordered, each entry: (compiled_regex, handler_fn)
# ---------------------------------------------------------------------------

def _build_patterns():
    p = []

    # 0a. Version numbers: 1.0.0 / 2.11.3 (3+ dot-separated components)
    #     Must come before decimal pattern.
    p.append((
        re.compile(r"\d+(?:\.\d+){2,}"),
        lambda m: "点".join(_int_to_zh(int(part)) for part in m.group(0).split(".")),
    ))

    # 0b. N.M号 → N月M号  (e.g. 10.11号 → 十月十一号)
    p.append((
        re.compile(r"(\d{1,2})\.(\d{1,2})号"),
        lambda m: f"{_int_to_zh(int(m.group(1)))}月{_int_to_zh(int(m.group(2)))}号",
    ))

    # 0c. No.N / no.N → 第N
    p.append((
        re.compile(r"[Nn][Oo]\.(\d+)"),
        lambda m: "第" + _int_to_zh(int(m.group(1))),
    ))

    # 0d. 第N (ordinal prefix already present)
    p.append((
        re.compile(r"第(\d+)"),
        lambda m: "第" + _int_to_zh(int(m.group(1))),
    ))

    # 1. Date: YYYY-MM-DD or YYYY/MM/DD
    #    Leading-zero month → prefix 零 (e.g. 04 → 零四月)
    p.append((
        re.compile(r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})"),
        lambda m: (
            _year_to_zh(m.group(1)) + "年"
            + ("零" if m.group(2).startswith("0") else "")
            + _int_to_zh(int(m.group(2))) + "月"
            + ("零" if m.group(3).startswith("0") else "")
            + _int_to_zh(int(m.group(3))) + "日"
        ),
    ))

    # 2. Date: M月D日
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
        lambda m: (
            _int_to_zh(int(m.group(1))) + "点"
            + ("零" if m.group(2).startswith("0") and int(m.group(2)) != 0 else "")
            + _int_to_zh(int(m.group(2))) + "分"
            + ("零" if m.group(3).startswith("0") and int(m.group(3)) != 0 else "")
            + _int_to_zh(int(m.group(3))) + "秒"
        ),
    ))

    # 5. Time: HH:MM  (leading-zero minutes → 零X分)
    p.append((
        re.compile(r"(\d{1,2}):(\d{2})"),
        lambda m: (
            _int_to_zh(int(m.group(1))) + "点"
            + (
                "" if int(m.group(2)) == 0
                else ("零" if m.group(2).startswith("0") else "")
                     + _int_to_zh(int(m.group(2))) + "分"
            )
        ),
    ))

    # 6. Speed unit: Nkm/h → 每小时N千米
    p.append((
        re.compile(r"(\d+(?:\.\d+)?)km/h"),
        lambda m: "每小时" + (
            _decimal_to_zh(m.group(1)) if "." in m.group(1) else _int_to_zh(int(m.group(1)))
        ) + "千米",
    ))

    # 7. 100% special case → 百分之百
    p.append((
        re.compile(r"100%"),
        lambda m: "百分之百",
    ))

    # 8. Percentage: N% → 百分之N
    p.append((
        re.compile(r"(\d+(?:\.\d+)?)%"),
        lambda m: "百分之" + (
            _decimal_to_zh(m.group(1)) if "." in m.group(1) else _int_to_zh(int(m.group(1)))
        ),
    ))

    # 9. CNY with decimal: ¥N.D → 元/角/分
    p.append((
        re.compile(r"[¥￥](\d+)\.(\d{1,2})"),
        lambda m: _cny_to_zh(m.group(1), m.group(2)),
    ))

    # 10. CNY integer: ¥N → N元
    p.append((
        re.compile(r"[¥￥](\d+)"),
        lambda m: _int_to_zh(int(m.group(1))) + "元",
    ))

    # 11. USD $
    p.append((
        re.compile(r"\$(\d+(?:\.\d+)?)"),
        lambda m: (
            _decimal_to_zh(m.group(1)) if "." in m.group(1) else _int_to_zh(int(m.group(1)))
        ) + "美元",
    ))

    # 12. Fraction: 3/4 → 四分之三
    p.append((
        re.compile(r"(\d+)/(\d+)"),
        lambda m: f"{_int_to_zh(int(m.group(2)))}分之{_int_to_zh(int(m.group(1)))}",
    ))

    # 13. Temperature: -10°C / 10°C / 10℃
    p.append((
        re.compile(r"(-?\d+(?:\.\d+)?)[°℃]C?"),
        lambda m: (
            ("负" if m.group(1).startswith("-") else "")
            + (_decimal_to_zh(m.group(1).lstrip("-")) if "." in m.group(1)
               else _int_to_zh(abs(int(m.group(1)))))
            + "摄氏度"
        ),
    ))

    # 14. Units: number + ASCII unit
    _unit_map = {
        "kg": "千克", "g": "克", "mg": "毫克",
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

    # 15. Landline phone: 0xx(x)-xxxxxxx(x)
    p.append((
        re.compile(r"\b(0\d{2,3})-(\d{7,8})\b"),
        lambda m: "".join(_DIGITS[int(c)] for c in m.group(1) + m.group(2)),
    ))

    # 16. Mobile phone: 11-digit 1xx-xxxx-xxxx
    p.append((
        re.compile(r"\b(1[3-9]\d)-?(\d{4})-?(\d{4})\b"),
        lambda m: "".join(_DIGITS[int(c)] for c in m.group(1) + m.group(2) + m.group(3)),
    ))

    # 17. Subtraction: digit-minus-digit (e.g. 10-3) → 减
    #     Lookbehind/lookahead so it doesn't match negative numbers at expression start.
    p.append((
        re.compile(r"(?<=\d)-(?=\d)"),
        lambda m: "减",
    ))

    # 18. Decimal number (must come before plain integer)
    p.append((
        re.compile(r"-?\d+\.\d+"),
        lambda m: ("负" if m.group(0).startswith("-") else "")
                  + _decimal_to_zh(m.group(0).lstrip("-")),
    ))

    # 19. Plain integer (possibly negative)
    p.append((
        re.compile(r"-?\d+"),
        lambda m: ("负" if m.group(0).startswith("-") else "")
                  + _int_to_zh(abs(int(m.group(0)))),
    ))

    # 20. Symbol map
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
