"""Chinese (Mandarin) TTS normalizer.

Handles:
- Integers (cardinal & ordinal), with 两 for 2 as direct multiplier of 百/千/万/亿
- Decimals (digit-by-digit after decimal point)
- Scientific notation (1.5×10^6, 2.5e-3)
- Percentages (100% → 百分之百)
- Dates (YYYY-MM-DD, YYYY年M月D日, M月D日, N.M号)
- Times (HH:MM, HH:MM:SS; leading-zero minutes → 零X分)
- Currency (元/¥/￥ with 角/分; $; €; £; ₩; comma-separated amounts)
- Physical units (kg, km, km/h, °C, …)
- Version numbers (1.0.0 → 一点零点零)
- IP addresses
- Phone numbers (mobile; landline)
- Code/serial contexts (邮编, 房间号, 末四位, …)
- Roman numerals (Ⅰ-Ⅻ → 一-十二)
- Fractions
- Ordinals (第N, No.N)
- Ratios/scores
- Ranges
- Subtraction
- 2 before measure words → 两
- Common symbols
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
    """Convert a non-negative integer to Chinese spoken form."""
    digits = _DIGITS_FORMAL if formal else _DIGITS

    if n < 0:
        return "负" + _int_to_zh(-n, formal)
    if n == 0:
        return digits[0]

    groups: List[int] = []
    tmp = n
    while tmp > 0:
        groups.append(tmp % 10000)
        tmp //= 10000

    result = ""
    for mag_idx, group in enumerate(reversed(groups)):
        if group == 0:
            if result:
                result += digits[0]
            continue
        group_str = _group4_to_zh(group, digits)
        result += group_str + _MAGNITUDES[len(groups) - 1 - mag_idx]

    result = re.sub(r"零+", "零", result).strip("零")

    # 一十 → 十 for 10-19
    if result.startswith("一十"):
        result = result[1:]

    # 二 → 两 only when directly multiplying 百/千/万/亿 (not when preceded by 十, i.e. ones digit)
    result = re.sub(r"(?<!十)二(百|千|万|亿)", r"两\1", result)

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
    return "".join(_DIGITS[int(c)] for c in year_str)


def _decimal_to_zh(s: str) -> str:
    """Decimal → spoken (digit-by-digit after point)."""
    parts = s.split(".")
    integer_part = _int_to_zh(int(parts[0]))
    frac_part = "".join(_DIGITS[int(c)] for c in parts[1])
    return integer_part + "点" + frac_part


def _cny_to_zh(int_str: str, dec_str: str) -> str:
    """CNY amount → 元/角/分 spoken form."""
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
        if result:          # yuan already present → add 零 before fen
            result += "零"
        result += _DIGITS[fen] + "分"
    return result or "零元"


def _sci_to_zh(base_str: str, exp_str: str, neg_exp: bool = False) -> str:
    """Convert scientific notation to Chinese spoken form."""
    e = int(exp_str)
    if neg_exp:
        denom = _int_to_zh(10 ** e)
        # Strip leading 一 for clean "千分之/万分之" etc.
        if len(denom) > 1 and denom[0] == "一":
            denom = denom[1:]
        num = _decimal_to_zh(base_str) if "." in base_str else _int_to_zh(int(base_str))
        return denom + "分之" + num
    else:
        val = round(float(base_str) * (10 ** e))
        return _int_to_zh(val)


# ---------------------------------------------------------------------------
# Pattern registry
# ---------------------------------------------------------------------------

def _build_patterns():
    p = []

    # PRE-0. Thousands-separator comma removal (12,345 → 12345)
    p.append((re.compile(r"(?<=\d),(?=\d{3})"), lambda m: ""))

    # 0a. IP address (before version-number pattern)
    p.append((
        re.compile(r"\b(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})\b"),
        lambda m: "点".join(
            "".join(_DIGITS[int(c)] for c in part)
            for part in [m.group(1), m.group(2), m.group(3), m.group(4)]
        ),
    ))

    # 0a1. Roman numerals (Unicode Ⅰ–Ⅻ) → Chinese
    _roman_zh = {
        "Ⅰ": "一", "Ⅱ": "二", "Ⅲ": "三", "Ⅳ": "四",
        "Ⅴ": "五", "Ⅵ": "六", "Ⅶ": "七", "Ⅷ": "八",
        "Ⅸ": "九", "Ⅹ": "十", "Ⅺ": "十一", "Ⅻ": "十二",
    }
    p.append((
        re.compile("[" + "".join(_roman_zh.keys()) + "]"),
        lambda m, rm=_roman_zh: rm.get(m.group(0), m.group(0)),
    ))

    # 0a2–5. Scientific notation (must precede symbol map and integer patterns)
    # N×10^-E  (negative exponent first to avoid partial match)
    p.append((
        re.compile(r"(\d+(?:\.\d+)?)[×x\*]10\^-(\d+)"),
        lambda m: _sci_to_zh(m.group(1), m.group(2), neg_exp=True),
    ))
    # N×10^E
    p.append((
        re.compile(r"(\d+(?:\.\d+)?)[×x\*]10\^(\d+)"),
        lambda m: _sci_to_zh(m.group(1), m.group(2)),
    ))
    # Ne-E
    p.append((
        re.compile(r"(\d+(?:\.\d+)?)[eE]-(\d+)"),
        lambda m: _sci_to_zh(m.group(1), m.group(2), neg_exp=True),
    ))
    # NeE
    p.append((
        re.compile(r"(\d+(?:\.\d+)?)[eE]\+?(\d+)"),
        lambda m: _sci_to_zh(m.group(1), m.group(2)),
    ))

    # 0b. Code / serial-number context words → digit-by-digit
    for ctx in ["邮编", "邮政编码", "房间号", "门牌号",
                "末四位", "末六位", "末八位", "末三位", "学号", "工号"]:
        p.append((
            re.compile(rf"{ctx}(\d+)"),
            lambda m, c=ctx: c + "".join(_DIGITS[int(d)] for d in m.group(1)),
        ))

    # 0c. Version numbers: N.N.N… (3+ components) → 一点零点零
    p.append((
        re.compile(r"\d+(?:\.\d+){2,}"),
        lambda m: "点".join(_int_to_zh(int(part)) for part in m.group(0).split(".")),
    ))

    # 0d. N.M号 → N月M号
    p.append((
        re.compile(r"(\d{1,2})\.(\d{1,2})号"),
        lambda m: f"{_int_to_zh(int(m.group(1)))}月{_int_to_zh(int(m.group(2)))}号",
    ))

    # 0e. No.N / no.N → 第N
    p.append((
        re.compile(r"[Nn][Oo]\.(\d+)"),
        lambda m: "第" + _int_to_zh(int(m.group(1))),
    ))

    # 0f. 第N ordinal
    p.append((
        re.compile(r"第(\d+)"),
        lambda m: "第" + _int_to_zh(int(m.group(1))),
    ))

    # 0g. Duration year: 过去N年 → integer (before YYYY年 digit-by-digit)
    p.append((
        re.compile(r"过去(\d+)年"),
        lambda m: "过去" + _int_to_zh(int(m.group(1))) + "年",
    ))

    # 1. Date: YYYY-MM-DD or YYYY/MM/DD (leading-zero month/day → 零X)
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

    # 3. Year: YYYY年 → digit-by-digit
    p.append((
        re.compile(r"(\d{4})年"),
        lambda m: _year_to_zh(m.group(1)) + "年",
    ))

    # 4. Time: HH:MM:SS
    p.append((
        re.compile(r"(\d{1,2}):(\d{2}):(\d{2})(?!\d)"),
        lambda m: (
            _int_to_zh(int(m.group(1))) + "点"
            + ("零" if m.group(2).startswith("0") and int(m.group(2)) != 0 else "")
            + _int_to_zh(int(m.group(2))) + "分"
            + ("零" if m.group(3).startswith("0") and int(m.group(3)) != 0 else "")
            + _int_to_zh(int(m.group(3))) + "秒"
        ),
    ))

    # 5. Time: HH:MM
    p.append((
        re.compile(r"(\d{1,2}):(\d{2})(?!\d)"),
        lambda m: (
            _int_to_zh(int(m.group(1))) + "点"
            + (
                "" if int(m.group(2)) == 0
                else ("零" if m.group(2).startswith("0") else "")
                     + _int_to_zh(int(m.group(2))) + "分"
            )
        ),
    ))

    # 5b. Ratio / score: N:M → N比M
    p.append((
        re.compile(r"(\d+):(\d+)"),
        lambda m: _int_to_zh(int(m.group(1))) + "比" + _int_to_zh(int(m.group(2))),
    ))

    # 6. Speed: Nkm/h → 每小时N千米
    p.append((
        re.compile(r"(\d+(?:\.\d+)?)km/h"),
        lambda m: "每小时" + (
            _decimal_to_zh(m.group(1)) if "." in m.group(1) else _int_to_zh(int(m.group(1)))
        ) + "千米",
    ))

    # 7. 100% → 百分之百
    p.append((re.compile(r"100%"), lambda m: "百分之百"))

    # 8. Percentage
    p.append((
        re.compile(r"(\d+(?:\.\d+)?)%"),
        lambda m: "百分之" + (
            _decimal_to_zh(m.group(1)) if "." in m.group(1) else _int_to_zh(int(m.group(1)))
        ),
    ))

    # 9. CNY with decimal: ¥N.D → 元/角/分  (truncates to 2 decimal places)
    p.append((
        re.compile(r"-[¥￥](\d+)\.(\d+)"),
        lambda m: "负" + _cny_to_zh(m.group(1), m.group(2)),
    ))
    p.append((
        re.compile(r"[¥￥](\d+)\.(\d+)"),
        lambda m: _cny_to_zh(m.group(1), m.group(2)),
    ))

    # 10. CNY integer
    p.append((
        re.compile(r"-[¥￥](\d+)"),
        lambda m: "负" + _int_to_zh(int(m.group(1))) + "元",
    ))
    p.append((
        re.compile(r"[¥￥](\d+)"),
        lambda m: _int_to_zh(int(m.group(1))) + "元",
    ))

    # 11. Other currencies (negative variants first)
    p.append((
        re.compile(r"-€(\d+(?:\.\d+)?)"),
        lambda m: "负" + (
            _decimal_to_zh(m.group(1)) if "." in m.group(1) else _int_to_zh(int(m.group(1)))
        ) + "欧元",
    ))
    p.append((
        re.compile(r"€(\d+(?:\.\d+)?)"),
        lambda m: (
            _decimal_to_zh(m.group(1)) if "." in m.group(1) else _int_to_zh(int(m.group(1)))
        ) + "欧元",
    ))
    p.append((
        re.compile(r"-£(\d+(?:\.\d+)?)"),
        lambda m: "负" + (
            _decimal_to_zh(m.group(1)) if "." in m.group(1) else _int_to_zh(int(m.group(1)))
        ) + "英镑",
    ))
    p.append((
        re.compile(r"£(\d+(?:\.\d+)?)"),
        lambda m: (
            _decimal_to_zh(m.group(1)) if "." in m.group(1) else _int_to_zh(int(m.group(1)))
        ) + "英镑",
    ))
    p.append((
        re.compile(r"-₩(\d+(?:\.\d+)?)"),
        lambda m: "负" + (
            _decimal_to_zh(m.group(1)) if "." in m.group(1) else _int_to_zh(int(m.group(1)))
        ) + "韩元",
    ))
    p.append((
        re.compile(r"₩(\d+(?:\.\d+)?)"),
        lambda m: (
            _decimal_to_zh(m.group(1)) if "." in m.group(1) else _int_to_zh(int(m.group(1)))
        ) + "韩元",
    ))

    # 12. USD $ (negative first)
    p.append((
        re.compile(r"-\$(\d+(?:\.\d+)?)"),
        lambda m: "负" + (
            _decimal_to_zh(m.group(1)) if "." in m.group(1) else _int_to_zh(int(m.group(1)))
        ) + "美元",
    ))
    p.append((
        re.compile(r"\$(\d+(?:\.\d+)?)"),
        lambda m: (
            _decimal_to_zh(m.group(1)) if "." in m.group(1) else _int_to_zh(int(m.group(1)))
        ) + "美元",
    ))

    # 13. Fraction: 3/4 → 四分之三
    p.append((
        re.compile(r"(\d+)/(\d+)"),
        lambda m: f"{_int_to_zh(int(m.group(2)))}分之{_int_to_zh(int(m.group(1)))}",
    ))

    # 14. Temperature
    p.append((
        re.compile(r"(-?\d+(?:\.\d+)?)[°℃]C?"),
        lambda m: (
            ("负" if m.group(1).startswith("-") else "")
            + (_decimal_to_zh(m.group(1).lstrip("-")) if "." in m.group(1)
               else _int_to_zh(abs(int(m.group(1)))))
            + "摄氏度"
        ),
    ))

    # 15. Units: number + ASCII unit
    _unit_map = {
        "kg": "千克", "g": "克", "mg": "毫克",
        "km": "千米", "m": "米", "cm": "厘米", "mm": "毫米",
        "L": "升", "ml": "毫升", "mL": "毫升",
        "GHz": "吉赫兹", "MHz": "兆赫兹", "kHz": "千赫兹", "Hz": "赫兹",
        "kW": "千瓦", "W": "瓦", "V": "伏", "A": "安",
    }
    unit_re = "|".join(re.escape(u) for u in sorted(_unit_map, key=len, reverse=True))
    p.append((
        re.compile(rf"(\d+(?:\.\d+)?)({unit_re})\b"),
        lambda m, um=_unit_map: (
            (_decimal_to_zh(m.group(1)) if "." in m.group(1) else _int_to_zh(int(m.group(1))))
            + um[m.group(2)]
        ),
    ))

    # 16. Landline phone
    p.append((
        re.compile(r"\b(0\d{2,3})-(\d{7,8})\b"),
        lambda m: "".join(_DIGITS[int(c)] for c in m.group(1) + m.group(2)),
    ))

    # 17. Mobile phone
    p.append((
        re.compile(r"\b(1[3-9]\d)-?(\d{4})-?(\d{4})\b"),
        lambda m: "".join(_DIGITS[int(c)] for c in m.group(1) + m.group(2) + m.group(3)),
    ))

    # 18. Range: digit-minus-digit + Chinese char → 到
    p.append((
        re.compile(r"(\d+)-(\d+)(?=[\u4e00-\u9fff])"),
        lambda m: _int_to_zh(int(m.group(1))) + "到" + _int_to_zh(int(m.group(2))),
    ))

    # 19. Subtraction: digit-minus-digit → 减
    p.append((re.compile(r"(?<=\d)-(?=\d)"), lambda m: "减"))

    # 19b. 2 before measure words → 两
    _mw = "个只位件杯碗张本台辆条块间套座名人份架棵幅头匹根"
    p.append((
        re.compile(rf"(?<!\d)2(?=[{_mw}])"),
        lambda m: "两",
    ))

    # 20. Decimal
    p.append((
        re.compile(r"-?\d+\.\d+"),
        lambda m: ("负" if m.group(0).startswith("-") else "")
                  + _decimal_to_zh(m.group(0).lstrip("-")),
    ))

    # 21. Plain integer
    p.append((
        re.compile(r"-?\d+"),
        lambda m: ("负" if m.group(0).startswith("-") else "")
                  + _int_to_zh(abs(int(m.group(0)))),
    ))

    # 22. Symbol map
    _sym_map = {
        "+": "加", "×": "乘", "÷": "除以", "=": "等于",
        "≈": "约等于", "≠": "不等于", "≤": "小于等于", "≥": "大于等于",
        "<": "小于", ">": "大于",
        "&": "和", "@": "艾特", "#": "井号",
        "~": "到",
        # Note: — and – intentionally NOT mapped (preserve em-dash punctuation)
        "·": "", "•": "",
    }
    sym_re = "[" + re.escape("".join(_sym_map.keys())) + "]"
    p.append((
        re.compile(sym_re),
        lambda m, sm=_sym_map: sm.get(m.group(0), m.group(0)),
    ))

    return p


_PATTERNS = _build_patterns()

# Default entity allowlist — single-letter-plus-digit codes that should be preserved.
# ISO paper sizes (A0-A6, B4-B6) and common short product codes.
# Users can extend via Normalizer(lang="zh", context={"entity_allowlist": [...]}).
_DEFAULT_ALLOWLIST: list[str] = [
    "A0", "A1", "A2", "A3", "A4", "A5", "A6",
    "B4", "B5", "B6",
]

# Entity protection regexes (applied before digit conversion)
_ENTITY_RE = re.compile(
    r"https?://\S+"                          # URLs
    r"|`[^`]*`"                              # backtick code spans
    r"|(?<![a-zA-Z\d])(?:[A-Z]{2,}-?\d+(?:\.\d+)*|[A-Z]-?\d{2,}(?:\.\d+)*)(?![a-zA-Z])"  # brand codes: USB3.0, A380 (not Q1)
)
# Use CJK Unified Ideographs offset as slot index (no digits → won't be converted by integer pattern)
_SLOT_BASE = 0x4E00


def _make_slot(i: int) -> str:
    return "\x00S" + chr(_SLOT_BASE + i) + "E\x00"


_SLOT_RE = re.compile(r"\x00S([\u4e00-\u9fff])E\x00")


def _build_allowlist_re(extra: list[str]) -> re.Pattern | None:
    terms = sorted(set(_DEFAULT_ALLOWLIST + extra), key=len, reverse=True)
    if not terms:
        return None
    return re.compile(r"(?<![a-zA-Z\d])(" + "|".join(re.escape(t) for t in terms) + r")(?![a-zA-Z\d])")


class ZhNormalizer(BaseNormalizer):
    def __init__(self, context: dict | None = None):
        super().__init__(context)
        extra = list(self.context.get("entity_allowlist", []))
        self._allowlist_re = _build_allowlist_re(extra)

    def normalize(self, text: str) -> str:
        return self._apply_patterns(text)

    def normalize_token(self, token: str) -> str:
        return self._apply_patterns(token)

    def _apply_patterns(self, text: str) -> str:
        # Protect entities from digit conversion
        slots: list[str] = []

        def _protect(m: re.Match) -> str:
            slots.append(m.group(0))
            return _make_slot(len(slots) - 1)

        # Allowlist-based protection (single-letter codes like A4) first
        if self._allowlist_re:
            text = self._allowlist_re.sub(_protect, text)

        # Regex-based protection (multi-letter brand codes, URLs, code spans)
        text = _ENTITY_RE.sub(_protect, text)

        for pattern, handler in _PATTERNS:
            text = pattern.sub(handler, text)

        # Restore protected entities
        text = _SLOT_RE.sub(lambda m: slots[ord(m.group(1)) - _SLOT_BASE], text)
        return text
