"""English normalizer sampled against NeMo TN public test cases.

Source: https://github.com/NVIDIA/NeMo-text-processing (Apache-2.0)
Sampling: ~5-8 representative cases per token type, kept small per product req.

Style divergences from NeMo defaults are marked with # STYLE.
NeMo uses British "and" in cardinals, "minus" for negatives, no hyphens in
compounds, and drops "and" in money amounts. We use American style.
These are NOT bugs — they reflect intentional style choices.
"""

import pytest
from tts_normalizer import Normalizer


@pytest.fixture
def en():
    return Normalizer(lang="en")


# ---------------------------------------------------------------------------
# Cardinals
# ---------------------------------------------------------------------------
class TestCardinals:
    def test_thirteen_thousand(self, en):
        assert en.normalize("13,000") == "thirteen thousand"

    def test_simple(self, en):
        assert en.normalize("3") == "three"

    def test_negative(self, en):
        # STYLE: NeMo → "minus two", we → "negative two"
        assert en.normalize("-2") == "negative two"

    def test_large(self, en):
        assert en.normalize("1000000") == "one million"

    def test_compound(self, en):
        # STYLE: NeMo → "one hundred and twenty three", we → "one hundred twenty-three"
        assert en.normalize("123") == "one hundred twenty-three"


# ---------------------------------------------------------------------------
# Ordinals
# ---------------------------------------------------------------------------
class TestOrdinals:
    def test_1st(self, en):
        assert en.normalize("1st") == "first"

    def test_1000th(self, en):
        assert en.normalize("1000th") == "one thousandth"

    def test_23rd(self, en):
        # STYLE: NeMo → "twenty third", we → "twenty-third"
        assert en.normalize("23rd") == "twenty-third"

    def test_2nd(self, en):
        assert en.normalize("2nd") == "second"


# ---------------------------------------------------------------------------
# Decimals
# ---------------------------------------------------------------------------
class TestDecimals:
    def test_two_point_zero(self, en):
        assert en.normalize("2.0") == "two point zero"

    def test_pi(self, en):
        assert en.normalize("3.14") == "three point one four"

    def test_negative_decimal(self, en):
        # STYLE: NeMo → "minus one point five", we → "negative one point five"
        assert en.normalize("-1.5") == "negative one point five"


# ---------------------------------------------------------------------------
# Time
# ---------------------------------------------------------------------------
class TestTime:
    def test_on_the_hour(self, en):
        assert en.normalize("01:00") == "one o'clock"

    def test_half_past(self, en):
        assert en.normalize("10:30") == "ten thirty"

    def test_oh_five(self, en):
        assert en.normalize("3:05") == "three oh five"

    def test_midnight_hour(self, en):
        assert en.normalize("23:00") == "twenty three o'clock"


# ---------------------------------------------------------------------------
# Money
# ---------------------------------------------------------------------------
class TestMoney:
    def test_whole_dollars(self, en):
        assert en.normalize("$2") == "two dollars"

    def test_dollars_and_cents(self, en):
        # STYLE: NeMo → "twenty dollars fifty cents", we → "twenty dollars and fifty cents"
        assert en.normalize("$20.50") == "twenty dollars and fifty cents"

    def test_one_dollar(self, en):
        assert en.normalize("$1") == "one dollar"

    def test_gbp(self, en):
        assert en.normalize("£10") == "ten pounds"


# ---------------------------------------------------------------------------
# Telephone
# ---------------------------------------------------------------------------
class TestTelephone:
    def test_with_country_code(self, en):
        assert en.normalize("1-800-555-1234") == "one eight hundred five five five one two three four"

    def test_bare_local(self, en):
        # Bug fix: was parsed as arithmetic before
        assert en.normalize("650-451-1234") == "six five zero four five one one two three four"

    def test_bare_local_2(self, en):
        assert en.normalize("212-867-5309") == "two one two eight six seven five three zero nine"


