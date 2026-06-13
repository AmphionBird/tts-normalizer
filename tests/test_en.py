"""Smoke tests for the English normalizer."""

import pytest
from tts_normalizer import Normalizer


@pytest.fixture
def en():
    return Normalizer(lang="en")


def test_integer(en):
    assert en.normalize("There are 42 apples") == "There are forty-two apples"


def test_decimal(en):
    assert en.normalize("Pi is 3.14") == "Pi is three point one four"


def test_ordinal(en):
    assert en.normalize("He finished 1st") == "He finished first"


def test_percentage(en):
    assert en.normalize("Success rate: 95%") == "Success rate: ninety-five percent"


def test_currency(en):
    assert en.normalize("Price: $10.50") == "Price: ten dollars and fifty cents"


def test_date(en):
    assert en.normalize("Date: 2026-04-13") == "Date: April thirteenth, twenty twenty six"


def test_time(en):
    assert en.normalize("Meeting at 10:30") == "Meeting at ten thirty"


def test_roman_cardinal_context(en):
    assert en.normalize("World War I") == "World War one"
    assert en.normalize("World War II") == "World War two"
    assert en.normalize("Chapter IV") == "Chapter four"
    assert en.normalize("Chapter V") == "Chapter five"


def test_roman_ordinal_context(en):
    assert en.normalize("Henry VIII") == "Henry eighth"
    assert en.normalize("Pope John Paul II") == "Pope John Paul second"


def test_range_expressions(en):
    assert en.normalize("Use 2-3 coats") == "Use two to three coats"
    assert en.normalize("The 1990-2000 period") == "The nineteen ninety to two thousand period"
    assert en.normalize("Expect 10%-20% growth") == "Expect ten to twenty percent growth"
    assert en.normalize("Open Mon-Fri") == "Open Monday to Friday"


def test_strict_whitelist(en):
    assert en.normalize("Mrs. Smith moved to Austin, TX") == "Missus Smith moved to Austin, Texas"
    assert en.normalize("Prof. Jones visited the U.K.") == "Professor Jones visited the U K"
    assert en.normalize("mrs. Smith") == "mrs. Smith"


def test_date_variants(en):
    assert en.normalize("2012.01.05") == "January fifth, twenty twelve"
    assert en.normalize("01/05/2012") == "January fifth, twenty twelve"
    assert en.normalize("25/07/2012") == "the twenty fifth of July twenty twelve"
    assert en.normalize("1H23 revenue") == "first half of twenty three revenue"
    assert en.normalize("3Q22 report") == "third quarter of twenty two report"
