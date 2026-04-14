"""Spanish TTS normalizer.

Handles:
- Cardinals (42 → cuarenta y dos; cien vs ciento; quinientos)
- Negatives (−5 → menos cinco)
- Decimals (3.14 → tres coma uno cuatro)
- Fractions (3/4 → tres cuartos)
- Percentages (50% → cincuenta por ciento)
- Currency (€/$/£)
- Dates (2026-04-13 → trece de abril de dos mil veintiséis)
- Times (10:30 → las diez y treinta; 1:05 → la una y cinco)
- Temperature (-5°C → menos cinco grados Celsius)
- Units (kg, km, cm, …)
- Scientific notation (1.5×10^6 → un millón quinientos mil)
- Ordinals (1.° / 1º → primero)
- Common abbreviations (Dr. → doctor, Sr. → señor)
- Common symbols
"""

from __future__ import annotations

import re

from .base import BaseNormalizer

# ---------------------------------------------------------------------------
# Lexicons
# ---------------------------------------------------------------------------
_ONES = [
    "cero", "uno", "dos", "tres", "cuatro", "cinco",
    "seis", "siete", "ocho", "nueve", "diez", "once",
    "doce", "trece", "catorce", "quince", "dieciséis",
    "diecisiete", "dieciocho", "diecinueve",
]
# Contracted 21-29 forms
_VEINTI = [
    "", "veintiuno", "veintidós", "veintitrés", "veinticuatro",
    "veinticinco", "veintiséis", "veintisiete", "veintiocho", "veintinueve",
]
_TENS = [
    "", "", "veinte", "treinta", "cuarenta", "cincuenta",
    "sesenta", "setenta", "ochenta", "noventa",
]
# Index 0 unused; index 1 = "ciento" (used for 101-199; 100 itself → "cien")
_HUNDREDS = [
    "", "ciento", "doscientos", "trescientos", "cuatrocientos",
    "quinientos", "seiscientos", "setecientos", "ochocientos", "novecientos",
]
_MONTHS_ES = [
    "", "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]
_ORDINALS_ES = {
    1: "primero", 2: "segundo", 3: "tercero", 4: "cuarto", 5: "quinto",
    6: "sexto", 7: "séptimo", 8: "octavo", 9: "noveno", 10: "décimo",
    11: "undécimo", 12: "duodécimo", 20: "vigésimo", 30: "trigésimo",
    40: "cuadragésimo", 50: "quincuagésimo", 60: "sexagésimo",
    70: "septuagésimo", 80: "octogésimo", 90: "nonagésimo", 100: "centésimo",
    1000: "milésimo",
}
_FRAC_DEN = {
    2: ("medio", "medios"),
    3: ("tercio", "tercios"),
    4: ("cuarto", "cuartos"),
    5: ("quinto", "quintos"),
    6: ("sexto", "sextos"),
    7: ("séptimo", "séptimos"),
    8: ("octavo", "octavos"),
    9: ("noveno", "novenos"),
    10: ("décimo", "décimos"),
    11: ("onceavo", "onceavos"),
    12: ("doceavo", "doceavos"),
}


# ---------------------------------------------------------------------------
# Number helpers
# ---------------------------------------------------------------------------

def _int_to_es(n: int) -> str:
    if n < 0:
        return "menos " + _int_to_es(-n)
    if n == 0:
        return "cero"
    if n < 20:
        return _ONES[n]
    if n < 30:
        return "veinte" if n == 20 else _VEINTI[n - 20]
    if n < 100:
        t, u = divmod(n, 10)
        return _TENS[t] + (" y " + _ONES[u] if u else "")
    if n < 1000:
        h, r = divmod(n, 100)
        if n == 100:
            return "cien"
        return _HUNDREDS[h] + (" " + _int_to_es(r) if r else "")
    if n < 1_000_000:
        th, r = divmod(n, 1000)
        prefix = "mil" if th == 1 else _int_to_es(th) + " mil"
        return prefix + (" " + _int_to_es(r) if r else "")
    if n < 1_000_000_000:
        m, r = divmod(n, 1_000_000)
        prefix = "un millón" if m == 1 else _int_to_es(m) + " millones"
        return prefix + (" " + _int_to_es(r) if r else "")
    b, r = divmod(n, 1_000_000_000)
    prefix = _int_to_es(b) + " mil millones"
    return prefix + (" " + _int_to_es(r) if r else "")


def _decimal_to_es(s: str) -> str:
    i, f = s.split(".")
    return _int_to_es(int(i)) + " coma " + " ".join(_ONES[int(c)] for c in f)


def _fraction_es(num: int, den: int) -> str:
    # "uno" → "un" before masculine nouns (un medio, un tercio, …)
    num_word = "un" if num == 1 else _int_to_es(num)
    if den in _FRAC_DEN:
        word_s, word_p = _FRAC_DEN[den]
        return num_word + " " + (word_s if num == 1 else word_p)
    den_word = _int_to_es(den) + "avo" + ("s" if num > 1 else "")
    return num_word + " " + den_word


def _eur(int_str: str, dec_str) -> str:
    """€ amount → euros y céntimos spoken form."""
    e = int(int_str)
    c = int((dec_str + "0")[:2]) if dec_str else 0
    euro_part = ("un euro" if e == 1
                 else _int_to_es(e) + " euros" if e > 0
                 else "")
    cent_part = ("un céntimo" if c == 1
                 else _int_to_es(c) + " céntimos" if c > 0
                 else "")
    if euro_part and cent_part:
        return euro_part + " y " + cent_part
    return euro_part or cent_part or "cero euros"


def _ordinal_es(n: int) -> str:
    if n in _ORDINALS_ES:
        return _ORDINALS_ES[n]
    if n < 100:
        t, u = divmod(n, 10)
        base = _ORDINALS_ES.get(t * 10, _int_to_es(t * 10) + "avo")
        unit = _ORDINALS_ES.get(u, _ONES[u] + "avo") if u else ""
        return base + unit
    return _int_to_es(n) + "avo"


def _sci_to_es(base_str: str, exp_str: str, neg_exp: bool = False) -> str:
    e = int(exp_str)
    if neg_exp:
        denom = _int_to_es(10 ** e)
        num = (_decimal_to_es(base_str) if "." in base_str
               else _int_to_es(int(base_str)))
        return num + " partido por " + denom
    val = round(float(base_str) * (10 ** e))
    return _int_to_es(val)


def _time_es(h: int, m: int) -> str:
    article = "la" if h == 1 else "las"
    hour_word = "una" if h == 1 else _int_to_es(h)
    if m == 0:
        return f"{article} {hour_word}"
    min_word = "cuarto" if m == 15 else "media" if m == 30 else _int_to_es(m)
    return f"{article} {hour_word} y {min_word}"


# ---------------------------------------------------------------------------
# Pattern registry
# ---------------------------------------------------------------------------

def _build_patterns():
    p = []

    # 0. Thousands comma removal
    p.append((re.compile(r"(?<=\d),(?=\d{3})"), lambda m: ""))

    # 1. Abbreviations
    p.append((re.compile(r"\bDr\."), lambda m: "doctor"))
    p.append((re.compile(r"\bSra\."), lambda m: "señora"))
    p.append((re.compile(r"\bSr\."), lambda m: "señor"))
    p.append((re.compile(r"\bNo\.\s*(\d+)"), lambda m: "número " + _int_to_es(int(m.group(1)))))
    p.append((re.compile(r"\bvs\."), lambda m: "versus"))
    p.append((re.compile(r"\betc\."), lambda m: "et cétera"))

    # 2. Scientific notation (negative exponent first)
    p.append((
        re.compile(r"(\d+(?:\.\d+)?)[×x\*]10\^-(\d+)"),
        lambda m: _sci_to_es(m.group(1), m.group(2), neg_exp=True),
    ))
    p.append((
        re.compile(r"(\d+(?:\.\d+)?)[×x\*]10\^(\d+)"),
        lambda m: _sci_to_es(m.group(1), m.group(2)),
    ))
    p.append((
        re.compile(r"(\d+(?:\.\d+)?)[eE]-(\d+)"),
        lambda m: _sci_to_es(m.group(1), m.group(2), neg_exp=True),
    ))
    p.append((
        re.compile(r"(\d+(?:\.\d+)?)[eE]\+?(\d+)"),
        lambda m: _sci_to_es(m.group(1), m.group(2)),
    ))

    # 3. Version numbers: N.N.N… (3+ components)
    p.append((
        re.compile(r"\d+(?:\.\d+){2,}"),
        lambda m: " punto ".join(_int_to_es(int(p)) for p in m.group(0).split(".")),
    ))

    # 4. Temperature (before ordinals to avoid 5°C → quinto C)
    p.append((
        re.compile(r"(-?\d+(?:\.\d+)?)[°℃]([CF]?)"),
        lambda m: (
            ("menos " if m.group(1).startswith("-") else "")
            + (_decimal_to_es(m.group(1).lstrip("-")) if "." in m.group(1)
               else _int_to_es(abs(int(m.group(1)))))
            + " grado" + ("s" if abs(float(m.group(1))) != 1 else "")
            + (" Celsius" if m.group(2) in ("C", "℃", "") else " Fahrenheit")
        ),
    ))

    # 4b. Ordinals: N.º / Nº (U+00BA masculine ordinal indicator, distinct from ° degree U+00B0)
    p.append((
        re.compile(r"\b(\d+)\.?º"),
        lambda m: _ordinal_es(int(m.group(1))),
    ))

    # 5. Fractions
    p.append((
        re.compile(r"\b(\d+)/(\d+)\b"),
        lambda m: _fraction_es(int(m.group(1)), int(m.group(2))),
    ))

    # 6. Date: YYYY-MM-DD or YYYY/MM/DD
    p.append((
        re.compile(r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})"),
        lambda m: (
            _int_to_es(int(m.group(3))) + " de "
            + _MONTHS_ES[int(m.group(2))] + " de "
            + _int_to_es(int(m.group(1)))
        ),
    ))

    # 7. Time: HH:MM:SS
    p.append((
        re.compile(r"(\d{1,2}):(\d{2}):(\d{2})(?!\d)"),
        lambda m: (
            _time_es(int(m.group(1)), int(m.group(2)))
            + " y " + _int_to_es(int(m.group(3))) + " segundos"
        ),
    ))

    # 8. Time: HH:MM
    p.append((
        re.compile(r"(\d{1,2}):(\d{2})(?!\d)"),
        lambda m: _time_es(int(m.group(1)), int(m.group(2))),
    ))

    # 9. Speed: km/h
    p.append((
        re.compile(r"(\d+(?:\.\d+)?)km/h"),
        lambda m: (
            _decimal_to_es(m.group(1)) if "." in m.group(1)
            else _int_to_es(int(m.group(1)))
        ) + " kilómetros por hora",
    ))

    # 10. Percentage
    p.append((
        re.compile(r"(\d+(?:\.\d+)?)%"),
        lambda m: (
            _decimal_to_es(m.group(1)) if "." in m.group(1)
            else _int_to_es(int(m.group(1)))
        ) + " por ciento",
    ))

    # 11. Negative currency
    p.append((
        re.compile(r"-€(\d+(?:\.\d+)?)"),
        lambda m: "menos " + (
            _decimal_to_es(m.group(1)) if "." in m.group(1)
            else _int_to_es(int(m.group(1)))
        ) + " euros",
    ))
    p.append((
        re.compile(r"-\$(\d+(?:\.\d+)?)"),
        lambda m: "menos " + (
            _decimal_to_es(m.group(1)) if "." in m.group(1)
            else _int_to_es(int(m.group(1)))
        ) + " dólares",
    ))

    # 12. Currency — € with optional cents: €1.50 → un euro y cincuenta céntimos
    p.append((
        re.compile(r"€(\d+)(?:\.(\d{1,2}))?"),
        lambda m: _eur(m.group(1), m.group(2)),
    ))
    p.append((
        re.compile(r"\$(\d+(?:\.\d+)?)"),
        lambda m: (
            _decimal_to_es(m.group(1)) if "." in m.group(1)
            else _int_to_es(int(m.group(1)))
        ) + " dólar" + ("es" if float(m.group(1)) != 1 else ""),
    ))
    p.append((
        re.compile(r"£(\d+(?:\.\d+)?)"),
        lambda m: (
            _decimal_to_es(m.group(1)) if "." in m.group(1)
            else _int_to_es(int(m.group(1)))
        ) + " libra" + ("s" if float(m.group(1)) != 1 else ""),
    ))

    # 13. Units
    _unit_map_es = {
        "kg": "kilogramos", "g": "gramos", "mg": "miligramos",
        "km": "kilómetros", "m": "metros", "cm": "centímetros", "mm": "milímetros",
        "L": "litros", "ml": "mililitros", "mL": "mililitros",
        "kW": "kilovatios", "W": "vatios",
        "GHz": "gigahercios", "MHz": "megahercios", "kHz": "kilohercios", "Hz": "hercios",
    }
    unit_re_es = "|".join(re.escape(u) for u in sorted(_unit_map_es, key=len, reverse=True))

    p.append((
        re.compile(rf"-(\d+(?:\.\d+)?)({unit_re_es})\b"),
        lambda m, um=_unit_map_es: "menos " + (
            _decimal_to_es(m.group(1)) if "." in m.group(1)
            else _int_to_es(int(m.group(1)))
        ) + " " + um[m.group(2)],
    ))
    p.append((
        re.compile(rf"(\d+(?:\.\d+)?)({unit_re_es})\b"),
        lambda m, um=_unit_map_es: (
            _decimal_to_es(m.group(1)) if "." in m.group(1)
            else _int_to_es(int(m.group(1)))
        ) + " " + um[m.group(2)],
    ))

    # 15. Decimal
    p.append((
        re.compile(r"-?\d+\.\d+"),
        lambda m: ("menos " if m.group(0).startswith("-") else "")
                  + _decimal_to_es(m.group(0).lstrip("-")),
    ))

    # 16. Integer
    p.append((
        re.compile(r"-?\d+"),
        lambda m: ("menos " if m.group(0).startswith("-") else "")
                  + _int_to_es(abs(int(m.group(0)))),
    ))

    # 17. Symbols
    _sym_map = {
        "+": "más", "×": "por", "÷": "entre", "=": "igual a",
        "≈": "aproximadamente", "≠": "distinto de", "≤": "menor o igual que",
        "≥": "mayor o igual que", "<": "menor que", ">": "mayor que",
        "&": "y", "@": "arroba", "#": "número", "~": "aproximadamente",
    }
    sym_re = "[" + re.escape("".join(_sym_map.keys())) + "]"
    p.append((
        re.compile(sym_re),
        lambda m, sm=_sym_map: sm.get(m.group(0), m.group(0)),
    ))

    return p


