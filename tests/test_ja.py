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


def test_ascii_roman_contexts(ja):
    assert ja.normalize("第IV章") == "第四章"
    assert ja.normalize("II型糖尿病") == "二型糖尿病"


def test_strict_whitelist_ja(ja):
    assert ja.normalize("Dr.山田が来た") == "ドクター山田が来た"
    assert ja.normalize("dr.山田が来た") == "dr.山田が来た"


def test_date_variants_ja(ja):
    assert ja.normalize("2026.04.13") == "二〇二六年四月十三日"
    assert ja.normalize("04/13/2026") == "二〇二六年四月十三日"
    assert ja.normalize("13/04/2026") == "二〇二六年四月十三日"
    assert ja.normalize("1H23業績") == "二〇二三年上半期業績"
    assert ja.normalize("3Q22レポート") == "二〇二二年第三四半期レポート"


def test_range_variants_ja(ja):
    assert ja.normalize("月-金営業") == "月曜日から金曜日営業"
    assert ja.normalize("2-3個") == "二から三個"
    assert ja.normalize("成長10%-20%") == "成長十から二十パーセント"
    assert ja.normalize("1990-2000年") == "一九九〇から二〇〇〇年"
