"""Smoke tests for the Chinese normalizer."""

import pytest
from tts_normalizer import Normalizer


@pytest.fixture
def zh():
    return Normalizer(lang="zh")


def test_integer(zh):
    assert zh.normalize("今天来了100人") == "今天来了一百人"


def test_decimal(zh):
    assert zh.normalize("气温10.5度") == "气温十点五度"


def test_decimal_date_ambiguity(zh):
    # Without date context, 10.11 should read as decimal
    assert zh.normalize("版本号10.11") == "版本号十点一一"


def test_date_iso(zh):
    # Leading zeros stripped in date context — 04月 reads "四月" not "零四月"
    assert zh.normalize("2026-04-13") == "二零二六年四月十三日"


def test_date_slash(zh):
    assert zh.normalize("2026/04/13") == "二零二六年四月十三日"


def test_time_hhmm(zh):
    assert zh.normalize("10:30") == "十点三十分"


def test_percentage(zh):
    assert zh.normalize("完成率80%") == "完成率百分之八十"


def test_currency_cny(zh):
    assert zh.normalize("售价¥199") == "售价一百九十九元"


def test_currency_usd(zh):
    assert zh.normalize("售价$50") == "售价五十美元"


def test_negative(zh):
    assert zh.normalize("温度-10度") == "温度负十度"


def test_negative_measure(zh):
    assert zh.normalize("海拔-100米") == "海拔负一百米"


def test_fraction(zh):
    assert zh.normalize("3/4的概率") == "四分之三的概率"


def test_twenty_four_seven_not_fraction(zh):
    assert zh.normalize("24/7服务") == "二十四小时七天服务"


def test_unit_kg(zh):
    assert zh.normalize("重量50kg") == "重量五十千克"


def test_km_per_hour_spelled_denominator(zh):
    assert zh.normalize("限速100km/hour") == "限速每小时一百千米"


def test_km_per_hour_with_spaces(zh):
    assert zh.normalize("限速100 km / h") == "限速每小时一百千米"


def test_metric_acceleration(zh):
    assert zh.normalize("重力9.8 m/s²") == "重力每平方秒九点八米"


def test_fuel_consumption(zh):
    assert zh.normalize("油耗5 L/100km") == "油耗每一百千米五升"


def test_medical_concentration(zh):
    assert zh.normalize("血糖90 mg/dL") == "血糖每分升九十毫克"


def test_usd_per_weight(zh):
    assert zh.normalize("价格$5/kg") == "价格每千克五美元"


def test_year_standalone(zh):
    assert zh.normalize("2026年") == "二零二六年"


def test_pinyin_tone_tokens_are_preserved(zh):
    assert zh.normalize("脏读作zang4，藏读作CANG2，再读作zai3") == "脏读作zang4，藏读作CANG2，再读作zai3"


def test_non_pinyin_letter_digit_tokens_are_not_preserved(zh):
    assert zh.normalize("A4纸，v2.3.1正式发布") == "A四纸，v二点三点一正式发布"


def test_pinyin_tone_digit_must_be_one_to_five(zh):
    assert zh.normalize("zang6不是拼音声调token") == "zang六不是拼音声调token"
