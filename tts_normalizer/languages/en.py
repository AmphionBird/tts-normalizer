"""English TTS normalizer.

Handles:
- Cardinals (42 → forty-two)
- Ordinals (1st, 2nd → first, second)
- Decimals (3.14 → three point one four)
- Percentages (50% → fifty percent)
- Currency ($10.50, £50)
- Dates (2026-04-13, April 13, 2026)
- Times (10:30 → ten thirty; 3:05 → three oh five)
- Units (50kg, 10cm, 100km/h, -5°C)
- US phone numbers (1-800-555-1234)
- Common symbols
"""

from __future__ import annotations

import re

from .base import BaseNormalizer

_ONES = [
    "", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
    "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen",
    "seventeen", "eighteen", "nineteen",
]
_TENS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
_ORDINALS = {
    "one": "first", "two": "second", "three": "third", "four": "fourth",
    "five": "fifth", "six": "sixth", "seven": "seventh", "eight": "eighth",
    "nine": "ninth", "ten": "tenth", "eleven": "eleventh", "twelve": "twelfth",
    "thirteen": "thirteenth", "fourteen": "fourteenth", "fifteen": "fifteenth",
    "sixteen": "sixteenth", "seventeen": "seventeenth", "eighteen": "eighteenth",
    "nineteen": "nineteenth", "twenty": "twentieth", "thirty": "thirtieth",
    "forty": "fortieth", "fifty": "fiftieth", "sixty": "sixtieth",
    "seventy": "seventieth", "eighty": "eightieth", "ninety": "ninetieth",
    "hundred": "hundredth", "thousand": "thousandth", "million": "millionth",
    "billion": "billionth",
}
_MONTHS_EN = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]
_MONTH_NAMES = "|".join(_MONTHS_EN[1:])


