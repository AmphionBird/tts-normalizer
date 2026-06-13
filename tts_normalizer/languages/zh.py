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


def _digits_to_zh(s: str) -> str:
    """Read digits one-by-one."""
    return "".join(_DIGITS[int(c)] for c in s)


def _number_to_zh(s: str) -> str:
    """Read an integer or decimal as a regular number."""
    return _decimal_to_zh(s) if "." in s else _int_to_zh(int(s))


def _silent_hyphen_token_to_zh(token: str) -> str:
    """Drop no-space hyphens in code-like tokens and read digits digit-by-digit."""
    token = token.replace("-", "")
    return re.sub(r"\d+", lambda m: _digits_to_zh(m.group(0)), token)


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


_RATE_UNIT_ZH = {
    "kg": "千克", "g": "克", "mg": "毫克",
    "km": "千米", "m": "米", "cm": "厘米", "mm": "毫米",
    "L": "升", "l": "升", "ml": "毫升", "mL": "毫升", "dL": "分升", "dl": "分升",
    "kWh": "千瓦时", "Wh": "瓦时", "kW": "千瓦", "W": "瓦",
    "TB": "太字节", "GB": "吉字节", "MB": "兆字节", "KB": "千字节",
    "Tb": "太比特", "Gb": "吉比特", "Mb": "兆比特", "Kb": "千比特",
    "tb": "太比特", "gb": "吉比特", "mb": "兆比特", "kb": "千比特", "b": "比特",
    "Hz": "赫兹", "kHz": "千赫兹", "MHz": "兆赫兹", "GHz": "吉赫兹",
    "Pa": "帕", "kPa": "千帕", "MPa": "兆帕",
    "beat": "次", "beats": "次", "breath": "次", "breaths": "次",
    "frame": "帧", "frames": "帧", "word": "词", "words": "词",
    "request": "请求", "requests": "请求", "r": "转",
}

_RATE_DEN_ZH = {
    **_RATE_UNIT_ZH,
    "h": "小时", "hr": "小时", "hrs": "小时", "hour": "小时", "hours": "小时",
    "s": "秒", "sec": "秒", "secs": "秒", "second": "秒", "seconds": "秒",
    "min": "分钟", "mins": "分钟", "minute": "分钟", "minutes": "分钟",
    "d": "天", "day": "天", "days": "天",
    "wk": "周", "wks": "周", "week": "周", "weeks": "周",
    "mo": "月", "month": "月", "months": "月",
    "yr": "年", "yrs": "年", "year": "年", "years": "年",
    "person": "人", "people": "人", "unit": "单位", "units": "单位",
    "piece": "件", "pieces": "件", "serving": "份", "servings": "份",
    "seat": "座", "seats": "座",
}

_RATE_UNIT_RE_ZH = "|".join(re.escape(u) for u in sorted(_RATE_UNIT_ZH, key=len, reverse=True))
_RATE_DEN_RE_ZH = "|".join(re.escape(u) for u in sorted(_RATE_DEN_ZH, key=len, reverse=True))
_RATE_TIME_DEN_ZH = {"h", "hr", "hrs", "hour", "hours"}


def _rate_number_to_zh(s: str) -> str:
    return _decimal_to_zh(s) if "." in s else _int_to_zh(int(s))


def _rate_den_part_zh(token: str, count: str | None = None, power: str | None = None) -> str:
    unit = _RATE_DEN_ZH.get(token, _RATE_DEN_ZH[token.lower()])
    if power in ("2", "^2", "²"):
        unit = "平方" + unit
    elif power in ("3", "^3", "³"):
        unit = "立方" + unit
    return (_rate_number_to_zh(count) if count is not None else "") + unit


