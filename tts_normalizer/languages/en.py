"""English TTS normalizer.

Handles:
- Cardinals (42 → forty-two)
- Ordinals (1st, 2nd → first, second)
- Decimals (3.14 → three point one four)
- Percentages (50% → fifty percent)
- Currency ($10.50, £50, ¥30, ₩460)
- Dates (2026-04-13, April 13 2026, 25 July 2012, jan. 15, etc.)
- Times (10:30, 5pm, 01:00 a.m., 1:01:01, 1:59 p.m. EST)
- Units (50kg, 10cm, 100km/h, -5°C)
- US phone numbers (1-800-555-1234, +1 123-456-7890, SSN)
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

# Month regex: full names, 3-char abbreviations (Sept allowed), optional dot, any case
_MONTH_RE_STR = (
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?"
    r"|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?"
    r"|Nov(?:ember)?|Dec(?:ember)?)\.?"
)

# Pre-processing: normalize dotted abbreviations
# No \b before [aApP] so we also catch "1:00a.m." (digit directly before a.m.)
_PRE_AMPM = re.compile(r"([aApP])\.([mM])\.?")
_PRE_TZ = re.compile(r"\b([eEcCmMpP])\.([sS])\.([tT])\.?")
# Plain (non-dotted) timezone abbreviations
_PRE_TZ_PLAIN = re.compile(r"\b(EST|PST|CST|MST|AST|GMT|UTC|est|pst|cst|mst|ast|gmt|utc)\b")
# Handle "pmest" / "amEST" produced when p.m. and est are adjacent (no space)
_PRE_AMPM_TZ = re.compile(r"\b(am|pm)(EST|PST|CST|MST|AST|GMT|UTC|est|pst|cst|mst|ast|gmt|utc)\b", re.IGNORECASE)


def _preprocess_en(text: str) -> str:
    """Normalize a.m./p.m. → am/pm and timezone abbreviations before pattern matching."""
    text = _PRE_AMPM.sub(lambda m: (m.group(1) + m.group(2)).lower(), text)
    text = _PRE_TZ.sub(lambda m: (m.group(1) + m.group(2) + m.group(3)).upper(), text)
    text = _PRE_TZ_PLAIN.sub(lambda m: m.group(0).upper(), text)
    # Insert space and uppercase when am/pm is immediately followed by timezone: pmest → pm EST
    text = _PRE_AMPM_TZ.sub(lambda m: m.group(1).lower() + " " + m.group(2).upper(), text)
    return text


def _month_num(s: str) -> int:
    """Convert any month token (full/abbrev, any case, optional dot) to 1-12."""
    key = s.rstrip(".").lower()[:3]
    return {
        "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
        "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    }[key]


def _month_full(s: str) -> str:
    return _MONTHS_EN[_month_num(s)]


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


def _time_hm(h: int, m: int) -> str:
    """HH:MM → spoken form (no AM/PM)."""
    if m == 0:
        return _int_to_en(h) + " o'clock"
    return (_int_to_en(h) + " "
            + ("oh " if m < 10 else "")
            + _int_to_en(m))


def _time_hms(h: int, m: int, s: int) -> str:
    """HH:MM:SS → 'N hours M minutes and S seconds'."""
    return (
        _int_to_en(h) + (" hour " if h == 1 else " hours ")
        + _int_to_en(m) + (" minute " if m == 1 else " minutes ")
        + "and " + _int_to_en(s) + (" second" if s == 1 else " seconds")
    )


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


def _silent_hyphen_token_to_en(token: str) -> str:
    """Drop no-space hyphens in code-like tokens and read digits digit-by-digit."""
    def _normalize_part(part: str) -> str:
        part = re.sub(r"\d+", lambda m: " " + _digits_en(m.group(0)) + " ", part)
        return re.sub(r"\s+", " ", part).strip()

    return " ".join(part for part in (_normalize_part(p) for p in token.split("-")) if part)


def _decade_to_en(year: int) -> str:
    """1980 → 'nineteen eighties', 2010 → 'twenty tens', 2000 → 'two thousands'."""
    lo = year % 100
    if lo == 0:
        return _int_to_en(year) + "s"
    if lo == 10:
        return _int_to_en(year // 100) + " tens"
    tens_word = _TENS[lo // 10]
    decade_plural = tens_word[:-1] + "ies"
    return _int_to_en(year // 100) + " " + decade_plural


def _short_decade_en(two_digit_str: str) -> str:
    """'80s → 'eighties' (just the decade word, no century prefix)."""
    lo = int(two_digit_str)
    if lo == 0:
        return "hundreds"
    if lo == 10:
        return "tens"
    tens_word = _TENS[lo // 10]
    return tens_word[:-1] + "ies"


def _usd_flex(d_str: str, c_raw: str | None) -> str:
    """USD handler that accepts 1-, 2-, or 3+-digit cent strings."""
    d = int(d_str)
    if c_raw is None or c_raw == "":
        return _usd(d_str, None)
    if len(c_raw) == 1:
        c = int(c_raw) * 10
    elif len(c_raw) == 2:
        c = int(c_raw)
    else:
        c2 = int(c_raw[:2])
        extra = int(c_raw[2:])
        if extra != 0:
            return (_int_to_en(d) + " point "
                    + " ".join(_ONES[int(ch)] or "zero" for ch in c_raw)
                    + " dollars")
        c = c2
    return _usd(d_str, f"{c:02d}" if c > 0 else None)


def _usd_str(s: str) -> str:
    """Convert a bare dollar amount string (no $ sign) to spoken form."""
    if "." in s:
        d_s, c_s = s.split(".", 1)
        return _usd_flex(d_s, c_s)
    return _usd_flex(s, None)


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

    # ── IP addresses ─────────────────────────────────────────────────────────
    p.append((
        re.compile(r"\b(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})\b"),
        lambda m: " dot ".join(_digits_en(part) for part in m.groups()),
    ))

    # ── Abbreviations ────────────────────────────────────────────────────────
    p.append((re.compile(r"\bNo\.\s*(\d+)"), lambda m: "Number " + _int_to_en(int(m.group(1)))))
    p.append((re.compile(r"\bDr\."), lambda m: "Doctor"))
    p.append((re.compile(r"\bMr\."), lambda m: "Mister"))
    p.append((re.compile(r"\bvs\."), lambda m: "versus"))
    p.append((re.compile(r"\betc\."), lambda m: "et cetera"))

    # ── Phone: international +1 ──────────────────────────────────────────────
    # +1 NXX-NXX-XXXX (with various separators)
    p.append((
        re.compile(r"\+1[-\s]?\(?(\d{3})\)?[-\s]?(\d{3})[-\s](\d{4})\b"),
        lambda m: (
            "plus one, " + _digits_en(m.group(1))
            + ", " + _digits_en(m.group(2))
            + ", " + _digits_en(m.group(3))
        ),
    ))

    # SSN: NNN-NN-NNNN (before NXX-NXX-XXXX phone which is 3-3-4)
    p.append((
        re.compile(r"\b(\d{3})-(\d{2})-(\d{4})\b"),
        lambda m: (
            _digits_en(m.group(1))
            + ", " + _digits_en(m.group(2))
            + ", " + _digits_en(m.group(3))
        ),
    ))

    # Phone: parenthesized NXX: (NXX) NXX-XXXX or (NXX)-NXX-XXXX
    p.append((
        re.compile(r"\((\d{3})\)[-\s]?(\d{3})[-\s](\d{4})\b"),
        lambda m: (
            _digits_en(m.group(1))
            + " " + _digits_en(m.group(2))
            + " " + _digits_en(m.group(3))
        ),
    ))

    # Phone: 1-NXX-NXX-XXXX (US toll-free / standard with country code)
    p.append((
        re.compile(r"\b1-(\d{3})-(\d{3})-(\d{4})\b"),
        lambda m: (
            "one " + _int_to_en(int(m.group(1)))
            + " " + _digits_en(m.group(2))
            + " " + _digits_en(m.group(3))
        ),
    ))

    # Phone: NXX-NXX-XXXX bare US local (without country code)
    p.append((
        re.compile(r"\b(\d{3})-(\d{3})-(\d{4})\b"),
        lambda m: (
            _digits_en(m.group(1))
            + " " + _digits_en(m.group(2))
            + " " + _digits_en(m.group(3))
        ),
    ))

    # ── Dates ─────────────────────────────────────────────────────────────────
    # European: D [ordinal] Month[.] YYYY → "the Nth of Month Year"
    p.append((
        re.compile(
            rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+({_MONTH_RE_STR})\s+(\d{{4}})\b",
            re.IGNORECASE,
        ),
        lambda m: (
            "the " + _to_ordinal(int(m.group(1)))
            + " of " + _month_full(m.group(2))
            + " " + _year_to_en(m.group(3))
        ),
    ))

    # European: D [ordinal] Month[.] (no year) → "the Nth of Month"
    p.append((
        re.compile(
            rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+({_MONTH_RE_STR})\b",
            re.IGNORECASE,
        ),
        lambda m: "the " + _to_ordinal(int(m.group(1))) + " of " + _month_full(m.group(2)),
    ))

    # American: Month[.] D[,] YYYY → "Month Nth, Year" (case-insensitive, abbreviated)
    p.append((
        re.compile(
            rf"\b({_MONTH_RE_STR})\s+(\d{{1,2}}),?\s*(\d{{4}})\b",
            re.IGNORECASE,
        ),
        lambda m: (
            _month_full(m.group(1)) + " " + _to_ordinal(int(m.group(2)))
            + ", " + _year_to_en(m.group(3))
        ),
    ))

    # American: Month[.] D (no year) → "Month Nth"
    p.append((
        re.compile(
            rf"\b({_MONTH_RE_STR})\s+(\d{{1,2}})\b",
            re.IGNORECASE,
        ),
        lambda m: _month_full(m.group(1)) + " " + _to_ordinal(int(m.group(2))),
    ))

    # Date: YYYY-MM-DD ISO
    p.append((
        re.compile(r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})"),
        lambda m: (f"{_MONTHS_EN[int(m.group(2))]} {_to_ordinal(int(m.group(3)))},"
                   f" {_year_to_en(m.group(1))}"),
    ))

    # ── Time ──────────────────────────────────────────────────────────────────
    # AM/PM time range: 2pm-5pm → "two PM to five PM"
    _tz_opt = r"(?:\s+([A-Z]{2,4}))?"
    p.append((
        re.compile(r"\b(\d{1,2})(am|pm)\s*-\s*(\d{1,2})(am|pm)\b", re.IGNORECASE),
        lambda m: (
            _int_to_en(int(m.group(1))) + " " + m.group(2).upper()
            + " to "
            + _int_to_en(int(m.group(3))) + " " + m.group(4).upper()
        ),
    ))

    # Allow optional space (or none) before TZ — handles "pmEST" from "p.m.est" preprocessing
    _tz_opt2 = r"(?:\s*([A-Z]{2,4}))?"

    # Time HH:MM:SS with optional AM/PM and TZ
    p.append((
        re.compile(r"\b(\d{1,2}):(\d{2}):(\d{2})\s*(am|pm)?" + _tz_opt2 + r"\b", re.IGNORECASE),
        lambda m: (
            _time_hms(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            + (" " + m.group(4).upper() if m.group(4) else "")
            + (" " + m.group(5) if m.group(5) else "")
        ),
    ))

    # Time HH:MM with AM/PM and optional TZ: 1:59 pm EST → "one fifty nine PM EST"
    p.append((
        re.compile(r"\b(\d{1,2}):(\d{2})\s*(am|pm)" + _tz_opt2 + r"\b", re.IGNORECASE),
        lambda m: (
            _time_hm(int(m.group(1)), int(m.group(2)))
            .replace(" o'clock", "")          # drop "o'clock" when AM/PM present
            .rstrip()
            + " " + m.group(3).upper()
            + (" " + m.group(4) if m.group(4) else "")
        ),
    ))

    # Time H.MM AM/PM (dot as time separator): "1.59 p.m." → "one fifty-nine PM"
    # Must be BEFORE decimal and bare am/pm patterns so "1.59 pm" isn't split
    p.append((
        re.compile(r"\b(\d{1,2})\.(\d{2})\s*(am|pm)\b", re.IGNORECASE),
        lambda m: (
            _time_hm(int(m.group(1)), int(m.group(2)))
            .replace(" o'clock", "")
            .rstrip()
            + " " + m.group(3).upper()
        ),
    ))

    # Bare AM/PM time with space: "1 am" → "one AM" (after a.m. → am preprocessing)
    p.append((
        re.compile(r"\b(\d{1,2})\s+(am|pm)\b", re.IGNORECASE),
        lambda m: _int_to_en(int(m.group(1))) + " " + m.group(2).upper(),
    ))

    # Bare AM/PM time attached: 5pm → "five PM"
    p.append((
        re.compile(r"\b(\d{1,2})(am|pm)\b", re.IGNORECASE),
        lambda m: _int_to_en(int(m.group(1))) + " " + m.group(2).upper(),
    ))

    # ── Code / serial-number context words → digit-by-digit ─────────────────
    _code_ctx = (
        r"verification code|security code|passcode|code|pin|otp|room number|room|"
        r"zip code|zip|postal code|id|account number|order number|serial number|"
        r"invoice number|ticket number"
    )
    p.append((
        re.compile(rf"\b({_code_ctx})\s*[:#-]?\s*(\d+)\b", re.IGNORECASE),
        lambda m: m.group(1) + " " + _digits_en(m.group(2)),
    ))

    # Time HH:MM plain (leading-zero minutes → "oh X")
    p.append((
        re.compile(r"\b(\d{1,2}):(\d{2})\b"),
        lambda m: _time_hm(int(m.group(1)), int(m.group(2))),
    ))

    # ── Minus / hyphen ───────────────────────────────────────────────────────
    # Only spaced non-whitespace expressions read the hyphen as "minus".
    p.append((re.compile(r"(?<=\S)\s+-\s+(?=\S)"), lambda m: " minus "))

    # No-space hyphenated tokens: hyphen is silent; digits are read as IDs.
    p.append((
        re.compile(r"(?<!-)([^\s-]+(?:-[^\s-]+)+)"),
        lambda m: _silent_hyphen_token_to_en(m.group(1)),
    ))

    # ── Temperature ──────────────────────────────────────────────────────────
    p.append((
        re.compile(r"(-?\d+(?:\.\d+)?)[°℃]([CF]?)"),
        lambda m: (
            ("negative " if m.group(1).startswith("-") else "")
            + _read_number(m.group(1).lstrip("-"))
            + " degree" + ("s" if abs(float(m.group(1))) != 1 else "")
            + (" Celsius" if m.group(2) in ("C", "℃", "") else " Fahrenheit")
        ),
    ))

    # ── Speed ────────────────────────────────────────────────────────────────
    p.append((
        re.compile(r"(\d+(?:\.\d+)?)km/h"),
        lambda m: _read_number(m.group(1)) + " kilometers per hour",
    ))

    # ── Units ────────────────────────────────────────────────────────────────
    _unit_map_en = {
        # weight
        "kg": "kilograms", "g": "grams", "mg": "milligrams",
        "lbs": "pounds", "lb": "pounds", "oz": "ounces",
        # length
        "km": "kilometers", "m": "meters", "cm": "centimeters", "mm": "millimeters",
        "mi": "miles", "ft": "feet", "yd": "yards", "in": "inches",
        # volume
        "L": "liters", "ml": "milliliters", "mL": "milliliters",
        # power
        "GW": "gigawatts", "MW": "megawatts", "kW": "kilowatts", "W": "watts",
        # speed (km/h handled separately above)
        "mph": "miles per hour",
        # frequency
        "GHz": "gigahertz", "MHz": "megahertz", "kHz": "kilohertz", "Hz": "hertz",
        # data
        "TB": "terabytes", "GB": "gigabytes", "MB": "megabytes",
        "KB": "kilobytes", "kB": "kilobytes",
        # time
        "ms": "milliseconds", "μs": "microseconds", "ns": "nanoseconds",
        # pressure
        "MPa": "megapascals", "kPa": "kilopascals", "Pa": "pascals",
        "psi": "pounds per square inch", "atm": "atmospheres",
        # energy / voltage / current
        "kWh": "kilowatt-hours", "Wh": "watt-hours",
        "kV": "kilovolts", "V": "volts", "mV": "millivolts",
        "A": "amperes", "mA": "milliamperes",
        # angle / other
        "rpm": "revolutions per minute",
    }
    unit_re_en = "|".join(re.escape(u) for u in sorted(_unit_map_en, key=len, reverse=True))
    p.append((
        re.compile(rf"(\d+(?:\.\d+)?)\s?({unit_re_en})\b"),
        lambda m, um=_unit_map_en: _read_number(m.group(1)) + " " + um[m.group(2)],
    ))

    # ── Fractions (before ordinals to avoid suffix conflict) ─────────────────
    # Mixed number fractions: 2 1/2 → two and a half, 3 2/4 → three and two quarters
    p.append((
        re.compile(r"\b(\d+)\s+(\d+)/(\d+)\b"),
        lambda m: (
            _int_to_en(int(m.group(1))) + " and "
            + ("a half" if m.group(2) == "1" and m.group(3) == "2"
               else _fraction_en(int(m.group(2)), int(m.group(3))))
        ),
    ))

    # Fraction with ordinal suffix: 1/4th → one quarter
    p.append((
        re.compile(r"\b(\d+)/(\d+)(?:st|nd|rd|th)\b", re.IGNORECASE),
        lambda m: _fraction_en(int(m.group(1)), int(m.group(2))),
    ))

    # ── Ordinals ────────────────────────────────────────────────────────────
    p.append((
        re.compile(r"\b(\d+)(st|nd|rd|th)\b"),
        lambda m: _to_ordinal(int(m.group(1))),
    ))

    # ── Percentage ──────────────────────────────────────────────────────────
    p.append((
        re.compile(r"(\d+(?:\.\d+)?)%"),
        lambda m: _read_number(m.group(1)) + " percent",
    ))

    # ── Currency: per-period before plain amounts ────────────────────────────
    _per_map = {
        "mo": "per month", "yr": "per year", "wk": "per week",
        "d": "per day", "hr": "per hour", "min": "per minute",
    }
    _per_re = "|".join(_per_map.keys())

    # $N/period and £N/period
    p.append((
        re.compile(rf"\$([\d.]+)\/({_per_re})\b"),
        lambda m, pm=_per_map: _usd_str(m.group(1)) + " " + pm[m.group(2)],
    ))
    p.append((
        re.compile(rf"£([\d.]+)\/({_per_re})\b"),
        lambda m, pm=_per_map: (
            _read_number(m.group(1))
            + " pound" + ("s" if float(m.group(1)) != 1 else "")
            + " " + pm[m.group(2)]
        ),
    ))

    # ── Non-USD currencies ───────────────────────────────────────────────────
    _scale_words = {
        "trillion": "trillion", "billion": "billion", "million": "million",
        "thousand": "thousand", "b": "billion", "m": "million", "k": "thousand",
    }
    _scale_re = r"(?:\s*(trillion|billion|million|thousand|[bBmMkK]))?"

    # ¥ (yen)
    p.append((
        re.compile(r"¥(\d+(?:\.\d+)?)" + _scale_re + r"\b", re.IGNORECASE),
        lambda m, sw=_scale_words: (
            _read_number(m.group(1))
            + (" " + sw.get(m.group(2).lower(), m.group(2).lower()) if m.group(2) else "")
            + " yen"
        ),
    ))

    # ₩ (won)
    p.append((
        re.compile(r"₩(\d+(?:\.\d+)?)" + _scale_re + r"\b", re.IGNORECASE),
        lambda m, sw=_scale_words: (
            _read_number(m.group(1))
            + (" " + sw.get(m.group(2).lower(), m.group(2).lower()) if m.group(2) else "")
            + " won"
        ),
    ))

    # ── USD scale suffix: $45 billion → "forty-five billion dollars" ─────────
    p.append((
        re.compile(r"\$(\d+(?:\.\d+)?)\s+(trillion|billion|million|thousand)\b", re.IGNORECASE),
        lambda m: _read_number(m.group(1)) + " " + m.group(2).lower() + " dollars",
    ))

    # ── Negative currency (-$50 → negative fifty dollars) ────────────────────
    p.append((
        re.compile(r"-\$(\d+)(?:\.(\d+))?"),
        lambda m: "negative " + _usd_flex(m.group(1), m.group(2)),
    ))

    # USD without leading integer: $.01 → one cent
    p.append((
        re.compile(r"\$\.(\d+)"),
        lambda m: _usd_flex("0", m.group(1)),
    ))

    # USD
    p.append((
        re.compile(r"\$(\d+)(?:\.(\d+))?"),
        lambda m: _usd_flex(m.group(1), m.group(2)),
    ))

    # GBP £: £1.20 → "one pound twenty pence"
    p.append((
        re.compile(r"£(\d+)(?:\.(\d{1,2}))?"),
        lambda m: _gbp(m.group(1), m.group(2)),
    ))

    # ── Fractions (regular) ──────────────────────────────────────────────────
    p.append((
        re.compile(r"\b(\d+)/(\d+)\b"),
        lambda m: _fraction_en(int(m.group(1)), int(m.group(2))),
    ))

    # ── Leading-dot decimal (.1665 → point one six six five) ─────────────────
    p.append((
        re.compile(r"(?<!\d)\.\d+"),
        lambda m: "point " + " ".join(_ONES[int(c)] or "zero" for c in m.group(0)[1:]),
    ))

    # ── Decimal ──────────────────────────────────────────────────────────────
    p.append((
        re.compile(r"-?\d+\.\d+"),
        lambda m: ("negative " if m.group(0).startswith("-") else "")
                  + _int_to_en(abs(int(m.group(0).split(".")[0])))
                  + " point "
                  + " ".join(_ONES[int(c)] or "zero" for c in m.group(0).split(".")[1]),
    ))

    # ── Comma-grouped cardinals ──────────────────────────────────────────────
    p.append((
        re.compile(r"\b\d{1,3}(?:,\d{3})+\b"),
        lambda m: _int_to_en(int(m.group(0).replace(",", ""))),
    ))

    # ── Long bare digit strings ──────────────────────────────────────────────
    # Unformatted long digit runs are usually identifiers, accounts, or phone-like
    # strings in TTS input; formatted numbers keep cardinal reading above.
    p.append((
        re.compile(r"\b\d{5,}\b"),
        lambda m: _digits_en(m.group(0)),
    ))

    # ── Short decade: '80s → eighties ────────────────────────────────────────
    p.append((
        re.compile(r"'(\d{2})s\b"),
        lambda m: _short_decade_en(m.group(1)),
    ))

    # ── Decade: 1980s → nineteen eighties ────────────────────────────────────
    p.append((
        re.compile(r"\b(\d{4})s\b"),
        lambda m: _decade_to_en(int(m.group(1))),
    ))

    # ── 4-digit year-style numbers ───────────────────────────────────────────
    p.append((
        re.compile(r"\b(\d{4})\b"),
        lambda m: _year_to_en(m.group(1)),
    ))

    # ── Integer ──────────────────────────────────────────────────────────────
    p.append((
        re.compile(r"-?\d+"),
        lambda m: ("negative " if m.group(0).startswith("-") else "")
                  + _int_to_en(abs(int(m.group(0)))),
    ))

    # ── Symbols ──────────────────────────────────────────────────────────────
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


def _gbp(pounds_str: str, pence_raw: str | None) -> str:
    """£1.20 → 'one pound twenty pence', £2 → 'two pounds'."""
    p = int(pounds_str)
    if pence_raw is None:
        return _int_to_en(p) + " pound" + ("s" if p != 1 else "")
    pence_str = pence_raw.ljust(2, "0")[:2]  # normalise to 2 digits
    c = int(pence_str)
    if c == 0:
        return _int_to_en(p) + " pound" + ("s" if p != 1 else "")
    pence_word = _int_to_en(c) + " penn" + ("y" if c == 1 else "ies")
    if p == 0:
        return pence_word
    return _int_to_en(p) + " pound" + ("s" if p != 1 else "") + " " + pence_word


_PATTERNS = _build_patterns()

# Entity protection: shield brand codes, URLs, and backtick spans from mangling.
_ENTITY_RE = re.compile(
    r"https?://\S+"
    r"|`[^`]*`"
    r"|(?<![a-zA-Z\d])(?:[A-Z]{2,}-?\d+(?:\.\d+)*[a-zA-Z]?|[A-Z]-?\d{2,}(?:\.\d+)*[a-zA-Z]?)(?![A-Z\d])"
)
_SLOT_BASE = 0xE000  # Unicode PUA


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
        text = _preprocess_en(text)

        for pattern, handler in _PATTERNS:
            text = pattern.sub(handler, text)

        def _restore(m: re.Match) -> str:
            value = slots[ord(m.group(1)) - _SLOT_BASE]
            if value.startswith(("http://", "https://", "`")):
                return value
            if re.search(r"\S-\S", value):
                return _silent_hyphen_token_to_en(value)
            return value

        text = _SLOT_RE_EN.sub(_restore, text)

        # Insert spaces at letter↔digit boundaries
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