def _int_to_en(n: int) -> str:
    if n < 0:
        return "negative " + _int_to_en(-n)
    if n == 0:
        return "zero"
    if n < 20:
        return _ONES[n]
    if n < 100:
        return _TENS[n // 10] + ("-" + _ONES[n % 10] if n % 10 else "")
    if n < 1000:
        rest = n % 100
        return _ONES[n // 100] + " hundred" + (" " + _int_to_en(rest) if rest else "")
    if n < 1_000_000:
        rest = n % 1000
        return _int_to_en(n // 1000) + " thousand" + (" " + _int_to_en(rest) if rest else "")
    if n < 1_000_000_000:
        rest = n % 1_000_000
        return _int_to_en(n // 1_000_000) + " million" + (" " + _int_to_en(rest) if rest else "")
    rest = n % 1_000_000_000
    return _int_to_en(n // 1_000_000_000) + " billion" + (" " + _int_to_en(rest) if rest else "")


def _to_ordinal(n: int) -> str:
    word = _int_to_en(n)
    last = word.rsplit(" ", 1)[-1].replace("-", " ").split()[-1]
    ordinal_last = _ORDINALS.get(last, last + "th")
    return word.rsplit(last, 1)[0] + ordinal_last


def _year_to_en(year_str: str) -> str:
    y = int(year_str)
    if 1100 <= y <= 1999 or 2010 <= y <= 2099:
        hi, lo = y // 100, y % 100
        return _int_to_en(hi) + " " + (_int_to_en(lo) if lo else "hundred")
    return _int_to_en(y)


def _read_number(s: str) -> str:
    if "." in s:
        i, f = s.split(".")
        return (_int_to_en(int(i)) + " point "
                + " ".join(_ONES[int(c)] or "zero" for c in f))
    return _int_to_en(int(s))


def _usd(dollars_str: str, cents_str: str | None) -> str:
    d = int(dollars_str)
    c = int(cents_str) if cents_str else 0
    if d > 0 and c > 0:
        return (_int_to_en(d) + " dollar" + ("s" if d != 1 else "")
                + " and " + _int_to_en(c) + " cent" + ("s" if c != 1 else ""))
    if d > 0:
        return _int_to_en(d) + " dollar" + ("s" if d != 1 else "")
    if c > 0:
        return _int_to_en(c) + " cent" + ("s" if c != 1 else "")
    return "zero dollars"


def _digits_en(s: str) -> str:
    """Read string of digits one-by-one in English."""
    return " ".join(_ONES[int(c)] or "zero" for c in s)


def _fraction_en(num: int, den: int) -> str:
    if den == 2:
        return _int_to_en(num) + (" half" if num == 1 else " halves")
    if den == 4:
        return _int_to_en(num) + (" quarter" if num == 1 else " quarters")
    den_word = _to_ordinal(den)
    if num > 1:
        den_word += "s"
    return _int_to_en(num) + " " + den_word


def _build_patterns():
    p = []

    # Comma removal (1,000 → 1000)
    p.append((re.compile(r"(?<=\d),(?=\d{3})"), lambda m: ""))

    # Abbreviations (before number patterns to avoid partial processing)
    p.append((re.compile(r"\bNo\.\s*(\d+)"), lambda m: "Number " + _int_to_en(int(m.group(1)))))
    p.append((re.compile(r"\bDr\."), lambda m: "Doctor"))
    p.append((re.compile(r"\bMr\."), lambda m: "Mister"))
    p.append((re.compile(r"\bvs\."), lambda m: "versus"))
    p.append((re.compile(r"\betc\."), lambda m: "et cetera"))

    # Phone: 1-NXX-NXX-XXXX (US toll-free / standard)
    # "800" component read as number; remaining 7 digits read individually
    p.append((
        re.compile(r"\b1-(\d{3})-(\d{3})-(\d{4})\b"),
        lambda m: (
            "one " + _int_to_en(int(m.group(1)))
            + " " + _digits_en(m.group(2))
            + " " + _digits_en(m.group(3))
        ),
    ))

    # Date: "Month D, YYYY" text format
    p.append((
        re.compile(
            rf"\b({_MONTH_NAMES})\s+(\d{{1,2}}),?\s*(\d{{4}})\b"
        ),
        lambda m: (
            m.group(1) + " " + _to_ordinal(int(m.group(2)))
            + ", " + _year_to_en(m.group(3))
        ),
    ))

    # Date: YYYY-MM-DD ISO
    p.append((
        re.compile(r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})"),
        lambda m: (f"{_MONTHS_EN[int(m.group(2))]} {_to_ordinal(int(m.group(3)))},"
                   f" {_year_to_en(m.group(1))}"),
    ))

    # Time HH:MM  (leading-zero minutes → "oh X")
    p.append((
        re.compile(r"\b(\d{1,2}):(\d{2})\b"),
        lambda m: (
            _int_to_en(int(m.group(1))) + " "
            + (
                "o'clock" if int(m.group(2)) == 0
                else ("oh " if m.group(2).startswith("0") else "")
                     + _int_to_en(int(m.group(2)))
            )
        ),
    ))

    # Temperature: -5°C / 37°F
    p.append((
        re.compile(r"(-?\d+(?:\.\d+)?)[°℃]([CF]?)"),
        lambda m: (
            ("negative " if m.group(1).startswith("-") else "")
            + _read_number(m.group(1).lstrip("-"))
            + " degree" + ("s" if abs(float(m.group(1))) != 1 else "")
            + (" Celsius" if m.group(2) in ("C", "℃", "") else " Fahrenheit")
        ),
    ))

    # Speed: Nkm/h → N kilometers per hour
    p.append((
        re.compile(r"(\d+(?:\.\d+)?)km/h"),
        lambda m: _read_number(m.group(1)) + " kilometers per hour",
    ))

    # Units
    _unit_map_en = {
        "kg": "kilograms", "g": "grams", "mg": "milligrams",
        "km": "kilometers", "m": "meters", "cm": "centimeters", "mm": "millimeters",
        "L": "liters", "ml": "milliliters", "mL": "milliliters",
        "kW": "kilowatts", "W": "watts",
    }
    unit_re_en = "|".join(re.escape(u) for u in sorted(_unit_map_en, key=len, reverse=True))
    p.append((
        re.compile(rf"(\d+(?:\.\d+)?)({unit_re_en})\b"),
        lambda m, um=_unit_map_en: _read_number(m.group(1)) + " " + um[m.group(2)],
    ))

    # Ordinals: 1st 2nd 3rd …
    p.append((
        re.compile(r"\b(\d+)(st|nd|rd|th)\b"),
        lambda m: _to_ordinal(int(m.group(1))),
    ))

    # Percentage
    p.append((
        re.compile(r"(\d+(?:\.\d+)?)%"),
        lambda m: _read_number(m.group(1)) + " percent",
    ))

    # Negative currency (-$50 → negative fifty dollars)
    p.append((
        re.compile(r"-\$(\d+)(?:\.(\d{2}))?"),
        lambda m: "negative " + _usd(m.group(1), m.group(2)),
    ))

    # USD
    p.append((
        re.compile(r"\$(\d+)(?:\.(\d{2}))?"),
        lambda m: _usd(m.group(1), m.group(2)),
    ))

    # GBP £
    p.append((
        re.compile(r"£(\d+(?:\.\d+)?)"),
        lambda m: _read_number(m.group(1)) + " pound" + ("s" if float(m.group(1)) != 1 else ""),
    ))

    # Fractions (1/2 → one half, 3/4 → three quarters, 2/5 → two fifths)
    p.append((
        re.compile(r"\b(\d+)/(\d+)\b"),
        lambda m: _fraction_en(int(m.group(1)), int(m.group(2))),
    ))

    # Decimal
    p.append((
        re.compile(r"-?\d+\.\d+"),
        lambda m: ("negative " if m.group(0).startswith("-") else "")
                  + _int_to_en(abs(int(m.group(0).split(".")[0])))
                  + " point "
                  + " ".join(_ONES[int(c)] or "zero" for c in m.group(0).split(".")[1]),
    ))

    # 4-digit year-style numbers (2026 → twenty twenty-six, 2000 → two thousand)
    p.append((
        re.compile(r"\b(\d{4})\b"),
        lambda m: _year_to_en(m.group(1)),
    ))

    # Integer
    p.append((
        re.compile(r"-?\d+"),
        lambda m: ("negative " if m.group(0).startswith("-") else "")
                  + _int_to_en(abs(int(m.group(0)))),
    ))

    # Symbols
    _sym_map = {
        "+": "plus", "×": "times", "÷": "divided by", "=": "equals",
        "&": "and", "@": "at", "#": "number", "~": "to", "%": "percent",
    }
    sym_re = "[" + re.escape("".join(_sym_map.keys())) + "]"
    p.append((
        re.compile(sym_re),
        lambda m, sm=_sym_map: sm.get(m.group(0), m.group(0)),
    ))

    return p


_PATTERNS = _build_patterns()

# Entity protection: shield brand codes, URLs, and backtick spans from mangling.
# e.g. "GPT-4" without protection → "GPTnegative four" (hyphen misread as minus).
# After restoration, a cleanup pass converts any remaining digits to spoken form.
_ENTITY_RE = re.compile(
    r"https?://\S+"
    r"|`[^`]*`"
    r"|(?<![a-zA-Z\d])(?:[A-Z]{2,}-?\d+(?:\.\d+)*[a-zA-Z]?|[A-Z]-?\d{2,}(?:\.\d+)*[a-zA-Z]?)(?![A-Z\d])"
)
_SLOT_BASE = 0xE000  # Unicode PUA — no word characters, won't be affected by patterns


def _make_slot_en(i: int) -> str:
    return "\x00E" + chr(_SLOT_BASE + i) + "\x00"


_SLOT_RE_EN = re.compile(r"\x00E([\uE000-\uF8FF])\x00")

_CLEANUP_DECIMAL_EN = re.compile(r"\d+\.\d+")
_CLEANUP_INT_EN = re.compile(r"\d+")


class EnNormalizer(BaseNormalizer):
    def normalize(self, text: str) -> str:
        return self._apply(text)

    def normalize_token(self, token: str) -> str:
        return self._apply(token)

    def _apply(self, text: str) -> str:
        slots: list[str] = []

        def _protect(m: re.Match) -> str:
            slots.append(m.group(0))
            return _make_slot_en(len(slots) - 1)

        text = _ENTITY_RE.sub(_protect, text)

        for pattern, handler in _PATTERNS:
            text = pattern.sub(handler, text)

        text = _SLOT_RE_EN.sub(lambda m: slots[ord(m.group(1)) - _SLOT_BASE], text)

        # Insert spaces at letter↔digit boundaries so tokens read naturally:
        # "USB3.0" → "USB 3.0", "GPT-4o" → "GPT-4 o"
        text = re.sub(r"(?<=[a-zA-Z])(?=\d)", " ", text)
        text = re.sub(r"(?<=\d)(?=[a-zA-Z])", " ", text)

        # Convert any digits that survived inside restored entities
        def _en_decimal(m: re.Match) -> str:
            s = m.group(0)
            i, f = s.split(".")
            return _int_to_en(int(i)) + " point " + " ".join(
                _ONES[int(c)] or "zero" for c in f
            )
        text = _CLEANUP_DECIMAL_EN.sub(_en_decimal, text)
        text = _CLEANUP_INT_EN.sub(lambda m: _int_to_en(int(m.group(0))), text)

        return text
