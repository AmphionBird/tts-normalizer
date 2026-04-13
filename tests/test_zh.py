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


def test_fraction(zh):
    assert zh.normalize("3/4的概率") == "四分之三的概率"


def test_unit_kg(zh):
    assert zh.normalize("重量50kg") == "重量五十千克"


def test_year_standalone(zh):
    assert zh.normalize("2026年") == "二零二六年"