def _slash_rate_zh(value: str, unit: str, denominator: str) -> str:
    value_phrase = _rate_number_to_zh(value) + _RATE_UNIT_ZH.get(unit, _RATE_UNIT_ZH[unit.lower()])
    den_parts = []
    for part in re.split(r"\s*/\s*", denominator):
        m = re.fullmatch(r"(\d+(?:\.\d+)?)?\s*([A-Za-zμ]+)(\^?[23]|[²³])?", part)
        if not m:
            den_parts.append(part)
            continue
        den_parts.append(_rate_den_part_zh(m.group(2), m.group(1), m.group(3)))

    return "每" + "每".join(den_parts) + value_phrase


_ASCII_ROMAN_VALUES_ZH = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
_ASCII_ROMAN_RE_ZH = r"M{0,3}(?:CM|CD|D?C{0,3})(?:XC|XL|L?X{0,3})(?:IX|IV|V?I{0,3})"
_WEEKDAY_ZH = {
    "一": "周一", "二": "周二", "三": "周三", "四": "周四",
    "五": "周五", "六": "周六", "日": "周日", "天": "周日",
}
_WHITELIST_ZH = {
    "Dr.": "博士",
    "Prof.": "教授",
    "Mr.": "先生",
    "Mrs.": "女士",
    "Ms.": "女士",
    "No.": "第",
}


def _roman_to_zh(token: str) -> str:
    if not token or not re.fullmatch(_ASCII_ROMAN_RE_ZH, token):
        return token
    total = 0
    prev = 0
    for ch in reversed(token):
        value = _ASCII_ROMAN_VALUES_ZH[ch]
        if value < prev:
            total -= value
        else:
            total += value
            prev = value
    return _int_to_zh(total) if 1 <= total <= 3999 else token


def _range_number_zh(s: str, year_like: bool = False) -> str:
    if year_like and re.fullmatch(r"\d{4}", s):
        return _year_to_zh(s)
    return _number_to_zh(s)


# ---------------------------------------------------------------------------
# Pattern registry
# ---------------------------------------------------------------------------

