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
    assert en.normalize("Date: 2026-04-13") == "Date: April thirteenth, twenty twenty-six"


def test_time(en):
    assert en.normalize("Meeting at 10:30") == "Meeting at ten thirty"
