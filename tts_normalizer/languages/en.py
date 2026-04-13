"""English TTS normalizer (basic implementation).

Handles:
- Cardinals (42 → forty-two)
- Ordinals (1st, 2nd → first, second)
- Decimals (3.14 → three point one four)
- Percentages (10% → ten percent)
- Currency ($10.50 → ten dollars and fifty cents)
- Dates (2026-04-13 → April thirteenth, twenty twenty-six)
- Times (10:30 → ten thirty)
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
_MONTHS = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


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


def _build_patterns():
    p = []

    # Date: YYYY-MM-DD
    p.append((
        re.compile(r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})"),
        lambda m: (f"{_MONTHS[int(m.group(2))]} {_to_ordinal(int(m.group(3)))},"
                   f" {_year_to_en(m.group(1))}"),
    ))

    # Time HH:MM
    p.append((
        re.compile(r"\b(\d{1,2}):(\d{2})\b"),
        lambda m: (_int_to_en(int(m.group(1))) + " "
                   + ("o'clock" if int(m.group(2)) == 0 else _int_to_en(int(m.group(2))))),
    ))

    # Ordinals: 1st 2nd 3rd 4th …
    p.append((
        re.compile(r"\b(\d+)(st|nd|rd|th)\b"),
        lambda m: _to_ordinal(int(m.group(1))),
    ))

    # Percentage
    p.append((
        re.compile(r"(\d+(?:\.\d+)?)%"),
        lambda m: _read_number(m.group(1)) + " percent",
    ))

    # USD
    p.append((
        re.compile(r"\$(\d+)(?:\.(\d{2}))?"),
        lambda m: (
            _int_to_en(int(m.group(1))) + " dollar" + ("s" if int(m.group(1)) != 1 else "")
            + ((" and " + _int_to_en(int(m.group(2))) + " cent"
                + ("s" if int(m.group(2)) != 1 else "")) if m.group(2) and int(m.group(2)) else "")
        ),
    ))

    # Decimal
    p.append((
        re.compile(r"-?\d+\.\d+"),
        lambda m: ("negative " if m.group(0).startswith("-") else "")
                  + _int_to_en(abs(int(m.group(0).split(".")[0])))
                  + " point "
                  + " ".join(_ONES[int(c)] or "zero" for c in m.group(0).split(".")[1]),
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


_PATTERNS = _build_patterns()


class EnNormalizer(BaseNormalizer):
    def normalize(self, text: str) -> str:
        return self._apply(text)

    def normalize_token(self, token: str) -> str:
        return self._apply(token)

    def _apply(self, text: str) -> str:
        for pattern, handler in _PATTERNS:
            text = pattern.sub(handler, text)
        return text
