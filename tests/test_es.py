"""Smoke tests for the Spanish normalizer."""

import pytest
from tts_normalizer import Normalizer


@pytest.fixture
def es():
    return Normalizer(lang="es")


def test_date_slash_not_fraction(es):
    assert es.normalize("2026/04/13") == "trece de abril de dos mil veintiséis"


def test_fraction(es):
    assert es.normalize("3/4") == "tres cuartos"


def test_twenty_four_seven_not_fraction(es):
    assert es.normalize("24/7") == "veinticuatro siete"


def test_km_per_hour_spelled_denominator(es):
    assert es.normalize("100km/hour") == "cien kilómetros por hora"


def test_km_per_hour_with_spaces(es):
    assert es.normalize("100 km / h") == "cien kilómetros por hora"


def test_metric_acceleration(es):
    assert es.normalize("9.8 m/s²") == "nueve coma ocho metros por segundo cuadrado"


def test_fuel_consumption(es):
    assert es.normalize("5 L/100km") == "cinco litros por cien kilómetros"


def test_medical_concentration(es):
    assert es.normalize("90 mg/dL") == "noventa miligramos por decilitro"


def test_usd_per_weight(es):
    assert es.normalize("$5/kg") == "cinco dólares por kilogramo"