# ---------------------------------------------------------------------------
# Measure / Units
# ---------------------------------------------------------------------------
class TestMeasure:
    def test_kilograms(self, en):
        assert en.normalize("12kg") == "twelve kilograms"

    def test_celsius(self, en):
        assert en.normalize("2°C") == "two degrees Celsius"

    def test_km_per_h(self, en):
        assert en.normalize("100km/h") == "one hundred kilometers per hour"

    def test_centimeters(self, en):
        assert en.normalize("5cm") == "five centimeters"


# ---------------------------------------------------------------------------
# Fractions
# ---------------------------------------------------------------------------
class TestFractions:
    def test_quarter(self, en):
        assert en.normalize("1/4") == "one quarter"

    def test_half(self, en):
        assert en.normalize("1/2") == "one half"

    def test_three_quarters(self, en):
        assert en.normalize("3/4") == "three quarters"

    def test_two_fifths(self, en):
        assert en.normalize("2/5") == "two fifths"


# ---------------------------------------------------------------------------
# Decades (bug fix regression)
# ---------------------------------------------------------------------------
class TestDecades:
    def test_1980s(self, en):
        assert en.normalize("1980s") == "nineteen eighties"

    def test_1990s(self, en):
        assert en.normalize("1990s") == "nineteen nineties"

    def test_1920s(self, en):
        assert en.normalize("1920s") == "nineteen twenties"

    def test_2000s(self, en):
        assert en.normalize("2000s") == "two thousands"

    def test_1970s(self, en):
        assert en.normalize("1970s") == "nineteen seventies"

    def test_1950s(self, en):
        assert en.normalize("1950s") == "nineteen fifties"

    def test_2010s(self, en):
        # Bug fix: _TENS[1] is empty → was "twenty ies" before fix
        assert en.normalize("2010s") == "twenty tens"


# ---------------------------------------------------------------------------
# Extended cardinals
# ---------------------------------------------------------------------------
class TestCardinalsExtended:
    def test_zero(self, en):
        assert en.normalize("0") == "zero"

    def test_hundred(self, en):
        assert en.normalize("100") == "one hundred"

    def test_thousand(self, en):
        assert en.normalize("1000") == "one thousand"

    def test_million(self, en):
        assert en.normalize("1,234,567") == "one million two hundred thirty-four thousand five hundred sixty-seven"

    def test_negative_large(self, en):
        assert en.normalize("-100") == "negative one hundred"


# ---------------------------------------------------------------------------
# Extended ordinals
# ---------------------------------------------------------------------------
class TestOrdinalsExtended:
    def test_5th(self, en):
        assert en.normalize("5th") == "fifth"

    def test_11th(self, en):
        assert en.normalize("11th") == "eleventh"

    def test_12th(self, en):
        assert en.normalize("12th") == "twelfth"

    def test_21st(self, en):
        assert en.normalize("21st") == "twenty-first"

    def test_100th(self, en):
        assert en.normalize("100th") == "one hundredth"


# ---------------------------------------------------------------------------
# Extended decimals
# ---------------------------------------------------------------------------
class TestDecimalsExtended:
    def test_zero_point_five(self, en):
        assert en.normalize("0.5") == "zero point five"

    def test_leading_zeros_in_frac(self, en):
        assert en.normalize("1.005") == "one point zero zero five"

    def test_negative_pi(self, en):
        # STYLE: NeMo → "minus three point one four"
        assert en.normalize("-3.14") == "negative three point one four"


# ---------------------------------------------------------------------------
# Extended time
# ---------------------------------------------------------------------------
class TestTimeExtended:
    def test_noon(self, en):
        assert en.normalize("12:00") == "twelve o'clock"

    def test_zero_thirty(self, en):
        assert en.normalize("00:30") == "zero thirty"

    def test_oh_five_bare(self, en):
        assert en.normalize("9:05") == "nine oh five"


# ---------------------------------------------------------------------------
# Extended money
# ---------------------------------------------------------------------------
class TestMoneyExtended:
    def test_cents_only(self, en):
        assert en.normalize("$0.50") == "fifty cents"

    def test_hundred_dollars(self, en):
        assert en.normalize("$100") == "one hundred dollars"

    def test_negative_dollars(self, en):
        # STYLE: NeMo → "minus fifty dollars"
        assert en.normalize("-$50") == "negative fifty dollars"

    def test_gbp_whole(self, en):
        assert en.normalize("£50") == "fifty pounds"


