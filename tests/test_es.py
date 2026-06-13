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


def test_roman_contexts(es):
    assert es.normalize("siglo XXI") == "siglo veintiuno"
    assert es.normalize("capítulo IV") == "capítulo cuatro"
    assert es.normalize("Felipe VI") == "Felipe sexto"


def test_strict_whitelist_es(es):
    assert es.normalize("Dra. García vive en EE. UU.") == "doctora García vive en Estados Unidos"
    assert es.normalize("dra. García") == "dra. García"


def test_date_variants_es(es):
    assert es.normalize("2012.01.05") == "cinco de enero de dos mil doce"
    assert es.normalize("25/07/2012") == "veinticinco de julio de dos mil doce"
    assert es.normalize("1H23 ingresos") == "primer semestre de veintitrés ingresos"
    assert es.normalize("3Q22 informe") == "tercer trimestre de veintidós informe"


def test_range_variants_es(es):
    assert es.normalize("lunes-viernes") == "lunes a viernes"
    assert es.normalize("2-3 muestras") == "dos a tres muestras"
    assert es.normalize("10%-20%") == "diez a veinte por ciento"
    assert es.normalize("5-10kg") == "cinco a diez kilogramos"