_PATTERNS = _build_patterns()

_ENTITY_RE_ES = re.compile(
    r"https?://\S+"
    r"|`[^`]*`"
    r"|(?<![a-zA-Z\d])(?:[A-Z]{2,}-?\d+(?:\.\d+)*[a-z]?|[A-Z]-?\d{2,}(?:\.\d+)*[a-z]?)(?![A-Z\d])"
)
_SLOT_BASE_ES = 0xE000


def _make_slot_es(i: int) -> str:
    return "\x00S" + chr(_SLOT_BASE_ES + i) + "\x00"


_SLOT_RE_ES = re.compile(r"\x00S([\uE000-\uF8FF])\x00")
_CLEANUP_DECIMAL_ES = re.compile(r"\d+\.\d+")
_CLEANUP_INT_ES = re.compile(r"\d+")


class EsNormalizer(BaseNormalizer):
    def normalize(self, text: str) -> str:
        return self._apply(text)

    def normalize_token(self, token: str) -> str:
        return self._apply(token)

    def _apply(self, text: str) -> str:
        slots: list[str] = []

        def _protect(m: re.Match) -> str:
            slots.append(m.group(0))
            return _make_slot_es(len(slots) - 1)

        text = _ENTITY_RE_ES.sub(_protect, text)

        for pattern, handler in _PATTERNS:
            text = pattern.sub(handler, text)

        text = _SLOT_RE_ES.sub(lambda m: slots[ord(m.group(1)) - _SLOT_BASE_ES], text)

        # Insert spaces at letter↔digit boundaries
        text = re.sub(r"(?<=[a-zA-Z])(?=\d)", " ", text)
        text = re.sub(r"(?<=\d)(?=[a-zA-Z])", " ", text)

        text = _CLEANUP_DECIMAL_ES.sub(lambda m: _decimal_to_es(m.group(0)), text)
        text = _CLEANUP_INT_ES.sub(lambda m: _int_to_es(int(m.group(0))), text)

        return text
