"""Smoke tests for the Japanese normalizer."""

import pytest
from tts_normalizer import Normalizer


@pytest.fixture
def ja():
    return Normalizer(lang="ja")


def test_date_slash_not_fraction(ja):
    assert ja.normalize("2026/04/13") == "二〇二六年四月十三日"


def test_fraction(ja):
    assert ja.normalize("3/4") == "四分の三"


def test_twenty_four_seven_not_fraction(ja):
    assert ja.normalize("24/7") == "二十四時間年中無休"


def test_km_per_hour_spelled_denominator(ja):
    assert ja.normalize("100km/hour") == "時速百キロメートル"


def test_km_per_hour_with_spaces(ja):
    assert ja.normalize("100 km / h") == "時速百キロメートル"


def test_metric_acceleration(ja):
    assert ja.normalize("9.8 m/s²") == "一秒の二乗あたり九点八メートル"


def test_fuel_consumption(ja):
    assert ja.normalize("5 L/100km") == "百キロメートルあたり五リットル"


def test_medical_concentration(ja):
    assert ja.normalize("90 mg/dL") == "一デシリットルあたり九十ミリグラム"


def test_usd_per_weight(ja):
    assert ja.normalize("$5/kg") == "一キログラムあたり五ドル"