def _build_patterns():
    p = []

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

    # 0a1b. Conservative ASCII Roman numerals in CJK contexts.
    roman_token_zh = r"(?=[MDCLXVI])" + _ASCII_ROMAN_RE_ZH
    p.append((
        re.compile(rf"第({roman_token_zh})(?=[章节卷部幕篇])"),
        lambda m: "第" + _roman_to_zh(m.group(1)),
    ))
    p.append((
        re.compile(rf"\b({roman_token_zh})(?=型|类|级|期|区|组)"),
        lambda m: _roman_to_zh(m.group(1)),
    ))

    # 0a1c. Strict cased whitelist for mixed English abbreviations.
    whitelist_zh_re = "|".join(re.escape(k) for k in sorted(_WHITELIST_ZH, key=len, reverse=True))
    p.append((
        re.compile(rf"(?<![A-Za-z])({whitelist_zh_re})(?![A-Za-z])"),
        lambda m: _WHITELIST_ZH[m.group(1)],
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
    for ctx in ["验证码", "校验码", "编号", "序列号", "订单号", "邮编", "邮政编码",
                "房间号", "门牌号", "末四位", "末六位", "末八位", "末三位", "学号", "工号"]:
        p.append((
            re.compile(rf"{ctx}[:：]?\s*(\d+)"),
            lambda m, c=ctx: c + "".join(_DIGITS[int(d)] for d in m.group(1)),
        ))

    # 0b1. Dot date must precede version numbers.
    p.append((
        re.compile(r"(\d{4})\.(\d{1,2})\.(\d{1,2})"),
        lambda m: (
            _year_to_zh(m.group(1)) + "年"
            + _int_to_zh(int(m.group(2))) + "月"
            + _int_to_zh(int(m.group(3))) + "日"
        ),
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

    # 1. Date: YYYY-MM-DD / YYYY/MM/DD / YYYY.MM.DD (leading zeros stripped)
    p.append((
        re.compile(r"(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})"),
        lambda m: (
            _year_to_zh(m.group(1)) + "年"
            + _int_to_zh(int(m.group(2))) + "月"
            + _int_to_zh(int(m.group(3))) + "日"
        ),
    ))
    # Date: MM/DD/YYYY by default; DD/MM/YYYY only when day disambiguates.
    p.append((
        re.compile(r"\b(0?[1-9]|1[0-2])/([0-2]?\d|3[01])/(\d{4})\b"),
        lambda m: (
            _year_to_zh(m.group(3)) + "年"
            + _int_to_zh(int(m.group(1))) + "月"
            + _int_to_zh(int(m.group(2))) + "日"
        ),
    ))
    p.append((
        re.compile(r"\b(1[3-9]|2\d|3[01])/([0]?[1-9]|1[0-2])/(\d{4})\b"),
        lambda m: (
            _year_to_zh(m.group(3)) + "年"
            + _int_to_zh(int(m.group(2))) + "月"
            + _int_to_zh(int(m.group(1))) + "日"
        ),
    ))
    p.append((
        re.compile(r"(?<![A-Za-z0-9])([12])H(\d{2})(?![A-Za-z0-9])"),
        lambda m: "二零" + _digits_to_zh(m.group(2)) + "年" + ("上半年" if m.group(1) == "1" else "下半年"),
    ))
    p.append((
        re.compile(r"(?<![A-Za-z0-9])([1-4])Q(\d{2})(?![A-Za-z0-9])"),
        lambda m: "二零" + _digits_to_zh(m.group(2)) + "年" + "第" + _int_to_zh(int(m.group(1))) + "季度",
    ))

    # 2. Date: M月D日
    p.append((
        re.compile(r"(\d{1,2})月(\d{1,2})日"),
        lambda m: f"{_int_to_zh(int(m.group(1)))}月{_int_to_zh(int(m.group(2)))}日",
    ))

    # 2b. Year ranges before standalone YYYY年.
    p.append((
        re.compile(r"(\d{4})\s*[-~〜到至]\s*(\d{4})年"),
        lambda m: _year_to_zh(m.group(1)) + "到" + _year_to_zh(m.group(2)) + "年",
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

    # 6. Slash rates / compound units: Nkm/hour, N mg/dL, N MB/s, etc.
    p.append((
        re.compile(
            rf"(\d+(?:\.\d+)?)\s*({_RATE_UNIT_RE_ZH})\s*/\s*"
            rf"((?:\d+(?:\.\d+)?\s*)?(?:{_RATE_DEN_RE_ZH})(?:\^?[23]|[²³])?"
            rf"(?:\s*/\s*(?:\d+(?:\.\d+)?\s*)?(?:{_RATE_DEN_RE_ZH})(?:\^?[23]|[²³])?)*)"
        ),
        lambda m: _slash_rate_zh(m.group(1), m.group(2), m.group(3)),
    ))

    _implied_rate_zh = {
        "mph": ("小时", "英里"), "kph": ("小时", "千米"), "rpm": ("分钟", "转"),
        "bpm": ("分钟", "次"), "fps": ("秒", "帧"), "dpi": ("英寸", "点"),
        "ppm": ("百万", "份"), "kbps": ("秒", "千比特"), "Kbps": ("秒", "千比特"),
        "Mbps": ("秒", "兆比特"), "Gbps": ("秒", "吉比特"), "Tbps": ("秒", "太比特"),
    }
    implied_rate_re_zh = "|".join(re.escape(u) for u in sorted(_implied_rate_zh, key=len, reverse=True))
    p.append((
        re.compile(rf"(\d+(?:\.\d+)?)\s?({implied_rate_re_zh})\b"),
        lambda m, irm=_implied_rate_zh: "每" + irm[m.group(2)][0] + _rate_number_to_zh(m.group(1)) + irm[m.group(2)][1],
    ))

    # Percentage range must precede standalone percentage.
    p.append((
        re.compile(r"(\d+(?:\.\d+)?)%\s*(?:-|到|至|~|〜)\s*(\d+(?:\.\d+)?)%"),
        lambda m: "百分之" + _range_number_zh(m.group(1)) + "到百分之" + _range_number_zh(m.group(2)),
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

    # 8a. Ranges that should precede fractions, hyphenated IDs, and plain numbers.
    p.append((
        re.compile(r"周([一二三四五六日天])\s*[-~〜到至]\s*周?([一二三四五六日天])"),
        lambda m: _WEEKDAY_ZH[m.group(1)] + "到" + _WEEKDAY_ZH[m.group(2)],
    ))
    p.append((
        re.compile(r"(?<![A-Za-z0-9])(\d+(?:\.\d+)?)\s*[~〜到至]\s*(\d+(?:\.\d+)?)(?![A-Za-z0-9])"),
        lambda m: _range_number_zh(m.group(1)) + "到" + _range_number_zh(m.group(2)),
    ))
    p.append((
        re.compile(r"~\s*(\d+(?:\.\d+)?)"),
        lambda m: "约" + _range_number_zh(m.group(1)),
    ))

    # 8b. Idiomatic slash expression that should not be treated as a fraction.
    p.append((re.compile(r"(?<!\d)24/7(?!\d)"), lambda m: "二十四小时七天"))

    # 8c. Currency per unit before plain currency amounts.
    _currency_unit_zh = {"$": "美元", "€": "欧元", "£": "英镑", "₩": "韩元", "¥": "元", "￥": "元"}
    p.append((
        re.compile(rf"([$€£₩¥￥])(\d+(?:\.\d+)?)\s*/\s*((?:{_RATE_DEN_RE_ZH}))"),
        lambda m, cm=_currency_unit_zh: "每" + _rate_den_part_zh(m.group(3)) + _rate_number_to_zh(m.group(2)) + cm[m.group(1)],
    ))

    # 9. CNY with decimal: ¥N.D → 元/角/分  (truncates to 2 decimal places)
    p.append((
        re.compile(r"-[¥￥](\d[\d,]*)\.(\d+)"),
        lambda m: "负" + _cny_to_zh(m.group(1).replace(",", ""), m.group(2)),
    ))
    p.append((
        re.compile(r"[¥￥](\d[\d,]*)\.(\d+)"),
        lambda m: _cny_to_zh(m.group(1).replace(",", ""), m.group(2)),
    ))

    # 10. CNY integer
    p.append((
        re.compile(r"-[¥￥](\d[\d,]*)"),
        lambda m: "负" + _int_to_zh(int(m.group(1).replace(",", ""))) + "元",
    ))
    p.append((
        re.compile(r"[¥￥](\d[\d,]*)"),
        lambda m: _int_to_zh(int(m.group(1).replace(",", ""))) + "元",
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

    _unit_map = {
        "kg": "千克", "g": "克", "mg": "毫克",
        "km/h": "千米每小时",
        "km": "千米", "m": "米", "cm": "厘米", "mm": "毫米",
        "L": "升", "ml": "毫升", "mL": "毫升",
        "GHz": "吉赫兹", "MHz": "兆赫兹", "kHz": "千赫兹", "Hz": "赫兹",
        "kW": "千瓦", "W": "瓦", "V": "伏", "A": "安",
    }
    unit_re = "|".join(re.escape(u) for u in sorted(_unit_map, key=len, reverse=True))
    range_suffix_re = "|".join(
        re.escape(s)
        for s in sorted(
            [
                *list(_unit_map),
                "摄氏度", "华氏度", "个百分点", "百分点", "人民币", "块钱",
                "美元", "欧元", "英镑", "韩元", "公里", "千米", "厘米", "毫米", "米",
                "公斤", "千克", "毫克", "小时", "分钟", "个月", "元", "块",
                "岁", "年", "月", "日", "天", "人", "名", "个", "页", "次",
                "倍", "分", "秒", "度", "℃", "°C",
            ],
            key=len,
            reverse=True,
        )
    )
    p.append((
        re.compile(rf"(?<![A-Za-z0-9])(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)(?:({range_suffix_re}))"),
        lambda m, um=_unit_map: (
            _number_to_zh(m.group(1)) + "到" + _number_to_zh(m.group(2))
            + um.get(m.group(3), "摄氏度" if m.group(3) in {"℃", "°C"} else m.group(3))
        ),
    ))

    # No-space equation subtraction, including variable expressions such as x-3=7.
    p.append((
        re.compile(r"(?<=[A-Za-z0-9\u4e00-\u9fff\)])-(?=[A-Za-z0-9\u4e00-\u9fff\(][^\s=]*=)"),
        lambda m: "减",
    ))

    negative_unit_map = {**_unit_map, "℃": "摄氏度", "°C": "摄氏度"}
    negative_unit_re = "|".join(re.escape(u) for u in sorted(negative_unit_map, key=len, reverse=True))
    p.append((
        re.compile(rf"(?<![A-Za-z0-9])-(\d+(?:\.\d+)?)({negative_unit_re})(?![A-Za-z])"),
        lambda m, um=negative_unit_map: "负" + _number_to_zh(m.group(1)) + um[m.group(2)],
    ))

    # Contextual negatives before CJK/unit suffixes: 温度-10度, 海拔-100米, 变化-3.5个百分点.
    p.append((
        re.compile(rf"(?<![A-Za-z0-9])-(\d+(?:\.\d+)?)(?=({range_suffix_re}))"),
        lambda m: "负" + _number_to_zh(m.group(1)),
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
    p.append((
        re.compile(rf"(\d+(?:\.\d+)?)({unit_re})\b"),
        lambda m, um=_unit_map: (
            (_decimal_to_zh(m.group(1)) if "." in m.group(1) else _int_to_zh(int(m.group(1))))
            + um[m.group(2)]
        ),
    ))

    # 16. Phone with explicit context
    p.append((
        re.compile(r"(?:手机号|联系电话|电话)[:：]?\s*(1[3-9]\d)-?(\d{4})-?(\d{4})"),
        lambda m: m.group(0)[:m.start(1) - m.start(0)] + "".join(
            _DIGITS[int(c)] for c in m.group(1) + m.group(2) + m.group(3)
        ),
    ))

    # 17. Landline phone
    p.append((
        re.compile(r"\b(0\d{2,3})-(\d{7,8})\b"),
        lambda m: "".join(_DIGITS[int(c)] for c in m.group(1) + m.group(2)),
    ))

    # 18. Mobile phone
    p.append((
        re.compile(r"\b(1[3-9]\d)-?(\d{4})-?(\d{4})\b"),
        lambda m: "".join(_DIGITS[int(c)] for c in m.group(1) + m.group(2) + m.group(3)),
    ))

    # 19. Subtraction: only spaced non-whitespace expressions read the hyphen.
    p.append((re.compile(r"(?<=\S)\s+-\s+(?=\S)"), lambda m: "减"))

    # 20. No-space hyphenated tokens: hyphen is silent; digits are read as IDs.
    p.append((
        re.compile(r"(?<!-)([^\s-]+(?:-[^\s-]+)+)"),
        lambda m: _silent_hyphen_token_to_zh(m.group(1)),
    ))

    # 20b. 2 before measure words → 两
    _mw = "个只位件杯碗张本台辆条块间套座名人份架棵幅头匹根颗粒把双对群批排栋层所道首篇封面堆捆串"
    p.append((
        re.compile(rf"(?<!\d)2(?=[{_mw}])"),
        lambda m: "两",
    ))

    # 21. Decimal
    p.append((
        re.compile(r"-?\d+\.\d+"),
        lambda m: ("负" if m.group(0).startswith("-") else "")
                  + _decimal_to_zh(m.group(0).lstrip("-")),
    ))

    # 22. Comma-grouped cardinals keep regular number reading.
    p.append((
        re.compile(r"(?<!\d)\d{1,3}(?:,\d{3})+(?!\d)"),
        lambda m: _int_to_zh(int(m.group(0).replace(",", ""))),
    ))

    # 23. Long numbers with CJK units/measure words keep regular number reading.
    long_number_suffix_re = "|".join([range_suffix_re, rf"[{_mw}]", "吨"])
    p.append((
        re.compile(rf"(?<!\d)(\d{{5,}})(?=(?:{long_number_suffix_re}))"),
        lambda m: _int_to_zh(int(m.group(1))),
    ))

    # 24. Long bare digit strings
    p.append((
        re.compile(r"(?<!\d)\d{5,}(?!\d)"),
        lambda m: _digits_to_zh(m.group(0)),
    ))

    # 25. Plain integer
    p.append((
        re.compile(r"-?\d+"),
        lambda m: ("负" if m.group(0).startswith("-") else "")
                  + _int_to_zh(abs(int(m.group(0)))),
    ))

    # 26. Symbol map
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

# Entity protection: brand codes, URLs, and backtick code spans are shielded
# from the main pattern pipeline to prevent structural mangling (e.g. "GPT-4"
# → "GPT负四"). After restoration, a final cleanup pass converts any remaining
# digits so TTS output is always digit-free.
_ENTITY_RE = re.compile(
    r"https?://\S+"                          # URLs
    r"|`[^`]*`"                              # backtick code spans
    r"|(?<![a-zA-Z\d])(?:[A-Z]{2,}-?\d+(?:\.\d+)*[a-zA-Z]?|[A-Z]-?\d{2,}(?:\.\d+)*[a-zA-Z]?)(?![A-Z\d])"  # brand codes: USB3.0, A380, GPT-4, GPT-4o
)

_PINYIN_BASES = frozenset(
    """
    ai an ang ao ba bai ban bang bao bei ben beng bi bian biao bie bin bing bo bu
    ca cai can cang cao ce cen ceng cha chai chan chang chao che chen cheng chi chong chou
    chu chua chuai chuan chuang chui chun chuo ci cong cou cu cuan cui cun cuo
    da dai dan dang dao de dei deng di dian diao die ding diu dong dou du duan dui dun duo
    ei en eng er fa fan fang fei fen feng fo fou fu
    ga gai gan gang gao ge gei gen geng gong gou gu gua guai guan guang gui gun guo
    ha hai han hang hao he hei hen heng hong hou hu hua huai huan huang hui hun huo
    ji jia jian jiang jiao jie jin jing jiong jiu ju juan jue jun
    ka kai kan kang kao ke ken keng kong kou ku kua kuai kuan kuang kui kun kuo
    la lai lan lang lao le lei leng li lia lian liang liao lie lin ling liu long lou
    lu luan lun luo lue lüe lv lü
    ma mai man mang mao me mei men meng mi mian miao mie min ming miu mo mou mu
    na nai nan nang nao ne nei nen neng ni nian niang niao nie nin ning niu nong nou
    nu nuan nuo nue nüe nv nü
    ou pa pai pan pang pao pei pen peng pi pian piao pie pin ping po pou pu
    qi qia qian qiang qiao qie qin qing qiong qiu qu quan que qun
    ran rang rao re ren reng ri rong rou ru rua ruan rui run ruo
    sa sai san sang sao se sen seng sha shai shan shang shao she shei shen sheng shi shou
    shu shua shuai shuan shuang shui shun shuo si song sou su suan sui sun suo
    ta tai tan tang tao te teng ti tian tiao tie ting tong tou tu tuan tui tun tuo
    wa wai wan wang wei wen weng wo wu
    xi xia xian xiang xiao xie xin xing xiong xiu xu xuan xue xun
    ya yan yang yao ye yi yin ying yo yong you yu yuan yue yun
    za zai zan zang zao ze zei zen zeng zha zhai zhan zhang zhao zhe zhei zhen zheng zhi
    zhong zhou zhu zhua zhuai zhuan zhuang zhui zhun zhuo zi zong zou zu zuan zui zun zuo
    """.split()
)

_PINYIN_TONE_RE = re.compile(r"(?<![a-zA-Z])([a-zA-ZüÜvV]+)([1-5])(?![a-zA-Z0-9])")


def _is_pinyin_tone_token(token: str) -> bool:
    base = token[:-1].lower().replace("ü", "v")
    return base in _PINYIN_BASES

# Use CJK Unified Ideographs offset as slot index (no digits → won't be re-converted)
_SLOT_BASE = 0x4E00

# Final cleanup patterns: convert any digits that survived entity restoration
# (e.g. digits inside protected URLs). Uses non-negative forms to avoid creating
# spurious "负N" for digits that follow hyphens in technical strings.
_CLEANUP_DECIMAL = re.compile(r"\d+\.\d+")
_CLEANUP_INT = re.compile(r"\d+")


def _make_slot(i: int) -> str:
    return "\x00S" + chr(_SLOT_BASE + i) + "E\x00"


_SLOT_RE = re.compile(r"\x00S([\u4e00-\u9fff])E\x00")


def _make_pinyin_slot(i: int) -> str:
    return "\x00P" + chr(_SLOT_BASE + i) + "E\x00"


_PINYIN_SLOT_RE = re.compile(r"\x00P([\u4e00-\u9fff])E\x00")


class ZhNormalizer(BaseNormalizer):
    def __init__(self, context: dict | None = None):
        super().__init__(context)
        # Optional user-supplied allowlist: these tokens are protected verbatim.
        # NOTE: protected tokens may still contain ASCII digits; callers are
        # responsible for further handling if strict no-digit output is required.
        extra: list[str] = list(self.context.get("entity_allowlist", []))
        if extra:
            terms = sorted(extra, key=len, reverse=True)
            self._allowlist_re: re.Pattern | None = re.compile(
                r"(?<![a-zA-Z\d])(" + "|".join(re.escape(t) for t in terms) + r")(?![a-zA-Z\d])"
            )
        else:
            self._allowlist_re = None

    def normalize(self, text: str) -> str:
        return self._apply_patterns(text)

    def normalize_token(self, token: str) -> str:
        return self._apply_patterns(token)

    def _apply_patterns(self, text: str) -> str:
        slots: list[str] = []
        pinyin_slots: list[str] = []

        def _protect(m: re.Match) -> str:
            slots.append(m.group(0))
            return _make_slot(len(slots) - 1)

        def _protect_pinyin(m: re.Match) -> str:
            if not _is_pinyin_tone_token(m.group(0)):
                return m.group(0)
            pinyin_slots.append(m.group(0))
            return _make_pinyin_slot(len(pinyin_slots) - 1)

        # Valid pinyin tone tokens are BPE tokens and must survive both the main
        # normalization pipeline and the final digit cleanup.
        text = _PINYIN_TONE_RE.sub(_protect_pinyin, text)

        # Optional user allowlist (verbatim preservation)
        if self._allowlist_re:
            text = self._allowlist_re.sub(_protect, text)

        # URLs and backtick code spans (preserved verbatim)
        text = _ENTITY_RE.sub(_protect, text)

        for pattern, handler in _PATTERNS:
            text = pattern.sub(handler, text)

        def _restore(m: re.Match) -> str:
            value = slots[ord(m.group(1)) - _SLOT_BASE]
            if value.startswith(("http://", "https://", "`")):
                return value
            if re.search(r"\S-\S", value):
                return _silent_hyphen_token_to_zh(value)
            return value

        # Restore protected entities
        text = _SLOT_RE.sub(_restore, text)

        # Final cleanup: convert any digits that survived inside restored entities
        text = _CLEANUP_DECIMAL.sub(lambda m: _decimal_to_zh(m.group(0)), text)
        text = _CLEANUP_INT.sub(lambda m: _int_to_zh(int(m.group(0))), text)

        text = _PINYIN_SLOT_RE.sub(lambda m: pinyin_slots[ord(m.group(1)) - _SLOT_BASE], text)

        return text
