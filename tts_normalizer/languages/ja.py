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


# ---------------------------------------------------------------------------
# Pattern registry
# ---------------------------------------------------------------------------

def _build_patterns():
    p = []

    # 0. Thousands comma removal (12,345 → 12345)
    p.append((re.compile(r"(?<=\d),(?=\d{3})"), lambda m: ""))

    # 1a. IP address (before version-number and decimal patterns)
    p.append((
        re.compile(r"\b(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})\b"),
        lambda m: "点".join(
            "".join(_DIGITS_JA[int(c)] for c in part)
            for part in [m.group(1), m.group(2), m.group(3), m.group(4)]
        ),
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

    # 1e. Fractions (1/2 → 二分の一)
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
    p.append((
        re.compile(r"(\d{1,2}):(\d{2})(?!\d)"),
        lambda m: (
            _int_to_ja(int(m.group(1))) + "時"
            + ("" if int(m.group(2)) == 0 else _int_to_ja(int(m.group(2))) + "分")
        ),
    ))

    # 5b. Ratio N:M → N対M (after time patterns to avoid conflict)
    p.append((
        re.compile(r"(\d+):(\d+)"),
        lambda m: _int_to_ja(int(m.group(1))) + "対" + _int_to_ja(int(m.group(2))),
    ))

    # 6. Speed: Nkm/h → 時速Nキロメートル
    p.append((
        re.compile(r"(\d+(?:\.\d+)?)km/h"),
        lambda m: "時速" + (
            _decimal_to_ja(m.group(1)) if "." in m.group(1) else _int_to_ja(int(m.group(1)))
        ) + "キロメートル",
    ))

    # 7. Percentage
    p.append((
        re.compile(r"(\d+(?:\.\d+)?)%"),
        lambda m: (
            _decimal_to_ja(m.group(1)) if "." in m.group(1) else _int_to_ja(int(m.group(1)))
        ) + "パーセント",
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

        text = _SLOT_RE_JA.sub(lambda m: slots[ord(m.group(1)) - _SLOT_BASE_JA], text)

        text = _CLEANUP_DECIMAL_JA.sub(lambda m: _decimal_to_ja(m.group(0)), text)
        text = _CLEANUP_INT_JA.sub(lambda m: _int_to_ja(int(m.group(0))), text)

        return text