# ---------------------------------------------------------------------------
# Extended measure
# ---------------------------------------------------------------------------
class TestMeasureExtended:
    def test_negative_celsius(self, en):
        assert en.normalize("-10°C") == "negative ten degrees Celsius"

    def test_fahrenheit(self, en):
        assert en.normalize("37°F") == "thirty-seven degrees Fahrenheit"

    def test_milliliters(self, en):
        assert en.normalize("50ml") == "fifty milliliters"

    def test_liters_decimal(self, en):
        assert en.normalize("1.5L") == "one point five liters"

    def test_watts(self, en):
        assert en.normalize("100W") == "one hundred watts"

    def test_speed(self, en):
        assert en.normalize("120km/h") == "one hundred twenty kilometers per hour"

    # Imperial / US units (regression lock for 2026-05-27 additions)
    def test_feet(self, en):
        assert en.normalize("6ft") == "six feet"

    def test_feet_space(self, en):
        assert en.normalize("6 ft") == "six feet"

    def test_inches(self, en):
        assert en.normalize("12in") == "twelve inches"

    def test_pounds_weight(self, en):
        assert en.normalize("3lbs") == "three pounds"

    def test_ounces(self, en):
        assert en.normalize("10oz") == "ten ounces"

    def test_miles(self, en):
        assert en.normalize("5mi") == "five miles"

    def test_yards(self, en):
        assert en.normalize("10yd") == "ten yards"

    def test_mph_attached(self, en):
        assert en.normalize("50mph") == "fifty miles per hour"

    def test_mph_space(self, en):
        assert en.normalize("60 mph") == "sixty miles per hour"

    def test_hertz(self, en):
        assert en.normalize("100Hz") == "one hundred hertz"

    def test_kilohertz(self, en):
        assert en.normalize("5kHz") == "five kilohertz"

    def test_megahertz(self, en):
        assert en.normalize("2.4 GHz") == "two point four gigahertz"

    def test_megabytes(self, en):
        assert en.normalize("512MB") == "five hundred twelve megabytes"

    def test_gigabytes(self, en):
        assert en.normalize("2GB") == "two gigabytes"

    def test_terabytes(self, en):
        assert en.normalize("1TB") == "one terabytes"

    def test_milliseconds(self, en):
        assert en.normalize("10ms") == "ten milliseconds"

    def test_psi(self, en):
        assert en.normalize("100psi") == "one hundred pounds per square inch"


# ---------------------------------------------------------------------------
# Extended fractions
# ---------------------------------------------------------------------------
class TestFractionsExtended:
    def test_third(self, en):
        assert en.normalize("1/3") == "one third"

    def test_three_eighths(self, en):
        assert en.normalize("3/8") == "three eighths"

    def test_two_sevenths(self, en):
        assert en.normalize("2/7") == "two sevenths"

    def test_one_tenth(self, en):
        assert en.normalize("1/10") == "one tenth"


# ---------------------------------------------------------------------------
# Dates
# ---------------------------------------------------------------------------
class TestDates:
    def test_text_format(self, en):
        assert en.normalize("January 5, 2026") == "January fifth, twenty twenty six"

    def test_text_format_1999(self, en):
        assert en.normalize("March 15, 1999") == "March fifteenth, nineteen ninety nine"


# ---------------------------------------------------------------------------
# Abbreviations
# ---------------------------------------------------------------------------
class TestAbbreviations:
    def test_number(self, en):
        assert en.normalize("No. 42") == "Number forty two"

    def test_doctor(self, en):
        assert en.normalize("Dr. Smith") == "Doctor Smith"


# ---------------------------------------------------------------------------
# Misc
# ---------------------------------------------------------------------------
class TestMisc:
    def test_percentage_decimal(self, en):
        assert en.normalize("2.5%") == "two point five percent"

    def test_year_eleven_hundred(self, en):
        assert en.normalize("1100") == "eleven hundred"
